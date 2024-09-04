from dataclasses import dataclass
from enum import IntEnum

from Options import PerGameCommonOptions, Toggle, Choice, OptionGroup, NamedRange

class ShipPieceOption(IntEnum):
    LEVEL_25 = 0
    ANYWHERE = 1

class GameOverOption(IntEnum):
    DISABLE = 0
    DROP_DOWN = 1
    RESET = 2

class TrapOption(IntEnum):
    NONE = 0
    ITEMS_ONLY = 1
    PRESENTS_ONLY = 2
    ALL = 3

class StartingPresentOption(IntEnum):
    NONE = 0
    HITOPS = 1
    MIX = 2
    ANY_GOOD = 3
    ANY = 4

class ElevatorKeyTypeOption(IntEnum):
    NONE = 0
    PROGRESSIVE = 1
    STATIC = 2

class ElevatorKeyType(Choice):
    """
    Adds elevator keys, new progression items that lock certain elevators until found. These come in two flavours:

    - None: No elevator keys.
    - Progressive: Each elevator key found unlocks an elevator one floor higher.
    - Static: Each elevator key is for a specific elevator.
    """

    display_name = "Elevator Key Type"

    option_none = ElevatorKeyTypeOption.NONE
    option_progressive = ElevatorKeyTypeOption.PROGRESSIVE
    option_static = ElevatorKeyTypeOption.STATIC

    default = ElevatorKeyTypeOption.PROGRESSIVE

class ProgElevatorKeyCount(NamedRange):
    """
    Progressive elevator keys only: determines how many keys will appear in the game.
    A maximum of 23 levels (2–24) can have locked elevators.
    This can be set to more than 23 (up to 46) for smoother progression.
    """

    display_name = "Progressive Elevator Key Count"

    range_start = 1
    range_end = 46

    special_range_names = {
        "single": 1,
        "full": 23,
        "extra": 30
    }

    default = 23

class StaticElevatorKeyGap(NamedRange):
    """
    Static elevator keys only: determines the spacing between levels with locked elevators.
    For example, setting this to 4 will add keys for the elevators on levels 4, 8, 12, 16, 20 and 24.

    Level 1 will never have an elevator key, even if this is set to 1.
    Any number greater than 12 will result in a single key only for that level's elevator.
    """

    display_name = "Static Elevator Key Spacing"

    range_start = 1
    range_end = 24

    special_range_names = {
        "extreme": 1,
        "regular": 5,
        "light": 8,
        "lightest" : 13
    }

    default = 5

class ExcludeItemsFromProgression(Toggle):
    """
    Whether regular items on the floor can be progression items.
    If enabled, only ship pieces and other priority checks (e.g. ranks) can have them.
    Very likely to make world generation impossible if combined with elevator keys etc.
    """

    display_name = "Restrict Progression Item Locations"

class FinalShipPieceLocation(Choice):
    """
    Determines the location of the final ship piece.

    - Level 25: The final ship piece will always appear on Level 25 in its usual, non-randomized location.
    - Anywhere: The final ship piece can appear anywhere, including in other worlds.
                If this option is chosen, the ending must be manually triggered from the ship piece screen.
    """

    display_name = "Location of Final Ship Piece"

    option_level_25 = ShipPieceOption.LEVEL_25
    option_anywhere = ShipPieceOption.ANYWHERE

    default = ShipPieceOption.LEVEL_25

class MaxRankCheck(NamedRange):
    """
    Enabling this (value > 0) adds eight additional checks, one for each rank.
    The number means the highest rank that can have a progression item. Later ranks are guaranteed not to.
    Set to 0 to disable.
    """

    display_name = "Highest Big Rank Check"

    range_start: 0
    range_end: 8

    special_range_names = {
        "off": 0,
        "dufus": 1,
        "poindexter": 2,
        "peanut": 3,
        "dude": 4,
        "bro": 5,
        "homey": 6,
        "rapmster": 7,
        "funk_lord": 8
    }

    default = 5

class UpwarpPresent(Toggle):
    """
    Mutator that changes the Un-fall present into an Up-warp present that always sends you up one level,
    even if you haven't yet made it that far by elevator. Poof!
    NB: Not currently accounted for in logic.
    """

    display_name = "Upwarp Present"

class GameOvers(Choice):
    """
    What to do in the event of a game over.

    - Disable: Forces infinite lives so game overs never happen. Also removes Extra Life presents.
    - Drop Down: Forces the player to fall down one level, after which they respawn with three lives.
    - Reset: Return to the title screen, as in the base game.
    """

    display_name = "Game Over Handling"

    option_disable = GameOverOption.DISABLE
    option_drop_down = GameOverOption.DROP_DOWN
    option_reset = GameOverOption.RESET

    default = GameOverOption.DROP_DOWN

class IncludeTraps(Choice):
    """
    Includes different categories of trap from the item pool.

    - None: No traps.
    - Items Only: Only bad food is included.
    - Presents Only: Only presents with negative effects are included.
    - All: All bad items and presents.
    """

    display_name = "Include Traps in Item Pool"

    option_none = TrapOption.NONE
    option_items_only = TrapOption.ITEMS_ONLY
    option_presents_only = TrapOption.PRESENTS_ONLY
    option_all = TrapOption.ALL

    default = option_all

class StartingPresents(Choice):
    """
    Toejam's starting presents.

    - None: no presents at all!
    - Hi-Tops: four Super Hi-Tops, same as base game
    - Mobility Mix: one each of Super Hi-Tops, Spring Shoes, Icarus Wings and Rocket Skates
    - Random Good: four random non-trap presents
    - Random Any: four completely random presents, may include traps
    """

    display_name = "Starting Presents"

    option_none = StartingPresentOption.NONE
    option_hitops = StartingPresentOption.HITOPS
    option_mobility_mix = StartingPresentOption.MIX
    option_any_good = StartingPresentOption.ANY_GOOD
    option_any = StartingPresentOption.ANY

    default = option_hitops
    
tje_option_groups = [
    OptionGroup("Basic Items/Locations", [
        IncludeTraps,
        FinalShipPieceLocation,
        ExcludeItemsFromProgression,
    ]),
    OptionGroup("Extra Items/Locations", [
        ElevatorKeyType,
        StaticElevatorKeyGap,
        ProgElevatorKeyCount,
        MaxRankCheck
    ]),
    OptionGroup("Mutators", [
        UpwarpPresent,
        GameOvers
    ]),
]


@dataclass
class TJEOptions(PerGameCommonOptions):
    final_ship_piece: FinalShipPieceLocation
    include_traps: IncludeTraps
    game_overs: GameOvers
    starting_presents: StartingPresents
    restrict_prog_items: ExcludeItemsFromProgression
    key_type: ElevatorKeyType
    static_key_gap: StaticElevatorKeyGap
    prog_key_count: ProgElevatorKeyCount
    max_major_rank: MaxRankCheck
    upwarp_present: UpwarpPresent