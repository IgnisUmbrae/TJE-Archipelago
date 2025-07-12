from collections import Counter
from dataclasses import dataclass
from itertools import batched, product, accumulate
from typing import Callable, Iterable
from math import floor, sqrt, atan2, pi

from .constants import EMPTY_ITEM, TREES
from .locations import floor_item_to_location_id

@dataclass
class TJEHint:
    location_id: int
    hint_text: str

#region Special tile groups

WATER_TILES = tuple(range(0x40, 0x66)) + (0x68, 0x69, 0x6B, 0x6D, 0x6F, 0x71, 0x73, 0x75, 0x76, 0x77, 0x79)

# 0x4, 0x7 = grass road; 0xB, 0xE = desert road
ROAD_ENDS = (0x4, 0x7, 0xB, 0xE)

# All void or sea, no items can spawn here
NO_SPAWN_TILES = (0x22, 0x52, 0x53, 0x54, 0x55)


#endregion

#region Text descriptions

DIRECTIONS = ("east", "northeast", "north", "northwest", "west", "southwest", "south", "southeast", "east")
# angle from NESW within which an item must be located to be considered NESW
NESW_ARC_SIZE = 20
OBLIQUE_ARC_SIZE = (360 - 4*NESW_ARC_SIZE)/4
DIRECTION_CUTOFFS = list(accumulate((NESW_ARC_SIZE/2, OBLIQUE_ARC_SIZE) + (NESW_ARC_SIZE, OBLIQUE_ARC_SIZE)*3 + (NESW_ARC_SIZE/2,)))

ADVS = [
    "a tiny bit",
    "slightly",
    "somewhat",
    "quite far",
    "very far",
    "extremely far",
]

TREE_NAMES_SING = {
    0x51: "tree",
    0x52: "palm tree",
    0x53: "cactus"
}

TREE_NAMES_PL = {
    0x51: "trees",
    0x52: "palm trees",
    0x53: "cacti"
}

NUMBER_NAMES = ["one", "two", "three", "four"]

STR_GRASSY_EDGE = "on some grass by space"
STR_GRASSY_MIDDLE = "in the middle of some grass"
STR_GRASSY_EDGE_JUT_VOID = "on some grass jutting into space"
STR_GRASSY_EDGE_WATER = "on some grass by water"
STR_GRASSY_EDGES_SEP_VOID = "where space divides two patches of grass"
STR_GRASSY_EDGES_SEP_WATER = "where water divides two patches of grass"
STR_DESERT_EDGE_GRASS = "at the grassy edge of a desert"
STR_DESERT_EDGE_WATER = "by water at the edge of a desert"
STR_DESERT_EDGE_VOID = "at the edge of a desert, at the edge of some land"
STR_DESERT_EDGES_SEP_VOID = "where space divides two patches of desert"
STR_DESERT_EDGES_SEP_WATER = "where water divides two patches of desert"
STR_DESERT_MIDDLE = "in the middle of a desert"
STR_DESERT_GRASS_OASIS = "in a grassy refuge in the middle of the desert"
STR_WALKWAY_CROSSROADS = "at a crossroads on a narrow walkway"
STR_WALKWAY_JUNCTION = "at a junction on a narrow walkway"
STR_WALKWAY_CORNER = "on the corner of a narrow walkway"
STR_WALKWAY_HORIZ = "on a narrow horizontal walkway"
STR_WALKWAY_VERT = "on a narrow vertical walkway"
STR_WALKWAY_NEAR_GRASS = "at the entrance to a walkway"
STR_WALKWAY_NEAR_DESERT = "where desert becomes a walkway"
STR_LAKE_ISLAND = "on a tiny island in a lake"
STR_SPACE_ISLAND_GRASS = "on a tiny island out in space"
STR_SPACE_ISLAND_DESERT = "on a tiny desert island out in space"

STR_LAKE = "in the middle of a lake??? this shouldn't happen what"
STR_VOID = "in the middle of the void??? this is a bug"

STR_BABY_ISLAND_GRASS = "near a baby island"
STR_BABY_ISLAND_DESERT = "near a baby island"

