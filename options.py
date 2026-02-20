from dataclasses import dataclass
from enum import IntEnum

from Options import PerGameCommonOptions, Toggle, Choice, OptionGroup, Range, NamedRange, DefaultOnToggle, DeathLink, \
                    OptionCounter

from .constants import TRAP_NAMES

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

class AutoOpenOption(IntEnum):
    NONE = 0
    NO_RANDOMIZER = 1
    ALL = 2

class SoundRandoOption(IntEnum):
    NONE = 0
    MOST = 1
    ALL = 2

class RankRescalingOption(IntEnum):
    NONE = 0
    MAX_CHECK = 1
    FUNK_LORD = 2

class GameVersionOption(IntEnum):
    REV00 = 0
    REV02 = 2

class EarthlingRandomizationOption(IntEnum):
    BASE = 0
    BASE_SHUFFLE = 1
    NICE_RANDOM = 2
    EARTHLINGSANITY = 3

class LocalShipPiecesOption(IntEnum):
    OFF = 0
    NONE = 1
    FULL = 2
    VANILLA = 3

class LastLevel(Range):
    """
    The last level of the game. Set lower for shorter runs.
    Defaults to 25 (the maximum), as in the base game.
    Cannot be less than 11 as the game mandates ten levels with ship items.
    Anything whose behaviour is relative to the last or second-last level of the game (e.g. restrictions on the use
    of Up-Warps) will change in lockstep with this option.
    """

    display_name = "Last Level"

    range_start = 11
    range_end = 25

    default = 25

class Islandless(DefaultOnToggle):
    """
    Prevents the game from creating tiny islands out in space, guaranteeing that every item will be accessible.
    Does not affect islands in water.
    Disabling this is *not recommended* as it will more often than not result in frustrating, incompletable worlds
    where crucial progression items spawn in the middle of nowhere.    
    """

    display_name = "Islandless"

class ExpandedInventory(DefaultOnToggle):
    """
    Expands the inventory to 64 slots (4× the base).
    The game will also remember how far you scrolled the inventory down when you reopen it.
    """

    display_name = "Expanded Inventory"

class SoundRando(Choice):
    """
    Randomizes all PCM and PSG sound effects in the game. For sanity's sake, two sounds will never be randomized:
    the menu blip and the Rocket Skates "blast-off" sound.

    None: No randomization.
    Most: Randomizes all PCM and PSG sound effects except the four that affect the music.
    All: Also randomizes the four sounds used in the music (clap, kick, record scratch and snare).
    """

    display_name = "Sound Randomization"

    option_none = SoundRandoOption.NONE.value
    option_most = SoundRandoOption.MOST.value
    option_all = SoundRandoOption.ALL.value

    default = option_none

class FastLoads(Toggle):
    """
    Massively speeds up loading by forcing the game to stop the elevator as soon as the next level is ready.
    """

    display_name = "Fast Loads"

