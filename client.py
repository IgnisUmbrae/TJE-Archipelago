from typing import TYPE_CHECKING
import logging

import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient
from NetUtils import ClientStatus, NetworkItem

from .constants import DEBUG
from .ram import TJEGameController
from .items import EDIBLE_IDS, ITEM_ID_TO_NAME, KEY_IDS, PRESENT_IDS, SHIP_PIECE_IDS
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

        self.patched_ending = False

        self.edible_queue = SpawnQueue(cooldown=1)
        self.present_queue = SpawnQueue(cooldown=1)

        self.ticks = 0

    async def validate_rom(self, ctx: "BizHawkClientContext") -> bool:
        try:
            rom_name = ((await bizhawk.read(ctx.bizhawk_ctx, [(0x150, 13, "MD CART")]))[0]).decode("ascii")
            version = ((await bizhawk.read(ctx.bizhawk_ctx, [(0x18c, 2, "MD CART")]))[0]).decode("ascii")
        except (UnicodeDecodeError, bizhawk.RequestFailedError):
            return False
        if rom_name != "TOEJAM & EARL" or version != "02":
            return False

        ctx.game = self.game
        ctx.items_handling = 0b011 # Local inventory handled in patch
        ctx.want_slot_data = True

        self.game_controller.add_monitors(ctx)
        await self.game_controller.load_saved_game_state(ctx)

        return True

    def on_package(self, ctx: "BizHawkClientContext", cmd: str, args: dict) -> None:
        super().on_package(ctx, cmd, args)
        if cmd == "Connected":
            self.game_controller.handle_slot_data(args["slot_data"])

    # We're 1 piece away from done so we need the last ship piece collection to trigger the ending
    async def prepare_for_final_ship_piece(self, ctx: "BizHawkClientContext") -> None:
        try:
            await bizhawk.write(ctx.bizhawk_ctx, [(0x00020cf8, b"\x4E\xBA\xFB\xEA", "MD CART")])
            self.patched_ending = True
        except bizhawk.RequestFailedError:
            return

    async def goal_in(self, ctx: "BizHawkClientContext") -> None:
        print("Finished game!")
        await ctx.send_msgs([{
            "cmd": "StatusUpdate",
            "status": ClientStatus.CLIENT_GOAL
        }])

    # Ship pieces are always the last in the list of locations for each level,
    # so pass index = -1 to trigger one for a particular level
    async def trigger_location(self, ctx: "BizHawkClientContext", name : str) -> bool:
        try:
            loc_id = LOCATION_NAME_TO_ID[name]
            if DEBUG: logger.debug("Triggering location: %s", name)
            await ctx.send_msgs([{
                "cmd": "LocationChecks",
                "locations": [loc_id]
            }])
            return True
        except (KeyError, IndexError):
            logger.warning("WARNING: Attempted to trigger nonexistent location: %s!", name)
            return False

    async def handle_items(self, ctx: "BizHawkClientContext") -> None:
        await self.handle_new_items(ctx)

        if DEBUG:
            edibles_waiting = len(self.edible_queue.queue)
            presents_waiting = len(self.present_queue.queue)
            if edibles_waiting > 0:
                print(f"{edibles_waiting} edibles waiting to spawn")
            if presents_waiting > 0:
                print(f"{presents_waiting} presents waiting to spawn")
        await self.handle_queue(ctx, self.present_queue)
        await self.handle_queue(ctx, self.edible_queue)

    async def handle_new_items(self, ctx: "BizHawkClientContext") -> None:
        num_new = len(ctx.items_received) - self.num_items_received
        # Sort items into the appropriate queues
        if num_new > 0:
            #if DEBUG: logger.debug(f"Sorting {num_new} new items (of {len(ctx.items_received)} total)")
            for nwi in ctx.items_received[-num_new:]:
                #if DEBUG: print(f"Sorting item: {ITEM_ID_TO_NAME[nwi.item]}")
                if nwi.item in PRESENT_IDS: self.present_queue.add(nwi)
                elif nwi.item in EDIBLE_IDS: self.edible_queue.add(nwi)
                elif nwi.item in SHIP_PIECE_IDS: await self.game_controller.spawn_item(ctx, nwi.item)
                elif nwi.item in KEY_IDS: await self.game_controller.receive_key(ctx, nwi.item)

            self.num_items_received = len(ctx.items_received)

    async def handle_queue(self, ctx: "BizHawkClientContext", queue: SpawnQueue) -> None:
        queue.tick()
        if queue.can_spawn():
            oldest = queue.oldest()
            success = await self.game_controller.spawn_item(ctx, oldest.item)
            if DEBUG:
                if success:
                    print(f"Successfully spawned queued item {ITEM_ID_TO_NAME[oldest.item]}")
            if success:
                queue.mark_spawned(oldest)

    async def game_watcher(self, ctx: "BizHawkClientContext") -> None:
        self.ticks += 1
        await self.game_controller.tick(ctx)

        if not ctx.finished_game:
            await self.handle_items(ctx)
        if not self.patched_ending and self.game_controller.num_ship_pieces_owned == 9:
            await self.prepare_for_final_ship_piece(ctx)
        if not ctx.finished_game and self.game_controller.num_ship_pieces_owned == 10:
            await self.goal_in(ctx)