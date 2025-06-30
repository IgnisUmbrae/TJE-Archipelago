from itertools import batched, chain, product, accumulate
from typing import Callable, Iterable
from math import floor, sqrt, atan2, pi
import pygame

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

#endregion

#region Special tile groups

WATER_TILES = tuple(range(0x40, 0x66)) + (0x68, 0x69, 0x6B, 0x6D, 0x6F, 0x71, 0x73, 0x75, 0x76, 0x77, 0x79)
DESERT_EDGES = (0x23, 0x24, 0x25, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
                0x30, 0x31, 0x32, 0x33, 0x36, 0x37, 0x58, 0x59, 0x5A, 0x5B, 0x5C, 0x5D, 0x5E, 0x5F,
                0x60, 0x61, 0x62, 0x63, 0x64, 0x65, 0x67, 0x69, 0x6A, 0x6B, 0x6C, 0x6D, 0x6E, 0x6F,
                0x70, 0x71, 0x72, 0x73, 0x74, 0x75, 0x76, 0x77, 0x78, 0x79)

STR_GRASSY_EDGE = "on grass at the edge of the land"
STR_GRASSY_MIDDLE = "in the middle of some grass"
STR_GRASSY_EDGE_JUT_VOID = "on a grassy promontory jutting into space"
STR_GRASSY_EDGE_WATER = "on grass at edge of the water"
STR_GRASSY_EDGES_SEP_VOID = "where two patches of grass are separated by space"
STR_GRASSY_EDGES_SEP_WATER = "where two patches of grass are separated by water"
STR_DESERT_EDGE_GRASS = "at desert's edge"
STR_DESERT_EDGE_WATER = "at the edge of a desert, at the edge of some water"
STR_DESERT_EDGE_VOID = "at the edge of a desert, at the edge of some land"
STR_DESERT_EDGES_SEP_VOID = "where two patches of desert are separated by space"
STR_DESERT_EDGES_SEP_WATER = "where two patches of desert are separated by water"
STR_DESERT_MIDDLE = "in the middle of a desert"
STR_DESERT_GRASS_OASIS = "where grass breaks through desert"
STR_WALKWAY_CROSSROADS = "at a narrow crossroads"
STR_WALKWAY_JUNCTION = "at a narrow junction"
STR_WALKWAY_CORNER = "on the corner of a narrow walkway"
STR_WALKWAY_HORIZ = "on a narrow horizontal walkway"
STR_WALKWAY_VERT = "on a narrow vertical walkway"
STR_WALKWAY_NEAR_GRASS = "near a grassy entrance to a walkway"
STR_WALKWAY_NEAR_DESERT = "where desert becomes a grassy walkway"
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

# 0x4, 0x7 = grass road; 0xB, 0xE = desert road
ROAD_ENDS = (0x4, 0x7, 0xB, 0xE)

# All void or sea, no items can spawn here
NO_SPAWN_TILES = (0x22, 0x52, 0x53, 0x54, 0x55)

#endregion

#region Test map data

FIXED_WORLD_LEVEL_2_A = b"\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x82\x00\x81\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x1A\x00\x22\x60\x22\x00\x1D\x00\x83\x00\x80\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x9A\x00\x22\x00\x22\x00\x82\x60\xA0\x00\x02\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x82\x14\x0B\x13\x1E\x00\x04\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x82\x00\x02\x00\x22\x00\x0D\x00\x91\x00\x21\x05\x1E\x00\x86\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x01\x00\x0B\x00\x08\x00\x87\x00\x10\x03\x0B\x06\x1E\x02\x21\x00\x08\x00\x02\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x00\x00\x0A\x03\x21\x0F\x21\x06\x1E\x02\x49\x00\xC9\x00\x21\x00\x8A\x00\x03\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x06\x15\x1E\x00\xA1\x00\x1E\x00\xC6\x00\x46\x00\xA1\x00\x86\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x82\x00\x88\x12\x21\x16\x1E\x13\x21\x00\x44\x00\x40\x00\xC9\x00\x8B\x00\x81\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x82\x00\x02\x00\x00\x00\x0A\x00\x9E\x00\x9E\x05\x21\x00\x48\x00\x57\x00\x4B\x00\x09\x00\x03\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x06\x00\x93\x00\x98\x00\x13\x14\x1E\x06\x21\x02\x21\x00\x21\x00\x09\x00\x9F\x00\x80\x00\x22\x00\x01\x00\x81\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x06\x00\x08\x00\xA0\x00\x66\x60\x9F\x00\x0A\x00\x8A\x00\x1F\x00\x80\x00\x22\x00\x22\x00\x9D\x00\x83\x00\x80\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x06\x00\x21\x00\x09\x00\x03\x60\x22\x00\x83\x00\x03\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x34\x00\x83\x60\x9B\x00\x80\x60\x22\x60\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x1D\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x60\x22\x60\x22\x00\x22\x60\x22\x00\x22\x00\x22\x00\x82\x00\x02\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x60\x22\x00\x82\x00\x02\x60\x22\x00\x22\x00\x22\x00\x00\x00\x03\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x60\x22\x60\x22\x60\x22\x00\x83\x00\x80\x60\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x60\x22\x00\x22\x60\x22\x60\x22\x60\x22\x60\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x60\x22\x60\x22\x60\x22\x60\x22\x60\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22\x00\x22"

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

