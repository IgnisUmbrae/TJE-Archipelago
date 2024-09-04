import struct
from typing import TYPE_CHECKING, Any, Callable, Optional
from enum import Enum

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from .constants import DEBUG, EMPTY_SHIP_PIECE, EMPTY_ITEM, SHIP_PIECE, RANK_NAMES, RAM_ADDRS, \
                       TJ_GHOST_SPRITES, TJ_SWIMMING_SPRITES, TOEJAM_STATE_LOAD_DOWN, ELEVATOR_LOCKED, \
                       ELEVATOR_UNLOCKED, END_ELEVATOR_UNLOCKED_STATES
from .items import PRESENT_IDS, EDIBLE_IDS, SHIP_PIECE_IDS, KEY_IDS, ITEM_ID_TO_CODE
from .locations import FLOOR_ITEM_LOC_TEMPLATE, RANK_LOC_TEMPLATE, SHIP_PIECE_LOC_TEMPLATE
from .options import TJEOptions

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

#region State constants & state groups

class TJEGameState(Enum):
    MAIN_MENU = 0
    NORMAL = 1
    IN_INVENTORY = 2
    IN_AIR = 3
    IN_WATER = 4
    IN_ELEVATOR = 5
    ARRIVED = 6
    TRAVELLING_DOWN = 7
    UNFALLING = 8
    GHOST = 9

LOADING_STATES = [TJEGameState.IN_ELEVATOR, TJEGameState.TRAVELLING_DOWN]
LOADING_STATES_STRICT = LOADING_STATES + [TJEGameState.UNFALLING]

SPAWN_BLOCKING_STATES = LOADING_STATES_STRICT + [TJEGameState.IN_AIR, TJEGameState.IN_WATER,
                                          TJEGameState.GHOST, TJEGameState.MAIN_MENU]

#endregion

class AddressMonitor():
    def __init__(self, name: str, address_fn: Callable, size: int, enable_test_fn: Callable, on_trigger_fn: Callable,
                 parent: "TJEGameController", ctx : "BizHawkClientContext", enabled=False):
        self.name = name
        self.parent = parent
        self.on_trigger = on_trigger_fn
        self.ctx = ctx

        self.old_data, self.new_data = None, None

        self.enable_test = enable_test_fn
        self.enabled = enabled
        if DEBUG: print("{} monitoring {}".format(self.name, "enabled" if self.enabled else "disabled"))

        self.address = None
        self.address_fn = address_fn
        self.size = size

    def reset_data(self):
        self.old_data, self.new_data = None, None

    def check_enabledness(self):
        new_state = self.enable_test()
        if DEBUG:
            if self.enabled != new_state:
                print("{} monitoring {}".format(self.name, "enabled" if new_state else "disabled"))
        self.enabled = new_state
        if not self.enabled:
            self.reset_data()

    async def tick(self):
        self.check_enabledness()
        if self.enabled:
            self.address = self.address_fn()
            self.old_data = self.new_data

            self.new_data = await self.parent.peek_ram(self.ctx, self.address, self.size)

            if self.old_data is not None and self.new_data is not None and self.old_data != self.new_data:
                await self.trigger()

    async def trigger(self):
        await self.on_trigger(self.ctx, self.old_data, self.new_data)

