from typing import Optional, NamedTuple
from enum import IntEnum

from BaseClasses import Item, ItemClassification, MultiWorld

from .constants import BASE_TJE_ID
from .generators import item_totals
from .options import StartingPresentOptions, TJEOptions, TrapOption, ShipPieceOption

# TO DO: lots of redundancy here; needs a big clean-up

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
    code: Optional[int]
    name: str
    type: TJEItemType
    classification: ItemClassification
    point_value: int

BASE_ITEM_LIST: list[TJEItemData] = [
    TJEItemData(None, "Rocketship Windshield", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Left Megawatt Speaker", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Super Funkomatic Amplamator", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Amplamator Connector Fin", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Forward Stabilizing Unit", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Rear Leg", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Awesome Snowboard", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Righteous Rapmaster Capsule", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Right Megawatt Speaker", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),
    TJEItemData(None, "Hyperfunk Thruster", TJEItemType.SHIP_PIECE, ItemClassification.progression, 0),

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
    TJEItemData(0x0D, "Rain Cloud", TJEItemType.PRESENT, ItemClassification.trap, 2),
    TJEItemData(0x0E, "Fudge Sundae Present", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x0F, "Decoy", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x10, "Total Bummer", TJEItemType.PRESENT, ItemClassification.trap, 2),
    TJEItemData(0x11, "Extra Life", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x12, "Randomizer", TJEItemType.PRESENT, ItemClassification.trap, 2),
    TJEItemData(0x13, "Telephone", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x14, "Extra Buck Present", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x15, "Jackpot", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x16, "Tomato Rain", TJEItemType.PRESENT, ItemClassification.useful, 2),
    TJEItemData(0x17, "Earthling", TJEItemType.PRESENT, ItemClassification.trap, 2),
    TJEItemData(0x18, "School Book", TJEItemType.PRESENT, ItemClassification.trap, 2),
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
    TJEItemData(0x4F, "Cabbage", TJEItemType.EDIBLE, ItemClassification.trap, 0),
    TJEItemData(0x50, "A Buck", TJEItemType.EDIBLE, ItemClassification.filler, 0),

    TJEItemData(0xFF, "Nothing", TJEItemType.ETHEREAL, ItemClassification.filler, 0)
]

ELEVATOR_KEY_ITEMS : list[TJEItemData] = [
    TJEItemData(None, "Level 2 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 3 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 4 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 5 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 6 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 7 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 8 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 9 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 10 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 11 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 12 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 13 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 14 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 15 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 16 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 17 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 18 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 19 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 20 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 21 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 22 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 23 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0),
    TJEItemData(None, "Level 24 Elevator Key", TJEItemType.ETHEREAL, ItemClassification.progression, 0)
]

MISC_ITEMS : list[TJEItemData] = [
    # Logically represents uncovering 1/8 of the map tiles for 7 points
    TJEItemData(None, "Uncover 7 Map Tiles", TJEItemType.ETHEREAL, ItemClassification.progression_skip_balancing, 7),
    TJEItemData(None, "Rank", TJEItemType.ETHEREAL, ItemClassification.progression_skip_balancing, 0)
]

MASTER_ITEM_LIST = BASE_ITEM_LIST + ELEVATOR_KEY_ITEMS + MISC_ITEMS

ITEM_NAME_TO_DATA : dict[str, TJEItemData] = {item.name: item for item in MASTER_ITEM_LIST}

ITEM_ID_TO_NAME = {id: name for id, name in enumerate([item.name for item in MASTER_ITEM_LIST], BASE_TJE_ID)}
ITEM_NAME_TO_ID = {name: id for id, name in enumerate([item.name for item in MASTER_ITEM_LIST], BASE_TJE_ID)}

ITEM_CODE_TO_ID = {code: id for id, code in enumerate(
                    [item.code for item in MASTER_ITEM_LIST], BASE_TJE_ID)}
ITEM_ID_TO_CODE = {v: k for k, v in ITEM_CODE_TO_ID.items()}

ITEM_CODE_TO_NAME = {item.code: item.name for item in MASTER_ITEM_LIST}
ITEM_NAME_TO_CODE = {v: k for k, v in ITEM_CODE_TO_NAME.items()}

SHIP_PIECE_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST if item.type == TJEItemType.SHIP_PIECE]
PRESENT_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST if item.type == TJEItemType.PRESENT]
EDIBLE_IDS = [ITEM_NAME_TO_ID[item.name] for item in BASE_ITEM_LIST if item.type == TJEItemType.EDIBLE]
KEY_IDS = [ITEM_NAME_TO_ID[item.name] for item in ELEVATOR_KEY_ITEMS]