FIXED_WORLD_LEVEL_2_ITEM_COORDS = [
    (1596, 918),
    (908, 1342),
    (2292, 1038),
    (1932, 822),
    (556, 1166),
    (1004, 974),
    (1036, 1102),
    (1972, 934),
    (1980, 598),
    (1484, 814),
    (2068, 718),
    (1892, 822),
]
FIXED_WORLD_LEVEL_2_TREE_COORDS = [
    (1008, 670),
    (2160, 366),
    (1520, 1262),
    (2336, 1038)
]
FIXED_WORLD_LEVEL_2_ELEVATOR_UP_COORD = (1776, 635)
FIXED_WORLD_LEVEL_2_SHIP_PIECE_COORD = (896, 1096)

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

#region Conversion helper functions

def tile_type_to_image_rect(tile_type: int) -> tuple:
    row, col = divmod(tile_type, 16)
    return (16*col, 8*row, 16, 8)

def road_type_to_image_rect(road_type: int) -> tuple:
    return (16*road_type, 0, 16, 8)

def item_world_coord_to_map_tile_coord(world_coord: tuple) -> tuple:
    return (world_coord[0]//8 - 12, world_coord[1]//8)

def elevator_world_coord_to_map_tile_coord(world_coord: tuple) -> tuple:
    return (world_coord[0]//8 - 16,
            world_coord[1]//8 - 8)

def ship_piece_world_coord_to_map_tile_coord(world_coord: tuple) -> tuple:
    return (world_coord[0]//8 - 21,
            world_coord[1]//8 - 8)

def item_coords_to_tilexy(item_coords: tuple[int]) -> tuple[int]:
    return item_coords[1]/(8*8) - 1, item_coords[0]//(8*16) - 1

#endregion

#region Other helper functions

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

def render_map(map_data: list[TJETile], extreme_points: list[tuple[int, int]]):
    SCALE = 4

    pygame.init()
    clock = pygame.time.Clock()
    running = True
    screen = pygame.display.set_mode((SCALE*320, SCALE*224))
    map_surface = pygame.Surface((320, 224))

    bg = pygame.image.load("map_tiles/map-bg+border.png").convert()
    map_tiles = pygame.image.load("map_tiles/maptiles_00-79.png").convert()
    road_tiles = pygame.image.load("map_tiles/roadtiles_00-0F.png").convert()
    elevator = pygame.image.load("map_tiles/elevator.png").convert()
    ship_piece = pygame.image.load("map_tiles/shippiece-on.png").convert()
    ship_piece.set_colorkey("black")

    map_surface.blit(bg, (0,0))

    special_tiles = []
    for item_coords in FIXED_WORLD_LEVEL_2_ITEM_COORDS:
        x, y = item_coords_to_tilexy(item_coords)
        special_tiles.append((floor(x), floor(y)))

    for i, t in enumerate(map_data):
        dest_row, dest_col = divmod(i, 19)
        dest_x = dest_col*16 + 6
        dest_y = dest_row*8 + 8

        # Main tile
        tile_src_rect = tile_type_to_image_rect(t.type)

        next_tile_img = pygame.Surface((16, 8))
        next_tile_img.set_colorkey("black")
        next_tile_img.blit(map_tiles, (0, 0), tile_src_rect)
        if t.mirrored:
            next_tile_img = pygame.transform.flip(next_tile_img, True, False)
        if t.hidden:
            pygame.draw.circle(next_tile_img, "red", (8, 4), 2, 0)

        # Road overlay
        if t.road_type > 0:
            road_src_rect = tile_type_to_image_rect(t.road_type)

            next_road_img = pygame.Surface((16, 8))
            next_road_img.set_colorkey("black")
            next_road_img.blit(road_tiles, (0, 0), road_src_rect)
            if t.road_mirrored:
                next_road_img = pygame.transform.flip(next_road_img, True, False)

            next_tile_img.blit(next_road_img, (0, 0))


        if (dest_row, dest_col) in special_tiles:
            next_tile_img.fill("blue", None, special_flags=pygame.BLEND_ADD)

        # Extreme points

        if t.type not in NO_SPAWN_TILES and (t.col in (extreme_points["east"], extreme_points["west"]) or
                                             t.row in (extreme_points["north"], extreme_points["south"])):
            next_tile_img.fill("red", None, special_flags=pygame.BLEND_ADD)

        map_surface.blit(next_tile_img, (dest_x, dest_y))

    # Items

    for coord in FIXED_WORLD_LEVEL_2_ITEM_COORDS:
        pygame.draw.circle(map_surface, "white", item_world_coord_to_map_tile_coord(coord), 2, 0)

    # Elevator

    map_surface.blit(elevator, elevator_world_coord_to_map_tile_coord(FIXED_WORLD_LEVEL_2_ELEVATOR_UP_COORD))

    # Ship piece

    map_surface.blit(ship_piece, ship_piece_world_coord_to_map_tile_coord(FIXED_WORLD_LEVEL_2_SHIP_PIECE_COORD))

    screen.blit(pygame.transform.scale(map_surface, screen.get_size()), (0, 0))
    pygame.display.flip()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        clock.tick(30)

    pygame.quit()

# Finds the most northern/southern/eastern/western points on the map
def get_extreme_points(map_data: list[list[TJETile]]) -> dict[str, int]:
    extremes = {}
    land_data_rows = [[int(tile.type not in NO_SPAWN_TILES) for tile in row] for row in map_data]
    extremes["north"] = first_matching_index(land_data_rows, lambda row: sum(row) > 0)
    extremes["south"] = 25 - first_matching_index(reversed(land_data_rows), lambda row: sum(row) > 0)

    land_data_cols = list(zip(*land_data_rows)) # switch rows and cols
    extremes["east"] = first_matching_index(land_data_cols, lambda col: sum(col) > 0)
    extremes["west"] = 18 - first_matching_index(reversed(land_data_cols), lambda col: sum(col) > 0)
    return extremes

def get_road_str(tile_coords: tuple, map_data: list[list[TJETile]]) -> str | None:
    candidate_tiles = product((tile_coords[0], tile_coords[0]-1, tile_coords[0]+1),
                              (tile_coords[1], tile_coords[1]-1, tile_coords[1]+1))
    for tile in candidate_tiles:
        road_type = map_data[tile[0]][tile[1]].road_type
        if road_type > 0:
            if road_type in ROAD_ENDS:
                return "the end of a road"
            else:
                return "a road"
    return None

def get_water_str(tile_coords: tuple, map_data: list[list[TJETile]]) -> str | None:
    candidate_tiles = product((tile_coords[0], tile_coords[0]-1, tile_coords[0]+1),
                              (tile_coords[1], tile_coords[1]-1, tile_coords[1]+1))
    for tile in candidate_tiles:
        if map_data[tile[0]][tile[1]].type in WATER_TILES:
            return "water"
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

def evaluate_item(item_coords: tuple, map_tiles: list[list[TJETile]]) -> str:
    # Convert to Cartesian coordinates, calculate compass direction from angle
    cart_coords = game_coords_to_cartesian(item_coords)
    ang = angle(cart_coords)
    ang = ang + 360.0 if ang < 0 else ang

    dir_idx = first_matching_index(DIRECTION_CUTOFFS, lambda cutoff: cutoff > ang)
    direction = DIRECTIONS[dir_idx]

    # Calculate distance, assign appropriate word
    d = dist((0, 0), cart_coords)
    adv_idx = floor(linear_rescale(d if d < EXTREMELY_FAR_DIST else MAX_DIST-1, 0, MAX_DIST, 0, len(ADVS)))

    ret_str = f"{ADVS[adv_idx]} {direction}"

    # Check for special tile types
    tile_x, tile_y = item_coords_to_tilexy(item_coords)
    tile_coords = (floor(tile_x), floor(tile_y))
    tile_type = map_tiles[tile_coords[0]][tile_coords[1]].type

    hint_body = TILE_STRS.get(tile_type, None)
    nearby_landmarks = []

    if "water" not in hint_body and "lake" not in hint_body:
        water_str = get_water_str(tile_coords, map_tiles)
        if water_str:
            nearby_landmarks.append(water_str)
    for tree_coord in FIXED_WORLD_LEVEL_2_TREE_COORDS:
        if dist(tree_coord, item_coords) < TREE_NEAR_DIST:
            nearby_landmarks.append("a tree") #TODO: check if cactus or not, change as appropriate
    road_str = get_road_str(tile_coords, map_tiles)
    if road_str:
        nearby_landmarks.append(road_str)

    if hint_body:
        ret_str = f"{ret_str}, {hint_body}"
    if nearby_landmarks:
        ret_str = f"{ret_str}, near {concat_item_list(nearby_landmarks)}"

    return ret_str

def binary_map_data_to_tile_list(map_bytes: bytes) -> list[TJETile]:
    return [
        [TJETile(i, j, *t) for j, t in enumerate(batched(group, 2))]
        for i, group in enumerate(batched(map_bytes, 19*2))
        ]

map_data = binary_map_data_to_tile_list(FIXED_WORLD_LEVEL_2_A)
extreme_points = get_extreme_points(map_data)

for i, item in enumerate(FIXED_WORLD_LEVEL_2_ITEM_COORDS):
    print(f"Item {i+1}:",evaluate_item(item, map_data))

render_map(chain(*map_data), get_extreme_points(map_data))