class TJEGameController():
    def __init__(self, client: "BizHawkClient"):
        self.client = client
        self.reset_game()

    #region Per-update high-level logic functions

    async def tick(self, ctx: "BizHawkClientContext"):
        if not self.game_complete:
            await self.floor_item_monitor.tick()
            await self.ship_item_monitor.tick()
            await self.rank_monitor.tick()
            await self.level_monitor.tick()
            
            await self.update_game_state(ctx)

            if self.is_playing:
                await self.update_elevator_lock_state(ctx)

    #endregion

    #region Initialization functions

    def add_monitors(self, ctx : "BizHawkClientContext"):
        self.floor_item_monitor = AddressMonitor(
            "Floor item",
            self.current_collected_items_addr,
            4,
            lambda: not self.is_loading_state_strict() and not self.is_on_menu(),
            self.handle_floor_item_change,
            self,
            ctx
        )

        self.ship_item_monitor = AddressMonitor(
            "Ship item",
            lambda: self.earthling_to_ram_address(1),
            1,
            lambda: not self.is_on_menu() and self.is_ship_piece_level() and not self.is_loading_state_strict(),
            self.handle_ship_item_change,
            self,
            ctx
        )

        self.rank_monitor = AddressMonitor(
            "Rank",
            lambda: RAM_ADDRS.TJ_RANK,
            1,
            lambda: not self.is_on_menu(),# and not self.is_loading_state(),
            self.handle_rank_change,
            self,
            ctx
        )

        self.level_monitor = AddressMonitor(
            "Level",
            lambda: RAM_ADDRS.TJ_LEVEL,
            1,
            lambda: True,
            self.handle_level_change,
            self,
            ctx,
            enabled=True
        )

    def handle_slot_data(self, slot_data : dict[str, Any]):
        if DEBUG: print("Got slot data!")
        self.ship_piece_levels = slot_data["ship_piece_levels"]
        self.key_levels = slot_data["key_levels"]
        self.prog_keys = slot_data["prog_keys"]
        self.starting_presents = slot_data["starting_presents"]
        self.strict_level_25 = slot_data["strict_level_25"]

    def reset_game(self):
        if DEBUG: print("Resetting game…")
        # Game state–related

        self.game_state: TJEGameState = TJEGameState.MAIN_MENU
        self.is_playing: bool = False
        self.game_complete: bool = False

        self.current_level = 0

        # Ship piece–related

        self.ship_piece_levels, self.collected_ship_piece_levels = [], []

        self.num_ship_pieces_owned = 0

        # Key-related

        self.key_levels: Optional[list[int]] = None
        self.unlocked_levels: list[int] = []

        # Present-related

        self.starting_presents = []

    async def load_saved_game_state(self, ctx) -> None:
        try:
            # Patch in an empty list of collected ship pieces so we don't win instantly
            # TO DO: In future this should patch in the pieces we actually have
            await self.poke_ram(ctx, RAM_ADDRS.SHIP_PIECES_COLLECTED_START, EMPTY_SHIP_PIECE*10)
        except bizhawk.RequestFailedError:
            pass

    # Initialization that cannot be done on the title screen (e.g. identifying starting presents)
    async def level_one_initialization(self, ctx) -> None:
        for present in self.starting_presents:
            await self.identify_present(ctx, present)

    #endregion

    #region Helper functions

    async def poke_ram(self, ctx: "BizHawkClientContext", address: int, value: bytes) -> bool:
        try:
            await bizhawk.write(ctx.bizhawk_ctx, [(address, value, "68K RAM")])
            return True
        except bizhawk.RequestFailedError:
            return False

    async def peek_ram(self, ctx: "BizHawkClientContext", address: int, size: int) -> Optional[bytes]:
        try:
            return (await bizhawk.read(ctx.bizhawk_ctx, [(address, size, "68K RAM")]))[0]
        except bizhawk.RequestFailedError:
            return None

    # Valid levels: 0–25
    def level_to_collected_items_address(self, level : int) -> Optional[int]:
        if level < 0 or level > 25: return None
        else: return RAM_ADDRS.COLLECTED_ITEMS_START + level * 4

    # Valid slots: 0–31
    def floor_item_slot_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 31: return None
        else: return RAM_ADDRS.FLOOR_ITEM_START + slot * 8

    # Valid slots: 0–15
    def inventory_slot_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 15: return None
        else: return RAM_ADDRS.INVENTORY_START + slot

    # Valid slots: 0–31
    def dropped_present_slot_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 31: return None
        else: return RAM_ADDRS.DROPPED_PRESENTS_START + slot * 8

    # Valid slots: 0–28
    def earthling_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 28: return None
        else: return RAM_ADDRS.EARTHLINGS_START + slot*18

    # Valid items: 0–9
    def triggered_ship_item_to_ram_address(self, item: int) -> Optional[int]:
        if item < 0 or item > 9: return None
        else: return RAM_ADDRS.SHIP_ITEMS_TRIGGERED_START + item

    # Valid pieces: 0–9
    def collected_ship_piece_to_ram_address(self, piece: int) -> Optional[int]:
        if piece < 0 or piece > 9: return None
        else: return RAM_ADDRS.SHIP_PIECES_COLLECTED_START + piece

    # Valid presents: 0x00–0x1B
    def present_to_identified_ram_address(self, present: int) -> Optional[int]:
        if present < 0x00 or present > 0x1B: return None
        else: return RAM_ADDRS.PRESENTS_IDENTIFIED_START + present * 2

    async def get_first_empty_inv_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:    
        current_inventory = await self.peek_ram(ctx, RAM_ADDRS.INVENTORY_START, 16)
        if current_inventory:
            split_inventory = [current_inventory[i:i+1] for i in range(len(current_inventory))]
            
            try: return split_inventory.index(EMPTY_ITEM)
            except ValueError: return None
        else:
            return None
    
    async def get_first_empty_dropped_present_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        dropped_presents_table = await self.peek_ram(ctx, RAM_ADDRS.DROPPED_PRESENTS_START, 256)
        if dropped_presents_table:
            dropped_present_types = [dropped_presents_table[i:i+8][0:1]
                                     for i in range(0, len(dropped_presents_table), 8)]
            try: return dropped_present_types.index(EMPTY_ITEM)
            except ValueError: return None
        else:
            return None
        
    async def get_empty_floor_item_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        floor_item_table = await self.peek_ram(ctx, RAM_ADDRS.FLOOR_ITEM_START, 256)
        if floor_item_table:
            floor_item_types = [floor_item_table[i:i+8][0:1]
                                for i in range(0, len(floor_item_table), 8)]
            try: return floor_item_types.index(EMPTY_ITEM)
            except ValueError: return None
        else:
            return None

    #endregion

    #region Spawning functions (also receipt of ethereal items)

    def receive_key(self, key_id: int) -> None:
        if DEBUG:
            print("Got a key!")
            print(f"Key levels: {self.key_levels}")
            print(f"Unlocked levels: {self.unlocked_levels}")
        if self.prog_keys:
            num_keys = len(self.unlocked_levels)
            print(f"Unlocking level {self.key_levels[num_keys]}")
            try:
                level = self.key_levels[num_keys]
            except KeyError:
                level = None
        else:
            level = KEY_IDS.index(key_id) + 2

        if level is not None:
            self.unlocked_levels.append(level)

    async def spawn_item(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if self.is_playing:
            if item_id in PRESENT_IDS:
                if self.game_state != TJEGameState.IN_INVENTORY:
                    success = await self.spawn_in_inventory(ctx, item_id)
                    if success:
                        await self.identify_present(ctx, item_id)
                else:
                    success = False
            elif item_id in EDIBLE_IDS:
                success = await self.spawn_on_floor(ctx, item_id)
            elif item_id in SHIP_PIECE_IDS:
                success = await self.award_ship_piece(ctx, item_id)
            else:
                success = False
            return success
        return False

    async def identify_present(self, ctx: "BizHawkClientContext", present_id: int) -> bool:
        present = ITEM_ID_TO_CODE[present_id]
        await self.poke_ram(ctx, self.present_to_identified_ram_address(present), b"\x01")
        return True

    async def award_ship_piece(self, ctx: "BizHawkClientContext", ship_piece_id: int) -> bool:
        slot = SHIP_PIECE_IDS.index(ship_piece_id)
        await self.poke_ram(ctx, self.collected_ship_piece_to_ram_address(slot), SHIP_PIECE)
        self.num_ship_pieces_owned += 1
        return True

    # Spawns any standard floor item at TJ's current position
    # Normally only used to spawn edibles; presents go directly into inventory
    async def spawn_on_floor(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if self.game_state not in SPAWN_BLOCKING_STATES:
            slot = await self.get_empty_floor_item_slot(ctx)
            if slot is not None and self.current_level is not None:
                toejam_position = await self.peek_ram(ctx, RAM_ADDRS.TJ_POSITION, 4)
                await self.poke_ram(ctx, self.floor_item_slot_to_ram_address(slot),
                    struct.pack(">BBBB", ITEM_ID_TO_CODE[item_id], self.current_level, 0, 0) + toejam_position)
                return True
            else:
                return False
        else:
            return False

    # Spawns a present in TJ's inventory
    async def spawn_in_inventory(self, ctx: "BizHawkClientContext", pres_id: int) -> bool:
        slot = await self.get_first_empty_inv_slot(ctx)
        if slot is not None:
            await self.poke_ram(ctx, self.inventory_slot_to_ram_address(slot), ITEM_ID_TO_CODE[pres_id].to_bytes(1))
            return True
        else:
            return (await self.spawn_present_as_dropped(ctx, pres_id))

    async def spawn_present_as_dropped(self, ctx: "BizHawkClientContext", pres_id: int) -> bool:
        if self.game_state not in SPAWN_BLOCKING_STATES:
            slot = await self.get_first_empty_dropped_present_slot(ctx)
            if slot is not None and self.current_level is not None:
                toejam_position = await self.peek_ram(ctx, RAM_ADDRS.TJ_POSITION, 4)
                success = await self.poke_ram(ctx, self.dropped_present_slot_to_ram_address(slot),
                    struct.pack(">BBBB", ITEM_ID_TO_CODE[pres_id], self.current_level, 0, 0) + toejam_position)
                return success
            else:
                return False
        else:
            return False

    #endregion

    #region Change handling & monitor-related functions

    def is_on_menu(self) -> bool:
        return (self.game_state == TJEGameState.MAIN_MENU)
    
    def is_ship_piece_level(self) -> bool:
        return (self.current_level in self.ship_piece_levels and
                self.current_level not in self.collected_ship_piece_levels)

    def is_loading_state(self) -> bool:
        return (self.game_state in LOADING_STATES)

    def is_loading_state_strict(self) -> bool:
        return (self.game_state in LOADING_STATES_STRICT)

    def current_collected_items_addr(self):
        return self.level_to_collected_items_address(self.current_level)

    async def handle_level_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        self.current_level, previous_level = int.from_bytes(new_data), int.from_bytes(old_data)
        if DEBUG: print(f"Level changed to {self.current_level}")
        # TO DO: ensure proper detection here
        if self.current_level == 1 and self.game_state == TJEGameState.MAIN_MENU:
            if DEBUG: print("Performing Level 1 initialization")
            await self.level_one_initialization(ctx)
            await self.load_saved_game_state(ctx)

    async def handle_floor_item_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        changes = int.from_bytes(new_data) ^ int.from_bytes(old_data)
        changed_indices = [31-i for i in range(changes.bit_length()) if changes & (1 << i)]

        for index in changed_indices:
            await self.client.trigger_location(ctx, FLOOR_ITEM_LOC_TEMPLATE.format(self.current_level, index+1))

    async def handle_ship_item_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        if (old_data, new_data) == (SHIP_PIECE, EMPTY_SHIP_PIECE):
            success = await self.client.trigger_location(ctx, SHIP_PIECE_LOC_TEMPLATE.format(self.current_level))
            if success:
                # Mark it as collected in the game (will be moved into ROM later)
                slot = self.ship_piece_levels.index(self.current_level)
                await self.poke_ram(ctx, self.triggered_ship_item_to_ram_address(slot), b"\x00")
                # And in the game state here
                self.collected_ship_piece_levels.append(self.current_level)

    async def handle_rank_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        rank = int.from_bytes(new_data)
        if rank > 0:
            loc = RANK_LOC_TEMPLATE.format(RANK_NAMES[rank-1])
            await self.client.trigger_location(ctx, loc)

    #endregion

    #region Game state update functions

    async def alter_current_elevator(self, ctx: "BizHawkClientContext", lock: bool) -> None:
        if DEBUG:
            if lock:
                print(f"Locking level {self.current_level}")
            else:
                print(f"Unlocking level {self.current_level}")
        await self.poke_ram(ctx, RAM_ADDRS.END_ELEVATOR_STATE, ELEVATOR_LOCKED if lock else ELEVATOR_UNLOCKED)

    def should_be_unlocked(self) -> bool:
        if self.current_level in [0,1]:
            return True

        if self.key_levels is not None:
            # Not a key level, or already unlocked
            key_check = (self.current_level not in self.key_levels or self.current_level in self.unlocked_levels)
        else:
            key_check = True

        if self.current_level == 24 and self.strict_level_25:
            level25_check = (self.num_ship_pieces_owned == 9)
        else:
            level25_check = True
        return key_check and level25_check

    async def update_elevator_lock_state(self, ctx: "BizHawkClientContext") -> None:
        should_be_unlocked = self.should_be_unlocked()
        current_elevator_state = await self.peek_ram(ctx, RAM_ADDRS.END_ELEVATOR_STATE, 1)

        # Should be locked, currently unlocked
        if not should_be_unlocked and current_elevator_state in END_ELEVATOR_UNLOCKED_STATES:
            await self.alter_current_elevator(ctx, lock=True)
        # Should be unlocked, currently locked, currently not in elevator (prevents being trolled by door)
        elif (should_be_unlocked and current_elevator_state not in END_ELEVATOR_UNLOCKED_STATES
                and self.game_state not in [TJEGameState.IN_ELEVATOR]):
            await self.alter_current_elevator(ctx, lock=False)

    async def update_game_state(self, ctx: "BizHawkClientContext") -> None:
        try:
            toejam_state = await self.peek_ram(ctx, RAM_ADDRS.TJ_STATE, 1)
            #toejam_lives = await self.peek_ram(ctx, RAM_ADDRS.TJ_LIVES, 1)
            toejam_sprite = int.from_bytes(await self.peek_ram(ctx, RAM_ADDRS.TJ_SPRITE, 1))
            menu_flag = await self.peek_ram(ctx, RAM_ADDRS.TJ_MENU_FLAG, 1)
            fall_state = await self.peek_ram(ctx, RAM_ADDRS.TJ_FALL_STATE, 1)
            unfall_flag = await self.peek_ram(ctx, RAM_ADDRS.TJ_UNFALL_FLAG, 1)
            global_elevator_state = await self.peek_ram(ctx, RAM_ADDRS.GLOBAL_ELEVATOR_STATE, 1)
            toejam_z = int.from_bytes(
                (await self.peek_ram(ctx, RAM_ADDRS.TJ_POSITION, 6))[4:6], byteorder="big", signed=True)

            self.is_playing: bool = (toejam_state != b"\x00")

            if self.is_playing:
                if toejam_sprite in TJ_GHOST_SPRITES:
                    self.game_state = TJEGameState.GHOST
                else:
                    match global_elevator_state:
                        case b"\x00": # Not in an elevator
                            if menu_flag == b"\x01":
                                self.game_state = TJEGameState.IN_INVENTORY
                            # Deepest possible falling into sand is -16;
                            # highest Z reachable with icarus wings is < 64
                            # The "bummer" state 0x41 is sometimes only detectable for a handful of frames
                            # so Z checking is a necessity
                            elif (toejam_state == TOEJAM_STATE_LOAD_DOWN or toejam_z < -32 or toejam_z > 96):
                                self.game_state = TJEGameState.TRAVELLING_DOWN
                            elif unfall_flag != b"\x00":
                                self.game_state = TJEGameState.UNFALLING
                            elif fall_state != b"\x00" or toejam_z > 0:
                                self.game_state = TJEGameState.IN_AIR
                            elif toejam_sprite in TJ_SWIMMING_SPRITES:
                                self.game_state = TJEGameState.IN_WATER
                            else:
                                self.game_state = TJEGameState.NORMAL
                        case b"\x01":
                            self.game_state = TJEGameState.IN_ELEVATOR
                        case b"\x02":
                            self.game_state = TJEGameState.ARRIVED
                        case _:
                            raise Exception("Something weird happened with the elevator state")                
            else:
                self.game_state = TJEGameState.MAIN_MENU

        except bizhawk.RequestFailedError:
            pass

        # if DEBUG:
        #     print(f"Game state: {self.game_state}")

    #endregion