from typing import NamedTuple
from enum import IntEnum

from BaseClasses import Item, ItemClassification, MultiWorld

from .constants import BASE_TJE_ID
from .generators import item_totals
from .options import TJEOptions, ElevatorKeyTypeOption, GameOverOption, StartingPresentOption

# TO DO: lots of redundancy here; needs a big clean-up

# Extra codes: 1C = AP item; 1D = AP progression item; 1E = elevator key; 1F = map reveal; 20 = ground ship piece

#region Item data

class TJEItem(Item):
    game: str = "ToeJam & Earl"
    type: str
    point_value: int = 0
    rank_value: int = 0

# "Ethereal" is used for extra items such as elevator keys that do not exist in the base game
class TJEItemType(IntEnum):
    ETHEREAL = 0
    PRESENT = 1
    EDIBLE = 2
    SHIP_PIECE = 3

class TJEItemData(NamedTuple):
    code: int
    name: str
    type: TJEItemType
    classification: ItemClassification
    point_value: int

BASE_ITEM_LIST: list[TJEItemData] = [
    TJEItemData(0x20, "Rocketship Windshield", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Left Megawatt Speaker", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Super Funkomatic Amplamator", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Amplamator Connector Fin", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Forward Stabilizing Unit", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Rear Leg", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Awesome Snowboard", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Righteous Rapmaster Capsule", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Right Megawatt Speaker", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(0x20, "Hyperfunk Thruster", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),

    TJEItemData(0x00, "Icarus Wings", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x01, "Spring Shoes", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x02, "Innertube", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x03, "Tomatoes", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x04, "Slingshot", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x05, "Rocket Skates", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x06, "Rose Bushes", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x07, "Super Hitops", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x08, "Doorway", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x09, "Food Present", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x0A, "Rootbeer", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x0B, "Promotion", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x0C, "Un-fall", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x0D, "Rain Cloud", TJEItemType.PRESENT, ItemClassification.trap, 0),
    TJEItemData(0x0E, "Fudge Sundae Present", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x0F, "Decoy", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x10, "Total Bummer", TJEItemType.PRESENT, ItemClassification.trap, 0),
    TJEItemData(0x11, "Extra Life", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x12, "Randomizer", TJEItemType.PRESENT, ItemClassification.trap, 0),
    TJEItemData(0x13, "Telephone", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x14, "Extra Buck Present", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x15, "Jackpot", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x16, "Tomato Rain", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x17, "Earthling", TJEItemType.PRESENT, ItemClassification.trap, 0),
    TJEItemData(0x18, "School Book", TJEItemType.PRESENT, ItemClassification.trap, 0),
    TJEItemData(0x19, "Boombox", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x1A, "Mystery Present", TJEItemType.PRESENT, ItemClassification.filler, 2),
    TJEItemData(0x1B, "Bonus Hitops", TJEItemType.PRESENT, ItemClassification.useful, 2),

    TJEItemData(0x40, "Burger", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x41, "Fudge Sundae", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x42, "Fudge Cake", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x43, "Candy Cane", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x44, "Fries", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x45, "Pancakes", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x46, "Watermelon", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x47, "Bacon & Eggs", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x48, "Cherry Pie", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x49, "Pizza", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x4A, "Cereal", TJEItemType.EDIBLE, ItemClassification.filler, 0),
    TJEItemData(0x4B, "Fish Bones", TJEItemType.EDIBLE, ItemClassification.trap, 0),
    TJEItemData(0x4C, "Moldy Cheese", TJEItemType.EDIBLE, ItemClassification.trap, 0),
    TJEItemData(0x4D, "Moldy Bread", TJEItemType.EDIBLE, ItemClassification.trap, 0),
    TJEItemData(0x4E, "Slimy Fungus", TJEItemType.EDIBLE, ItemClassification.trap, 0),
    TJEItemData(0x4F, "Old Cabbage", TJEItemType.EDIBLE, ItemClassification.trap, 0),
    TJEItemData(0x50, "A Buck", TJEItemType.EDIBLE, ItemClassification.filler, 0),

    TJEItemData(0xFF, "Nothing", TJEItemType.ETHEREAL, ItemClassification.filler, 0)
]

ELEVATOR_KEY_ITEMS: list[TJEItemData] = [
    TJEItemData(0x1E, "Progressive Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0)
]

INSTATRAP_ITEMS: list[TJEItemData] = [
    TJEItemData(0x1C, "Cupid Trap", TJEItemType.ETHEREAL, ItemClassification.trap, 0),
    TJEItemData(0x1C, "Burp Trap", TJEItemType.ETHEREAL, ItemClassification.trap, 0),
    TJEItemData(0x1C, "Sleep Trap", TJEItemType.ETHEREAL, ItemClassification.trap, 0),
    TJEItemData(0x1C, "Earthling Trap", TJEItemType.ETHEREAL, ItemClassification.trap, 0),
    TJEItemData(0x1C, "Rocket Skates Trap", TJEItemType.ETHEREAL, ItemClassification.trap, 0),
    TJEItemData(0x1C, "Randomizer Trap", TJEItemType.ETHEREAL, ItemClassification.trap, 0),
]

MISC_ITEMS: list[TJEItemData] = [
    TJEItemData(0x1F, "Progressive Map Reveal", TJEItemType.ETHEREAL, ItemClassification.useful, 0)
]

MASTER_ITEM_LIST = BASE_ITEM_LIST + ELEVATOR_KEY_ITEMS + INSTATRAP_ITEMS + MISC_ITEMS

ITEM_NAME_TO_DATA : dict[str, TJEItemData] = {item.name: item for item in MASTER_ITEM_LIST}

ITEM_ID_TO_NAME = dict(enumerate([item.name for item in MASTER_ITEM_LIST], BASE_TJE_ID)) 
ITEM_NAME_TO_ID = {name: id for id, name in ITEM_ID_TO_NAME.items()}

ITEM_ID_TO_CODE = dict(enumerate([item.code for item in MASTER_ITEM_LIST], BASE_TJE_ID))
ITEM_CODE_TO_ID = {code: id for id, code in ITEM_ID_TO_CODE.items()}

ITEM_CODE_TO_NAME = {item.code: item.name for item in MASTER_ITEM_LIST}
ITEM_NAME_TO_CODE = {item.name: item.code for item in MASTER_ITEM_LIST}

SHIP_PIECE_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST if item.type == TJEItemType.SHIP_PIECE]
PRESENT_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST if item.type == TJEItemType.PRESENT]
EDIBLE_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST if item.type == TJEItemType.EDIBLE]
KEY_IDS = [ITEM_NAME_TO_ID[item.name] for item in ELEVATOR_KEY_ITEMS]
INSTATRAP_IDS = [ITEM_NAME_TO_ID[item.name] for item in INSTATRAP_ITEMS]
TRAP_PRESENT_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST
                    if item.type == TJEItemType.PRESENT and item.classification == ItemClassification.trap]

