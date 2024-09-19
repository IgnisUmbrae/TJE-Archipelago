import random
import struct
import functools
from typing import TYPE_CHECKING, Any, Callable, Optional
from enum import Enum

import worlds._bizhawk as bizhawk
from worlds._bizhawk import ConnectionStatus
from worlds._bizhawk.client import BizHawkClient

from .constants import DEBUG, EMPTY_ITEM, COLLECTED_SHIP_ITEM, RANK_NAMES, RAM_ADDRS, \
                       TJ_GHOST_SPRITES, TJ_SWIMMING_SPRITES, TJ_HITOPS_JUMP_SPRITES, TOEJAM_STATE_LOAD_DOWN, \
                       ELEVATOR_LOCKED, ELEVATOR_UNLOCKED, END_ELEVATOR_UNLOCKED_STATES, SAVE_DATA_POINTS
from .items import ITEM_ID_TO_NAME, ITEM_NAME_TO_ID, ITEM_ID_TO_CODE, \
                    PRESENT_IDS, EDIBLE_IDS, SHIP_PIECE_IDS, KEY_IDS, INSTATRAP_IDS
from .locations import FLOOR_ITEM_LOC_TEMPLATE, RANK_LOC_TEMPLATE, SHIP_PIECE_LOC_TEMPLATE

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

#region State constants & state groups

class TJEGameState(Enum):
    WAITING_FOR_LOAD = -1
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
LOADING_STATES_STRICT = LOADING_STATES + [TJEGameState.UNFALLING, TJEGameState.IN_INVENTORY]

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

class TickDelay():
    def __init__(self, callback: Callable, delay: int = 3):
        self.callback = callback
        self.delay = delay
    
    async def tick(self):
        self.delay -= 1
        if self.delay == 0: await self.callback()

