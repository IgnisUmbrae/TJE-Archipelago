import random
import struct
import functools
import logging
from typing import TYPE_CHECKING, Callable, Optional
from enum import IntEnum

import worlds._bizhawk as bizhawk
from worlds._bizhawk import ConnectionStatus
from worlds._bizhawk.client import BizHawkClient

from .constants import EMPTY_ITEM, COLLECTED_SHIP_ITEM, PLAYER_SLOT_STRUCTURES, RANK_NAMES, \
                        get_slot_addr, get_ram_addr, expand_inv_constants
from .items import ITEM_ID_TO_NAME, ITEM_NAME_TO_ID, ITEM_ID_TO_CODE, STATIC_DIALOGUE_LIST, \
                    PRESENT_IDS, SHIP_PIECE_IDS,INSTATRAP_IDS, TRAP_PRESENT_IDS
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
        if state is None:
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

class TJEGameController():
    def __init__(self, client: "BizHawkClient"):
        self.client = client

        logger.debug("Resetting game…")

        # self.save_data: dict[str, bytes] | None = None

        # Game state–related

        self.is_playing: bool = False
        self.game_complete: bool = False

        self.current_level = -1

        # Ship piece–related

        self.ship_item_levels, self.collected_ship_item_levels = [], []

        self.num_ship_pieces_owned = 0

        # Map-related

        self.num_map_reveals: int = 0

        # Saving and loading–related

        self.connected = False
        # self.load_delay = None

        # Misc

        #self.paused = False

        self.char = 0

        self.auto_trap_presents = False
        self.expanded_inv = False

    #region Per-update high-level logic functions

    async def tick(self, ctx: "BizHawkClientContext"):
        self.connected = (ctx.bizhawk_ctx.connection_status == ConnectionStatus.CONNECTED)
        if self.connected:
            # if self.load_delay is not None: await self.load_delay.tick()
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
                lambda: not self.is_on_menu(),# and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_floor_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Ship item",
                "TRIGGERED_SHIP_ITEMS",
                10,
                MonitorLevel.GLOBAL,
                lambda: not self.is_on_menu(),# and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_ship_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Rank",
                "RANK",
                1,
                level,
                lambda: not self.is_on_menu(),# and not self.is_awaiting_load() and not self.is_paused(),
                self.handle_rank_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Level",
                "LEVEL",
                1,
                level,
                lambda: True, #not self.is_awaiting_load(),
                self.handle_level_change,
                self,
                ctx,
                enabled=True
            ),
        ]

    def initialize_slot_data(self, ship_item_levels: list[int], auto_trap_presents: bool, expanded_inv: bool):
        self.ship_item_levels = ship_item_levels
        self.auto_trap_presents = auto_trap_presents
        self.expanded_inv = expanded_inv
        if self.expanded_inv:
            expand_inv_constants()

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

    async def is_item_waiting(self, ctx: "BizHawkClientContext") -> bool:
        return (await self.peek_ram(ctx, get_ram_addr("AP_GIVE_ITEM", self.char), 1)) != b"\xFF"

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
        if self.is_playing:# and self.game_state != TJEGameState.WAITING_FOR_LOAD:
            dialogue = (None, None)
            if item_id in SHIP_PIECE_IDS:
                success, dialogue = await self.award_ship_piece(ctx, item_id)
            elif item_id in INSTATRAP_IDS:
                success, dialogue = await self.receive_trap(ctx, item_id)
            else:
                success = await self.give_item_directly(ctx, item_id)
            if success and dialogue:
                await self.emit_dialogue(ctx, dialogue)
            return success
        return False

    async def give_item_directly(self, ctx: "BizHawkClientContext", item_id: int) -> bool:
        if await self.is_item_waiting(ctx):
            return False
        if item_id in PRESENT_IDS and await self.is_inventory_full(ctx): #and self.game_state == TJEGameState.IN_INVENTORY:
            return False
        item_code = ITEM_ID_TO_CODE[item_id]
        return await self.poke_ram(ctx, get_ram_addr("AP_GIVE_ITEM"), item_code.to_bytes(1))

    async def is_inventory_full(self, ctx: "BizHawkClientContext") -> bool:
        return await self.peek_ram(ctx,
                                   get_slot_addr("INVENTORY", PLAYER_SLOT_STRUCTURES["INVENTORY"].max_slot, self.char),
                                   1) != b"\xFF"

    async def emit_dialogue(self, ctx: "BizHawkClientContext", lines: tuple[str, str]) -> None:
        if lines[0] is not None and lines[1] is not None:
            line1 = lines[0].encode("ascii") + b"\x00"*(12 - len(lines[0]))
            line2 = lines[1].encode("ascii") + b"\x00"*(12 - len(lines[1]))
            await self.poke_ram(ctx, get_ram_addr("AP_DIALOGUE_LINE1"), line1)
            await self.poke_ram(ctx, get_ram_addr("AP_DIALOGUE_LINE2"), line2)
            await self.poke_ram(ctx, get_ram_addr("AP_DIALOGUE_TRIGGER"), b"\x01")

    async def award_ship_piece(self, ctx: "BizHawkClientContext", ship_piece_id: int) -> tuple[bool, tuple[str, str]]:
        piece = SHIP_PIECE_IDS.index(ship_piece_id)
        await self.poke_ram(ctx, get_slot_addr("COLLECTED_SHIP_PIECES", piece, self.char), COLLECTED_SHIP_ITEM)
        self.num_ship_pieces_owned += 1
        logger.debug("Currently have %i ship pieces", self.num_ship_pieces_owned)
        return True, STATIC_DIALOGUE_LIST[ITEM_ID_TO_NAME[ship_piece_id]]

    #endregion

    #region Change handling & monitor-related functions

    def is_on_menu(self) -> bool:
        return (not self.is_playing or self.current_level == -1)

    # def is_ship_piece_level(self) -> bool:
    #     return (self.current_level in self.ship_item_levels and
    #             self.current_level not in self.collected_ship_item_levels)

    async def handle_level_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        await self.update_game_state(ctx)
        # Special handling for menu, aka "level -1"
        self.current_level = int.from_bytes(new_data) if self.is_playing else -1
        # if self.current_level == -1:
        #     logger.debug("Reboot detected; force unpausing")
        #     self.paused = False
        logger.debug("Level changed to %i", self.current_level)

    async def handle_floor_item_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        new_as_int, old_as_int = int.from_bytes(new_data), int.from_bytes(old_data)
        if new_as_int > old_as_int:
            changed_indices = self.one_indices(new_as_int ^ old_as_int, 104*8)
            level_item_pairs = [divmod(i, 32) for i in changed_indices]
            for (level, item_num) in level_item_pairs:
                await self.client.trigger_location(ctx, FLOOR_ITEM_LOC_TEMPLATE.format(level, item_num+1))

    async def handle_ship_item_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        triggered_levels = [old_data[i] for i in range(10) if new_data[i] != old_data[i] and old_data[i] != 0]
        for level in triggered_levels:
            # if level in self.ship_item_levels:
            logger.debug("Triggering ship piece on level %i", level)
            success = await self.client.trigger_location(ctx, SHIP_PIECE_LOC_TEMPLATE.format(level))
            if success:
                self.collected_ship_item_levels.append(self.current_level)

    async def handle_rank_change(self, ctx: "BizHawkClientContext", old_data: bytes, new_data: bytes):
        rank = int.from_bytes(new_data)
        if rank > 0:
            loc = RANK_LOC_TEMPLATE.format(RANK_NAMES[rank-1])
            await self.client.trigger_location(ctx, loc)

    async def update_game_state(self, ctx: "BizHawkClientContext") -> None:
        player_state = await self.peek_ram(ctx, get_ram_addr("STATE", self.char), 1)
        self.is_playing = (player_state != b"\x00")

    #endregion