TILE_STRS = {
    0x0: STR_GRASSY_EDGE,
    0x1: STR_GRASSY_EDGE,
    0x2: STR_GRASSY_EDGE,
    0x3: STR_GRASSY_EDGE,
    0x4: STR_GRASSY_EDGE,
    0x5: STR_GRASSY_EDGE,
    0x6: STR_GRASSY_EDGE,
    0x7: STR_GRASSY_EDGE,
    0x8: STR_GRASSY_EDGE,
    0x9: STR_GRASSY_EDGE,
    0xA: STR_GRASSY_EDGE,
    0xB: STR_GRASSY_EDGE,
    0xC: STR_WALKWAY_CORNER,
    0xD: STR_WALKWAY_CORNER,
    0xE: STR_WALKWAY_CORNER,
    0xF: STR_WALKWAY_CORNER,
    0x10: STR_WALKWAY_NEAR_GRASS,
    0x11: STR_WALKWAY_NEAR_GRASS,
    0x12: STR_WALKWAY_NEAR_GRASS,
    0x13: STR_WALKWAY_NEAR_GRASS,
    0x14: STR_GRASSY_EDGE_JUT_VOID, # down
    0x15: STR_GRASSY_EDGE_JUT_VOID, # left (or right)
    0x16: STR_GRASSY_EDGE_JUT_VOID, # up
    0x17: STR_GRASSY_EDGE_JUT_VOID, # right (or left),
    0x18: STR_WALKWAY_HORIZ,
    0x19: STR_WALKWAY_VERT,
    0x1A: STR_SPACE_ISLAND_GRASS,
    0x1B: STR_BABY_ISLAND_GRASS,
    0x1C: STR_SPACE_ISLAND_GRASS,
    0x1D: STR_SPACE_ISLAND_GRASS,
    0x1E: STR_GRASSY_MIDDLE,
    0x1F: STR_GRASSY_EDGE,
    0x20: STR_GRASSY_EDGE,
    0x21: STR_GRASSY_MIDDLE,
    0x22: STR_VOID,
    0x23: STR_DESERT_EDGE_VOID,
    0x24: STR_DESERT_EDGE_VOID,
    0x25: STR_DESERT_EDGE_VOID,
    0x26: STR_DESERT_EDGE_VOID, # maybe JUT_VOID
    0x27: STR_DESERT_EDGE_VOID,
    0x28: STR_DESERT_EDGE_VOID,
    0x29: STR_DESERT_EDGE_VOID,
    0x2A: STR_DESERT_EDGE_VOID,
    0x2B: STR_DESERT_EDGE_VOID,
    0x2C: STR_DESERT_EDGE_VOID,
    0x2D: STR_DESERT_EDGE_VOID,
    0x2E: STR_DESERT_EDGE_VOID,
    0x2F: STR_WALKWAY_NEAR_DESERT,
    0x30: STR_WALKWAY_NEAR_DESERT,
    0x31: STR_WALKWAY_NEAR_DESERT,
    0x32: STR_WALKWAY_NEAR_DESERT,
    0x33: STR_BABY_ISLAND_DESERT,
    0x34: STR_SPACE_ISLAND_DESERT,
    0x35: STR_DESERT_MIDDLE,
    0x36: STR_DESERT_EDGE_VOID,
    0x37: STR_DESERT_EDGE_VOID,
    0x38: STR_DESERT_MIDDLE,
    0x39: STR_DESERT_GRASS_OASIS,
    0x3A: STR_DESERT_GRASS_OASIS,
    0x3B: STR_WALKWAY_CROSSROADS,
    0x3C: STR_WALKWAY_JUNCTION,
    0x3D: STR_WALKWAY_JUNCTION,
    0x3E: STR_WALKWAY_JUNCTION,
    0x3F: STR_WALKWAY_JUNCTION,
    0x40: STR_GRASSY_EDGE_WATER,
    0x41: STR_GRASSY_EDGE_WATER,
    0x42: STR_GRASSY_EDGE_WATER,
    0x43: STR_GRASSY_EDGE_WATER,
    0x44: STR_GRASSY_EDGE_WATER,
    0x45: STR_GRASSY_EDGE_WATER,
    0x46: STR_GRASSY_EDGE_WATER,
    0x47: STR_GRASSY_EDGE_WATER,
    0x48: STR_GRASSY_EDGE_WATER,
    0x49: STR_GRASSY_EDGE_WATER,
    0x4A: STR_GRASSY_EDGE_WATER,
    0x4B: STR_GRASSY_EDGE_WATER,
    0x4C: STR_LAKE_ISLAND,
    0x4D: STR_LAKE_ISLAND,
    0x4E: STR_LAKE_ISLAND,
    0x4F: STR_LAKE_ISLAND,
    0x50: STR_LAKE_ISLAND,
    0x51: STR_LAKE_ISLAND,
    0x52: STR_LAKE,
    0x53: STR_LAKE,
    0x54: STR_LAKE,
    0x55: STR_LAKE,
    0x56: STR_GRASSY_EDGE_WATER,
    0x57: STR_GRASSY_EDGE_WATER,
    0x58: STR_DESERT_EDGE_WATER,
    0x59: STR_DESERT_EDGE_WATER,
    0x5A: STR_DESERT_EDGE_WATER,
    0x5B: STR_DESERT_EDGE_WATER,
    0x5C: STR_DESERT_EDGE_WATER,
    0x5D: STR_DESERT_EDGE_WATER,
    0x5E: STR_DESERT_EDGE_WATER,
    0x5F: STR_DESERT_EDGE_WATER,
    0x60: STR_DESERT_EDGE_WATER,
    0x61: STR_DESERT_EDGE_WATER,
    0x62: STR_DESERT_EDGE_WATER,
    0x63: STR_DESERT_EDGE_WATER,
    0x64: STR_DESERT_EDGE_WATER,
    0x65: STR_DESERT_EDGE_WATER,
    0x66: STR_GRASSY_EDGES_SEP_VOID,
    0x67: STR_DESERT_EDGES_SEP_VOID,
    0x68: STR_GRASSY_EDGES_SEP_WATER,
    0x69: STR_DESERT_EDGES_SEP_WATER,
    0x6A: STR_DESERT_EDGES_SEP_VOID,
    0x6B: STR_DESERT_EDGES_SEP_WATER,
    0x6C: STR_DESERT_EDGE_VOID,
    0x6D: STR_DESERT_EDGE_WATER,
    0x6E: STR_DESERT_EDGE_VOID,
    0x6F: STR_DESERT_EDGE_WATER,
    0x70: STR_DESERT_EDGE_VOID,
    0x71: STR_DESERT_EDGE_WATER,
    0x72: STR_DESERT_EDGE_VOID,
    0x73: STR_DESERT_EDGE_WATER,
    0x74: STR_DESERT_EDGE_VOID,
    0x75: STR_DESERT_EDGE_WATER,
    0x76: STR_DESERT_EDGE_WATER,
    0x77: STR_DESERT_EDGE_WATER,
    0x78: STR_DESERT_EDGE_VOID,
    0x79: STR_DESERT_EDGE_WATER,
}