class AutoOpenBadPresents(Choice):
    """
    Whether bad presents should automatically open when received from other players.
    Presents collected locally will not auto-open.
    Recommended to reduce the burden of inventory management.
    Auto-opening randomizers may cause the game to softlock in certain circumstances so be prepared to rewind.
    """

    display_name = "Automatically Open Bad Presents"

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
    Adds five Progressive Map Reveal items, which reveal 1/5 of the remaining maps at a time.
    If last_level is 25 (the default), this means 1–5, 6–10, etc. Otherwise these ranges will vary somewhat.
    In-game dialogue will always explain exactly which maps have been uncovered.
    Revealed squares will be "glass" as if revealed by a telephone, so still give points when fully uncovered.
    
    Note that because the game isn't able to(? or isn't programmed to) render an entire map full of glass tiles,
    the outer border of each map will be left as is.
    """

    display_name = "Map Reveal Items"

class LocalMapReveals(Toggle):
    """
    Forces map reveals to be local items and balances placement so that they never appear too late to be useful
    (assuming you've collected all of them up to that point). Highly recommended for solo games.
    For example, if a particular map reveal would uncover levels 1–5, it is guaranteed to appear on one of those levels.
    Map reveals placed on level 1 will be one of the four immediately-accessible items on the starting islands.
    """

    display_name = "Local Map Reveals"

class ElevatorKeys(DefaultOnToggle):
    """
    Adds progressive elevator keys, new progression items that lock certain elevators until found.
    """

    display_name = "Elevator Keys"

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

class MaxRankCheck(NamedRange):
    """
    Adds one additional check for each rank up to the value chosen.

    If this setting is enabled, two extra Mole safeguards will be automatically patched in:
    - Moles will not steal Promotion presents.
    - You will receive points for any presents stolen by Moles.

    If you have changed last_level, min_items or max_items, rank point thresholds will be rescaled
    to be attainable in the smaller game world. See also: the rank_rescaling option.

    Set to 0 to disable.
    """

    display_name = "Maximum Rank Check"

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

class RankRescalingMode(Choice):
    """
    Determines how rank point thresholds rescale in smaller worlds.
    Only functions if max_rank_check > 0 *and* at least one of last_level, min_items and max_items has been changed.

    - None: No rescaling. Rank thresholds are vanilla.
            ⚠ Likely to result in fill errors if last_level is low and max_rank_check is high.
    - Max check: Rescales point thresholds so that you reach your chosen max_rank_check towards the end of the game.
    - Funk Lord (default): Rescales point thresholds so that you reach Funk Lord towards the end of the game.

    """

    display_name = "Rank Rescaling Mode"

    option_none = RankRescalingOption.NONE.value
    option_max_check = RankRescalingOption.MAX_CHECK.value
    option_funk_lord = RankRescalingOption.FUNK_LORD.value

    default = option_funk_lord

class ReachLevelChecks(Toggle):
    """
    Adds extra checks that trigger when you reach a new highest level.
    """

    display_name = "Reach Level Checks"

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
    - Drop Down: Forces TJ/E to fall down one level, after which they respawn normally.
    - Reset: Return to the title screen, as in the base game. Some progress will be lost.
    """

    display_name = "Game Over Handling"

    option_disable = GameOverOption.DISABLE.value
    option_drop_down = GameOverOption.DROP_DOWN.value
    option_reset = GameOverOption.RESET.value

    default = option_drop_down

class BadPresents(DefaultOnToggle):
    """
    Includes bad presents (Earthling, Total Bummer etc) in the item pool.
    """

    display_name = "Include Bad Presents"

class BadFood(DefaultOnToggle):
    """
    Includes bad food (Slimy Fungus, Fish Bones etc) in the item pool.
    """

    display_name = "Include Bad Food"

class TrapWeights(OptionCounter):
    """
    Specifies the relative frequency of each type of trap in the item pool.
    Set a trap weight to zero to disable it.

    Available traps:

    - Cupid: scrambles controls
    - Burp: makes you burp
    - Sleep: makes you fall asleep
    - Skates: gives you rocket skates
    - Earthling: spawns an earthling
    - Randomizer: randomizes all of your presents

    """
    display_name = "Trap Weights"
    valid_keys = TRAP_NAMES
    min = 0
    default = dict(zip(TRAP_NAMES, range(5,-1,-1)))

class TrapPercentage(Range):
    """
    What percentage of the item pool will be traps.
    """

    display_name = "Trap Percentage"

    range_start = 0
    range_end = 10

    default = 3

class StartingPresents(Choice):
    """
    TJ/E's starting presents.

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
    Whether TJ/E will fall asleep if left idle.
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

class GameVersion(Choice):
    """
    Which revision of the game your ROM is. Defaults to the more easily obtainable REV02.
    
    REV02 is the version that was available e.g. via Mega Drive/Genesis Classics on Steam.
    You may have a REV00 ROM if you dumped your original cartridge.
    
    If you aren't sure which version you have, open it in any editor (text or binary)
    and check the header. A date of 1991.JUL is REV00; a date of 1991.OCT is REV02.
    """

    display_name = "Game Version"

    option_rev00 = GameVersionOption.REV00.value
    option_rev02 = GameVersionOption.REV02.value

    default = option_rev02


class EarthlingRando(Choice):
    """
    Randomizes Earthling placement.

    - Base: as in the vanilla game
    - Base shuffle: shuffles the vanilla 25 sets of Earthlings
    - Nice random: controlled random Earthlings (see below)
    - Full random: completely random Earthlings, no restrictions
    
    * "Nice random" means the Earthling numbers and distribution across levels are based on the vanilla game, but
      much more variation is possible. Some restrictions still apply, e.g. there is a maximum of 1 of each friendly
      Earthling on each level.
    """

    display_name = "Earthling Randomization"

    option_base = EarthlingRandomizationOption.BASE.value
    option_base_shuffle = EarthlingRandomizationOption.BASE_SHUFFLE.value
    option_nice_random = EarthlingRandomizationOption.NICE_RANDOM.value
    option_earthlingsanity = EarthlingRandomizationOption.EARTHLINGSANITY.value

    default = option_base

class EarthlingRandoNiceness(Range):
    """
    Only has an effect if earthling_rando is set to nice_random.

    Tightens the distribution of Earthlings, making "normal" Earthling placements more likely.
    Rare spawns will never be impossible, but will become vanishingly unlikely at higher values.
    """

    display_name = "Earthling Randomization Niceness"

    range_start = 1
    range_end = 10

    default = 1

class LocalShipPieces(Choice):
    """
    Forces all Ship Pieces to be local or remote, in various modes.

    - Off (default): Ship Pieces can be in any world.
    - None: all Ship Pieces will be in other worlds, with the exception of the piece on Level 25.
    - Full: all Ship Pieces will be local, but may spawn on the ground in addition to the big flashy pedestals.
    - Vanilla: all Ship Pieces will be local with vanilla placement (i.e. all on the big flashy pedestals).

    """

    display_name = "Local Ship Pieces"

    option_off = LocalShipPiecesOption.OFF.value
    option_none = LocalShipPiecesOption.NONE.value
    option_full = LocalShipPiecesOption.FULL.value
    option_vanilla = LocalShipPiecesOption.VANILLA.value

    default = option_off


tje_option_groups = [
    OptionGroup("Basic Items/Locations", [
        StartingPresents,
        Islandless,
        MapRandomization,
        MinItemCount,
        MaxItemCount,
        LastLevel,
        LocalShipPieces,
    ]),
    OptionGroup("Bad/Trap Options", [
        AutoOpenBadPresents,
        BadFood,
        BadPresents,
        TrapWeights,
        TrapPercentage
    ]),
    OptionGroup("Extra Items/Locations", [
        UpwarpPresent,
        MapReveals,
        LocalMapReveals,
        ElevatorKeys,
        ElevatorKeyGap,
        MaxRankCheck,
        RankRescalingMode,
        ReachLevelChecks,
    ]),
    OptionGroup("Difficulty/QoL", [
        Character,
        GameOvers,
        EarthlingRando,
        EarthlingRandoNiceness,
        SleepWhenIdle,
        WalkSpeedBoost,
        ExtendedPresentTimers,
        FreeEarthlingServices,
        FastLoads,
        ExpandedInventory
    ]),
    OptionGroup("Misc", [
        SoundRando,
        GameVersion
    ])
]

@dataclass
class TJEOptions(PerGameCommonOptions):
    death_link: DeathLink
    starting_presents: StartingPresents
    islandless: Islandless
    map_rando: MapRandomization
    min_items: MinItemCount
    max_items: MaxItemCount
    last_level: LastLevel
    local_ship_pieces: LocalShipPieces
    auto_bad_presents: AutoOpenBadPresents
    bad_food: BadFood
    bad_presents: BadPresents
    trap_weights: TrapWeights
    trap_percentage: TrapPercentage
    map_reveals: MapReveals
    local_map_reveals: LocalMapReveals
    elevator_keys: ElevatorKeys
    key_gap: ElevatorKeyGap
    max_rank_check: MaxRankCheck
    rank_rescaling: RankRescalingMode
    reach_level_checks: ReachLevelChecks
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
    game_version: GameVersion
    earthling_rando: EarthlingRando
    earthling_rando_niceness: EarthlingRandoNiceness