import random
import struct
import functools
import logging
from typing import TYPE_CHECKING, Callable, Optional
from enum import IntEnum

import worlds._bizhawk as bizhawk
from worlds._bizhawk import ConnectionStatus
from worlds._bizhawk.client import BizHawkClient

from .constants import EMPTY_ITEM, COLLECTED_SHIP_ITEM, RANK_NAMES, SPRITES_GHOST, SPRITES_WATER, SPRITES_HITOPS_JUMP, \
                       STATE_LOAD_DOWN, ELEVATOR_LOCKED, ELEVATOR_UNLOCKED, END_ELEVATOR_UNLOCKED_STATES, \
                       SAVE_DATA_POINTS, add_save_data_points, get_slot_addr, get_ram_addr, expand_inv_constants, \
                       TJEGameState, LOADING_STATES, SPAWN_BLOCKING_STATES
from .items import ITEM_ID_TO_NAME, ITEM_NAME_TO_ID, ITEM_ID_TO_CODE, STATIC_DIALOGUE_LIST, \
                    PRESENT_IDS, EDIBLE_IDS, SHIP_PIECE_IDS, KEY_IDS, INSTATRAP_IDS, TRAP_PRESENT_IDS
from .locations import FLOOR_ITEM_LOC_TEMPLATE, RANK_LOC_TEMPLATE, SHIP_PIECE_LOC_TEMPLATE

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger(__name__)

class MonitorLevel(IntEnum):
    GLOBAL = -1
    TOEJAM = 0
    EARL = 1
    BOTH = 2

