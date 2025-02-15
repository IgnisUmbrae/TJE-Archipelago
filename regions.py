from typing import NamedTuple

from BaseClasses import Region, MultiWorld, LocationProgressType, ItemClassification
from worlds.generic.Rules import forbid_item, add_rule

from .constants import RANK_NAMES
from .items import EDIBLE_IDS, ITEM_ID_TO_NAME, TJEItem
from .generators import expected_map_points_on_level, item_totals
from .options import TJEOptions
from .locations import TJELocation, FLOOR_ITEM_LOCATIONS, SHIP_PIECE_LOCATIONS, RANK_LOC_TEMPLATE

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

    connect_regions_basic(level_regions, options)

    add_floor_items(world, player, options, level_regions)
    add_ship_pieces(world, player, level_regions)
    handle_final_ship_piece(multiworld, options, player)

    restrict_lv1_items(level_regions)

    handle_key_options(multiworld, world, player, options)
    handle_rank_options(multiworld, world, player, options, level_regions)

    multiworld.regions.extend(level_regions)

def connect_regions_basic(level_regions, options: TJEOptions):
    for i in range(1, options.last_level.value):
        level_regions[i].connect(level_regions[i+1], f"Level {i} Elevator")

    for i in range(1, options.last_level.value+1):
        level_regions[i].connect(level_regions[i-1], f"Level {i} Bummer", None)

#region Misc

def restrict_lv1_items(level_regions):
    banned = set(["Icarus Wings", "Innertube", "Rocket Skates", "Mystery Present", "Randomizer", "Total Bummer"] + \
             [ITEM_ID_TO_NAME[food] for food in EDIBLE_IDS[:-1]] + ["Rocket Skates Trap"])
    for loc in level_regions[1].get_locations()[:4]:
        loc.item_rule = lambda item: item.name not in banned

#endregion

#region Options handling routines

def handle_key_options(multiworld, world, player,  options: TJEOptions):
    for i in world.key_levels:
        add_rule(multiworld.get_entrance(f"Level {i} Elevator", player),
                    lambda state, lvl=i: state.has("Progressive Elevator Key", player, world.key_levels.index(lvl)+1))

def handle_final_ship_piece(multiworld, options: TJEOptions, player):
    add_rule(multiworld.get_entrance(f"Level {options.last_level.value-1} Elevator", player),
                lambda state: state.has_group("Ship Pieces", player, 9))

def handle_rank_options(multiworld, world, player,  options: TJEOptions, level_regions):
    if options.max_rank_check > 0:
        menu_region = multiworld.get_region("Menu", player)
        #add_rank_events(menu_region, world, player, options)
        add_rank_checks(menu_region, world, player, options)
        for i in range(1, options.last_level.value+1):
            add_reach_level_event(level_regions[i], player, i)
            add_exploration_points(level_regions[i], player, i)

#endregion

#region Main location adding routines

def add_floor_items(world, player,  options: TJEOptions, level_regions):
    per_level_limits = item_totals(True, options.min_items.value, options.max_items.value)
    for i in range(1, options.last_level.value+1):
        locs_to_add: list[TJELocation] = []
        for loc_data in FLOOR_ITEM_LOCATIONS[i][:per_level_limits[i]]:
            new_loc = TJELocation(player, loc_data.name, world.location_name_to_id[loc_data.name],
                                  level_regions[loc_data.level])
            # No progression items on the two potentially inaccessible islands on Level 1
            if loc_data.level == 1 and loc_data.item_index > 4:
                new_loc.progress_type = LocationProgressType.EXCLUDED
            locs_to_add.append(new_loc)
        level_regions[i].locations.extend(locs_to_add)

def add_ship_pieces(world, player, level_regions):
    for loc_data in SHIP_PIECE_LOCATIONS:
        if loc_data.level in world.ship_item_levels:
            new_loc = TJELocation(player, loc_data.name, world.location_name_to_id[loc_data.name],
                                  level_regions[loc_data.level])
            new_loc.progress_type = LocationProgressType.PRIORITY
            level_regions[loc_data.level].locations.append(new_loc)

def add_rank_checks(menu: Region, world, player, options: TJEOptions):
    for number, rank in enumerate(RANK_NAMES[1:], start=1):
        loc_name = RANK_LOC_TEMPLATE.format(rank)
        loc = TJELocation(player, loc_name, world.location_name_to_id[loc_name], menu)
        loc.access_rule = lambda state, rank_num=number: state.has("ranks", player, rank_num)
        if number <= options.max_rank_check.value:
            loc.progress_type = LocationProgressType.PRIORITY
            forbid_item(loc, "Promotion", player)
        else:
            loc.progress_type = LocationProgressType.EXCLUDED
        menu.locations.append(loc)

#endregion

#region Logic-tracking events

def create_event(player: int, event: str, point_value: int = 0, progression = True) -> TJEItem:
    item = TJEItem(event, ItemClassification.progression_skip_balancing if progression else ItemClassification.filler,
                    None, player)
    item.point_value = point_value
    return item

def add_reach_level_event(level: Region, player: int, number: int):
    reach_loc = TJELocation(player, f"Reached Level {number}", None, level)
    reach_loc.place_locked_item(create_event(player, f"Reached Level {number}"))
    reach_loc.show_in_spoiler = False
    level.locations.append(reach_loc)

# Points for exploring the map (values are tentative)
def add_exploration_points(level: Region, player: int, level_number: int):
    value = expected_map_points_on_level(level_number)
    map_loc = TJELocation(player, f"Uncover {value} Map Tiles on Level {level_number}", None, level)
    map_loc.show_in_spoiler = False
    map_loc.place_locked_item(create_event(player, f"{value} Points (Map Exploration)", value))
    level.locations.append(map_loc)

#endregion
