from typing import TYPE_CHECKING
import logging
import struct

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem

from .ram import TJEGameController
from .items import EDIBLE_IDS, ITEM_ID_TO_NAME, PRESENT_IDS, INSTATRAP_IDS, TRAP_PRESENT_IDS
from .locations import LOCATION_ID_TO_NAME, LOCATION_NAME_TO_ID

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger(__name__)

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
        self.num_items_received = 0
        self.auto_trap_presents = False

        self.edible_queue = SpawnQueue(cooldown=2)
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
            char = int.from_bytes(await self.peek_rom(ctx, 0x000242c5, 1))
            self.game_controller.add_monitors(ctx, char)
            self.game_controller.create_save_points()

            key_type = int.from_bytes(await self.peek_rom(ctx, 0x001f0000, 1))
            self.auto_trap_presents = int.from_bytes(await self.peek_rom(ctx, 0x001f0001, 1))

            key_count = int.from_bytes(await self.peek_rom(ctx, 0x001f0010, 1))
            key_levels = struct.unpack(f">{key_count}B", await self.peek_rom(ctx, 0x001f0011, key_count))

            ship_item_levels = struct.unpack(">10B", await self.peek_rom(ctx, 0x00097738, 10))

            self.game_controller.initialize_slot_data(ship_item_levels, key_levels, key_type, self.auto_trap_presents)

            return True
        except (bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            logger.error("Failed to initialize game controller")
            return False

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
        try:
            loc_id = LOCATION_NAME_TO_ID[name]
        except KeyError:
            return False

        logger.debug("Triggering location: %s", name)
        await ctx.send_msgs([{
            "cmd": "LocationChecks",
            "locations": [loc_id]
        }])
        return True

    async def handle_items(self, ctx: "BizHawkClientContext") -> None:
        await self.handle_new_items(ctx)

        await self.handle_queue(ctx, self.edible_queue)
        await self.handle_queue(ctx, self.present_queue)
        await self.handle_queue(ctx, self.misc_queue)
        await self.handle_queue(ctx, self.trap_queue)

    # Determines whether an item should be spawned by the client or left to the game's own code to award
    # Rank checks and ship pieces are currently unable to award items purely via ROM
    def spawn_from_remote(self, ctx: "BizHawkClientContext", nwi: NetworkItem) -> bool:
        if nwi.location == -1 or nwi.player != ctx.slot:
            return True
        loc_name = LOCATION_ID_TO_NAME[nwi.location]
        return "Promoted" in loc_name or "Ship Piece" in loc_name

    async def handle_new_items(self, ctx: "BizHawkClientContext") -> None:
        num_new = len(ctx.items_received) - self.num_items_received
        # Sort items into the appropriate queues
        if num_new > 0:
            logger.debug("Received %i new items", num_new)
            for nwi in ctx.items_received[-num_new:]:
                spawn_from_remote = self.spawn_from_remote(ctx, nwi)
                if nwi.item in PRESENT_IDS:
                    if spawn_from_remote:
                        if (self.auto_trap_presents > 0 and nwi.item in TRAP_PRESENT_IDS and
                            not (self.auto_trap_presents == 1 and ITEM_ID_TO_NAME[nwi.item] == "Randomizer")):
                            self.trap_queue.add(nwi)
                        else:
                            self.present_queue.add(nwi)
                elif nwi.item in EDIBLE_IDS:
                    if spawn_from_remote:
                        self.edible_queue.add(nwi)
                elif nwi.item in INSTATRAP_IDS:
                    self.trap_queue.add(nwi)
                else:
                    self.misc_queue.add(nwi)

            self.num_items_received = len(ctx.items_received)

    async def handle_queue(self, ctx: "BizHawkClientContext", queue: SpawnQueue) -> None:
        queue.tick()
        if queue.can_spawn():
            oldest = queue.oldest()
            logger.debug("Sending item: %s", ITEM_ID_TO_NAME[oldest.item])
            success = await self.game_controller.receive_item(ctx, oldest.item)
            if success:
                queue.mark_spawned(oldest)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        await self.game_controller.tick(ctx)

        if not ctx.finished_game:
            await self.handle_items(ctx)
            if self.game_controller.num_ship_pieces_owned == 10:
                await self.goal_in(ctx)
