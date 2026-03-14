import os
import pkgutil
import functools
import re
from typing import Optional, Any, ClassVar
from itertools import takewhile, product

from BaseClasses import CollectionState, ItemClassification
import settings
from worlds.AutoWorld import World, WebWorld

from .client import TJEClient # required to register with BizHawkClient
from .constants import MAILBOX_ITEM_REFS, VANILLA_RANK_THRESHOLDS, BASE_EARTHLINGS, REV00_MD5, REV02_MD5
from .generators import TJEGenerator, TJEInternalRNG, get_key_levels, item_totals, scaled_rank_thresholds, \
                                                      get_flat_promotion_value
from .items import Item, TJEItem, ITEM_GROUPS, ITEM_ID_TO_CODE, ITEM_NAME_TO_ID, ITEM_NAME_TO_DATA, MASTER_ITEM_LIST, \
                   TJEItemType, create_items, create_starting_presents, create_starting_bucks
from .locations import FLOOR_ITEM_LOC_TEMPLATE, MAILBOX_LOC_TEMPLATE, LOCATION_GROUPS, LOCATION_NAME_TO_ID
from .options import RankRescalingOption, EarthlingRandomizationOption, LocalShipPiecesOption, TJEOptions
from .regions import create_regions
from .rom import TJEProcedurePatch, write_tokens

class TJESettings(settings.Group):
    class ROMFile(settings.UserFilePath):
        """Location of the ToeJam & Earl ROM file."""

        copy_to = "ToeJamEarl.SGD"
        description = "ToeJam & Earl ROM file"
        md5s = [REV00_MD5, REV02_MD5]

        def browse(self, filetypes = None, **kwargs):
            if not filetypes:
                return super().browse([("Mega Drive/Genesis ROM", ["*.sgd", "*.md", "*.smd", "*.bin"])], **kwargs)
            else:
                return super().browse(filetypes, **kwargs)

    rom_file: ROMFile = ROMFile(ROMFile.copy_to)

class TJEWeb(WebWorld):
    theme = "partyTime"

