from enum import Enum, auto
from typing import NamedTuple
import itertools

from BaseClasses import Location

from .constants import BASE_TJE_ID, RANK_NAMES, MAILBOX_ITEM_REFS
from .generators import item_totals

class TJELocationType(Enum):
    FLOOR_ITEM = auto()
    SHIP_PIECE = auto()
    RANK = auto()
    REACH = auto()
    MAILBOX = auto()

class TJELocation(Location):
    game: str = "ToeJam & Earl"

class TJELocationData(NamedTuple):
    name: str
    type: TJELocationType
    level: int | None
    item_index: int | None

FLOOR_ITEM_LOC_TEMPLATE = "Level {} - Item {}"
BIG_ITEM_LOC_TEMPLATE = "Level {} - Big Item"
RANK_LOC_TEMPLATE = "Promoted to {}"
REACH_LOC_TEMPLATE = "Reach Level {}"
MAILBOX_LOC_TEMPLATE = "Level {} Mailbox - {} Item"

FLOOR_ITEM_LOCATIONS : list[list[TJELocationData]] = [[]]

max_items_per_level = item_totals(singleplayer=True, min_items=28, max_items=28)
for level in range(1, 26):
    FLOOR_ITEM_LOCATIONS.append([
        TJELocationData(FLOOR_ITEM_LOC_TEMPLATE.format(level, i+1), TJELocationType.FLOOR_ITEM, level, i+1)
        for i in range(max_items_per_level[level])
    ])

SHIP_PIECE_LOCATIONS: list[TJELocationData] = [
    TJELocationData(BIG_ITEM_LOC_TEMPLATE.format(level), TJELocationType.SHIP_PIECE, level, None)
    for level in range(2, 26)
]

RANK_LOCATIONS: list[TJELocationData] = [
    TJELocationData(RANK_LOC_TEMPLATE.format(rank), TJELocationType.RANK, -1, None)
    for rank in RANK_NAMES[1:]
]

REACH_LOCATIONS: list[TJELocationData] = [
    TJELocationData(REACH_LOC_TEMPLATE.format(level), TJELocationType.REACH, -1, None)
    for level in range(2, 26)
]

MAILBOX_LOCATIONS: list[TJELocationData] = [
    TJELocationData(MAILBOX_LOC_TEMPLATE.format(level, pos), TJELocationType.MAILBOX, -1, None)
    for level in range(2, 26) for pos in MAILBOX_ITEM_REFS
]

MASTER_LOCATION_LIST = list(itertools.chain(*FLOOR_ITEM_LOCATIONS)) + SHIP_PIECE_LOCATIONS + RANK_LOCATIONS \
                                                                    + REACH_LOCATIONS + MAILBOX_LOCATIONS

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
        [FLOOR_ITEM_LOC_TEMPLATE.format(lvl, i+1) for i in range(max_items_per_level[lvl])] + 
        ([BIG_ITEM_LOC_TEMPLATE.format(lvl)] if lvl > 1 else []) +
        ([MAILBOX_LOC_TEMPLATE.format(lvl, pos) for pos in MAILBOX_ITEM_REFS])
        for lvl in range(1,26)
    ]
    )) \
       | {"Ranks" : [RANK_LOC_TEMPLATE.format(rank) for rank in RANK_NAMES[1:]]} \
       | {"Big Items" : [BIG_ITEM_LOC_TEMPLATE.format(level) for level in range(2, 26)]} \
       | {"Level Reaches" : [REACH_LOC_TEMPLATE.format(level) for level in range(2, 26)]} \
       | {"Mailboxes" : [MAILBOX_LOC_TEMPLATE.format(level, pos)
                         for level in range(2, 26) for pos in MAILBOX_ITEM_REFS]}
       
REMOTE_SPAWN_ONLY_LOCS = (LOCATION_GROUPS["Ranks"] + LOCATION_GROUPS["Big Items"] +
                          LOCATION_GROUPS["Level Reaches"] + LOCATION_GROUPS["Mailboxes"])