#endregion

#region Dialogue-related

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

def create_items(world, multiworld: MultiWorld, player: int, options: TJEOptions) -> None:
    item_list: list[TJEItem] = []

    total_locations = sum(item_totals(True, options.min_items.value, options.max_items.value, options.last_level.value))

    create_ship_pieces(multiworld, world, options, player, item_list)

    handle_trap_options(world, options)
    handle_gameover_options(world, options)

    # This number is relative to the number of *base* locations (floor items + ship pieces)
    # Negative means we need to add items; positive means we have too many
    differential = create_rank_items(world, options, item_list) \
                   + create_elevator_keys(world, options, item_list) \
                   + create_map_reveals(world, options, item_list) \
                   + create_instatraps(world, options, total_locations, item_list)

    create_main_items(world, item_list, total_locations, differential)

    multiworld.itempool.extend(item_list)

def handle_trap_options(world, options) -> None:
    if not options.trap_presents:
        world.generator.forbid_trap_presents()
    if not options.trap_food:
        world.generator.forbid_trap_food()

def handle_gameover_options(world, options) -> None:
    if options.game_overs == GameOverOption.DISABLE:
        world.generator.forbid_item(ITEM_NAME_TO_CODE["Extra Life"])

def create_ship_pieces(multiworld, world, options, player, item_list) -> None:
    ship_pieces_total = 10

    multiworld.get_location(f"Level {options.last_level.value} - Ship Piece", player).place_locked_item(
        world.create_item("Hyperfunk Thruster", ItemClassification.progression)
    )
    ship_pieces_total -= 1

    for item in MASTER_ITEM_LIST[:ship_pieces_total]:
        item_list.append(world.create_item(item.name, item.classification))