class TJEWorld(World):
    """ToeJam & Earl"""

    game = "ToeJam and Earl"
    options_dataclass = TJEOptions
    options: TJEOptions
    settings: ClassVar[TJESettings]
    topology_present = True

    item_name_to_id = ITEM_NAME_TO_ID
    location_name_to_id = LOCATION_NAME_TO_ID

    item_name_groups = ITEM_GROUPS
    location_name_groups = LOCATION_GROUPS

    def get_current_rank(self, state: "CollectionState", item: "TJEItem") -> int:
        rank_progress = list(takewhile(lambda i: self.rank_thresholds[i] <= state.prog_items[item.player]["points"],
                                        range(len(self.rank_thresholds))))
        rank = rank_progress[-1] if rank_progress != [] else 0
        return rank

    def collect(self, state: "CollectionState", item: "TJEItem") -> bool:
        change = super().collect(state, item)
        if change:
            # Bucks
            if item.buck_value > 0:
                state.prog_items[item.player]["bucks"] += item.buck_value
            if item.location is not None:
                if item.location.name in LOCATION_GROUPS["Mailboxes"] and hasattr(item.location, "price"):
                    state.prog_items[item.player]["bucks"] -= item.location.price

            # Points, ranks
            if item.point_value > 0:
                if self.options.flat_promotions:
                    state.prog_items[item.player]["points"] += item.point_value
                else:
                    rank = self.get_current_rank(state, item)
                    if item.name == "Promotion" and rank < 8:
                        state.prog_items[item.player]["points"] = self.rank_thresholds[rank+1]
                    else:
                        state.prog_items[item.player]["points"] += item.point_value
        return change
    
    def remove(self, state: "CollectionState", item: "TJEItem") -> bool:
        change = super().collect(state, item)
        if change:
            # Bucks
            if item.buck_value > 0:
                state.prog_items[item.player]["bucks"] -= item.buck_value
            if item.location is not None:
                if item.location.name in LOCATION_GROUPS["Mailboxes"] and hasattr(item.location, "price"):
                    state.prog_items[item.player]["bucks"] += item.location.price

            # Points, ranks
            if item.point_value > 0:
                if self.options.flat_promotions:
                    state.prog_items[item.player]["points"] -= item.point_value
                else:
                    rank = self.get_current_rank(state, item)
                    if item.name == "Promotion" and rank > 0:
                        state.prog_items[item.player]["points"] = self.rank_thresholds[rank-1]
                    else:
                        state.prog_items[item.player]["points"] -= item.point_value
        return change

    def generate_early(self) -> None:
        self.seeds = [self.random.getrandbits(16) for _ in range(26)]
        self.generator = TJEGenerator(self)
        self.tjerng = TJEInternalRNG()
        self.key_levels = (get_key_levels(self.options.key_gap.value, self.options.last_level.value)
                           if self.options.elevator_keys else [])
        self.mailbox_levels = (self.tjerng.generate_mailboxes(self.seeds, self.options.last_level.value)
                               if self.options.mailbox_checks else [])
        self.ship_item_levels = self.generator.generate_ship_piece_levels(self.options.last_level.value)
        self.map_reveal_potencies = self.generator.generate_map_reveal_potencies(self.options.last_level.value)

        match self.options.earthling_rando:
            case EarthlingRandomizationOption.BASE:
                self.earthling_list = BASE_EARTHLINGS
            case EarthlingRandomizationOption.BASE_SHUFFLE:
                self.earthling_list = list(BASE_EARTHLINGS)
                self.random.shuffle(self.earthling_list)
            case EarthlingRandomizationOption.NICE_RANDOM:
                self.earthling_list = self.generator.generate_nice_random_earthlings(self.options.earthling_rando_niceness.value,
                                                                                     self.options.last_level.value)
            case EarthlingRandomizationOption.EARTHLINGSANITY:
                self.earthling_list = self.generator.generate_full_random_earthlings()

        self.earthling_list = [[0xFF]*(20 - len(l)) + l for l in self.earthling_list]

        match self.options.rank_rescaling:
            case RankRescalingOption.NONE:
                self.rank_thresholds = VANILLA_RANK_THRESHOLDS
            case _:
                if self.options.rank_rescaling == RankRescalingOption.FUNK_LORD or self.options.max_rank_check == 0:
                    scale_threshold = 8
                else:
                    scale_threshold = self.options.max_rank_check
                self.rank_thresholds = scaled_rank_thresholds(self.options.last_level.value,
                                                            self.options.min_items.value,
                                                            self.options.max_items.value,
                                                            scale_threshold
                                                            )

        if self.options.flat_promotions:
            self.flat_promotion_value = get_flat_promotion_value(self.rank_thresholds, self.options.max_rank_check.value)
        
        if self.options.upwarp_present:
            self.generator.fewer_upwarps()
        
        if self.options.local_ship_pieces.value != self.options.local_ship_pieces.default:
            ship_pieces = {item.name for item in MASTER_ITEM_LIST[:9]}
            match self.options.local_ship_pieces.value:
                case LocalShipPiecesOption.FULL:
                    self.options.local_items.value.update(ship_pieces)
                case LocalShipPiecesOption.NONE:
                    self.options.non_local_items.value.update(ship_pieces)

    def create_regions(self) -> None:
        create_regions(self.multiworld, self.player, self.options)

    def create_item(self, identifier: str | int, new_classification: Optional[ItemClassification] = None) -> TJEItem:
        name = identifier if isinstance(identifier, str) else self.item_id_to_name[identifier]

        data = ITEM_NAME_TO_DATA[name]
        classification = new_classification if new_classification else data.classification

        item = TJEItem(name, classification, self.item_name_to_id[name], self.player)
        if self.options.max_rank_check.value > 0 and data.type == TJEItemType.PRESENT:
            if name == "Promotion":
                item.classification |= ItemClassification.progression
            else:
                item.classification |= ItemClassification.progression_skip_balancing
        
        if self.options.flat_promotions and name == "Promotion":
            item.point_value = self.flat_promotion_value
        else:
            item.point_value = data.point_value

        if self.options.mailbox_checks:
            if data.buck_value > 0:
                item.classification |= ItemClassification.progression_skip_balancing

        item.buck_value = data.buck_value

        return item

    def create_items(self) -> None:
        create_items(self, self.multiworld, self.player, self.options)
        create_starting_presents(self, self.multiworld, self.options)
        create_starting_bucks(self, self.multiworld)

    # Any rules that need setting post–item creation
    # Currently only used for mailbox items & completion condition
    def set_rules(self) -> None:
        if self.options.mailbox_checks:
            self.mailbox_item_prices = self.generator.generate_item_prices(len(self.mailbox_levels), self.total_bucks)
            for (n, (i, pos)) in enumerate(product(self.mailbox_levels, MAILBOX_ITEM_REFS)):
                loc = self.get_location(MAILBOX_LOC_TEMPLATE.format(i, pos))
                price = self.mailbox_item_prices[n]
                loc.access_rule = lambda state, p=price: state.has("bucks", self.player, p)
                loc.price = price

        self.multiworld.completion_condition[self.player] = (
            lambda state: state.has_all(TJEWorld.item_name_groups["Ship Pieces"], self.player)
        )

    def pre_fill(self) -> None:
        if self.options.local_ship_pieces.value == LocalShipPiecesOption.VANILLA:
            ship_piece_items = [self.create_item(item.name, item.classification) for item in MASTER_ITEM_LIST[:9]]
            big_item_locs = [self.get_location(f"Level {i} - Big Item") for i in self.ship_item_levels[:9]]
            self.random.shuffle(ship_piece_items)
            for i, piece in enumerate(ship_piece_items):
                big_item_locs[i].place_locked_item(piece)

    def generate_output(self, output_directory: str):
        self.create_patchable_item_list()
        if self.options.mailbox_checks:
            self.create_patchable_mailbox_item_list()

        patch = TJEProcedurePatch(player=self.player, player_name=self.multiworld.player_name[self.player])
        
        if self.options.game_version.value == 0:
            patch.hash = REV00_MD5
            patch.procedure.insert(0, ("apply_bsdiff4", ["00to02.bsdiff4"]))
            patch.write_file("00to02.bsdiff4", pkgutil.get_data(__name__, "data/00to02.bsdiff4"))
        else:
            patch.hash = REV02_MD5

        patch.write_file("base_patch.bsdiff4", pkgutil.get_data(__name__, "data/base_patch.bsdiff4"))
        write_tokens(self, patch)

        out_file_name = self.multiworld.get_out_file_name_base(self.player)
        patch.write(os.path.join(output_directory, f"{out_file_name}{patch.patch_file_ending}"))

    def item_to_tje_hex(self, item: Item) -> int:
        if item.player == self.player:
            return ITEM_ID_TO_CODE.get(item.code, 0xFF)
        else:
            if item.classification in \
                (ItemClassification.progression, ItemClassification.progression_skip_balancing):
                return 0x1D # Progression AP item
            else:
                return 0x1C # Regular AP item

    def create_patchable_item_list(self):
        items_per_level = item_totals(True, self.options.min_items.value, self.options.max_items.value)
        self.patchable_item_list = [0xFF]*28
        for level in range(1, self.options.last_level.value+1):
            num = items_per_level[level]
            for i in range(num):
                item = self.get_location(FLOOR_ITEM_LOC_TEMPLATE.format(level, i+1)).item
                item_hex = self.item_to_tje_hex(item)
                self.patchable_item_list.append(item_hex)
            self.patchable_item_list.extend([0xFF]*(28 - num))
        assert len(self.patchable_item_list) == (self.options.last_level.value+1)*28

    def shorten_item_name(self, name: str) -> str:
        strip_chars = re.compile(f"[^a-zA-Z0-9 ?!',.-]")
        try:
            from ._vendor.unidecode import unidecode
            string_processor = functools.partial(unidecode, errors="ignore", replace_str="")
        except ImportError:
            import unicodedata
            string_processor = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii", "ignore")

        #self.multiworld.player_name[item.player]
        #item.game

        processed = string_processor(name)
        processed = processed.replace(": ", " - ")
        processed = strip_chars.sub("", processed)
        n = (processed[:26] + " ").ljust(30, ".") + " "
        return n

    def create_patchable_mailbox_item_list(self):
        self.mailbox_item_names, self.mailbox_item_types = [], []
        for (i, pos) in product(self.mailbox_levels, MAILBOX_ITEM_REFS):
            item = self.get_location(MAILBOX_LOC_TEMPLATE.format(i, pos)).item
            self.mailbox_item_names.append(self.shorten_item_name(item.name).encode("ascii") + b"\x00")
            self.mailbox_item_types.append(self.item_to_tje_hex(item))

    # For tracker use
    def fill_slot_data(self) -> dict[str, Any]:
        return self.options.as_dict("key_gap", "max_rank_check", "last_level") | {
            "key_level_access": self.key_levels + [self.options.last_level.value],
            "items_per_level": item_totals(True, self.options.min_items.value, self.options.max_items.value),
            "ship_item_levels": self.ship_item_levels,
            "rank_thresholds": self.rank_thresholds,
            "map_reveal_potencies": self.map_reveal_potencies,
            "reach_level_checks": bool(self.options.reach_level_checks.value),
            "mailbox_levels": self.mailbox_levels if self.options.mailbox_checks else [],
            "mailbox_item_prices": self.mailbox_item_prices if self.options.mailbox_checks else [],
        }