#endregion

#region Misc constants

# Original game world coordinates: (0,0) top left → (19*16*8, 26*8*8) bottom right
X_RANGE_GAME = range(0, 2432)
Y_RANGE_GAME = range(0, 1664)
X_RANGE_CART = range(-1216, 1216)
Y_RANGE_CART = range(-832, 832)

# Minimum distance to be considered "extremely" far
EXTREMELY_FAR_DIST = 1300
# Actual maximum distance possible in-game
MAX_DIST: float = 1473.3906474523312

# Maximum distance to be considered "near" a tree or cactus
TREE_NEAR_DIST = 80

#endregion

#region Map data and tile structure

# 19 tiles wide, 26 tiles high
# 2 bytes per tile
# Tile structure: EM, where E is an extra byte and M is the main byte
# E structure: ?HUF₁ RRRR
# • ? is a bit of unknown use
# • H is a "hidden" flag for hidden paths
# • U is an "uncovered" flag for hidden paths
# • F₁ is a horizontal mirror flag for the road
# • R is the road type
# M structure: F₂TTT TTTT
# • F₂ is a horizontal mirror flag for the base tile
# • T is the tile type

#endregion

#region Helper functions

def item_coords_to_tilexy(item_coords: tuple[int]) -> tuple[int]:
    return item_coords[1]/(8*8) - 1, item_coords[0]//(8*16) - 1

def first_matching_index(iterable: Iterable, condition: Callable, default=None) -> int | None:
    return next((i for i, x in enumerate(iterable) if condition(x)), default)

def linear_rescale(n: float, old_min: float, old_max: float, new_min: float, new_max: float) -> float:
    return (new_max - new_min)/(old_max - old_min) * (n - old_min) + new_min

def round_to_nearest_multiple(n: float, multiple: float) -> float:
    return round(n/multiple)*multiple

def dist(point1: tuple, point2: tuple) -> float:
    return sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)

# Changes game coordinates (top left is (0,0), y increasing downwards)
# to usual Cartesian coordinates ((0,0) is central, y increasing upwards)
def game_coords_to_cartesian(point: tuple) -> tuple:
    new_x = linear_rescale(point[0], 0, 19*16*8, -19*16*4, +19*16*4)
    new_y = linear_rescale(point[1], 0, 26*8*8, +26*8*4, -26*8*4)
    return (new_x, new_y)

def angle(point: tuple) -> float:
    return (180.0/pi)*atan2(point[1], point[0])

#endregion

class TJETile:
    def __init__(self, row: int, col: int, extra_byte: int, main_byte: int):
        self.row, self.col = row, col
        self.type = main_byte & 0x7F
        self.mirrored = main_byte & 0x80 > 0
        self.road_type = extra_byte & 0xF
        self.road_mirrored = extra_byte & 0x10
        self.uncovered = extra_byte & 0x20
        self.hidden = extra_byte & 0x40
        self.unknown_property = extra_byte & 0x80

