from typing import NamedTuple

BASE_TJE_ID = 25101991

#region Sound effects

PCM_SFX_ADDRS = [0x00044d8a, 0x000491c8, 0x0004c276, 0x0004d75a, 0x0004dfa0, 0x0004f79a, 0x00051472, 0x00053920,
                 0x00054626, 0x00055a9a, 0x0005747c, 0x0005a02e, 0x0005d7a0, 0x0005f5e2, 0x000601b4, 0x00061bd6,
                 0x00064178, 0x00067cba, 0x0006a13c, 0x0006ac3e, 0x0006b4a8, 0x0006f5aa, 0x0007177c, 0x000730de,
                 0x000741f0, 0x000752ba, 0x00076ecc, 0x0007763e, 0x00079170, 0x0007a2e2, 0x0007be44, 0x0007ccc6,
                 0x0007de38, 0x0007e8ba, 0x0008233c, 0x0008381e, 0x00088060]

# These four sounds are also used as part of the music
PCM_SFX_ADDRS_MUSIC = [0x00089a42, 0x0008a4ac, 0x0008addc, 0x0008b104]

# Excluding in Jam Out
PCM_SFX_USAGE_ADDRS = [
    (0x0002009c, 0x0002160c), (0x0000f8c0,), (0x0001b2e6,), (0x0010a1f4, 0x0010a220), (0x0001070c,),
    (0x0001663a, 0x000166f6), (0x0001015c, 0x0001059c, 0x0001089e, 0x00011cbe, 0x00023f8c), (0x0000fcda, 0x0001b3cc),
    (0x0000f3ca, 0x0002ad16, 0x0002ad42, 0x0002b1b2, 0x0002b200, 0x000378ea), (0x0001e600, 0x0003a658), (0x0001bdba,),
    (0x00019824,), (0x0001d420,), (0x0001b2f4,), (0x0002185e,), (0x00021b08,), (0x00022c92,), (0x0001a30e,),
    (0x000169c6, 0x00023daa), (0x0001c510,), (0x0000943c,), (0x0001b53c,), (), (0x00019d88, 0x00019e6c), (0x000200b6,),
    (0x0002135a,), (0x000120d2, 0x000120fa), (0x0001661e, 0x0001683c), (), (), (0x0000fa0c,), (0x0000fa1c,),
    (0x0000fa7e,), (0x00012598,), (0x0010a18e,), (0x000125c6,), (0x00012580,)
]

PCM_SFX_USAGE_ADDRS_MUSIC = [
    (0x00012182, 0x0002002a, 0x00020076, 0x0003779c, 0x0003efe6), (0x0003effe,), (0x0003efce,), (0x0001677a, 0x0003f01e)
]

# Not included: the menu blip 0x7, rocket skates sound 0x5
PSG_SFX = [0x1, 0x2, 0x3, 0x4, 0x8, 0xA, 0xC, 0xE, 0xF, 0x10, 0x11, 0x12, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19]

# Not included: menu blips @ (0x00009482, 0x000095ae, 0x000097f6, 0x00013d8a, 0x000239bc, 0x000239ea)
#               rocket skates @ (0001738a, 000224f6)
PSG_SFX_USAGE_ADDRS = [
    (0x0010a2b8,), (0x0001cd8c,), (0x00013db4,), (), (0x0002b6ba,), (0x0002b240,),
    (0x000206ec,), (0x0001be8e,), (0x00014024,), (0x00015c0c, 0x0001f18c), (0x00013b38, 0x00013d36),
    (0x0010a22e, 0x000165ca, 0x000166ce, 0x00016c34), (0x0001db66, 0x0001dd80, 0x0001de9c),
    (0x0002aede, 0x0002af76, 0x0003a690), (0x0002af36,), (0x00011c56,), (0x00013eb2, 0x00014134), (),
    (0x00009a4e, 0x00009b1c, 0x00009cd4, 0x00009da2, 0x00009e1a, 0x00021622, 0x00021b1e, 0x0002398a)
]

#endregion

#region Inventory-related ROM addresses

INV_REF_ADDRS = (0x0000934a+2, 0x000097aa+2, 0x000099a8+2, 0x000099ca+2, 0x00009b02+2, 0x00009c10+2,
                       0x00009c98+2, 0x00009d76+2, 0x00009dcc+2, 0x0000a23a+2, 0x0000a460+2, 0x00014310+2,
                       0x0010a0e0+2, 0x0010a0f8+2, 0x0001ac24+4, 0x00021fba+2, 0x0002227a+2, 0x0010a902+2)

