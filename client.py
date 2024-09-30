from typing import TYPE_CHECKING
import logging

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem

from .ram import TJEGameController
from .items import EDIBLE_IDS, PRESENT_IDS, INSTATRAP_IDS
from .locations import LOCATION_NAME_TO_ID

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

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

        self.edible_queue = SpawnQueue(cooldown=2)
        self.present_queue = SpawnQueue(cooldown=1)
        self.trap_queue = SpawnQueue(cooldown=1)
        self.misc_queue = SpawnQueue(cooldown=1)

        self.ticks = 0

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            rom_name = ((await bizhawk.read(ctx.bizhawk_ctx, [(0x150, 13, "MD CART")]))[0]).decode("ascii")
            version = ((await bizhawk.read(ctx.bizhawk_ctx, [(0x18c, 2, "MD CART")]))[0]).decode("ascii")
        except (UnicodeDecodeError, bizhawk.RequestFailedError, bizhawk.NotConnectedError):
            return False
        if rom_name != "TOEJAM & EARL" or version != "02":
            return False

        ctx.game = self.game
        ctx.items_handling = 0b011 # Initial inventory handled in patch; everything else remote
        ctx.want_slot_data = True
        ctx.watcher_timeout = 0.125

        char = int.from_bytes((await bizhawk.read(ctx.bizhawk_ctx, [(0x000242c5, 1, "MD CART")]))[0])

        self.game_controller.add_monitors(ctx, char)
        self.game_controller.create_save_points()

        return True

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        super().on_package(ctx, cmd, args)
        if cmd == "Connected":
            self.game_controller.handle_slot_data(args["slot_data"])

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

    async def handle_new_items(self, ctx: "BizHawkClientContext") -> None:
        num_new = len(ctx.items_received) - self.num_items_received
        # Sort items into the appropriate queues
        if num_new > 0:
            for nwi in ctx.items_received[-num_new:]:
                if nwi.item in PRESENT_IDS: self.present_queue.add(nwi)
                elif nwi.item in EDIBLE_IDS: self.edible_queue.add(nwi)
                elif nwi.item in INSTATRAP_IDS: self.trap_queue.add(nwi)
                else: self.misc_queue.add(nwi)

            self.num_items_received = len(ctx.items_received)

    async def handle_queue(self, ctx: "BizHawkClientContext", queue: SpawnQueue) -> None:
        queue.tick()
        if queue.can_spawn():
            oldest = queue.oldest()
            success = await self.game_controller.receive_item(ctx, oldest.item)
            if success:
                queue.mark_spawned(oldest)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        self.ticks += 1
        await self.game_controller.tick(ctx)

        if not ctx.finished_game:
            await self.handle_items(ctx)
            if self.game_controller.num_ship_pieces_owned == 10:
                await self.goal_in(ctx)
