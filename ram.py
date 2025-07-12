import random
import logging
from typing import TYPE_CHECKING, Callable, Optional
from enum import IntEnum

import worlds._bizhawk as bizhawk
from worlds._bizhawk import ConnectionStatus
from worlds._bizhawk.client import BizHawkClient

from .constants import DEAD_SPRITES, EMPTY_ITEM, COLLECTED_SHIP_ITEM, EMPTY_PRESENT, GLOBAL_DATA_STRUCTURES, \
                       PLAYER_DATA_STRUCTURES, RANK_NAMES, SAVE_DATA_POINTS_GLOBAL, SAVE_DATA_POINTS_PLAYER, \
                       STATIC_DIALOGUE_LIST, \
                       get_datastructure, get_max_health, get_slot_addr, get_ram_addr, expand_inv_constants
from .items import ITEM_ID_TO_NAME, ITEM_NAME_TO_ID, ITEM_ID_TO_CODE, \
                   PRESENT_IDS, SHIP_PIECE_IDS,INSTATRAP_IDS, BAD_PRESENT_IDS
from .hint import generate_hints_for_current_level
from .locations import FLOOR_ITEM_LOC_TEMPLATE, RANK_LOC_TEMPLATE, SHIP_PIECE_LOC_TEMPLATE

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger(__name__)

class MonitorLevel(IntEnum):
    GLOBAL = -1
    TOEJAM = 0
    EARL = 1
    BOTH = 2

def one_indices(bitfield: int, total_bits: int) -> list[int]:
    return [(total_bits-1)-i for i in range(bitfield.bit_length()) if bitfield & (1 << i)]

def character_to_monitor_level(char: int) -> MonitorLevel:
    match char:
        case 0:
            return MonitorLevel.TOEJAM
        case 1:
            return MonitorLevel.EARL
        case 2:
            return MonitorLevel.BOTH
        case _:
            return MonitorLevel.GLOBAL

class SaveManager():
    def __init__(self, sync_interval: int, char: int, gc: "TJEGameController", ctx: "BizHawkClientContext"):
        player_monitor_level = character_to_monitor_level(char)
        self.char = char
        self.ticks = 0
        self.sync_interval = sync_interval
        self.game_controller = gc
        self.monitors: list[AddressMonitor] = []
        self.monitors.append(
            AddressMonitor(
                "Initialization complete",
                "AP_INIT_COMPLETE",
                1,
                MonitorLevel.GLOBAL,
                lambda: True,
                self.handle_init_flag_changed,
                gc,
                ctx,
                enabled=True
            ))
        for structure in SAVE_DATA_POINTS_GLOBAL:
            self.monitors.append(AddressMonitor.create_as_save_monitor(
                structure,
                MonitorLevel.GLOBAL,
                self.data_changed,
                gc,
                ctx,
            ))
        for structure in SAVE_DATA_POINTS_PLAYER:
            self.monitors.append(AddressMonitor.create_as_save_monitor(
                structure,
                player_monitor_level,
                self.data_changed,
                gc,
                ctx,
            ))

        self.post_loading_routines: dict[str, Callable] = {
            "RANK" : self.rank_post_load,
            "COLLECTED_ITEMS" : self.collected_items_post_load,
        }

        self.ctx = ctx
        self.save_queue: dict[str, int] = {}
        self.data_to_load = {}

    async def post_load_routine(self) -> None:
        # Force redraw
        await self.game_controller.poke_ram(self.ctx, get_ram_addr("REDRAW_FLAG"), b"\x01")

    async def rank_post_load(self, load_bytes: bytes) -> None:
        rank = int.from_bytes(load_bytes)
        if rank > 0:
            hp = get_max_health(self.char, rank)
            await self.game_controller.poke_ram(self.ctx, get_ram_addr("HEALTH", self.char), int.to_bytes(hp))

    async def collected_items_post_load(self, load_bytes: bytes) -> None:
        # Manually remove items on Level 1 if already collected
        for index in one_indices(int.from_bytes(load_bytes[4:8]), 32):
            await self.game_controller.poke_ram(self.ctx, get_slot_addr("FLOOR_ITEMS", index), EMPTY_ITEM)

    async def append_to_save_queue(self, name: str, data: int) -> None:
        self.save_queue[name] = data

    async def tick(self) -> None:
        for monitor in self.monitors:
            await monitor.tick()
        if self.save_queue:
            self.ticks += 1
            if self.ticks > self.sync_interval:
                await self.update_save_on_server()
                self.ticks = 0

    async def data_changed(self, from_monitor: "AddressMonitor", ctx: "BizHawkClientContext",
                           old_data: bytes, new_data: bytes):
        if from_monitor.monitor_level == MonitorLevel.GLOBAL:
            data_to_save = GLOBAL_DATA_STRUCTURES[from_monitor.name].repr_for_saving(new_data)
        else:
            data_to_save = PLAYER_DATA_STRUCTURES[from_monitor.name].repr_for_saving(new_data)
        await self.append_to_save_queue(from_monitor.name, data_to_save)

    async def update_save_on_server(self) -> None:
        await self.ctx.send_msgs([{
            "cmd": "Set",
            "key": k,
            "want_reply": False,
            "operations": [
                {
                    "operation": "replace",
                    "value": v,
                }
            ]
        } for k, v in self.save_queue.items()])
        self.save_queue.clear()

    async def handle_init_flag_changed(self, from_monitor: "AddressMonitor", ctx: "BizHawkClientContext",
                                   old_data: bytes, new_data: bytes):
        if int.from_bytes(new_data) == 1:
            logger.debug("Game initialization complete")
            if self.data_to_load:
                logger.debug("Loading data retrieved from server")
                await bizhawk.lock(ctx.bizhawk_ctx)
                # Load data
                for name, data in self.data_to_load.items():
                    if data is not None:
                        addr = get_ram_addr(name)
                        structure = get_datastructure(name)
                        load_bytes = structure.repr_for_loading(data)
                        await self.game_controller.poke_ram(ctx, addr, load_bytes)

                        if name in self.post_loading_routines:
                            await self.post_loading_routines.get(name)(load_bytes)

                await self.post_load_routine()

                await bizhawk.unlock(ctx.bizhawk_ctx)
                logger.debug("Loading complete")
            self.game_controller.awaiting_load = False
        else:
            logger.debug("Possible reset from in-game detected")
            self.game_controller.awaiting_load = True

