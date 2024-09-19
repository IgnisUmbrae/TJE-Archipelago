from enum import IntEnum
from typing import NamedTuple

BASE_TJE_ID = 25101991

DEBUG = True

#region Floor items and ship pieces

TREES = [b"\x51", b"\x52", b"\x53"]

# 0x00 to 0x04 are open(ing) states; 0x0b is a special state on level 25 when there's no elevator to the next floor
END_ELEVATOR_UNLOCKED_STATES = [b"\x00", b"\x01", b"\x02", b"\x03", b"\x04"]

FIXED_SHIP_PIECE_LEVELS = [2, 6, 10, 12, 15, 17, 20, 21, 23, 25]

COLLECTED_SHIP_ITEM = b"\x00"
EMPTY_SHIP_PIECE = b"\xFF"
EMPTY_ITEM = b"\xFF"
EMPTY_PRESENT = b"\xFF"

#endregion

#region Elevator and rank checks

ELEVATOR_LOCKED = b"\x0A"
ELEVATOR_UNLOCKED = b"\x00"

RANK_THRESHOLDS = [40, 100, 180, 280, 400, 540, 700, 880]
RANK_NAMES = ["Dufus", "Poindexter", "Peanut", "Dude", "Bro", "Homey", "Rapmaster", "Funk Lord"]

#endregion

#region Toejam state flags

TOEJAM_STATE_LOAD_DOWN = b"\x41"

TJ_HITOPS_JUMP_SPRITES = [0x70, 0x71, 0x72, 0x73]
TJ_SWIMMING_SPRITES = [0x03, 0x07, 0x22, 0x23, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
                       0x30, 0x31, 0x32, 0x33, 0x48, 0x49, 0x4A, 0x4B, 0x64, 0x65, 0x66, 0x67, 0x77, 0x78]
TJ_GHOST_SPRITES = [0x05, 0x06]

#endregion

#region Misc

INITIAL_PRESENT_ADDRS = [0x00014393, 0x00014397, 0x000143a5, 0x000143ab,
                         0x000143c5, 0x000143cb, 0x000143d9, 0x000143df]

class RAM_ADDRS(IntEnum):
    # Global
    HIGHEST_LEVEL_REACHED = 0x9132

    # Toejam-related
    TJ_CURRENT_BUTTONS = 0x801E
    TJ_PREV_BUTTONS = 0x8020
    TJ_MENU_FLAG = 0x9364
    TJ_UNFALL_FLAG = 0x936C
    TJ_GAME_OVER_FLAG = 0xA2A7
    TJ_LIVES = 0xA248
    TJ_BUCKS = 0xA24A
    TJ_POINTS = 0xA24C
    TJ_RANK = 0xA250
    TJ_HEALTH = 0xA252
    TJ_HP_DISPLAY = 0xA254
    TJ_HP_RESTORE = 0xA258
    TJ_POSITION = 0xA25A
    TJ_STATE = 0xA289
    TJ_SPRITE = 0xA2A5
    TJ_LEVEL = 0xA2A6 # 0x912C also seems to work
    TJ_FALL_STATE = 0xDA22
    TJ_SLEEP_TIMER = 0xDA44
    TJ_YUPNOPE_MENU_FLAG = 0xE234

    # Elevator-related
    END_ELEVATOR_STATE = 0xDA4F
    GLOBAL_ELEVATOR_STATE = 0xDA6A

    # Entity-related
    PRESENTS_WRAPPING = 0xDA8A
    INVENTORY = 0xDAC2
    FLOOR_ITEMS = 0xDAE2
    DROPPED_PRESENTS = 0xDCE6
    COLLECTED_ITEMS = 0xDDE8
    EARTHLINGS = 0xDE72
    TRIGGERED_SHIP_ITEMS = 0xE212
    COLLECTED_SHIP_PIECES = 0xF444

    # Map-related
    UNCOVERED_MAP_MASK = 0x91EC
    TRANSP_MAP_MASK = 0x92A2

    # Trap-related

    CUPID_HEART_REF = 0xE1DC
    CUPID_EFF_TIMER = 0xE1DF
    CUPID_EFF_TYPE = 0xE1E2

#endregion

#region Save data–related

class DataPoint(NamedTuple):
    name: str
    address: int
    size: int

SAVE_DATA_POINTS: list[DataPoint] = [
    DataPoint("Highest level reached", RAM_ADDRS.HIGHEST_LEVEL_REACHED.value, 1),

    DataPoint("Rank (TJ)", RAM_ADDRS.TJ_RANK.value, 1),
    DataPoint("Points (TJ)", RAM_ADDRS.TJ_POINTS.value, 2),
    DataPoint("Bucks (TJ)", RAM_ADDRS.TJ_BUCKS.value, 1),
    DataPoint("Lives (TJ)", RAM_ADDRS.TJ_LIVES, 1),

    DataPoint("Inventory", RAM_ADDRS.INVENTORY.value, 16),
    DataPoint("Collected items", RAM_ADDRS.COLLECTED_ITEMS.value, 104),
    DataPoint("Dropped presents", RAM_ADDRS.DROPPED_PRESENTS.value, 256),
    DataPoint("Collected ship pieces", RAM_ADDRS.COLLECTED_SHIP_PIECES.value, 10),
    DataPoint("Triggered ship items", RAM_ADDRS.TRIGGERED_SHIP_ITEMS.value, 10),
    DataPoint("Present wrapping", RAM_ADDRS.PRESENTS_WRAPPING.value, 56),
    DataPoint("Uncovered/glass map tiles", RAM_ADDRS.UNCOVERED_MAP_MASK.value, 364),

    DataPoint("Max health (TJ)", RAM_ADDRS.TJ_HP_DISPLAY, 1),
    DataPoint("Health (TJ)", RAM_ADDRS.TJ_HEALTH, 1),
]

#endregion
