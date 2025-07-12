from typing import TYPE_CHECKING
import time
import logging

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem, add_json_text, JSONTypes
from Utils import async_start

from .constants import SAVE_DATA_POINTS_ALL, expand_inv_constants, ret_val_to_char
from .hint import TJEHint
from .items import EDIBLE_IDS, ITEM_ID_TO_NAME, PRESENT_IDS, INSTATRAP_IDS, SHIP_PIECE_IDS, BAD_PRESENT_IDS
from .locations import LOCATION_ID_TO_NAME, LOCATION_NAME_TO_ID
from .ram import TJEGameController, SaveManager

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger(__name__)

class SpawnQueue():
    def __init__(self, name: str, cooldown: int = 1):
        self.name = name
        self.queue: list[NetworkItem] = []
        self.counter = cooldown
        self.cooldown = cooldown
        self.spawned_count = 0
        self.save_manager = None
        self.reset_cooldown()

    def can_spawn(self) -> bool:
        return (self.counter == 0 and self.queue)

    def tick(self) -> None:
        self.counter = max(self.counter - 1, 0)

    def oldest(self) -> NetworkItem:
        return self.queue[0]

    def add(self, nwi: NetworkItem) -> None:
        self.queue.append(nwi)

    async def mark_spawned(self, nwi: NetworkItem) -> None:
        self.spawned_count += 1
        if self.save_manager:
            await self.save_manager.append_to_save_queue(self.name, self.spawned_count)
        self.queue.remove(nwi)
        self.reset_cooldown()

    def reset_cooldown(self) -> None:
        self.counter = self.cooldown

    def empty(self) -> None:
        self.queue.clear()

    def connect_save_manager(self, manager: SaveManager) -> None:
        self.save_manager = manager

