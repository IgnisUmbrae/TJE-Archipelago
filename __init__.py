import os
import pkgutil
from typing import Optional, Any

from BaseClasses import CollectionState, ItemClassification
from worlds.AutoWorld import World, WebWorld

from .client import TJEClient # required to register with BizHawkClient
from .generators import TJEGenerator, get_key_levels
from .items import TJEItem, ITEM_NAME_TO_ID, ITEM_NAME_TO_DATA, create_items, create_starting_presents
from .locations import LOCATION_NAME_TO_ID
from .options import TJEOptions
from .regions import create_regions
from .rom import TJEProcedurePatch, write_tokens

class TJEWeb(WebWorld):
    theme = "partyTime"

class TJEWorld(World):
    """ToeJam & Earl"""

    game = "ToeJam and Earl"
    options_dataclass = TJEOptions
    options: TJEOptions
    topology_present = True

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    item_name_groups = {
        "Ship Pieces" : {
                        "Rocketship Windshield", "Left Megawatt Speaker", "Super Funkomatic Amplamator",
                        "Amplamator Connector Fin", "Forward Stabilizing Unit", "Rear Leg",
                        "Awesome Snowboard", "Righteous Rapmaster Capsule", "Right Megawatt Speaker",
                        "Hyperfunk Thruster"
                        }
    }

    def collect(self, state: "CollectionState", item: "TJEItem") -> bool:
        change = super().collect(state, item)
        if change:
            state.prog_items[item.player]["points"] += item.point_value
            state.prog_items[item.player]["ranks"] += item.rank_value
        return change

    def generate_early(self) -> None:
        self.seeds = [self.random.getrandbits(16) for _ in range(26)]
        self.generator = TJEGenerator(self)
        if self.options.key_type:
            self.key_levels = get_key_levels(self.options.key_gap.value)
        else:
            self.key_levels = []
        self.ship_item_levels = self.generator.generate_ship_piece_levels()
        if self.options.upwarp_present:
            self.generator.fewer_upwarps()

    def create_regions(self) -> None:
        create_regions(self.multiworld, self.player, self.options)

    def create_item(self, identifier: str | int, new_classification: Optional[ItemClassification] = None) -> TJEItem:
        name = identifier if isinstance(identifier, str) else self.item_id_to_name[identifier]

        data = ITEM_NAME_TO_DATA[name]
        classification = new_classification if new_classification else data.classification

        # Required to ensure all items can be on excluded locations
        if self.options.restrict_prog_items and classification == ItemClassification.useful:
            classification = ItemClassification.filler

        item = TJEItem(name, classification, self.item_name_to_id[name], self.player)
        if name == "Promotion":
            item.rank_value = 1
            if self.options.max_rank_check.value > 0:
                item.classification = ItemClassification.progression

        item.point_value = data.point_value

        return item

    def create_items(self) -> None:
        create_items(self, self.multiworld, self.player, self.options)
        create_starting_presents(self, self.multiworld, self.options)

    def set_rules(self) -> None:
        self.multiworld.completion_condition[self.player] = (
            lambda state: state.has_all(TJEWorld.item_name_groups["Ship Pieces"], self.player)
        )

    def generate_output(self, output_directory: str):
        patch = TJEProcedurePatch(player=self.player, player_name=self.multiworld.player_name[self.player])
        patch.write_file("base_patch.bsdiff4", pkgutil.get_data(__name__, "data/base_patch.bsdiff4"))
        write_tokens(self, patch)

        out_file_name = self.multiworld.get_out_file_name_base(self.player)
        patch.write(os.path.join(output_directory, f"{out_file_name}{patch.patch_file_ending}"))