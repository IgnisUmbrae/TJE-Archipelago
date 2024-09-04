from typing import NamedTuple

from BaseClasses import Region, MultiWorld, LocationProgressType, ItemClassification

from .constants import RANK_NAMES, RANK_THRESHOLDS
from .items import TJEItem
from .options import TJEOptions
from .generators import expected_map_points_on_level
from .locations import TJELocation, TJELocationType, \
                       FLOOR_ITEM_LOCATIONS, SHIP_PIECE_LOCATIONS, RANK_LOCATIONS, RANK_LOC_TEMPLATE

class TJERegion(NamedTuple):
    name: str
    number: int

TJE_LEVEL_LIST : list[TJERegion] = [
    TJERegion("Level 0", 0),
    TJERegion("Level 1", 1),
    TJERegion("Level 2", 2),
    TJERegion("Level 3", 3),
    TJERegion("Level 4", 4),
    TJERegion("Level 5", 5),
    TJERegion("Level 6", 6),
    TJERegion("Level 7", 7),
    TJERegion("Level 8", 8),
    TJERegion("Level 9", 9),
    TJERegion("Level 10", 10),
    TJERegion("Level 11", 11),
    TJERegion("Level 12", 12),
    TJERegion("Level 13", 13),
    TJERegion("Level 14", 14),
    TJERegion("Level 15", 15),
    TJERegion("Level 16", 16),
    TJERegion("Level 17", 17),
    TJERegion("Level 18", 18),
    TJERegion("Level 19", 19),
    TJERegion("Level 20", 20),
    TJERegion("Level 21", 21),
    TJERegion("Level 22", 22),
    TJERegion("Level 23", 23),
    TJERegion("Level 24", 24),
    TJERegion("Level 25", 25),
    TJERegion("Funkotron", 26)
]

def create_regions(multiworld: MultiWorld, player: int, options: TJEOptions):
    world = multiworld.worlds[player]
    menu_region = Region("Menu", player, multiworld)
    multiworld.regions.append(menu_region)

    level_regions = [Region(level.name, player, multiworld) for level in TJE_LEVEL_LIST]

    menu_region.connect(level_regions[1], "Start game")

    # Connect all levels upwards, via exit elevator (except 0, 25 and 26)
    for i in range(1, 25):
        level_regions[i].connect(
                                level_regions[i+1],
                                f"Level {i} Elevator",
                                (lambda state, level=i: state.has(f"Level {level} Elevator Key", player))
                                if i in world.key_levels else None
        )

    # Connect all levels downwards, via falling off edge (except 0 and 26)
    for i in range(1, 26):
        level_regions[i].connect(level_regions[i-1], f"Level {i} Bummer", None)

    # Add floor item locations to all levels (except 0 and 26)
    for i in range(1, 26):
        locs_to_add: list[TJELocation] = []
        for loc_data in FLOOR_ITEM_LOCATIONS[i-1]:
            new_loc = TJELocation(player, loc_data.name, world.location_name_to_id[loc_data.name], level_regions[loc_data.level])
            if loc_data.level == 1 or options.restrict_prog_items:
                new_loc.progress_type = LocationProgressType.EXCLUDED
            locs_to_add.append(new_loc)
        level_regions[i].locations.extend(locs_to_add)

    # Add ship piece checks to relevant levels

    for loc_data in SHIP_PIECE_LOCATIONS:
        if loc_data.level in world.ship_piece_levels:
            new_loc = TJELocation(player, loc_data.name, world.location_name_to_id[loc_data.name], level_regions[loc_data.level])
            new_loc.progress_type = LocationProgressType.PRIORITY
            level_regions[loc_data.level].locations.append(new_loc)

    # Add checks and logic for points and ranks

    if options.max_major_rank > 0:
        add_rank_events(menu_region, player, options)
        add_rank_checks(menu_region, world, player, options)
        for i in range(1, 26):
            add_reach_level_event(level_regions[i], player, i)
            add_map_points(level_regions[i], player, i)

    multiworld.regions.extend(level_regions)

def create_event(player: int, event: str, point_value: int = 0, rank_value: int = 0, progression = True) -> TJEItem:
    item = TJEItem(event, ItemClassification.progression_skip_balancing if progression else ItemClassification.filler,
                    None, player)
    item.point_value = point_value
    item.rank_value = rank_value
    return item

def add_reach_level_event(level: Region, player: int, number: int):
    reach_loc = TJELocation(player, f"Reached Level {number}", None, level)
    reach_loc.place_locked_item(create_event(player, f"Reached Level {number}"))
    reach_loc.show_in_spoiler = False
    level.locations.append(reach_loc)

def add_rank_checks(menu : Region, world, player: int, options : TJEOptions):
    for rank_number, rank in zip(range(1, 9), RANK_NAMES):
        loc_name = RANK_LOC_TEMPLATE.format(rank)
        loc = TJELocation(player, loc_name, world.location_name_to_id[loc_name], menu)
        loc.access_rule = lambda state, actual_rank_number=rank_number: state.has("ranks", player, actual_rank_number)
        if rank_number <= options.max_major_rank.value:
            loc.progress_type = LocationProgressType.PRIORITY
        else:
            loc.progress_type = LocationProgressType.EXCLUDED
        menu.locations.append(loc)

# For internal rank number and logic tracking only
def add_rank_events(menu : Region, player: int, options : TJEOptions):
    for rank_number, rank, threshold in zip(range(1, 9), RANK_NAMES, RANK_THRESHOLDS):
        rank_loc = TJELocation(player, f"Reached {rank}", None, menu)
        rank_loc.show_in_spoiler = False
        prog : bool = (rank_number <= options.max_major_rank.value)
        rank_loc.place_locked_item(create_event(player, f"Reached {rank}",
                                                point_value = 0, rank_value = 1, progression = prog))
        rank_loc.access_rule = lambda state, actual_threshold=threshold: state.has("points", player, actual_threshold)
        menu.locations.append(rank_loc)

# Points for exploring the map (values are tentative)
def add_map_points(level: Region, player: int, level_number: int):
    value = expected_map_points_on_level(level_number)
    map_loc = TJELocation(player, f"Uncover {value} Map Tiles on Level {level_number}", None, level)
    map_loc.show_in_spoiler = False
    map_loc.place_locked_item(create_event(player, f"Uncover {value} Map Tiles on Level {level_number}", value))
    level.locations.append(map_loc)