INV_SIZE_ADDRS = (0x00009396+3, 0x00009c04+3, 0x00009c34+3, 0x00009ce0+3, 0x00014320+5, 0x00014328+3,
                  0x0010a12a+3, 0x0010a130+3, 0x00021fd8+3, 0x0010a922+3, 0x0010a93a+3)

INV_SIZE_ADDRS_INITIAL = (0x000143c2+5, 0x000143c8+5, 0x000143d6+5, 0x000143dc+5)

INV_SIZE_ADDRS_ASL_D0 = [0x00009358, 0x0000936c, 0x00009380, 0x000097a8, 0x00009a0c, 0x00009a64, 0x00009a8e,
                         0x00009a9c, 0x00009abc, 0x00009ad6, 0x00009b68, 0x00009b7c, 0x00009b8a, 0x00009baa,
                         0x00009bc4, 0x00009c0e, 0x00009c96, 0x00009d74, 0x00009dca, 0x0000a238, 0x0000a45e,
                         0x0010a0de, 0x0010a0f6, 0x00021fc6, 0x00022042, 0x0002205a, 0x0002207e, 0x00022278]

#endregion

#region Dialogue-related ROM addresses

MAP_REVEAL_DIALOGUE_ADDRS = (0x00105b73, 0x00105b7e, 0x00105b8a, 0x00105b97, 0x00105ba4)

#region Dialogue templates

MAP_REVEAL_DIALOGUE_TEMPLATE = "Lv{}-{} map!"
MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN = "Lv{} map!"

STATIC_DIALOGUE_LIST: dict[str, tuple[str,str]] = {
    "Rocketship Windshield": ("Windshield!", "jammin'"),
    "Left Megawatt Speaker": ("L. speaker!", "jammin'"),
    "Super Funkomatic Amplamator": ("Amp!", "jammin'"),
    "Amplamator Connector Fin": ("Amp fin!", "jammin'"),
    "Forward Stabilizing Unit": ("Front leg!", "jammin'"),
    "Rear Leg": ("Rear leg!", "jammin'"),
    "Awesome Snowboard": ("Snowboard!", "jammin'"),
    "Righteous Rapmaster Capsule": ("Capsule!", "jammin'"),
    "Right Megawatt Speaker": ("R. speaker!", "jammin'"),
    "Hyperfunk Thruster": ("Thruster!", "jammin'"),
    "Cupid Trap": ("Uh-oh...", "cupid trap!"),
    "Burp Trap": ("Uh-oh...", "burp trap!"),
    "Sleep Trap": ("Uh-oh...", "study time!"),
    "Earthling Trap": ("Uh-oh...", "earthling!!"),
    "Rocket Skates Trap": ("Uh-oh...", "skates trap!"),
    "Randomizer Trap": ("Uh-oh...", "randomizer!!"),
}

#endregion

#region Floor items and ship pieces

TREES = [b"\x51", b"\x52", b"\x53"]

FIXED_SHIP_PIECE_LEVELS = [2, 6, 10, 12, 15, 17, 20, 21, 23, 25]

COLLECTED_SHIP_ITEM = b"\x00"
EMPTY_SHIP_PIECE = b"\xFF"
EMPTY_ITEM = b"\xFF"
EMPTY_PRESENT = b"\xFF"

#endregion

#region Elevator and rank checks

VANILLA_RANK_THRESHOLDS = [0, 40, 100, 180, 280, 400, 540, 700, 880]
RANK_NAMES = ["Wiener", "Dufus", "Poindexter", "Peanut", "Dude", "Bro", "Homey", "Rapmaster", "Funk Lord"]

#endregion

#region Misc

INITIAL_PRESENT_ADDRS = [0x00014393, 0x00014397, 0x000143a5, 0x000143ab,
                         0x000143c5, 0x000143cb, 0x000143d9, 0x000143df]

BASE_LEVEL_TYPES = [0, 1, 5, 2, 7, 3, 4, 2, 6, 7, 2, 3, 6, 2, 4, 7, 2, 4, 2, 7, 4, 5, 1, 7]