class AddressMonitor():
    def __init__(self, name: str, addr_name: str, size: int, level: MonitorLevel, enable_test_fn: Callable,
                 on_trigger_fn: Callable, parent: "TJEGameController", ctx: "BizHawkClientContext", enabled=False):
        self.name = name
        self.parent = parent
        self.on_trigger = on_trigger_fn
        self.ctx = ctx

        self.old_data, self.new_data = None, None

        self.monitor_level = None
        self.monitor_addrs = []

        self.enable_test = enable_test_fn
        self.enabled = enabled
        self.log_state()

        self.addr_name = addr_name
        self.size = size

        self.set_monitor_level(level)

    def log_state(self, state=None):
        if not state:
            state = self.enabled
        logger.debug("%s monitoring %s", self.name, "enabled" if state else "disabled")

    def set_monitor_level(self, level: MonitorLevel):
        self.monitor_level = level
        match level:
            case MonitorLevel.GLOBAL:
                self.monitor_addrs.append(get_ram_addr(self.addr_name))
            case MonitorLevel.TOEJAM | MonitorLevel.EARL:
                self.monitor_addrs.append(get_ram_addr(self.addr_name, level.value))
            case MonitorLevel.BOTH:
                self.monitor_addrs = [get_ram_addr(self.addr_name, 0), get_ram_addr(self.addr_name, 1)]
        self.reset_data()

    def reset_data(self):
        entries = len(self.monitor_addrs)
        self.old_data, self.new_data = [None]*entries, [None]*entries

    def check_enabledness(self):
        new_state = self.monitor_addrs and self.enable_test()
        if self.enabled != new_state:
            self.log_state(new_state)
        self.enabled = new_state
        if not self.enabled:
            self.reset_data()

    async def tick(self):
        self.check_enabledness()
        if self.enabled:
            for i, addr in enumerate(self.monitor_addrs):
                self.old_data[i] = self.new_data[i]
                self.new_data[i] = await self.parent.peek_ram(self.ctx, addr, self.size)

                if (self.old_data[i] is not None and self.new_data[i] is not None
                    and self.old_data[i] != self.new_data[i]):
                    await self.trigger(i)

    async def trigger(self, index: int):
        await self.on_trigger(self.ctx, self.old_data[index], self.new_data[index])

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

        logger.debug("Resetting game…")

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

        self.prog_keys = False
        self.key_levels: Optional[list[int]] = None
        self.unlocked_levels: list[int] = []

        # Map-related

        self.num_map_reveals: int = 0

        # Saving and loading–related

        self.connected = False
        self.load_delay = None

        # Misc

        self.paused = False

        self.char = 0

        self.auto_trap_presents = False
        self.expanded_inv = False

    #region Per-update high-level logic functions

    async def tick(self, ctx: "BizHawkClientContext"):
        self.connected = (ctx.bizhawk_ctx.connection_status == ConnectionStatus.CONNECTED)
        if self.connected:
            if self.load_delay is not None: await self.load_delay.tick()
            if not self.game_complete:
                await self.update_game_state(ctx)
                for monitor in self.monitors: await monitor.tick()

    #endregion

    #region Initialization functions

    def add_monitors(self, ctx: "BizHawkClientContext", char: int):
        # These are the values returned by the menu, which don't match the others in-game
        match char:
            case 1:
                level = MonitorLevel.TOEJAM
                self.char = 0
            case 2:
                level = MonitorLevel.EARL
                self.char = 1
            case 0:
                level = MonitorLevel.BOTH
                self.char = 2

        self.monitors = [
            AddressMonitor(
                "Floor item",
                "COLLECTED_ITEMS",
                104,
                MonitorLevel.GLOBAL,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_floor_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Ship item",
                "TRIGGERED_SHIP_ITEMS",
                10,
                MonitorLevel.GLOBAL,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_ship_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Rank",
                "RANK",
                1,
                level,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_rank_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Level",
                "LEVEL",
                1,
                level,
                lambda: not self.is_awaiting_load(),
                self.handle_level_change,
                self,
                ctx,
                enabled=True
            ),
            AddressMonitor(
                "Elevator",
                "END_ELEVATOR_STATE",
                1,
                MonitorLevel.GLOBAL,
                lambda: not self.is_on_menu() and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_elevator_state_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Player input",
                "CURRENT_BUTTONS",
                1,
                level,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_input,
                self,
                ctx
            ),
            AddressMonitor(
                "Game over",
                "GAME_OVER_FLAG",
                1,
                level,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_game_over_flag,
                self,
                ctx
            )
        ]

    def create_save_points(self):
        if self.char < 2:
            add_save_data_points(self.char, self.expanded_inv)
        else:
            add_save_data_points(0, self.expanded_inv)
            add_save_data_points(1, self.expanded_inv)

    def initialize_slot_data(self, ship_item_levels: list[int], key_levels: list[int],
                             prog_keys: bool, auto_trap_presents: bool, expanded_inv: bool):
        self.ship_item_levels = ship_item_levels
        self.key_levels = key_levels
        self.prog_keys = prog_keys
        self.auto_trap_presents = auto_trap_presents
        self.expanded_inv = expanded_inv
        if self.expanded_inv:
            expand_inv_constants()

    #endregion

    #region Saving and loading functions

    async def load_save_data(self, ctx: "BizHawkClientContext") -> None:
        logger.debug("Loading save data…")
        if self.save_data is not None:
            try:
                await bizhawk.lock(ctx.bizhawk_ctx)
                for point in SAVE_DATA_POINTS:
                    # Failsafe to ensure we don't instakill/gameover
                    if (point.name in ["Lives", "Max health", "Health"] and
                        int.from_bytes(self.save_data[point.name]) == 0):
                        self.save_data[point.name] = b"\x03"
                    await self.poke_ram(ctx, point.address, self.save_data[point.name])

                # Fill HP bar
                await self.poke_ram(ctx, get_ram_addr("HP_RESTORE", self.char), b"\x7F")

                # Level 1 floor items have to be manually altered as it has already loaded in
                level_1_collected = self.one_indices(int.from_bytes(self.save_data["Collected items"][4:8]), 32)
                for index in level_1_collected:
                    await self.poke_ram(ctx, get_slot_addr("FLOOR_ITEMS", index, self.char), EMPTY_ITEM)

                await bizhawk.unlock(ctx.bizhawk_ctx)
            except bizhawk.RequestFailedError:
                logger.debug("Failed to load save data!")
            finally:
                self.load_delay = None
                self.game_state = TJEGameState.NORMAL

    async def update_save_data(self, ctx: "BizHawkClientContext") -> None:
        logger.debug("Updating save data…")
        try:
            await bizhawk.display_message(ctx.bizhawk_ctx, "AP CLIENT: Updating save data")
            await bizhawk.lock(ctx.bizhawk_ctx)
            self.save_data = {}
            for point in SAVE_DATA_POINTS:
                self.save_data[point.name] = await self.peek_ram(ctx, point.address, point.size)
        except bizhawk.RequestFailedError:
            logger.debug("Failed to update save data!")
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

    async def get_empty_inv_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        current_inventory = await self.peek_ram(ctx, get_ram_addr("INVENTORY", self.char),
                                                64 if self.expanded_inv else 16)
        if current_inventory:
            split_inventory = [current_inventory[i:i+1] for i in range(len(current_inventory))]
            try:
                return split_inventory.index(EMPTY_ITEM)
            except ValueError:
                return None
        else:
            return None

    async def get_empty_dropped_present_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        dropped_presents_table = await self.peek_ram(ctx,get_ram_addr("DROPPED_PRESENTS", self.char), 256)
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
        floor_item_table = await self.peek_ram(ctx, get_ram_addr("FLOOR_ITEMS", self.char), 256)
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

    async def receive_trap(self, ctx: "BizHawkClientContext", trap_id: int) -> tuple[bool, tuple[str, str]]:
        if self.is_playing:
            trap_name = ITEM_ID_TO_NAME[trap_id]
            logger.debug("Attempting to activate %s", trap_name)
            match trap_name:
                case "Burp Trap":
                    success = await self.trap_burp(ctx)
                case "Cupid Trap":
                    success = await self.trap_cupid(ctx)
                case "Sleep Trap":
                    success = await self.trap_present(ctx, b"\x18")
                case "Rocket Skates Trap":
                    success = await self.trap_present(ctx, b"\x05")
                case "Earthling Trap":
                    success = await self.trap_present(ctx, b"\x17")
                case "Randomizer Trap":
                    success = await self.trap_present(ctx, b"\x12")
                case _:
                    logger.error("Attempted to activate a non-existent trap")
                    success = True
            return success, STATIC_DIALOGUE_LIST[trap_name]
        return False

    async def is_present_trap_waiting(self, ctx: "BizHawkClientContext") -> bool:
        return (await self.peek_ram(ctx, get_ram_addr("AP_AUTO_PRESENT", self.char), 1)) != b"\xFF"

    async def trap_cupid(self, ctx: "BizHawkClientContext") -> bool:
        return (await self.poke_ram(ctx, get_ram_addr("AP_CUPID_TRAP", self.char), b"\x01"))

    async def trap_burp(self, ctx: "BizHawkClientContext") -> bool:
        num = random.randint(15,25) # In game seems to be between 12 and 16
        return (await self.poke_ram(ctx, get_ram_addr("BURP_TIMER", self.char), b"\x10") and
                await self.poke_ram(ctx, get_ram_addr("BURPS_LEFT", self.char), num.to_bytes(1)))

    async def trap_present(self, ctx: "BizHawkClientContext", present_code: bytes) -> bool:
        if await self.is_present_trap_waiting(ctx):
            return False
        await bizhawk.lock(ctx.bizhawk_ctx)
        success = (await self.poke_ram(ctx, get_ram_addr("AP_AUTO_NO_POINTS", self.char), b"\x01") and
                   await self.poke_ram(ctx, get_ram_addr("AP_AUTO_PRESENT", self.char), present_code))
        await bizhawk.unlock(ctx.bizhawk_ctx)
        return success

    #endregion

    #region Spawning functions (also receipt of ethereal items)

    async def receive_map_reveal(self, ctx: "BizHawkClientContext") -> tuple[bool, tuple[str, str]]:
        logger.debug("Got a map reveal!")
        if self.num_map_reveals >= 5:
            return True, (None, None)

        self.num_map_reveals += 1
        start_level = 5*self.num_map_reveals - 4
        dialogue = (f"Lv{start_level}-{start_level+4} map!","let's go")
        try:
            revealed_tiles = int.from_bytes(
                await self.peek_ram(ctx, get_slot_addr("UNCOVERED_MAP_MASK", start_level, self.char), 7*5))
            payload = (revealed_tiles ^ int.from_bytes(b"\x00\x7E\x7E\x7E\x7E\x7E\x00"*5)).to_bytes(35)
            await self.poke_ram(ctx, get_slot_addr("TRANSP_MAP_MASK", start_level, self.char), payload)
        except bizhawk.RequestFailedError:
            return False
        return True, dialogue

    async def receive_key(self, ctx: "BizHawkClientContext", key_id: int) -> tuple[bool, tuple[str, str]]:
        logger.debug("Got a key!")
        if self.prog_keys:
            num_keys = len(self.unlocked_levels)
            try:
                level = self.key_levels[num_keys]
            except IndexError:
                level = None
        else:
            level = KEY_IDS.index(key_id) + 2

        dialogue = (None, None)
        if level is not None:
            logger.debug("Key unlocks level %i", level)
            dialogue = (f"Lv{level} key!", "'vator open")
            self.unlocked_levels.append(level)
            if self.current_level == level:
                await self.recheck_elevator_unlock(ctx)

        return True, dialogue

    async def receive_item(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if self.auto_trap_presents > 0 and item_id in TRAP_PRESENT_IDS:
            if not (self.auto_trap_presents == 1 and item_id == ITEM_NAME_TO_ID["Randomizer"]):
                return await self.open_trap_present(ctx, item_id)
        return await self.spawn_item(ctx, item_id)

    async def open_trap_present(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        item_code = ITEM_ID_TO_CODE[item_id]
        # Locking possibly not required here
        await bizhawk.lock(ctx.bizhawk_ctx)
        success = (await self.poke_ram(ctx, get_ram_addr("AP_AUTO_NO_POINTS", self.char), b"\x00") and
                   await self.poke_ram(ctx, get_ram_addr("AP_AUTO_PRESENT", self.char),item_code.to_bytes(1)))
        await bizhawk.unlock(ctx.bizhawk_ctx)
        return success

    async def spawn_item(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if self.is_playing and self.game_state != TJEGameState.WAITING_FOR_LOAD:
            dialogue = (None, None)
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
                success, dialogue = await self.award_ship_piece(ctx, item_id)
            elif item_id in KEY_IDS:
                success, dialogue = await self.receive_key(ctx, item_id)
            elif item_id in INSTATRAP_IDS:
                success, dialogue = await self.receive_trap(ctx, item_id)
            elif item_id == ITEM_NAME_TO_ID["Progressive Map Reveal"]:
                success, dialogue = await self.receive_map_reveal(ctx)
            else:
                success = False
            if success and dialogue:
                await self.emit_dialogue(ctx, dialogue)
            return success
        return False

    async def emit_dialogue(self, ctx: "BizHawkClientContext", lines: tuple[str, str]) -> None:
        if lines[0] is not None and lines[1] is not None:
            line1 = lines[0].encode("ascii") + b"\x00"*(12 - len(lines[0]))
            line2 = lines[1].encode("ascii") + b"\x00"*(12 - len(lines[1]))
            await self.poke_ram(ctx, get_ram_addr("AP_DIALOGUE_LINE1"), line1)
            await self.poke_ram(ctx, get_ram_addr("AP_DIALOGUE_LINE2"), line2)
            await self.poke_ram(ctx, get_ram_addr("AP_DIALOGUE_TRIGGER"), b"\x01")

    async def identify_present(self, ctx: "BizHawkClientContext", present_id: int) -> bool:
        present = ITEM_ID_TO_CODE[present_id]
        logger.debug("Identifying present %s", present)
        await self.poke_ram(ctx, get_slot_addr("PRESENTS_IDENTIFIED", present, self.char), b"\x01")
        return True

    async def award_ship_piece(self, ctx: "BizHawkClientContext", ship_piece_id: int) -> tuple[bool, tuple[str, str]]:
        piece = SHIP_PIECE_IDS.index(ship_piece_id)
        await self.poke_ram(ctx, get_slot_addr("COLLECTED_SHIP_PIECES", piece, self.char), COLLECTED_SHIP_ITEM)
        self.num_ship_pieces_owned += 1
        logger.debug("Currently have %i ship pieces", self.num_ship_pieces_owned)
        if self.current_level == 24:
            await self.recheck_elevator_unlock(ctx)
        return True, STATIC_DIALOGUE_LIST[ITEM_ID_TO_NAME[ship_piece_id]]

    # Spawns any standard floor item at TJ's current position
    # Normally only used to spawn edibles; presents go directly into inventory
    async def spawn_on_floor(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if self.game_state not in SPAWN_BLOCKING_STATES:
            slot = await self.get_empty_floor_item_slot(ctx)
            print(f"Slot to spawn in: {slot}")
            if slot is not None and self.current_level is not None:
                player_xy = await self.peek_ram(ctx, get_ram_addr("POSITION", self.char), 4)
                await self.poke_ram(ctx, get_slot_addr("FLOOR_ITEMS", slot, self.char),
                    struct.pack(">BBBB", ITEM_ID_TO_CODE[item_id], self.current_level, 0, 0) + player_xy)
                return True
            else:
                return False
        else:
            return False

    # Spawns a present in TJ's inventory
    async def spawn_in_inventory(self, ctx: "BizHawkClientContext", pres_id: int) -> bool:
        slot = await self.get_empty_inv_slot(ctx)
        if slot is not None:
            await self.poke_ram(ctx, get_slot_addr("INVENTORY", slot, self.char), ITEM_ID_TO_CODE[pres_id].to_bytes(1))
            return True
        else:
            return await self.spawn_present_as_dropped(ctx, pres_id)

    async def spawn_present_as_dropped(self, ctx: "BizHawkClientContext", pres_id: int) -> bool:
        logger.debug("Spawning present on floor (no room in inventory)")
        if self.game_state not in SPAWN_BLOCKING_STATES:
            slot = await self.get_empty_dropped_present_slot(ctx)
            if slot is not None and self.current_level is not None:
                toejam_position = await self.peek_ram(ctx, get_ram_addr("POSITION", self.char), 4)
                success = await self.poke_ram(ctx, get_slot_addr("DROPPED_PRESENTS", slot, self.char),
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
        if new_data & 0x80:
            if not self.paused and not self.game_state == TJEGameState.IN_INVENTORY:#not previous_inputs & 0x80:
                logger.debug("Game paused")
                await self.update_save_data(ctx)
                self.paused = True
        elif old_data & 0x80:
            logger.debug("Game unpaused")
            self.paused = False

    async def handle_game_over_flag(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        if int.from_bytes(new_data) & 0x80 != 0:
            await self.update_save_data(ctx)

    async def handle_level_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        toejam_state = await self.peek_ram(ctx, get_ram_addr("STATE", self.char), 1)
        # Special handling for menu, aka "level -1"
        self.current_level = int.from_bytes(new_data) if toejam_state != b"\x00" else -1
        if self.current_level == -1:
            logger.debug("Reboot detected; force unpausing")
            self.paused = False
        logger.debug("Level changed to %i", self.current_level)

        if self.current_level == 1 and self.game_state == TJEGameState.MAIN_MENU and self.save_data is not None:
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
            if level in self.ship_item_levels:
                logger.debug("Triggering ship piece on level %i", level)
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
            logger.debug("Locking level %i", self.current_level)
        # Should be unlocked, currently locked, currently not in elevator (prevents being trolled by door)
        elif (should_be_unlocked and new_data not in END_ELEVATOR_UNLOCKED_STATES
                and self.game_state not in [TJEGameState.IN_ELEVATOR]):
            lock = False
            logger.debug("Unlocking level %i", self.current_level)
        if lock is not None:
            await self.poke_ram(ctx, get_ram_addr("END_ELEVATOR_STATE", self.char),
                                ELEVATOR_LOCKED if lock else ELEVATOR_UNLOCKED)

    async def recheck_elevator_unlock(self, ctx: "BizHawkClientContext"):
        await self.handle_elevator_state_change(ctx, b"\x00", b"\x0A")

    async def update_game_state(self, ctx: "BizHawkClientContext") -> None:
        old_state = self.game_state
        if self.load_delay is not None:
            self.game_state = TJEGameState.WAITING_FOR_LOAD
        else:
            try:
                try:
                    player_state = await self.peek_ram(ctx, get_ram_addr("STATE", self.char), 1)
                    player_sprite = int.from_bytes(
                        await self.peek_ram(ctx, get_ram_addr("SPRITE", self.char), 1))
                    fall_state = await self.peek_ram(ctx, get_ram_addr("FALL_STATE", self.char), 1)
                    unfall_flag = await self.peek_ram(ctx, get_ram_addr("UNFALL_FLAG", self.char), 1)
                    global_elevator_state = await self.peek_ram(ctx,
                                                                get_ram_addr("GLOBAL_ELEVATOR_STATE", self.char), 1)
                    player_z = int.from_bytes((
                        await self.peek_ram(ctx,get_ram_addr("POSITION", self.char), 6))[4:6],
                        byteorder="big", signed=True)
                except TypeError:
                    return

                self.is_playing: bool = (player_state != b"\x00")

                if self.is_playing:
                    if player_sprite in SPRITES_GHOST:
                        self.game_state = TJEGameState.GHOST
                    else:
                        match global_elevator_state:
                            case b"\x00": # Not in an elevator
                                if player_state == b"\x0B": #menu_flag == b"\x01":
                                    self.game_state = TJEGameState.IN_INVENTORY
                                # Deepest possible falling into sand is -16;
                                # highest Z reachable with icarus wings is < 64
                                # The "bummer" state 0x41 is sometimes only detectable for a handful of frames
                                # so Z checking is a necessity
                                elif (player_state == STATE_LOAD_DOWN or player_z < -32 or player_z > 96):
                                    self.game_state = TJEGameState.TRAVELLING_DOWN
                                elif unfall_flag != b"\x00":
                                    self.game_state = TJEGameState.UNFALLING
                                elif fall_state != b"\x00" or player_z > 0 or player_sprite in SPRITES_HITOPS_JUMP:
                                    self.game_state = TJEGameState.IN_AIR
                                elif player_sprite in SPRITES_WATER:
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

        if old_state != self.game_state:
            logger.debug("Game state changed to %s", self.game_state.name)

    #endregion
