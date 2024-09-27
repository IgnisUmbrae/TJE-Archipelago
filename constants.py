from enum import IntEnum
from typing import NamedTuple

BASE_TJE_ID = 25101991

DEBUG = True

#region Floor items and ship pieces

TREES = [b"\x51", b"\x52", b"\x53"]

FIXED_SHIP_PIECE_LEVELS = [2, 6, 10, 12, 15, 17, 20, 21, 23, 25]

COLLECTED_SHIP_ITEM = b"\x00"
EMPTY_SHIP_PIECE = b"\xFF"
EMPTY_ITEM = b"\xFF"
EMPTY_PRESENT = b"\xFF"

#endregion

#region Elevator and rank checks

ELEVATOR_LOCKED = b"\x0A"
ELEVATOR_UNLOCKED = b"\x00"

END_ELEVATOR_UNLOCKED_STATES = [b"\x00", b"\x01", b"\x02", b"\x03", b"\x04"]

RANK_THRESHOLDS = [40, 100, 180, 280, 400, 540, 700, 880]
RANK_NAMES = ["Dufus", "Poindexter", "Peanut", "Dude", "Bro", "Homey", "Rapmaster", "Funk Lord"]

#endregion

#region Toejam state flags

STATE_LOAD_DOWN = b"\x41"

SPRITES_HITOPS_JUMP = [0x70, 0x71, 0x72, 0x73]
SPRITES_WATER = [0x03, 0x07, 0x22, 0x23, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
                       0x30, 0x31, 0x32, 0x33, 0x48, 0x49, 0x4A, 0x4B, 0x4D, 0x64, 0x65, 0x66, 0x67, 0x77, 0x78]
SPRITES_GHOST = [0x05, 0x06]

#endregion

#region Misc

INITIAL_PRESENT_ADDRS = [0x00014393, 0x00014397, 0x000143a5, 0x000143ab,
                         0x000143c5, 0x000143cb, 0x000143d9, 0x000143df]

BASE_LEVEL_TYPES = [0, 1, 5, 2, 7, 3, 4, 2, 6, 7, 2, 3, 6, 2, 4, 7, 2, 4, 2, 7, 4, 5, 1, 7]

# The values at 0xFFA2AC
class SPRITE_SETS(IntEnum):
    IDLE = 0x1
    WINGS_GHOST = 0x2
    WALKING = 0x4
    SNEAKING = 0x8
    TEETERING = 0x10
    FALLING = 0x20
    BOUNCING = 0x40
    DIVE_PREP = 0x80
    DIVE_1 = 0x100
    DIVE_2 = 0x200
    DIVE_3 = 0x400
    UNDERWATER = 0x800
    CLIMBING_OUT = 0x1000
    YOUCHED = 0x2000
    SPRING_SHOES = 0x4000
    FLYING = 0x8000
    UNKNOWN1 = 0x10000
    ZAPPED = 0x20000
    TUBE_SWIM = 0x40000
    TUBE_IDLE = 0x80000
    TOMATO = 0x100000
    SLINGSHOT = 0x200000
    DANCING = 0x400000
    UNKNOWN2 = 0x800000
    SKATES_HOLD = 0x1000000
    SKATES_WATER = 0x2000000
    SKATES_AIR = 0x4000000
    HITOPS_RUN = 0x8000000
    HITOPS_JUMP = 0x10000000
    SLEEPING = 0x20000000
    UNKNOWN3 = 0x40000000
    UNKNOWN4 = 0x80000000

NO_SPAWN_SPRITE_SETS = [
    SPRITE_SETS.FALLING,
    SPRITE_SETS.DIVE_1,
    SPRITE_SETS.DIVE_2,
    SPRITE_SETS.DIVE_3,
    SPRITE_SETS.UNDERWATER,
    SPRITE_SETS.CLIMBING_OUT,
    SPRITE_SETS.FLYING,
    SPRITE_SETS.UNKNOWN1,
    SPRITE_SETS.TUBE_SWIM,
    SPRITE_SETS.TUBE_IDLE,
    SPRITE_SETS.UNKNOWN2,
    SPRITE_SETS.SKATES_WATER,
    SPRITE_SETS.SKATES_AIR,
    SPRITE_SETS.HITOPS_JUMP,
    SPRITE_SETS.UNKNOWN3,
    SPRITE_SETS.UNKNOWN4
]

# 0 = Toejam, 1 = Earl
def get_ram_addr(name: str, player: int = 0) -> int:
    if name in GLOBAL_RAM_ADDRS:
        return GLOBAL_RAM_ADDRS[name]
    addr, earl_offset = PLAYER_RAM_ADDRS[name]
    return addr + player * earl_offset