def get_road_str(tile_coords: tuple, map_tiles: list[list[TJETile]]) -> str | None:
    candidate_tiles = product((tile_coords[0], tile_coords[0]-1, tile_coords[0]+1),
                              (tile_coords[1], tile_coords[1]-1, tile_coords[1]+1))
    for tile in candidate_tiles:
        try:
            road_type = map_tiles[tile[0]][tile[1]].road_type
            if road_type > 0:
                if road_type in ROAD_ENDS:
                    return "the end of a road"
                else:
                    return "a road"
        except IndexError:
            pass
    return None

def get_water_str(tile_coords: tuple, map_data: list[list[TJETile]]) -> str | None:
    candidate_tiles = product((tile_coords[0], tile_coords[0]-1, tile_coords[0]+1),
                              (tile_coords[1], tile_coords[1]-1, tile_coords[1]+1))
    for tile in candidate_tiles:
        try:
            if map_data[tile[0]][tile[1]].type in WATER_TILES:
                return "water"
        except IndexError:
            pass
    return None

def concat_item_list(items: list[str]) -> str:
    match len(items):
        case 0:
            return ""
        case 1:
            return items[0]
        case 2:
            return " and ".join(items)
        case _:
            return f"{", ".join(items[:-1])} and {items[-1]}"

def evaluate_item(item_coords: tuple, map_tiles: list[list[TJETile]], tree_coords: list[tuple[int, int]], tree_types) -> str:
    # Convert to Cartesian coordinates, calculate compass direction from angle
    cart_coords = game_coords_to_cartesian(item_coords)
    ang = angle(cart_coords)
    ang = ang + 360.0 if ang < 0 else ang

    dir_idx = first_matching_index(DIRECTION_CUTOFFS, lambda cutoff: cutoff > ang)
    direction = DIRECTIONS[dir_idx]

    # Calculate distance, assign appropriate word
    d = dist((0, 0), cart_coords)
    adv_idx = floor(linear_rescale(d if d < EXTREMELY_FAR_DIST else MAX_DIST-1, 0, MAX_DIST, 0, len(ADVS)))

    direction_str = f"{ADVS[adv_idx]} {direction}"

    # Check for special tile types
    tile_x, tile_y = item_coords_to_tilexy(item_coords)
    tile_coords = (floor(tile_x), floor(tile_y))
    tile_type = map_tiles[tile_coords[0]][tile_coords[1]].type

    hint_body = TILE_STRS.get(tile_type, None)
    nearby_landmarks = []
    nearby_trees = Counter()

    if "water" not in hint_body and "lake" not in hint_body:
        water_str = get_water_str(tile_coords, map_tiles)
        if water_str:
            nearby_landmarks.append(water_str)

    for i, tree_coord in enumerate(tree_coords):
        if dist(tree_coord, item_coords) < TREE_NEAR_DIST:
            nearby_trees[TREE_NAMES_SING[i]] += 1
    if len(nearby_trees) > 0:
        for tree in nearby_trees:
            count = nearby_trees[tree]
            nearby_landmarks.append(f"a {TREE_NAMES_SING[count]}" if count == 1
                                    else f"{NUMBER_NAMES[count]} {TREE_NAMES_PL[count]}")

    road_str = get_road_str(tile_coords, map_tiles)
    if road_str:
        nearby_landmarks.append(road_str)

    if hint_body:
        hint_body = f"{direction_str}, {hint_body}"
    if nearby_landmarks:
        hint_body = f"{hint_body}, near {concat_item_list(nearby_landmarks)}"

    return hint_body

def binary_map_data_to_tile_list(map_bytes: bytes) -> list[TJETile]:
    return [
        [TJETile(i, j, *t) for j, t in enumerate(batched(group, 2))]
        for i, group in enumerate(batched(map_bytes, 19*2))
        ]

def item_data_to_coord_list(item_data: bytes, max_index, accept_func: Callable) -> Iterable[tuple[int, int]]:
    item_x_coords = (int.from_bytes(item_data[8*i+4 : 8*i+6]) for i in range(28) if accept_func(item_data[8*i:8*i+1]))
    item_y_coords = (int.from_bytes(item_data[8*i+6 : 8*i+8]) for i in range(28) if accept_func(item_data[8*i:8*i+1]))
    return zip(item_x_coords, item_y_coords, strict=True)

def generate_hints_for_current_level(level: int, map_bytes: bytes, floor_item_bytes: bytes) -> list[str]:
    map_data = binary_map_data_to_tile_list(map_bytes)

    item_coords = item_data_to_coord_list(floor_item_bytes[:28*8], 28, lambda b: b != EMPTY_ITEM)
    tree_coords = item_data_to_coord_list(floor_item_bytes[28*8:], 4, lambda b: b in TREES)
    tree_types = list(floor_item_bytes[28*8:][8*i] for i in range(4))

    return {floor_item_to_location_id(level, i): TJEHint(floor_item_to_location_id(level, i),
                    evaluate_item(item, map_data, tree_coords, tree_types))
                    for i, item in enumerate(item_coords)}