from typing import TYPE_CHECKING
import time
import logging

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem, add_json_text, JSONTypes
from Utils import async_start

from .constants import SAVE_DATA_POINTS_ALL, expand_inv_constants, ret_val_to_char
# from .hint import TJEHint
from .items import ITEM_ID_TO_NAME, INSTATRAP_IDS, SHIP_PIECE_IDS
from .locations import LOCATION_ID_TO_NAME, LOCATION_NAME_TO_ID
from .ram import TJEGameController, SaveManager

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger(__name__)

class SpawnQueue():
    def __init__(self, cooldown: int = 0):
        self.queue: list[NetworkItem] = []
        self.counter = cooldown
        self.cooldown = cooldown
        self.awarded_count = None # will be initialized to 0 / saved value after checking for savedata on server
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

    async def mark_awarded(self, nwi: NetworkItem) -> None:
        self.awarded_count += 1
        if self.save_manager:
            await self.save_manager.append_to_save_queue("awarded_count", self.awarded_count)
        if nwi in self.queue:
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

    save_manager = None

    queue = SpawnQueue()

    auto_bad_presents = 0

    pending_deathlink = False

    def __init__(self):
        super().__init__()

        self.game_controller = TJEGameController(self)

        self.post_reset_init()

    def post_reset_init(self) -> None:
        self.game_controller.awaiting_load = True
        self.queue.awarded_count = None
        self.queue.empty()

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

        ctx.game = self.game
        ctx.items_handling = 0b011 # Initial inventory handled locally; everything else remote
        ctx.want_slot_data = False
        ctx.watcher_timeout = 0.125
        ctx.sent_death_time = None
        ctx.save_retrieved = False

        death_link = bool(await self.peek_rom(ctx, 0x001f0001, 1))
        await ctx.update_death_link(death_link)

        success = await self.setup_game_controller(ctx, death_link)

        return success

    async def setup_game_controller(self, ctx: "BizHawkClientContext", death_link: bool) -> bool:
        try:
            # Game controller

            menu_ret_val = int.from_bytes(await self.peek_rom(ctx, 0x000242c5, 1))
            char = ret_val_to_char(menu_ret_val)

            self.auto_bad_presents = int.from_bytes(await self.peek_rom(ctx, 0x001f0005, 1))
            expanded_inv = int.from_bytes(await self.peek_rom(ctx, 0x0000979c+3, 1)) == 0x1D

            self.game_controller.initialize_slot_data(self.auto_bad_presents, expanded_inv)
            self.game_controller.add_monitors(ctx, char, death_link)

            # Save manager

            if expanded_inv:
                expand_inv_constants()
            self.save_manager = SaveManager(1, char, self.game_controller, ctx)
            self.queue.connect_save_manager(self.save_manager)

            return True
        except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            logger.error("Failed to initialize game controller")
            return False

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        async_start(self.process_tje_cmd(ctx, cmd, args))

    async def process_network_items(self, ctx: "BizHawkClientContext", args: dict) -> None:
        for index, nwi in enumerate(args["items"], start=args["index"]):
            if index >= self.queue.awarded_count:
                await self.process_item(ctx, nwi)

    async def retrieve_server_save(self, ctx: "BizHawkClientContext"):
        await ctx.send_msgs([{
            "cmd": "Get",
            "keys": ["awarded_count"] + list(SAVE_DATA_POINTS_ALL)
        }])

    async def process_tje_cmd(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        match cmd:
            case "Connected":
                await self.retrieve_server_save(ctx)
            case "Bounced":
                if "DeathLink" in args.get("tags", []) and \
                    args["data"]["time"] != ctx.sent_death_time:
                        self.pending_deathlink = True
            case "Retrieved":
                if "awarded_count" in args["keys"]:
                    saved_ac = args["keys"].get("awarded_count")
                    if saved_ac:
                        self.queue.awarded_count = saved_ac
                    else:
                        self.queue.awarded_count = 0
                    # initial loading of entire save state
                    savedata_keys = set(args["keys"].keys()) & frozenset(SAVE_DATA_POINTS_ALL)
                    if len(savedata_keys) > 0:
                        self.save_manager.data_to_load = {k:v for k, v in args["keys"].items()
                                                          if k in savedata_keys and v is not None}
                    await ctx.send_msgs([{
                        "cmd": "Sync"
                    }])
            case "ReceivedItems":
                if self.queue.awarded_count is not None:
                    await self.process_network_items(ctx, args)

    async def goal_in(self, ctx: "BizHawkClientContext") -> None:
        await ctx.send_msgs([{
            "cmd": "StatusUpdate",
            "status": ClientStatus.CLIENT_GOAL
        }])
        self.game_controller.game_complete = True
        ctx.finished_game = True
        self.queue.empty()

    async def trigger_location(self, ctx: "BizHawkClientContext", name: str) -> bool:
        loc_id = LOCATION_NAME_TO_ID.get(name, None)

        if loc_id is not None:
            await ctx.send_msgs([{
                "cmd": "LocationChecks",
                "locations": [loc_id]
            }])
            return True
        return False

    # Determines whether an item should be spawned by the client or left to the game's own code to award
    def should_spawn_from_remote(self, ctx: "BizHawkClientContext", nwi: NetworkItem) -> bool:
        #!getitem'ed / server / remote
        if nwi.location <= 0 or nwi.player != ctx.slot:
            return True
        # instatrap or ship piece, any source
        if nwi.item in INSTATRAP_IDS or nwi.item in SHIP_PIECE_IDS:
            return True
        # local promotion, ship piece or reach check
        loc_name = LOCATION_ID_TO_NAME[nwi.location]
        return "Reach" in loc_name or "Promoted" in loc_name or "Ship Piece" in loc_name

    async def process_item(self, ctx: "BizHawkClientContext", nwi: NetworkItem) -> None:
        if self.should_spawn_from_remote(ctx, nwi):
            self.queue.add(nwi)
        else:
            await self.queue.mark_awarded(nwi)

    async def handle_queue(self, ctx: "BizHawkClientContext") -> None:
        if self.queue.awarded_count is not None:
            self.queue.tick()
            if self.queue.can_spawn():
                oldest = self.queue.oldest()
                success = await self.game_controller.receive_item(ctx, oldest.item)
                if success:
                    await self.queue.mark_awarded(oldest)

    async def handle_deathlink(self, ctx: "BizHawkClientContext") -> None:
        if self.pending_deathlink:
            self.pending_deathlink = False
            await self.game_controller.kill_player(ctx)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        await self.game_controller.level_monitor.tick()
        if await self.game_controller.check_if_on_menu(ctx):
            self.game_controller.current_level = -1
            # retrieve save data after local reset; if not connected, on_package will request the same on connect
            if not ctx.save_retrieved:
                await self.retrieve_server_save(ctx)
                ctx.save_retrieved = True
                self.game_controller.awaiting_load = True
        else:
            await self.game_controller.tick(ctx)
            if not ctx.finished_game:
                await self.handle_queue(ctx)
                await self.handle_deathlink(ctx)
                await self.save_manager.tick()
                if self.game_controller.current_level == 26:
                    await self.goal_in(ctx)
