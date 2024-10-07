from dataclasses import dataclass
from enum import IntEnum

from Options import PerGameCommonOptions, Toggle, Choice, OptionGroup, Range, NamedRange, DefaultOnToggle

class CharacterOption(IntEnum):
    TOEJAM = 0
    EARL = 1
    BOTH = 2

class MapRandomizationOption(IntEnum):
    BASE = 0
    BASE_SHUFFLE = 1
    BASE_RANDOM = 2
    FULL_RANDOM = 3
    MAPSANITY = 4

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

class AutoOpenOption(IntEnum):
    NONE = 0
    NO_RANDOMIZER = 1
    ALL = 2

class SoundRandoOption(IntEnum):
    NONE = 0
    MOST = 1
    ALL = 2

class ExpandedInventory(DefaultOnToggle):
    """
    Expands the inventory to 64 slots (4× the base). Recommended.
    """

    display_name = "Expanded Inventory"

class SoundRando(Choice):
    """
    Randomizes all PCM and PSG sound effects in the game. For sanity's sake, the menu blip will always be left alone.

    None: No randomization.
    Most: Randomizes all PCM and PSG sound effects except the four that affect the music.
    All: Also randomizes the four sounds used in the music (clap, kick, record scratch and snare).
    """

    display_name = "Sound Randomization Level"

    option_none = SoundRandoOption.NONE.value
    option_most = SoundRandoOption.MOST.value
    option_all = SoundRandoOption.ALL.value

    default = option_none

class FastLoads(Toggle):
    """
    Massively speeds up loading by forcing the game to stop the elevator as soon as the next level is ready.
    """

    display_name = "Fast Loads"

class AutoOpenTrapPresents(Choice):
    """
    Whether trap presents should automatically open when received from other players.
    Presents collected locally will not auto-open.
    Recommended to reduce the burden of inventory management.
    Auto-opening randomizers may cause the game to softlock in certain circumstances so be prepared to rewind.
    """

    display_name = "Automatically Open Trap Presents"

    option_none = AutoOpenOption.NONE.value
    option_no_randomizer = AutoOpenOption.NO_RANDOMIZER.value
    option_all = AutoOpenOption.ALL.value

    default = option_no_randomizer

class Character(Choice):
    """
    Which character you want to play as.
    """
    display_name = "Character"

    option_toejam = CharacterOption.TOEJAM.value
    option_earl = CharacterOption.EARL.value
    option_both = CharacterOption.BOTH.value

    default = option_toejam

class MinItemCount(Range):
    """
    The minimum number of items per level. Defaults to the base value of 12.

    Levels 1 and 2 will have exactly this many items.
    For each subsequent level one more item will spawn, up to the configured maximum.

    Should be less than or equal to the maximum item count. If not, the maximum value will take precedence.
    For example, a minimum of 12 and a maximum of 8 will result in every level from 2 onwards having 8 items.
    """

    display_name = "Minimum Items Per Level"

    range_start = 4
    range_end = 28

    default = 12

class MaxItemCount(Range):
    """
    The maximum number of items per level. Defaults to the base value of 28.
    Level 1 will always have a maximum of 12 items, regardless of what this is set to.
    
    Should be greater than or equal to the minimum item count. If not, will take precedence over the minimum item count.
    For example, a minimum of 12 and a maximum of 8 will result in every level from 2 onwards having 8 items.
    """

    display_name = "Maximum Items Per Level"

    range_start = 4
    range_end = 28

    default = 28

class MapRandomization(Choice):
    """
    Adds extra randomization to the base game's level generation.

    The base game uses eight different level types, each of which specifies different ranges for 8 different parameters,
    which are randomized just prior to level generation. These include the size of main islands, the amount of water,
    and how many islets appear in lakes.

    In the base game, the order of these level types is fixed — for example, level 4 is always a "big lake" level.

    NOTE: Choosing any of these options besides "base" will slightly alter one of the level generation parameters to
          ensure that the levels always generate and thereby avoid softlocks during the elevator loading screens.

    - Base: Unchanged from the base game.
    - Base shuffle: Randomizes the order of the base level types. The number of each type remains the same.
    - Base random: Randomizes both the order and number of the base level types.
    - Full random: Randomizes all the parameters for every level. This may produce strange-looking levels.
    - Mapsanity: As full_random, but in addition every level will be completely regenerated every time it's loaded.
    """

    display_name = "Map Randomization"

    option_base = MapRandomizationOption.BASE.value
    option_base_shuffle = MapRandomizationOption.BASE_SHUFFLE.value
    option_base_random = MapRandomizationOption.BASE_RANDOM.value
    option_full_random = MapRandomizationOption.FULL_RANDOM.value
    option_mapsanity = MapRandomizationOption.MAPSANITY.value

    default = option_base

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

    option_none = ElevatorKeyTypeOption.NONE.value
    option_progressive = ElevatorKeyTypeOption.PROGRESSIVE.value
    option_static = ElevatorKeyTypeOption.STATIC.value

    default = option_progressive

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

    option_disable = GameOverOption.DISABLE.value
    option_drop_down = GameOverOption.DROP_DOWN.value
    option_reset = GameOverOption.RESET.value

    default = option_drop_down

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

