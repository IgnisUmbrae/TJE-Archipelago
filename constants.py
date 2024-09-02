from enum import IntEnum

BASE_TJE_ID = 25101991

DEBUG = False

#region Floor items and ship pieces

TREES = [b"\x51", b"\x52", b"\x53"]

# 0x00 to 0x04 are open(ing) states; 0x0b is a special state on level 25 when there's no elevator to the next floor
END_ELEVATOR_UNLOCKED_STATES = [b"\x00", b"\x01", b"\x02", b"\x03", b"\x04"]

FIXED_SHIP_PIECE_LEVELS = [2, 6, 10, 12, 15, 17, 20, 21, 23, 25]

SHIP_PIECE = b"\x00"
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

TJ_SWIMMING_SPRITES = [0x03, 0x07, 0x22, 0x26, 0x23, 0x27, 0x2B, 0x2C, 0x2D, 0x2E, 0x2F,
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
    TJ_MENU_FLAG = 0x9364
    TJ_UNFALL_FLAG = 0x936C
    TJ_LIVES = 0xA248
    TJ_POINTS = 0xA24C
    TJ_RANK = 0xA250
    TJ_POSITION = 0xA25A
    TJ_STATE = 0xA289
    TJ_SPRITE = 0xA2A5
    TJ_LEVEL = 0xA2A6 # 0x912C also seems to work
    TJ_FALL_STATE = 0xDA22
    TJ_YUPNOPE_MENU_FLAG = 0xE234

    # Elevator-related
    END_ELEVATOR_STATE = 0xDA4F
    GLOBAL_ELEVATOR_STATE = 0xDA6A

    # Entity-related
    PRESENTS_IDENTIFIED_START = 0xDA8B
    INVENTORY_START = 0xDAC2
    FLOOR_ITEM_START = 0xDAE2
    DROPPED_PRESENTS_START = 0xDCE6
    COLLECTED_ITEMS_START = 0xDDE8
    EARTHLINGS_START = 0xDE72
    SHIP_ITEMS_TRIGGERED_START = 0xE212
    SHIP_PIECES_COLLECTED_START = 0xF444

#endregion