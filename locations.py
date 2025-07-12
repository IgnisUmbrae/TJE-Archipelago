from enum import Enum
from typing import NamedTuple
import itertools

from BaseClasses import Location

from .constants import BASE_TJE_ID, RANK_NAMES
from .generators import item_totals

class TJELocationType(Enum):
    FLOOR_ITEM = 0
    SHIP_PIECE = 1
    RANK = 2

class TJELocation(Location):
    game: str = "ToeJam & Earl"

class TJELocationData(NamedTuple):
    name: str
    type: TJELocationType
    level: int | None
    item_index: int | None

FLOOR_ITEM_LOC_TEMPLATE = "Level {} - Item {}"
SHIP_PIECE_LOC_TEMPLATE = "Level {} - Ship Piece"
RANK_LOC_TEMPLATE = "Promoted to {}"

FLOOR_ITEM_LOCATIONS : list[list[TJELocationData]] = [[]]

max_items_per_level = item_totals(singleplayer=True, min_items=28, max_items=28)
for level in range(1, 26):
    FLOOR_ITEM_LOCATIONS.append([
        TJELocationData(FLOOR_ITEM_LOC_TEMPLATE.format(level, i+1), TJELocationType.FLOOR_ITEM, level, i+1)
        for i in range(max_items_per_level[level])
    ])

SHIP_PIECE_LOCATIONS: list[TJELocationData] = [
    TJELocationData(SHIP_PIECE_LOC_TEMPLATE.format(level), TJELocationType.SHIP_PIECE, level, None)
    for level in range(2, 26)
]

RANK_LOCATIONS: list[TJELocationData] = [
    TJELocationData(RANK_LOC_TEMPLATE.format(rank), TJELocationType.RANK, -1, None)
    for rank in RANK_NAMES[1:]
]

MASTER_LOCATION_LIST = list(itertools.chain(*FLOOR_ITEM_LOCATIONS)) + SHIP_PIECE_LOCATIONS + RANK_LOCATIONS

LOCATION_NAME_TO_ID : dict[str, int] = {
    loc.name: id
    for id, loc in enumerate(MASTER_LOCATION_LIST, BASE_TJE_ID)
}

LOCATION_ID_TO_NAME : dict[int, str] = {
    id: name
    for name, id in LOCATION_NAME_TO_ID.items()
}

LOCATION_GROUPS = dict(zip(
    [f"Level {level}" for level in range(1, 26)],
    [
        ([SHIP_PIECE_LOC_TEMPLATE.format(lvl)] if lvl > 1 else []) +
        [FLOOR_ITEM_LOC_TEMPLATE.format(lvl, i+1) for i in range(max_items_per_level[lvl])]
        for lvl in range(1,26)
    ]
    )) \
       | {"Ranks" : [RANK_LOC_TEMPLATE.format(rank) for rank in RANK_NAMES[1:]]} \
       | {"Ship Items" : [SHIP_PIECE_LOC_TEMPLATE.format(level) for level in range(2, 26)]}

def floor_item_to_location_id(level: int, item_idx: int) -> int | None:
    if level < 1 or level > 25 or item_idx < 1 or item_idx > 28:
        return None
    if level == 1:
        return BASE_TJE_ID + item_idx
    return BASE_TJE_ID + 12 + (level-2)*28 + item_idx