PLAYER_RAM_ADDRS: dict[tuple[int, int]] = {
    # Main data store (P2 = P1 + 0x80)
    "POSITION": (0xA25A, 0x80),
    "STATE": (0xA289, 0x80),
    "SPRITE": (0xA2A5, 0x80),
    "LEVEL": (0xA2A6, 0x80),
    "GAME_OVER_FLAG": (0xA2A7, 0x80),
    "SPRITE_SET": (0xA2AC, 0x80),

    # Sequential, variable offset for Earl
    "HIGHEST_LEVEL_REACHED": (0x9132, 0x1),
    "LIVES": (0xA248, 0x01),
    "BUCKS": (0xA24A, 0x01),
    "POINTS": (0xA24C, 0x02),
    "RANK": (0xA250, 0x01),
    "HEALTH": (0xA252, 0x01),
    "HP_DISPLAY": (0xA254, 0x02),
    "HP_RESTORE": (0xA258, 0x02),
    "FALL_STATE": (0xDA22, 0x1),
    "SLEEP_TIMER": (0xDA44, 0x2),
    "GLOBAL_ELEVATOR_STATE": (0xDA6A, 0x1),
    "INVENTORY": (0xDAC2, 0x10),
    "CUPID_HEART_REF": (0xE1DC, 0x1),
    "CUPID_EFF_TIMER": (0xE1DF, 0x2),
    "CUPID_EFF_TYPE": (0xE1E2, 0x1)
}

GLOBAL_RAM_ADDRS: dict[int] = {
    # Global
    "P1_CURRENT_BUTTONS": 0x801E,
    "P1_PREV_BUTTONS": 0x8020,
    "UNFALL_FLAG": 0x936C,
    #UNFALL_FLAG_2 = 0x936D

    # Elevator-related
    "END_ELEVATOR_STATE": 0xDA4F,

    # Entity-related
    "PRESENTS_WRAPPING": 0xDA8A,
    "PRESENTS_IDENTIFIED": 0xDA8A,
    "FLOOR_ITEMS": 0xDAE2,
    "DROPPED_PRESENTS": 0xDCE6,
    "COLLECTED_ITEMS": 0xDDE8,
    "EARTHLINGS": 0xDE72,
    "TRIGGERED_SHIP_ITEMS": 0xE212,
    "COLLECTED_SHIP_PIECES": 0xF444,

    # Map-related": 
    "UNCOVERED_MAP_MASK": 0x91EC,
    "TRANSP_MAP_MASK": 0x92A2
}

def get_slot_addr(name: str, slot: int, player: int = 0) -> int | None:
    if name in GLOBAL_SLOT_STRUCTURES:
        struct = GLOBAL_SLOT_STRUCTURES[name]
        addr = GLOBAL_RAM_ADDRS[name]
    else:
        struct = PLAYER_SLOT_STRUCTURES[name]
        addr = get_ram_addr(name, player)
    if slot < 0 or slot > struct.max_slot:
        return None
    return addr + slot * struct.slot_size + struct.fixed_offset

class SlotStructure(NamedTuple):
    max_slot: int
    slot_size: int # bytes
    fixed_offset: int # bytes

GLOBAL_SLOT_STRUCTURES: dict[SlotStructure] = {
    "COLLECTED_ITEMS": SlotStructure(25, 4, 0),
    "FLOOR_ITEMS": SlotStructure(31, 8, 0),
    "DROPPED_PRESENTS": SlotStructure(31, 8, 0),
    "EARTHLINGS": SlotStructure(28, 18, 0),
    "TRIGGERED_SHIP_ITEMS": SlotStructure(9, 1, 0),
    "COLLECTED_SHIP_PIECES": SlotStructure(9, 1, 0),
    "PRESENTS_WRAPPING": SlotStructure(0x1B, 2, 0),
    "PRESENTS_IDENTIFIED": SlotStructure(0x1B, 2, 1),
    "TRANSP_MAP_MASK": SlotStructure(25, 7, 0),
    "UNCOVERED_MAP_MASK": SlotStructure(25, 7, 0),
}

PLAYER_SLOT_STRUCTURES: dict[SlotStructure] = {
    "INVENTORY": SlotStructure(15, 1, 0)
}

#endregion

#region Save data–related

class DataPoint(NamedTuple):
    name: str
    address: int
    size: int

SAVE_DATA_POINTS: list[DataPoint] = [
    DataPoint("Collected items", GLOBAL_RAM_ADDRS["COLLECTED_ITEMS"], 104),
    DataPoint("Dropped presents", GLOBAL_RAM_ADDRS["DROPPED_PRESENTS"], 256),
    DataPoint("Collected ship pieces", GLOBAL_RAM_ADDRS["COLLECTED_SHIP_PIECES"], 10),
    DataPoint("Triggered ship items", GLOBAL_RAM_ADDRS["TRIGGERED_SHIP_ITEMS"], 10),
    DataPoint("Present wrapping", GLOBAL_RAM_ADDRS["PRESENTS_WRAPPING"], 56),
    DataPoint("Map masks", GLOBAL_RAM_ADDRS["UNCOVERED_MAP_MASK"], 364),
]

def create_save_data_points(player: int = 0) -> None:
    SAVE_DATA_POINTS.extend([
        DataPoint("Highest level reached", get_ram_addr("HIGHEST_LEVEL_REACHED", player), 1),

        DataPoint("Rank", get_ram_addr("RANK", player), 1),
        DataPoint("Points", get_ram_addr("POINTS", player), 2),
        DataPoint("Bucks", get_ram_addr("BUCKS", player), 1),
        DataPoint("Lives", get_ram_addr("LIVES", player), 1),

        DataPoint("Inventory", get_ram_addr("INVENTORY", player), 16),

        DataPoint("Max health", get_ram_addr("HP_DISPLAY", player), 1),
        DataPoint("Health", get_ram_addr("HEALTH", player), 1),
    ])

#endregion
