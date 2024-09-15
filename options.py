from dataclasses import dataclass
from enum import IntEnum

from Options import PerGameCommonOptions, Toggle, Choice, OptionGroup, NamedRange, DefaultOnToggle

class ShipPieceOption(IntEnum):
    LEVEL_25 = 0
    ANYWHERE = 1

class GameOverOption(IntEnum):
    DISABLE = 0
    DROP_DOWN = 1
    RESET = 2

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

class MapReveals(Toggle):
    """
    Adds five Progressive Map Reveal items, which reveal maps five levels at a time (1–5, 6–10, etc).
    Revealed squares are "glass" as if revealed by a telephone, so still give points when fully uncovered.
    
    Note that because the game isn't able to(? or isn't programmed to) render an entire map full of glass tiles,
    the outer border of each map will be left as is.
    """

    display_name = "Map Reveal Items"

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

class ElevatorKeyGap(NamedRange):
    """
    Determines the spacing between levels with locked elevators.
    For example, setting this to 4 will lock the elevators on levels 4, 8, 12, 16, 20 and 24.

    Level 1 will never require an elevator key, even if this is set to 1.
    Any number greater than 12 will result in a single key only for that level's elevator.
    """

    display_name = "Elevator Key Spacing"

    range_start = 1
    range_end = 24

    special_range_names = {
        "all": 1,
        "regular": 4,
        "light": 8,
        "lightest" : 13
    }

    default = 4

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
                Selecting this will lock the Level 24 elevator until the other 9 have been found.
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
    The number means the highest rank that *can* have a progression item. Later ranks are guaranteed not to.
    Set to 0 to disable.
    """

    display_name = "Highest Big Rank Check"

    range_start = 0
    range_end = 8

    special_range_names = {
        "off": 0,
        "dufus": 1,
        "poindexter": 2,
        "peanut": 3,
        "dude": 4,
        "bro": 5,
        "homey": 6,
        "rapmaster": 7,
        "funk_lord": 8
    }

    default = 5

class UpwarpPresent(Toggle):
    """
    Mutator that changes the Un-Fall present into an Up-Warp present that always sends you up one level,
    even if you haven't yet made it that far by elevator. Poof!
    NB: Not currently accounted for in logic.
    """

    display_name = "Upwarp Present"

class GameOvers(Choice):
    """
    What to do in the event of a game over.

    - Disable: Forces infinite lives so game overs never happen. Also removes Extra Life presents.
    - Drop Down: Forces the player to fall down one level, after which they respawn normally.
    - Reset: Return to the title screen, as in the base game. Some progress will be lost.
    """

    display_name = "Game Over Handling"

    option_disable = GameOverOption.DISABLE
    option_drop_down = GameOverOption.DROP_DOWN
    option_reset = GameOverOption.RESET

    default = GameOverOption.DROP_DOWN

class TrapPresents(DefaultOnToggle):
    """
    Include trap presents (Earthling, Total Bummer etc) in the item pool.
    """

    display_name = "Include Trap Presents"

class TrapFood(DefaultOnToggle):
    """
    Include trap food (Slimy Fungus, Fish Bones etc) in the item pool.
    """

    display_name = "Include Trap Food"

class TrapCupid(Toggle):
    """
    Add control-scrambling Cupid traps into the item pool.
    """

    display_name = "Enable Cupid Traps"

class TrapSleep(Toggle):
    """
    Add sleep traps into the item pool.
    """

    display_name = "Enable Sleep Traps"


class StartingPresents(Choice):
    """
    Toejam's starting presents.

    - None: no presents at all!
    - Hitops: four Super Hitops, same as base game
    - Mobility Mix: one each of Super Hitops, Spring Shoes, Icarus Wings and Rocket Skates
    - Good: four random non-trap presents
    - Any: four completely random presents, may include traps
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
        FinalShipPieceLocation,
        ExcludeItemsFromProgression
    ]),
    OptionGroup("Trap Options", [
        TrapFood,
        TrapPresents,
        TrapCupid,
        TrapSleep
    ]),
    OptionGroup("Extra Items/Locations", [
        MapReveals,
        ElevatorKeyType,
        ElevatorKeyGap,
        MaxRankCheck
    ]),
    OptionGroup("Mutators", [
        StartingPresents,
        UpwarpPresent,
        GameOvers
    ]),
]


@dataclass
class TJEOptions(PerGameCommonOptions):
    final_ship_piece: FinalShipPieceLocation
    restrict_prog_items: ExcludeItemsFromProgression
    trap_food: TrapFood
    trap_presents: TrapPresents
    trap_cupid: TrapCupid
    trap_sleep: TrapSleep
    map_reveals: MapReveals
    key_type: ElevatorKeyType
    key_gap: ElevatorKeyGap
    max_rank_check: MaxRankCheck
    starting_presents: StartingPresents
    upwarp_present: UpwarpPresent
    game_overs: GameOvers