# ROM-internal menu return values → AP-internal character values
def ret_val_to_char(ret_val: int) -> int:
    match ret_val:
        # ToeJam only
        case 1:
            return 0
        # Earl only
        case 2:
            return 1
        # Both
        case 0:
            return 2

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
    "CURRENT_BUTTONS": (0x801E, 0x1),
    "PREV_BUTTONS": (0x8020, 0x1),
    "HIGHEST_LEVEL_REACHED": (0x9132, 0x1),
    "LIVES": (0xA248, 0x1),
    "BUCKS": (0xA24A, 0x1),
    "POINTS": (0xA24C, 0x2),
    "RANK": (0xA250, 0x1),
    "HEALTH": (0xA252, 0x1),
    "HP_DISPLAY": (0xA254, 0x2),
    "HP_RESTORE": (0xA258, 0x2),
    "FALL_STATE": (0xDA22, 0x1),
    "SLEEP_TIMER": (0xDA44, 0x2),
    "GLOBAL_ELEVATOR_STATE": (0xDA6A, 0x1),
    "INVENTORY": (0xDAC2, 0x10),
    "BURPS_LEFT": (0xDE62, 0x1),
    "BURP_TIMER" : (0xDE64, 0x1),
    "CUPID_HEART_REF": (0xE1DC, 0x1),
    "CUPID_EFF_TIMER": (0xE1DF, 0x2),
    "CUPID_EFF_TYPE": (0xE1E2, 0x1)
}

GLOBAL_RAM_ADDRS: dict[int] = {
    "UNFALL_FLAG": 0x936C,
    #UNFALL_FLAG_2 = 0x936D
    "FLOOR_ITEMS": 0xDAE2,
    "END_ELEVATOR_STATE": 0xDA4F,
    "PRESENTS_WRAPPING": 0xF300, # vanilla: 0xDA8A
    "PRESENTS_IDENTIFIED": 0xF300, # vanilla: 0xDA8A
    "DROPPED_PRESENTS": 0xDCE6,
    "COLLECTED_ITEMS": 0xDDE8,
    "EARTHLINGS": 0xDE72,
    "TRIGGERED_SHIP_ITEMS": 0xE212,
    "COLLECTED_SHIP_PIECES": 0xF444,
    "UNCOVERED_MAP_MASK": 0x91EC,
    "TRANSP_MAP_MASK": 0x92A2,
    # Special AP addresses
    "AP_CHARACTER": 0xF000,
    "AP_GIVE_ITEM": 0xF554,
    "AP_AUTO_PRESENT": 0xF555,
    "AP_AUTO_NO_POINTS": 0xF556,
    "AP_CUPID_TRAP": 0xF557,
    "AP_DIALOGUE_TRIGGER": 0xF558,
    "AP_DIALOGUE_LINE1": 0xF600,
    "AP_DIALOGUE_LINE2": 0xF60C
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
    slot_size: int # in bytes
    fixed_offset: int # in bytes

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
    "UNCOVERED_MAP_MASK": SlotStructure(25, 7, 0)
}

PLAYER_SLOT_STRUCTURES: dict[SlotStructure] = {
    "INVENTORY": SlotStructure(15, 1, 0)
}

def expand_inv_constants() -> None:
    PLAYER_SLOT_STRUCTURES["INVENTORY"] = SlotStructure(63, 1, 0)
    PLAYER_RAM_ADDRS["INVENTORY"] = (0xF280, 0x40)

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

def add_save_data_points(player: int = 0, expanded_inv: bool = False) -> None:
    SAVE_DATA_POINTS.extend([
        DataPoint("Highest level reached", get_ram_addr("HIGHEST_LEVEL_REACHED", player), 1),

        DataPoint("Rank", get_ram_addr("RANK", player), 1),
        DataPoint("Points", get_ram_addr("POINTS", player), 2),
        DataPoint("Bucks", get_ram_addr("BUCKS", player), 1),
        DataPoint("Lives", get_ram_addr("LIVES", player), 1),

        DataPoint("Inventory", get_ram_addr("INVENTORY", player), 64 if expanded_inv else 16),

        DataPoint("Max health", get_ram_addr("HP_DISPLAY", player), 1),
        DataPoint("Health", get_ram_addr("HEALTH", player), 1),
    ])

#endregion