class TrapBurp(Toggle):
    """
    Add traps that make you constantly burp.
    """

    display_name = "Enable Burp Traps"

class TrapSleep(Toggle):
    """
    Add traps that instantly send you to sleep into the item pool.
    """

    display_name = "Enable Sleep Traps"

class TrapRocketSkates(Toggle):
    """
    Add traps that instantly give you Rocket Skates into the item pool.
    """

    display_name = "Enable Rocket Skates Traps"

class TrapEarthling(Toggle):
    """
    Add traps that spawn Earthlings into the item pool.
    """

    display_name = "Enable Earthling Traps"

class TrapRandomizer(Toggle):
    """
    Add traps that force-randomize all your presents into the item pool.
    """

    display_name = "Enable Randomizer Traps"

class StartingPresents(Choice):
    """
    Toejam's starting presents.

    - None: No presents at all!
    - Hitops: Four Super Hitops, same as base game
    - Mobility Mix: One each of Super Hitops, Spring Shoes, Icarus Wings and Rocket Skates
    - Good: Four random non-trap presents
    - Any: Four completely random presents, possibly including traps
    """

    display_name = "Starting Presents"

    option_none = StartingPresentOption.NONE.value
    option_hitops = StartingPresentOption.HITOPS.value
    option_mobility_mix = StartingPresentOption.MIX.value
    option_any_good = StartingPresentOption.ANY_GOOD.value
    option_any = StartingPresentOption.ANY.value

    default = option_hitops

class SleepWhenIdle(DefaultOnToggle):
    """
    Determines whether Toejam will fall asleep if left idle.
    Defaults to on, as in the base game.
    School books and sleep traps will still work even if this is set to off.
    """

    display_name = "Fall Asleep When Idle"

class WalkSpeedBoost(NamedRange):
    """
    Increases/decreases walking speed, as a percentage of the base speed.
    Roads boost this by a further 25%, as in the base game.
    """

    range_start = 50
    range_end = 150

    special_range_names = {
        "highest": 150,
        "higher": 125,
        "base": 100,
        "lower": 75,
        "lowest": 50
    }

    default = 100

    display_name = "Walking Speed Boost"

class ExtendedPresentTimers(NamedRange):
    """
    Increases/decreases duration of action presents (Super Hitops etc), as a percentage of the base time.
    """

    range_start = 50
    range_end = 150

    special_range_names = {
        "highest": 150,
        "higher": 125,
        "base": 100,
        "lower": 75,
        "lowest": 50
    }

    default = 100

    display_name = "Action Present Timers"

class FreeEarthlingServices(Toggle):
    """
    Makes all Earthling services free. (Wiseman/Opera Singer/Wizard)
    """

    display_name = "Free Earthling Services"

tje_option_groups = [
    OptionGroup("Basic Items/Locations", [
        StartingPresents,
        ExcludeItemsFromProgression,
        MapRandomization,
        MinItemCount,
        MaxItemCount
    ]),
    OptionGroup("Trap Options", [
        AutoOpenTrapPresents,
        TrapFood,
        TrapPresents,
        TrapCupid,
        TrapSleep,
        TrapRocketSkates,
        TrapEarthling,
        TrapRandomizer
    ]),
    OptionGroup("Extra Items/Locations", [
        UpwarpPresent,
        MapReveals,
        ElevatorKeyType,
        ElevatorKeyGap,
        MaxRankCheck
    ]),
    OptionGroup("Difficulty/QoL", [
        Character,
        GameOvers,
        SleepWhenIdle,
        WalkSpeedBoost,
        ExtendedPresentTimers,
        FreeEarthlingServices,
        FastLoads,
        ExpandedInventory
    ]),
    OptionGroup("Misc", [
        SoundRando
    ])
]

@dataclass
class TJEOptions(PerGameCommonOptions):
    starting_presents: StartingPresents
    restrict_prog_items: ExcludeItemsFromProgression
    map_rando: MapRandomization
    min_items: MinItemCount
    max_items: MaxItemCount
    auto_trap_presents: AutoOpenTrapPresents
    trap_food: TrapFood
    trap_presents: TrapPresents
    trap_cupid: TrapCupid
    trap_burp: TrapBurp
    trap_sleep: TrapSleep
    trap_skates: TrapRocketSkates
    trap_earthling: TrapEarthling
    trap_randomizer: TrapRandomizer
    map_reveals: MapReveals
    key_type: ElevatorKeyType
    key_gap: ElevatorKeyGap
    max_rank_check: MaxRankCheck
    upwarp_present: UpwarpPresent
    character: Character
    game_overs: GameOvers
    sleep_when_idle: SleepWhenIdle
    walk_speed: WalkSpeedBoost
    present_timers: ExtendedPresentTimers
    free_earthling_services: FreeEarthlingServices
    fast_loads: FastLoads
    expanded_inventory: ExpandedInventory
    sound_rando: SoundRando