#endregion

def create_items(world, multiworld: MultiWorld, player: int, options: TJEOptions) -> None:
    item_list: list[TJEItem] = []

    extra_added = 0

    if options.max_major_rank > 0:
        extra_added -= 8

    # Handle trap options

    forbidden_combos : list[tuple[TJEItemType, ItemClassification]] = []
    match options.include_traps:
        case TrapOption.none:
            forbidden_combos += [(TJEItemType.EDIBLE, ItemClassification.trap),
                                (TJEItemType.PRESENT, ItemClassification.trap)]
        case TrapOption.items_only:
            forbidden_combos += [(TJEItemType.EDIBLE, ItemClassification.trap)]
        case TrapOption.presents_only:
            forbidden_combos += [(TJEItemType.PRESENT, ItemClassification.trap)]
        case TrapOption.all:
            pass

    # Create ship pieces

    ship_pieces_total = 10
    
    if options.final_ship_piece == ShipPieceOption.level_25:
        multiworld.get_location("Level 25 - Ship Piece", player).place_locked_item(
            world.create_item("Hyperfunk Thruster", ItemClassification.progression)
        )
        ship_pieces_total -= 1

    for item in MASTER_ITEM_LIST[:ship_pieces_total]:
        item_list.append(world.create_item(item.name, item.classification))

    # Add elevator keys if needed

    if options.elevator_key_gap:
        key_levels = world.key_levels
        for lvl in key_levels:
            item_list.append(world.create_item(f"Level {lvl} Elevator Key", ItemClassification.progression))
        extra_added += len(key_levels)

    # Add an extra promotion if rank check is 7, two if 8; this helps avoid fill errors from impossible seeds
    extra_promos = max(options.max_major_rank - 6, 0)
    if extra_promos > 0:
        item_list.extend([world.create_item("Promotion") for _ in range(extra_promos)])
        extra_added += extra_promos

    # Generate the main chunk of items

    total_locations = sum(item_totals())
    item_pool_raw = world.generator.generate_item_blob(total_locations - extra_added)

    for item in item_pool_raw:
        item_id = ITEM_CODE_TO_ID[item]
        item_name = ITEM_ID_TO_NAME[item_id]
        item_data = ITEM_NAME_TO_DATA[item_name]
        item_classification = item_data.classification

        if (item_data.type, item_classification) not in forbidden_combos:
            item_list.append(world.create_item(item_name, item_classification))
        else:
            extra_added -= 1

    # Finally, pad out item pool if needed
    # Currently only partially honours trap rules

    if extra_added < 0:
        item_list.extend([
            world.create_item(ITEM_CODE_TO_ID[code])
            for code in world.generator.generate_item_blob(extra_added, include_bad=False if TrapOption.none else True)
        ])


    multiworld.itempool.extend(item_list)

def create_starting_presents(world, multiworld : MultiWorld, options: TJEOptions) -> None:
    match options.starting_presents:
        case StartingPresentOptions.none:
            world.starting_presents = []
        case StartingPresentOptions.hitops:
            world.starting_presents = [ITEM_NAME_TO_ID["Super Hitops"]]*8
        case StartingPresentOptions.mix:
            world.starting_presents = [ITEM_NAME_TO_ID["Icarus Wings"], ITEM_NAME_TO_ID["Super Hitops"],
                                       ITEM_NAME_TO_ID["Spring Shoes"], ITEM_NAME_TO_ID["Rocket Skates"]]*2
        case StartingPresentOptions.any_good:
            world.starting_presents = [ITEM_CODE_TO_ID[p]
                                       for p in world.generator.generate_initial_inventory(include_bad=False)]*2
        case StartingPresentOptions.any:
            world.starting_presents = [ITEM_CODE_TO_ID[p]
                                       for p in world.generator.generate_initial_inventory(include_bad=True)]*2
    for item in world.starting_presents:
        multiworld.push_precollected(world.create_item(item))