def create_instatraps(world, options, total_locations, item_list) -> int:
    instatrap_total = 0

    instatrap_weights = [
                        5 if options.trap_cupid else 0,
                        3 if options.trap_burp else 0,
                        3 if options.trap_sleep else 0,
                        4 if options.trap_earthling else 0,
                        2 if options.trap_skates else 0,
                        1 if options.trap_randomizer else 0
                        ]

    if sum(instatrap_weights) > 0:
        instatrap_total = world.random.randint(round(0.03*total_locations), round(0.06*total_locations))
        item_list.extend([
            world.create_item(id, ItemClassification.trap)
            for id in world.random.choices(INSTATRAP_IDS, weights=instatrap_weights, k=instatrap_total)
        ])

    return instatrap_total

def create_elevator_keys(world, options, item_list) -> int:
    item_list.extend([world.create_item("Progressive Elevator Key", ItemClassification.progression)
                        for _ in range(len(world.key_levels))])
    return len(world.key_levels)

def create_rank_items(world, options: TJEOptions, item_list) -> int:
    differential = 0
    if options.max_rank_check > 0:
        differential -= 8

    # Add an extra promotion if rank check is 7, two if 8; this helps avoid fill errors from impossible seeds
    # These may end up being unplaceable, but the seed will still be completable in that instance
    extra_promos = max(options.max_rank_check - 6, 0)
    if extra_promos > 0:
        item_list.extend([world.create_item("Promotion") for _ in range(extra_promos)])
        differential += extra_promos
    return differential

def create_map_reveals(world, options, item_list) -> int:
    if options.map_reveals:
        item_list.extend([world.create_item("Progressive Map Reveal", ItemClassification.useful) for _ in range(5)])
        return 5
    return 0

def create_main_items(world, item_list, total_locations, differential) -> None:

    item_pool_raw = world.generator.generate_item_blob(total_locations - differential)

    for item in item_pool_raw:
        item_id = ITEM_CODE_TO_ID[item]
        item_name = ITEM_ID_TO_NAME[item_id]
        item_data = ITEM_NAME_TO_DATA[item_name]
        item_classification = item_data.classification

        item_list.append(world.create_item(item_name, item_classification))

def create_starting_presents(world, multiworld : MultiWorld, options: TJEOptions) -> None:
    match options.starting_presents:
        case StartingPresentOption.NONE:
            world.starting_presents = []
        case StartingPresentOption.HITOPS:
            world.starting_presents = [ITEM_NAME_TO_ID["Bonus Hitops"]]*8
        case StartingPresentOption.MIX:
            world.starting_presents = [ITEM_NAME_TO_ID["Icarus Wings"], ITEM_NAME_TO_ID["Bonus Hitops"],
                                       ITEM_NAME_TO_ID["Spring Shoes"], ITEM_NAME_TO_ID["Rocket Skates"]]*2
        case StartingPresentOption.ANY_GOOD:
            world.starting_presents = [ITEM_CODE_TO_ID[p]
                                       for p in world.generator.generate_initial_inventory(include_bad=False)]*2
        case StartingPresentOption.ANY:
            world.starting_presents = [ITEM_CODE_TO_ID[p]
                                       for p in world.generator.generate_initial_inventory(include_bad=True)]*2
    for item in world.starting_presents[:4]:
        multiworld.push_precollected(world.create_item(item))