class TJEGameController():
    def __init__(self, client: "BizHawkClient"):
        self.client = client

        if DEBUG: print("Resetting game…")

        self.save_data: dict[str, bytes] | None = None

        # Game state–related

        self.game_state: TJEGameState = TJEGameState.MAIN_MENU
        self.is_playing: bool = False
        self.game_complete: bool = False

        self.current_level = -1

        # Ship piece–related

        self.ship_item_levels, self.collected_ship_item_levels = [], []

        self.num_ship_pieces_owned = 0

        # Key-related

        self.key_levels: Optional[list[int]] = None
        self.unlocked_levels: list[int] = []

        # Present-related

        self.starting_presents = []

        # Map-related

        self.num_map_reveals: int = 0

        # Saving and loading–related

        self.connected = False
        self.load_delay = None

        #self.deathlink = False

        self.paused = False

    #region Per-update high-level logic functions

    async def tick(self, ctx: "BizHawkClientContext"):
        self.connected = (ctx.bizhawk_ctx.connection_status == ConnectionStatus.CONNECTED)
        if self.connected:
            if self.load_delay is not None: await self.load_delay.tick()
            if not self.game_complete:
                for monitor in self.monitors: await monitor.tick()
 
                await self.update_game_state(ctx)

    #endregion

    #region Initialization functions

    def add_monitors(self, ctx : "BizHawkClientContext"):
        self.monitors = [
            AddressMonitor(
                "Floor item",
                lambda: RAM_ADDRS.COLLECTED_ITEMS,
                104,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_floor_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Ship item",
                lambda: RAM_ADDRS.TRIGGERED_SHIP_ITEMS,
                10,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_ship_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Rank",
                lambda: RAM_ADDRS.TJ_RANK,
                1,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_rank_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Level",
                lambda: RAM_ADDRS.TJ_LEVEL,
                1,
                lambda: not self.is_awaiting_load(),
                self.handle_level_change,
                self,
                ctx,
                enabled=True
            ),
            AddressMonitor(
                "Elevator",
                lambda: RAM_ADDRS.END_ELEVATOR_STATE,
                1,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_elevator_state_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Player input",
                lambda: RAM_ADDRS.TJ_CURRENT_BUTTONS,
                1,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_input,
                self,
                ctx
            ),
            AddressMonitor(
                "Game over",
                lambda: RAM_ADDRS.TJ_GAME_OVER_FLAG,
                1,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_game_over_flag,
                self,
                ctx
            )
        ]

    def handle_slot_data(self, slot_data : dict[str, Any]):
        if DEBUG: print("Got slot data!")
        self.ship_item_levels = slot_data["ship_piece_levels"]
        self.key_levels = slot_data["key_levels"]
        self.prog_keys = slot_data["prog_keys"]
        self.starting_presents = slot_data["starting_presents"]
        #self.strict_level_25 = slot_data["strict_level_25"]
        #self.deathlink = slot_data["deathlink"]

    # Initialization that cannot be done on the title screen (e.g. identifying starting presents)
    async def level_one_initialization(self, ctx: "BizHawkClientContext") -> None:
        if DEBUG: print("Performing Level 1 initialization")
        for present in self.starting_presents:
            await self.identify_present(ctx, present)

    #endregion

    #region Saving and loading functions

    async def load_save_data(self, ctx: "BizHawkClientContext") -> None:
        if DEBUG: print("Loading save data…")
        if self.save_data is not None:
            try:
                await bizhawk.lock(ctx.bizhawk_ctx)
                for point in SAVE_DATA_POINTS:
                    # Failsafe to ensure we don't instakill/gameover
                    if (point.name in ["Lives (TJ)", "Max health (TJ)", "Health (TJ)"] and
                        int.from_bytes(self.save_data[point.name]) == 0):
                        self.save_data[point.name] = b"\x03"
                    await self.poke_ram(ctx, point.address, self.save_data[point.name])

                # Fill HP bar
                await self.poke_ram(ctx, RAM_ADDRS.TJ_HP_RESTORE, b"\x7F")

                # Level 1 floor items have to be manually altered as it has already loaded in
                level_1_collected = self.one_indices(int.from_bytes(self.save_data["Collected items"][4:8]), 32)
                for index in level_1_collected:
                    await self.poke_ram(ctx, self.floor_item_slot_to_ram_address(index), EMPTY_ITEM)

                await bizhawk.unlock(ctx.bizhawk_ctx)
            except bizhawk.RequestFailedError:
                if DEBUG: print("Failed to load save data!")
            finally:
                self.load_delay = None
                self.game_state = TJEGameState.NORMAL

    async def update_save_data(self, ctx: "BizHawkClientContext") -> None:
        if DEBUG: print("Updating save data…")
        try:
            await bizhawk.display_message(ctx.bizhawk_ctx, "AP CLIENT: Updating save data")
            await bizhawk.lock(ctx.bizhawk_ctx)
            self.save_data = {}
            for point in SAVE_DATA_POINTS:
                self.save_data[point.name] = await self.peek_ram(ctx, point.address, point.size)
        except bizhawk.RequestFailedError:
            if DEBUG: print("Failed to update save data!")
        finally:
            await bizhawk.unlock(ctx.bizhawk_ctx)

    #endregion

    #region Helper functions

    async def poke_ram(self, ctx: "BizHawkClientContext", address: int, value: bytes) -> bool:
        try:
            await bizhawk.write(ctx.bizhawk_ctx, [(address, value, "68K RAM")])
            return True
        except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            return False

    async def peek_ram(self, ctx: "BizHawkClientContext", address: int, size: int) -> Optional[bytes]:
        try:
            return (await bizhawk.read(ctx.bizhawk_ctx, [(address, size, "68K RAM")]))[0]
        except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            return None

    def one_indices(self, bitfield: int, total_bits: int) -> list[int]:
        return [(total_bits-1)-i for i in range(bitfield.bit_length()) if bitfield & (1 << i)]

    # Valid levels: 0–25
    def level_to_collected_items_address(self, level: int) -> Optional[int]:
        if level < 0 or level > 25:
            return None
        return RAM_ADDRS.COLLECTED_ITEMS + level * 4

    # Valid slots: 0–31
    def floor_item_slot_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 31:
            return None
        return RAM_ADDRS.FLOOR_ITEMS + slot * 8

    # Valid slots: 0–15
    def inventory_slot_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 15:
            return None
        return RAM_ADDRS.INVENTORY + slot

    # Valid slots: 0–31
    def dropped_present_slot_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 31:
            return None
        return RAM_ADDRS.DROPPED_PRESENTS + slot * 8

    # Valid slots: 0–28
    def earthling_to_ram_address(self, slot: int) -> Optional[int]:
        if slot < 0 or slot > 28:
            return None
        return RAM_ADDRS.EARTHLINGS + slot*18

    # Valid items: 0–9
    def triggered_ship_item_to_ram_address(self, item: int) -> Optional[int]:
        if item < 0 or item > 9:
            return None
        return RAM_ADDRS.TRIGGERED_SHIP_ITEMS + item

    # Valid pieces: 0–9
    def collected_ship_piece_to_ram_address(self, piece: int) -> Optional[int]:
        if piece < 0 or piece > 9:
            return None
        return RAM_ADDRS.COLLECTED_SHIP_PIECES + piece

    # Valid presents: 0x00–0x1B
    def present_to_identified_ram_address(self, present: int) -> Optional[int]:
        if present < 0x00 or present > 0x1B:
            return None
        return RAM_ADDRS.PRESENTS_WRAPPING + present * 2 + 1

    def level_to_transp_tiles_ram_address(self, level: int) -> Optional[int]:
        if level < 0 or level > 25:
            return None
        return RAM_ADDRS.TRANSP_MAP_MASK + level*7

    def level_to_open_tiles_ram_address(self, level: int) -> Optional[int]:
        if level < 0 or level > 25:
            return None
        return RAM_ADDRS.UNCOVERED_MAP_MASK + level*7

    async def get_empty_inv_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:    
        current_inventory = await self.peek_ram(ctx, RAM_ADDRS.INVENTORY, 16)
        if current_inventory:
            split_inventory = [current_inventory[i:i+1] for i in range(len(current_inventory))]
            try:
                return split_inventory.index(EMPTY_ITEM)
            except ValueError:
                return None
        else:
            return None

    async def get_empty_dropped_present_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        dropped_presents_table = await self.peek_ram(ctx, RAM_ADDRS.DROPPED_PRESENTS, 256)
        if dropped_presents_table:
            dropped_present_types = [dropped_presents_table[i:i+8][0:1]
                                     for i in range(0, len(dropped_presents_table), 8)]
            try:
                return dropped_present_types.index(EMPTY_ITEM)
            except ValueError:
                return None
        else:
            return None
        
    async def get_empty_floor_item_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        floor_item_table = await self.peek_ram(ctx, RAM_ADDRS.FLOOR_ITEMS, 256)
        if floor_item_table:
            floor_item_types = [floor_item_table[i:i+8][0:1]
                                for i in range(0, len(floor_item_table), 8)]
            try:
                return floor_item_types.index(EMPTY_ITEM)
            except ValueError:
                return None
        else:
            return None

    def should_be_unlocked(self) -> bool:
        if self.current_level in [0,1]:
            return True

        if self.key_levels is not None:
            # Not a key level, or already unlocked
            key_check = (self.current_level not in self.key_levels or self.current_level in self.unlocked_levels)
        else:
            key_check = True

        if self.current_level == 24:
            level25_check = (self.num_ship_pieces_owned == 9)
        else:
            level25_check = True

        return key_check and level25_check

    #endregion

    #region Trap activation functions

    async def receive_trap(self, ctx: "BizHawkClientContext", trap_id: int) -> bool:
        if self.is_playing:
            print(f"Activating {ITEM_ID_TO_NAME[trap_id]}")
            match ITEM_ID_TO_NAME[trap_id]:
                case "Cupid Trap":
                    return await self.trap_cupid(ctx)
                case "Sleep Trap":
                    return await self.trap_sleep(ctx)
                case _:
                    pass
        else:
            return False

    async def trap_cupid(self, ctx: "BizHawkClientContext", evil=True) -> bool:
        return (await self.poke_ram(ctx, RAM_ADDRS.CUPID_EFF_TIMER, b"\xF0") and
                await self.poke_ram(ctx, RAM_ADDRS.CUPID_HEART_REF, b"\xFF") and
                await self.poke_ram(ctx, RAM_ADDRS.CUPID_EFF_TYPE, random.randint(0, 63 if evil else 3).to_bytes(1)))
    
    async def trap_sleep(self, ctx: "BizHawkClientContext") -> bool:
        return await self.poke_ram(ctx, RAM_ADDRS.TJ_SLEEP_TIMER, b"\01\x2D")

    #endregion

    #region Spawning functions (also receipt of ethereal items)

    async def receive_map_reveal(self, ctx: "BizHawkClientContext") -> bool:
        if DEBUG: print("Got a map reveal!")
        if self.num_map_reveals >= 5:
            return True

        self.num_map_reveals += 1
        start_level = 5*self.num_map_reveals - 4
        try:
            revealed_tiles = int.from_bytes(
                await self.peek_ram(ctx, self.level_to_open_tiles_ram_address(start_level), 7*5))
            payload = (revealed_tiles ^ int.from_bytes(b"\x00\x7E\x7E\x7E\x7E\x7E\x00"*5)).to_bytes(35)
            await self.poke_ram(ctx, self.level_to_transp_tiles_ram_address(start_level), payload)
        except bizhawk.RequestFailedError:
            return False
        return True

    async def receive_key(self, ctx: "BizHawkClientContext", key_id: int) -> bool:
        if DEBUG:
            print("Got a key!")
        if self.prog_keys:
            num_keys = len(self.unlocked_levels)
            try:
                level = self.key_levels[num_keys]
            except IndexError:
                level = None
        else:
            level = KEY_IDS.index(key_id) + 2

        if level is not None:
            if DEBUG: print(f"Key unlocks level {level}")
            self.unlocked_levels.append(level)
            if self.current_level == level:
                await self.recheck_elevator_unlock(ctx)

        return True

    async def spawn_item(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if self.is_playing and self.game_state != TJEGameState.WAITING_FOR_LOAD:
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
            elif item_id in KEY_IDS:
                success = await self.receive_key(ctx, item_id)
            elif item_id in INSTATRAP_IDS:
                success = await self.receive_trap(ctx, item_id)
            elif item_id == ITEM_NAME_TO_ID["Progressive Map Reveal"]:
                success = await self.receive_map_reveal(ctx)
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
        await self.poke_ram(ctx, self.collected_ship_piece_to_ram_address(slot), COLLECTED_SHIP_ITEM)
        self.num_ship_pieces_owned += 1
        if DEBUG: print(f"Currently have {self.num_ship_pieces_owned} ship pieces")
        if self.current_level == 24:
            await self.recheck_elevator_unlock(ctx)
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
        slot = await self.get_empty_inv_slot(ctx)
        if slot is not None:
            await self.poke_ram(ctx, self.inventory_slot_to_ram_address(slot), ITEM_ID_TO_CODE[pres_id].to_bytes(1))
            return True
        else:
            return await self.spawn_present_as_dropped(ctx, pres_id)

    async def spawn_present_as_dropped(self, ctx: "BizHawkClientContext", pres_id: int) -> bool:
        if self.game_state not in SPAWN_BLOCKING_STATES:
            slot = await self.get_empty_dropped_present_slot(ctx)
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

    def is_paused(self) -> bool:
        return self.paused

    def is_dead(self) -> bool:
        return (self.game_state == TJEGameState.GHOST)

    def is_awaiting_load(self) -> bool:
        return (self.load_delay is not None)

    def is_on_menu(self) -> bool:
        return (self.game_state == TJEGameState.MAIN_MENU or self.current_level == -1)
    
    def is_ship_piece_level(self) -> bool:
        return (self.current_level in self.ship_item_levels and
                self.current_level not in self.collected_ship_item_levels)

    # def is_loading_state(self) -> bool:
    #     return (self.game_state in LOADING_STATES)

    # def is_loading_state_strict(self) -> bool:
    #     return (self.game_state in LOADING_STATES_STRICT)

    async def handle_input(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        new_data, old_data = int.from_bytes(new_data), int.from_bytes(old_data)
        #previous_inputs = int.from_bytes(await self.peek_ram(ctx, 0x8020, 1))
        if new_data & 0x80:
            if not self.paused and not self.game_state == TJEGameState.IN_INVENTORY:#not previous_inputs & 0x80:
                if DEBUG: print("Game paused; saving")
                await self.update_save_data(ctx)
                self.paused = True
        elif old_data & 0x80:
            if DEBUG: print("Game unpaused")
            self.paused = False

    async def handle_game_over_flag(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        if int.from_bytes(new_data) & 0x80 != 0:
            await self.update_save_data(ctx)

    async def handle_level_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        #self.current_level, previous_level = int.from_bytes(new_data), int.from_bytes(old_data)
        toejam_state = await self.peek_ram(ctx, RAM_ADDRS.TJ_STATE, 1)
        # Special handling for menu, aka "level -1"
        self.current_level = int.from_bytes(new_data) if toejam_state != b"\x00" else -1
        if self.current_level == -1:
            if DEBUG: print("Reboot detected; force unpausing")
            self.paused = False
        if DEBUG: print(f"Level changed to {self.current_level}")

        if self.current_level == 1 and self.game_state == TJEGameState.MAIN_MENU:
            if self.save_data is None:
                await self.level_one_initialization(ctx)
            else:
                self.load_delay = TickDelay(functools.partial(self.load_save_data, ctx), 8)
                await bizhawk.display_message(ctx.bizhawk_ctx, "AP CLIENT: Loading save data")
                self.game_state = TJEGameState.WAITING_FOR_LOAD
        if self.game_state in LOADING_STATES and self.current_level != -1:
            if self.load_delay is None:
                await self.update_save_data(ctx)

    async def handle_floor_item_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        changed_indices = self.one_indices(int.from_bytes(new_data) ^ int.from_bytes(old_data), 104*8)
        level_item_pairs = [divmod(i, 32) for i in changed_indices]
        for (level, item_num) in level_item_pairs:
            await self.client.trigger_location(ctx, FLOOR_ITEM_LOC_TEMPLATE.format(level, item_num+1))

    async def handle_ship_item_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        triggered_levels = [old_data[i] for i in range(10) if new_data[i] != old_data[i]]
        for level in triggered_levels:
            success = await self.client.trigger_location(ctx, SHIP_PIECE_LOC_TEMPLATE.format(level))
            if success:
                self.collected_ship_item_levels.append(self.current_level)

    async def handle_rank_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        rank = int.from_bytes(new_data)
        if rank > 0:
            loc = RANK_LOC_TEMPLATE.format(RANK_NAMES[rank-1])
            await self.client.trigger_location(ctx, loc)

    async def handle_elevator_state_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        should_be_unlocked = self.should_be_unlocked()
        lock = None
        # Should be locked, currently unlocked
        if not should_be_unlocked and new_data in END_ELEVATOR_UNLOCKED_STATES:
            lock = True
            if DEBUG: print(f"Locking level {self.current_level}")
        # Should be unlocked, currently locked, currently not in elevator (prevents being trolled by door)
        elif (should_be_unlocked and new_data not in END_ELEVATOR_UNLOCKED_STATES
                and self.game_state not in [TJEGameState.IN_ELEVATOR]):
            lock = False
            if DEBUG: print(f"Unlocking level {self.current_level}")
        if lock is not None:
            await self.poke_ram(ctx, RAM_ADDRS.END_ELEVATOR_STATE, ELEVATOR_LOCKED if lock else ELEVATOR_UNLOCKED)

    async def recheck_elevator_unlock(self, ctx: "BizHawkClientContext"):
        await self.handle_elevator_state_change(ctx, b"\x00", b"\x0A")

    async def update_game_state(self, ctx: "BizHawkClientContext") -> None:
        old_state = self.game_state
        if self.load_delay is not None:
            self.game_state = TJEGameState.WAITING_FOR_LOAD
        else:
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
                                elif fall_state != b"\x00" or toejam_z > 0 or toejam_sprite in TJ_HITOPS_JUMP_SPRITES:
                                    self.game_state = TJEGameState.IN_AIR
                                elif toejam_sprite in TJ_SWIMMING_SPRITES:
                                    self.game_state = TJEGameState.IN_WATER
                                else:
                                    self.game_state = TJEGameState.NORMAL
                            case b"\x01":
                                self.game_state = TJEGameState.IN_ELEVATOR
                            case b"\x02":
                                self.game_state = TJEGameState.ARRIVED
                else:
                    self.game_state = TJEGameState.MAIN_MENU

            except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
                pass

        if DEBUG:
            if old_state != self.game_state:
                print(f"Game state changed to {self.game_state}")

    #endregion