class AddressMonitor():
    @staticmethod
    def create_as_save_monitor(structure_name: str, level: MonitorLevel, on_trigger_fn: Callable,
                                   gc: "TJEGameController", ctx: "BizHawkClientContext") -> "AddressMonitor":
        if level == MonitorLevel.GLOBAL:
            structure = GLOBAL_DATA_STRUCTURES[structure_name]
        else:
            structure = PLAYER_DATA_STRUCTURES[structure_name]
        return AddressMonitor(
            structure_name,
            structure_name,
            structure.size(),
            level,
            lambda: not gc.is_on_menu() and not gc.is_awaiting_load(),
            on_trigger_fn,
            gc,
            ctx,
            False
            )

    def __init__(self, name: str, addr_name: str, size: int, level: MonitorLevel, enable_test_fn: Callable,
                 on_trigger_fn: Callable, parent: "TJEGameController", ctx: "BizHawkClientContext",
                 enabled: bool = False):
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
        await self.on_trigger(self, self.ctx, self.old_data[index], self.new_data[index])

class TJEGameController():
    def __init__(self, client: "BizHawkClient"):
        self.client = client

        logger.debug("Resetting game…")

        # Game state–related

        self.is_playing: bool = False
        self.game_complete: bool = False

        self.current_level = -1

        # Saving and loading–related

        self.connected = False
        self.awaiting_load = True

        # Misc

        self.monitors = []
        self.dynamic_hints = {}

        self.char = 0

        self.auto_bad_presents = 0
        self.expanded_inv = False

    #region Per-update high-level logic functions

    async def tick(self, ctx: "BizHawkClientContext"):
        self.connected = (ctx.bizhawk_ctx.connection_status == ConnectionStatus.CONNECTED)
        if self.connected:
            if not self.game_complete:
                await self.update_game_state(ctx)
                for monitor in self.monitors: await monitor.tick()

    #endregion

    #region Initialization functions

    def add_monitors(self, ctx: "BizHawkClientContext", char: int, death_link: bool):
        level = character_to_monitor_level(char)

        self.char = char

        self.monitors = [
            AddressMonitor(
                "Collected items",
                "COLLECTED_ITEMS",
                104,
                MonitorLevel.GLOBAL,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_collected_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Ship item",
                "TRIGGERED_SHIP_ITEMS",
                10,
                MonitorLevel.GLOBAL,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_ship_item_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Rank",
                "RANK",
                1,
                level,
                lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                self.handle_rank_change,
                self,
                ctx
            ),
            AddressMonitor(
                "Level",
                "LEVEL",
                1,
                level,
                lambda: True,
                self.handle_level_change,
                self,
                ctx,
                enabled=True
            ),
            AddressMonitor( # only used for on-the-fly hint generation
                "Items set",
                "AP_LEVEL_ITEMS_SET",
                1,
                MonitorLevel.GLOBAL,
                lambda: True,
                self.handle_items_set,
                self,
                ctx,
            )
        ]

        if death_link:
            self.monitors.append(
                AddressMonitor(
                    "Lives",
                    "LIVES",
                    1,
                    level,
                    lambda: not self.is_on_menu() and not self.is_awaiting_load(),
                    self.handle_lives_change,
                    self,
                    ctx
                ),
            )

    def initialize_slot_data(self, auto_bad_presents: int, expanded_inv: bool):
        self.auto_bad_presents = auto_bad_presents
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

    async def get_empty_dropped_present_slot(self, ctx: "BizHawkClientContext") -> Optional[int]:
        dropped_presents_table = await self.peek_ram(ctx, get_ram_addr("DROPPED_PRESENTS", self.char), 256)
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
        if self.auto_bad_presents > 0 and item_id in BAD_PRESENT_IDS:
            if not (self.auto_bad_presents == 1 and item_id == ITEM_NAME_TO_ID["Randomizer"]):
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
        logger.debug("Attempting to spawn item %s", ITEM_ID_TO_NAME[item_id])
        if self.is_playing:
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
        if item_id in PRESENT_IDS and await self.is_inventory_full(ctx):
            return False
        item_code = ITEM_ID_TO_CODE[item_id]
        return await self.poke_ram(ctx, get_ram_addr("AP_GIVE_ITEM"), item_code.to_bytes(1))

    async def is_inventory_full(self, ctx: "BizHawkClientContext") -> bool:
        return await self.peek_ram(ctx,
                                   get_slot_addr("INVENTORY", PLAYER_DATA_STRUCTURES["INVENTORY"].max_slot, self.char),
                                   1) != EMPTY_PRESENT

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
        return True, STATIC_DIALOGUE_LIST[ITEM_ID_TO_NAME[ship_piece_id]]

    #endregion

    #region Change handling & monitor-related functions

    def is_on_menu(self) -> bool:
        return (not self.is_playing or self.current_level == -1)

    def is_awaiting_load(self) -> bool:
        return self.awaiting_load

    async def is_player_dead(self, ctx: "BizHawkClientContext") -> bool:
        sprite = await self.peek_ram(ctx, get_ram_addr("SPRITE", self.char), 1)
        return sprite in DEAD_SPRITES

    async def handle_lives_change(self, from_monitor: AddressMonitor, ctx: "BizHawkClientContext",
                                  old_data: bytes, new_data: bytes):
        if int.from_bytes(new_data) < int.from_bytes(old_data):
            await ctx.send_death()

    async def kill_player(self, ctx: "BizHawkClientContext"):
        if not await self.is_player_dead(ctx):
            await self.poke_ram(ctx, get_ram_addr("HEALTH", self.char), b"\x00")

    async def handle_items_set(self, from_monitor: AddressMonitor, ctx: "BizHawkClientContext",
                                  old_data: bytes, new_data: bytes):
        if int.from_bytes(new_data) == 1 and self.current_level != -1:
            map_data = await self.peek_ram(ctx, get_ram_addr("CURRENT_LEVEL_DATA"), 988)
            floor_item_data = await self.peek_ram(ctx, get_ram_addr("FLOOR_ITEMS"), 256)
            if self.dynamic_hints.get(self.current_level, None) is None:
                hints = generate_hints_for_current_level(self.current_level, map_data, floor_item_data)
                self.dynamic_hints.update(hints)
            await self.poke_ram(ctx, get_ram_addr("AP_LEVEL_ITEMS_SET"), b"\x00")

    async def handle_level_change(self, from_monitor: AddressMonitor, ctx: "BizHawkClientContext",
                                  old_data: bytes, new_data: bytes):
        await self.update_game_state(ctx)
        # Special handling for menu, aka "level -1"
        old_level = self.current_level
        self.current_level = int.from_bytes(new_data) if self.is_playing else -1
        logger.debug("Level changed from %i to %i", old_level, self.current_level)

    async def handle_collected_item_change(self, from_monitor: AddressMonitor, ctx: "BizHawkClientContext",
                                       old_data: bytes, new_data: bytes):
        new_as_int, old_as_int = int.from_bytes(new_data), int.from_bytes(old_data)
        if new_as_int > old_as_int:
            changed_indices = one_indices(new_as_int ^ old_as_int, 104*8)
            level_item_pairs = [divmod(i, 32) for i in changed_indices]
            for (level, item_num) in level_item_pairs:
                await self.client.trigger_location(ctx, FLOOR_ITEM_LOC_TEMPLATE.format(level, item_num+1))

    async def handle_ship_item_change(self, from_monitor: AddressMonitor, ctx: "BizHawkClientContext",
                                      old_data: bytes, new_data: bytes):
        # This is an extra failsafe to avoid trouble during resets
        await self.update_game_state(ctx)
        if self.is_playing:
            triggered_levels = [old_data[i] for i in range(10) if new_data[i] != old_data[i] and old_data[i] != 0]
            for level in triggered_levels:
                logger.debug("Triggering ship piece on level %i", level)
                await self.client.trigger_location(ctx, SHIP_PIECE_LOC_TEMPLATE.format(level))

    async def handle_rank_change(self, from_monitor: AddressMonitor, ctx: "BizHawkClientContext",
                                 old_data: bytes, new_data: bytes):
        rank = int.from_bytes(new_data)
        if rank > 0:
            loc = RANK_LOC_TEMPLATE.format(RANK_NAMES[rank])
            await self.client.trigger_location(ctx, loc)

    async def update_game_state(self, ctx: "BizHawkClientContext") -> None:
        player_state = await self.peek_ram(ctx, get_ram_addr("STATE", self.char), 1)
        self.is_playing = (player_state != b"\x00")

    #endregion