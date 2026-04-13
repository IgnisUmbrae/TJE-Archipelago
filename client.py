from calendar import c
from typing import TYPE_CHECKING
import logging

import worlds._bizhawk as bizhawk
from worlds._bizhawk import ConnectionStatus
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem
from Utils import async_start

from .constants import SAVE_DATA_POINTS_ALL, expand_inv_constants, ret_val_to_char
# from .hint import TJEHint
from .items import ITEM_ID_TO_NAME, INSTATRAP_IDS, SHIP_PIECE_IDS
from .locations import LOCATION_ID_TO_NAME, LOCATION_NAME_TO_ID, REMOTE_SPAWN_ONLY_LOCS
from .ram import TJEGameController, SaveManager

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext, BizHawkClientCommandProcessor

logger = logging.getLogger("Client")

class SpawnQueue():
    def __init__(self, cooldown: int = 0):
        self.queue: list[NetworkItem | None] = []
        self.counter = cooldown
        self.cooldown = cooldown
        self.awarded_count = None # will be initialized to 0 / saved value after checking for savedata on server
        self.save_manager = None
        self.reset_cooldown()

    def can_spawn(self) -> bool:
        return (self.counter == 0 and self.queue)

    def tick(self) -> None:
        self.counter = max(self.counter - 1, 0)

    def oldest(self) -> NetworkItem | None:
        return self.queue[0]

    def add(self, nwi: NetworkItem | None) -> None:
        self.queue.append(nwi)

    async def mark_awarded_multiple(self, number: int) -> None:
        for _ in range(number):
            try:
                oldest = self.oldest()
            except IndexError:
                break # to catch rewinds throwing the count off sync
            await self.mark_awarded(oldest)

    async def mark_awarded(self, nwi: NetworkItem | None) -> None:
        self.awarded_count += 1
        if self.save_manager:
            await self.save_manager.append_to_save_queue("awarded_count", self.awarded_count)
        if nwi is None or nwi in self.queue:
            self.queue.pop(0)
        self.reset_cooldown()

    def reset_cooldown(self) -> None:
        self.counter = self.cooldown

    def empty(self) -> None:
        self.queue.clear()

    def connect_save_manager(self, manager: SaveManager) -> None:
        self.save_manager = manager

def cmd_unlock(self: "BizHawkClientCommandProcessor", level: str) -> None:
    """
    Force-unlocks elevators on levels <= the level specified.
    The argument 'all' will unlock every elevator.
    To be used as a failsafe in case of key count desync.
    """
    if self.ctx.game != "ToeJam and Earl":
        logger.warning("This command is only for use with ToeJam and Earl.")
        return
    if self.ctx.bizhawk_ctx.connection_status != ConnectionStatus.CONNECTED:
        logger.warning("Please connect to BizHawk before using this command.")
        return
    if self.ctx.on_menu:
        logger.warning("Please use this command in a level, not on the menu, " \
                       "as its effect is reset when you spawn into level 1.")
        return

    conversion_error = False
    if level == "all":
        level = 24
    else:
        try:
            level = int(level)
        except (ValueError, TypeError):
            conversion_error = True

    if conversion_error or not 2 <= level <= 24:
        logger.warning("Invalid level. Please specify a whole number between 2 and 24, or the keyword 'all'.")
        return
    async_start(bizhawk.write(self.ctx.bizhawk_ctx, [(0xf458, level.to_bytes(1), "68K RAM")]))
    logger.info(f"All elevators on levels <= {level} are now unlocked.")

class TJEClient(BizHawkClient):
    game = "ToeJam and Earl"
    system = "GEN"
    patch_suffix = ".aptje"

    save_manager = None

    queue = SpawnQueue()

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
        ctx.on_menu = True
        ctx.pending_deathlink = False

        elev_keys = int.from_bytes(await self.peek_rom(ctx, 0x001f0000, 1)) != 0

        if elev_keys and "unlock" not in ctx.command_processor.commands:
            ctx.command_processor.commands["unlock"] = cmd_unlock

        death_link = bool(int.from_bytes(await self.peek_rom(ctx, 0x001f0001, 1)))
        await ctx.update_death_link(death_link)
        mailboxes = int.from_bytes(await self.peek_rom(ctx, 0x001f0030, 1)) == 2
        lemonade = int.from_bytes(await self.peek_rom(ctx, 0x001f0008, 1)) == 1

        success = await self.setup_game_controller(ctx, death_link, mailboxes, lemonade)

        return success

    async def setup_game_controller(self, ctx: "BizHawkClientContext", death_link: bool, mailboxes: bool, lemonade: bool) -> bool:
        try:
            # Game controller

            menu_ret_val = int.from_bytes(await self.peek_rom(ctx, 0x000242c5, 1))
            char = ret_val_to_char(menu_ret_val)

            auto_bad_presents = int.from_bytes(await self.peek_rom(ctx, 0x001f0005, 1))
            auto_buck_presents = int.from_bytes(await self.peek_rom(ctx, 0x001f0006, 1))
            auto_point_presents = int.from_bytes(await self.peek_rom(ctx, 0x001f0007, 1))
            expanded_inv = int.from_bytes(await self.peek_rom(ctx, 0x0000979c+3, 1)) == 0x1D

            self.game_controller.initialize_slot_data(auto_bad_presents, auto_buck_presents,
                                                      auto_point_presents, expanded_inv)
            self.game_controller.add_monitors(ctx, char, death_link, mailboxes, lemonade)

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
        ctx.save_retrieved = True

    async def process_tje_cmd(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        match cmd:
            case "Connected":
                await self.retrieve_server_save(ctx)
            case "Bounced":
                if "DeathLink" in args.get("tags", []) and \
                    args["data"]["time"] != ctx.sent_death_time:
                        ctx.pending_deathlink = True
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
                if ctx.save_retrieved and self.queue.awarded_count is not None:
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
        # local promotion, ship piece, reach check or mailbox check
        loc_name = LOCATION_ID_TO_NAME[nwi.location]
        return loc_name in REMOTE_SPAWN_ONLY_LOCS

    async def process_item(self, ctx: "BizHawkClientContext", nwi: NetworkItem) -> None:
        if self.should_spawn_from_remote(ctx, nwi):
            self.queue.add(nwi)
        else: # add blank item to queue (keeps everything in strict order of receipt)
            self.queue.add(None)

    async def handle_queue(self, ctx: "BizHawkClientContext") -> None:
        if self.queue.awarded_count is not None:
            self.queue.tick()
            if self.queue.can_spawn():
                oldest = self.queue.oldest()
                if oldest is not None: # actual item
                    await self.game_controller.receive_item(ctx, oldest.item)
                else: # phantom entry for local item (to keep everything in sync)
                    await self.report_item_success(1, ctx)

    async def report_item_success(self, number: int, ctx: "BizHawkClientContext") -> None:
        await self.queue.mark_awarded_multiple(number)

    async def handle_deathlink(self, ctx: "BizHawkClientContext") -> None:
        if ctx.pending_deathlink:
            ctx.pending_deathlink = False
            await self.game_controller.kill_player(ctx)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        if await self.game_controller.check_if_on_menu(ctx):
            if not ctx.on_menu:
                self.game_controller.awaiting_load = True
                ctx.save_retrieved = False
                await self.retrieve_server_save(ctx)
            ctx.on_menu = True
        else:
            ctx.on_menu = False
            await self.game_controller.tick(ctx)
            if not ctx.finished_game:
                await self.handle_queue(ctx)
                await self.handle_deathlink(ctx)
                await self.save_manager.tick()
                if await self.game_controller.check_clear_condition(ctx):
                    await self.goal_in(ctx)
