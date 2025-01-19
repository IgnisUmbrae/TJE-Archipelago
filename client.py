from typing import TYPE_CHECKING, Any, Callable
import json
import logging

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem
from Utils import async_start, home_path

from .constants import add_save_data_points, ret_val_to_char
from .items import EDIBLE_IDS, ITEM_ID_TO_NAME, PRESENT_IDS, INSTATRAP_IDS, SHIP_PIECE_IDS, BAD_PRESENT_IDS
from .locations import LOCATION_ID_TO_NAME, LOCATION_NAME_TO_ID
from .ram import TJEGameController

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger(__name__)

class SaveManager():
    def __init__(self, get_save_data_fn: Callable):
        self.save_file_name = None
        self.last_saved_hash = None
        self.get_save_data = get_save_data_fn

    def save_to_disk(self) -> bool:
        save_data, save_hash = self.get_save_data()
        if (self.save_file_name is not None and save_data is not None
            and (self.last_saved_hash is None or (self.last_saved_hash != save_hash))):
            with open(home_path(f"{self.save_file_name}.aptjesave"), "wb") as f:
                basd = f.write(b"".join(save_data))
                print(f"Wrote {basd} bytes")
            self.last_saved_hash = save_hash
            return True
        return False

class SpawnQueue():
    def __init__(self, cooldown : int = 5):
        self.queue : list[NetworkItem] = []
        self.counter = cooldown
        self.cooldown = cooldown
        self.reset_cooldown()

    def can_spawn(self) -> bool:
        return (self.counter == 0 and self.queue)

    def tick(self) -> None:
        self.counter = max(self.counter - 1, 0)

    def oldest(self) -> NetworkItem:
        return self.queue[0]

    def add(self, nwi : NetworkItem) -> None:
        self.queue.append(nwi)

    def mark_spawned(self, nwi : NetworkItem) -> None:
        self.queue.remove(nwi)
        self.reset_cooldown()

    def reset_cooldown(self) -> None:
        self.counter = self.cooldown

    def empty(self) -> None:
        self.queue.clear()

class TJEClient(BizHawkClient):
    game = "ToeJam and Earl"
    system = "GEN"
    patch_suffix = ".aptje"

    def __init__(self):
        super().__init__()

        self.game_controller = TJEGameController(self)
        self.save_manager = SaveManager(self.game_controller.get_save_state)

        self.last_processed_index = None
        self.auto_bad_presents = False

        self.edible_queue = SpawnQueue(cooldown=1)
        self.present_queue = SpawnQueue(cooldown=1)
        self.trap_queue = SpawnQueue(cooldown=1)
        self.misc_queue = SpawnQueue(cooldown=1)

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

        success = await self.setup_game_controller(ctx)

        return success

    async def setup_game_controller(self, ctx: "BizHawkClientContext") -> bool:
        try:
            menu_ret_val = int.from_bytes(await self.peek_rom(ctx, 0x000242c5, 1))
            char = ret_val_to_char(menu_ret_val)

            self.auto_bad_presents = bool.from_bytes(await self.peek_rom(ctx, 0x001f0005, 1))
            expanded_inv = int.from_bytes(await self.peek_rom(ctx, 0x0000979c+3, 1)) == 0x1D

            self.game_controller.initialize_slot_data(self.auto_bad_presents, expanded_inv)
            self.game_controller.add_monitors(ctx, char)

            add_save_data_points(char, expanded_inv)

            self.last_processed_index = -1

            return True
        except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            logger.error("Failed to initialize game controller")
            return False

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        async_start(self.process_tje_cmd(ctx, cmd, args))

    async def process_tje_cmd(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        match cmd:
            case "RoomInfo":
                self.save_manager.save_file_name = args["seed_name"] + ctx.auth
            case "ReceivedItems":
                ignore_realtime_items = True if self.last_processed_index == -1 else False
                for index, nwi in enumerate(args["items"], start=args["index"]):
                    if (index > self.last_processed_index
                        and not (ignore_realtime_items and nwi.item in EDIBLE_IDS+INSTATRAP_IDS)):
                        logger.debug("* Processing item: %s", ITEM_ID_TO_NAME[nwi.item])
                        self.process_item(ctx, nwi)
                        self.last_processed_index = index
                logger.debug("Last processed: item index %s", self.last_processed_index)

    async def goal_in(self, ctx: "BizHawkClientContext") -> None:
        logger.debug("Finished game!")
        await ctx.send_msgs([{
            "cmd": "StatusUpdate",
            "status": ClientStatus.CLIENT_GOAL
        }])
        self.game_controller.game_complete = True
        ctx.finished_game = True

        self.edible_queue.empty()
        self.present_queue.empty()
        self.misc_queue.empty()
        self.trap_queue.empty()

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
        await self.handle_queue(ctx, self.edible_queue)
        await self.handle_queue(ctx, self.present_queue)
        await self.handle_queue(ctx, self.misc_queue)
        await self.handle_queue(ctx, self.trap_queue)

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
            #logger.debug("Sending item: %s", ITEM_ID_TO_NAME[oldest.item])
            success = await self.game_controller.receive_item(ctx, oldest.item)
            if success:
                queue.mark_spawned(oldest)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        await self.game_controller.tick(ctx)

        if not ctx.finished_game:
            await self.handle_items(ctx)
            if self.game_controller.current_level == 26:
                await self.goal_in(ctx)
            #self.save_manager.save_to_disk(ctx)