class TJEClient(BizHawkClient):
    game = "ToeJam and Earl"
    system = "GEN"
    patch_suffix = ".aptje"

    def __init__(self):
        super().__init__()

        self.game_controller = TJEGameController(self)
        self.save_manager = None

        self.auto_bad_presents = 0
        self.death_link = False

        self.edible_queue = SpawnQueue("EDIBLE_QUEUE")
        self.present_queue = SpawnQueue("PRESENT_QUEUE")
        self.trap_queue = SpawnQueue("TRAP_QUEUE")
        self.misc_queue = SpawnQueue("MISC_QUEUE")
        self.queues = [self.edible_queue, self.present_queue, self.trap_queue, self.misc_queue]

        self.hints_seen = 0

        self.post_reset_init()

    def post_reset_init(self) -> None:
        self.game_controller.awaiting_load = True
        self.last_processed_index = None
        self.ignore_realtime = False
        for queue in self.queues:
            queue.empty()

    async def peek_rom(self, ctx: "BizHawkClientContext", address: int, size: int) -> bytes:
        return (await bizhawk.read(ctx.bizhawk_ctx, [(address, size, "MD CART")]))[0]

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            rom_name = (await self.peek_rom(ctx, 0x150, 13)).decode("ascii")
            version = (await self.peek_rom(ctx, 0x18c, 2)).decode("ascii")
        except (UnicodeDecodeError, bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            return False

        if rom_name != "TOEJAM & EARL":
            logger.error("Selected ROM is not a ToeJam & Earl ROM")
            return False
        elif version != "02":
            logger.error("Selected ToeJam & Earl ROM appears to be REV00, not REV02")
            return False

        ctx.game = self.game
        ctx.items_handling = 0b011 # Initial inventory handled locally; everything else remote
        ctx.want_slot_data = False
        ctx.watcher_timeout = 0.125

        death_link = bool(await self.peek_rom(ctx, 0x001f0001, 1))
        if death_link:
            await ctx.update_death_link(death_link)
            self.death_link = death_link

        success = await self.setup_game_controller(ctx)

        return success

    async def setup_game_controller(self, ctx: "BizHawkClientContext") -> bool:
        try:
            # Game controller

            menu_ret_val = int.from_bytes(await self.peek_rom(ctx, 0x000242c5, 1))
            char = ret_val_to_char(menu_ret_val)

            self.auto_bad_presents = int.from_bytes(await self.peek_rom(ctx, 0x001f0005, 1))
            expanded_inv = int.from_bytes(await self.peek_rom(ctx, 0x0000979c+3, 1)) == 0x1D

            self.game_controller.initialize_slot_data(self.auto_bad_presents, expanded_inv)
            self.game_controller.add_monitors(ctx, char, ("DeathLink" in ctx.tags))

            # Save manager

            if expanded_inv:
                expand_inv_constants()
            self.save_manager = SaveManager(1, char, self.game_controller, ctx)
            for queue in self.queues:
                queue.connect_save_manager(self.save_manager)

            return True
        except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            logger.error("Failed to initialize game controller")
            return False

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        async_start(self.process_tje_cmd(ctx, cmd, args))

    async def set_last_processed_index(self, ctx: "BizHawkClientContext") -> None:
        await ctx.send_msgs([{
            "cmd": "Set",
            "key": "last_index",
            "default": -1,
            "want_reply": False,
            "operations": [
                {
                    "operation": "replace",
                    "value": self.last_processed_index,
                }
            ]
        }])

    async def process_network_items(self, ctx: "BizHawkClientContext", args: dict) -> None:
        for index, nwi in enumerate(args["items"], start=args["index"]):
            if index > self.last_processed_index:
                logger.debug("* Processing item: %s", ITEM_ID_TO_NAME[nwi.item])
                self.process_item(ctx, nwi)
                self.last_processed_index = index
        self.ignore_realtime = False
        await self.set_last_processed_index(ctx)

    async def process_tje_cmd(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        match cmd:
            case "Connected":
                await ctx.send_msgs([{
                    "cmd": "Get",
                    "keys": ["last_index"] + list(SAVE_DATA_POINTS_ALL)
                }])
            case "DeathLink":
                logger.debug("DEATHLINK: Received deathlink death")
                if self.death_link and ctx.last_death_link + 1 < time.time():
                    logger.debug("DEATHLINK: Awarding death")
                    await self.game_controller.kill_player(ctx)
            case "RoomInfo":
                pass
            case "SetReply": # only displays hints the first time they're requested
                pass
                # if args.get("key") == f"_read_{ctx.team}_{ctx.slot}":
                #     hints = args.get("value")
                #     for hint in hints[self.hints_seen:]:
                #         hint_data = self.game_controller.dynamic_hints.get(hint["location"], None)
                #         if hint_data:
                #             await self.display_local_hint(ctx, hint_data)
                #     self.hints_seen = len(hints)
            case "Retrieved":
                if "last_index" in args["keys"]:
                    val = args["keys"].get("last_index")
                    if val:
                        self.last_processed_index = args["keys"].get("last_index")
                        self.ignore_realtime = True
                    else:
                        self.last_processed_index = -1
                        self.ignore_realtime = False
                    await ctx.send_msgs([{
                        "cmd": "Sync"
                    }])
                # initial loading of entire save state
                savedata_keys = set(args["keys"].keys()) & frozenset(SAVE_DATA_POINTS_ALL)
                if len(savedata_keys) > 0:
                    self.save_manager.data_to_load = {k:v for k, v in args["keys"].items() if k in savedata_keys}
            case "ReceivedItems":
                if self.last_processed_index is not None:
                    await self.process_network_items(ctx, args)

    async def display_local_hint(self, ctx: "BizHawkClientContext", hint: TJEHint) -> None:
        parts = []
        add_json_text(parts, LOCATION_ID_TO_NAME(hint.location_id), type=JSONTypes.location_name)
        add_json_text(parts, hint.hint_text, type=JSONTypes.text)
        ctx.on_print_json({"data": parts, "cmd": "PrintJSON"})

    async def goal_in(self, ctx: "BizHawkClientContext") -> None:
        logger.debug("Finished game!")
        await ctx.send_msgs([{
            "cmd": "StatusUpdate",
            "status": ClientStatus.CLIENT_GOAL
        }])
        self.game_controller.game_complete = True
        ctx.finished_game = True

        for queue in self.queues:
            queue.empty()

    async def trigger_location(self, ctx: "BizHawkClientContext", name: str) -> bool:
        loc_id = LOCATION_NAME_TO_ID.get(name, None)

        if loc_id is not None:
            logger.debug("Triggering location: %s", name)
            await ctx.send_msgs([{
                "cmd": "LocationChecks",
                "locations": [loc_id]
            }])
            return True
        return False

    async def handle_items(self, ctx: "BizHawkClientContext") -> None:
        for queue in self.queues:
            await self.handle_queue(ctx, queue)

    # Determines whether an item should be spawned by the client or left to the game's own code to award
    # Rank checks and ship pieces are currently unable to award items purely via ROM
    def should_spawn_from_remote(self, ctx: "BizHawkClientContext", nwi: NetworkItem) -> bool:
        #!getitem'ed / server / remote
        if nwi.location <= 0 or nwi.player != ctx.slot:
            return True
        loc_name = LOCATION_ID_TO_NAME[nwi.location]
        return "Promoted" in loc_name or "Ship Piece" in loc_name

    def should_spawn_present_as_trap(self, nwi: NetworkItem) -> bool:
        return (self.auto_bad_presents > 0 and nwi.item in BAD_PRESENT_IDS and
                            not (self.auto_bad_presents == 1 and ITEM_ID_TO_NAME[nwi.item] == "Randomizer"))

    def process_item(self, ctx: "BizHawkClientContext", nwi: NetworkItem) -> None:
        if self.ignore_realtime and nwi.item in EDIBLE_IDS+INSTATRAP_IDS:
            logger.debug("Ignoring realtime item received while offline")
            return
        if nwi.item in INSTATRAP_IDS:
            self.trap_queue.add(nwi)
        elif nwi.item in SHIP_PIECE_IDS:
            self.misc_queue.add(nwi)
        else:
            if self.should_spawn_from_remote(ctx, nwi): # non-local item
                if nwi.item in PRESENT_IDS:
                    if self.should_spawn_present_as_trap(nwi):
                        self.trap_queue.add(nwi)
                    else:
                        self.present_queue.add(nwi)
                elif nwi.item in EDIBLE_IDS:
                    self.edible_queue.add(nwi)
                else:
                    self.misc_queue.add(nwi)

    async def handle_queue(self, ctx: "BizHawkClientContext", queue: SpawnQueue) -> None:
        queue.tick()
        if queue.can_spawn():
            oldest = queue.oldest()
            success = await self.game_controller.receive_item(ctx, oldest.item)
            if success:
                await queue.mark_spawned(oldest)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        await self.game_controller.tick(ctx)

        if not ctx.finished_game:
            await self.handle_items(ctx)
            await self.save_manager.tick()
            if self.game_controller.current_level == 26:
                await self.goal_in(ctx)
