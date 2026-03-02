import copy
import struct
from itertools import chain
from math import sqrt, ceil
from pathlib import Path

from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from .constants import EMPTY_PRESENT, INITIAL_PRESENT_ADDRS, BASE_LEVEL_TYPES, INV_REF_ADDRS, INV_SIZE_ADDRS, \
                       INV_SIZE_ADDRS_ASL_D0, INV_SIZE_ADDRS_INITIAL, MAP_REVEAL_DIALOGUE_ADDRS, PCM_SFX_ADDRS, \
                       PCM_SFX_ADDRS_MUSIC, PCM_SFX_USAGE_ADDRS, PCM_SFX_USAGE_ADDRS_MUSIC, PSG_SFX, PSG_SFX_USAGE_ADDRS
from .generators import map_reveal_text
from .items import ITEM_ID_TO_CODE
from .options import CharacterOption, SoundRandoOption, StartingPresentOption, GameOverOption, MapRandomizationOption
from .tools.patch_util import read_bin, BinType, set_bin_paths

class TJEProcedurePatch(APProcedurePatch, APTokenMixin):
    game = "ToeJam and Earl"
    patch_file_ending = ".aptje"
    result_file_ending = ".bin"

    procedure = [
        ("apply_bsdiff4", ["base_patch.bsdiff4"]),
        ("apply_tokens", ["token_data.bin"])
    ]

    @classmethod
    def get_source_data(cls) -> bytes:
        filename = get_settings().tje_options.rom_file
        with open(filename, "rb") as f:
            base_rom_bytes = bytes(f.read())

        return base_rom_bytes

#region Individual patching sections

def patch_slot_data(world, patch) -> None:
    patch.write_token(APTokenTypes.WRITE, 0x00097704, struct.pack(">26H", *world.seeds))
    patch.write_token(APTokenTypes.WRITE, 0x00097738, struct.pack(">10B", *world.ship_item_levels))

    key_gap = world.options.key_gap.value if world.options.elevator_keys else 0
    patch.write_token(APTokenTypes.WRITE, 0x001f0000, struct.pack(">B", key_gap))
    patch.write_token(APTokenTypes.WRITE, 0x001f0001, struct.pack(">B", world.options.death_link.value))
    patch.write_token(APTokenTypes.WRITE, 0x001f0005, struct.pack(">B", world.options.auto_bad_presents.value))
    num_key_levels = len(world.key_levels)
    patch.write_token(APTokenTypes.WRITE, 0x001f0010, struct.pack(">B", num_key_levels))
    patch.write_token(APTokenTypes.WRITE, 0x001f0011, struct.pack(f">{num_key_levels}B", *world.key_levels))

def patch_item_list(world, patch) -> None:
    patch.write_token(APTokenTypes.WRITE, 0x001a0000, struct.pack(f">{(world.options.last_level.value+1)*28}B",
                                                                  *world.patchable_item_list))
def patch_main_menu(world, patch) -> None:
    # Menu return options: 0 for 2-player, 1 for TJ only, 2 for Earl only
    match world.options.character:
        case CharacterOption.TOEJAM:
            ret_val = 1
            char_init = 0
            menu_string = read_bin("who_menu_toejam_string", BinType.ASM)
            no_2player = True
        case CharacterOption.EARL:
            ret_val = 2
            char_init = 1
            menu_string = read_bin("who_menu_earl_string", BinType.ASM)
            no_2player = True
        case CharacterOption.BOTH:
            ret_val = 0
            char_init = world.random.randint(0, 1)
            menu_string = None
            no_2player = False

    patch.write_token(APTokenTypes.WRITE, 0x0010b400+3, struct.pack(">B", char_init)) # DYNRP_PLAYER_CHAR

    if menu_string:
        patch.write_token(APTokenTypes.WRITE, 0x000242c5, struct.pack(">B", ret_val))
        patch.write_token(APTokenTypes.WRITE, 0x000242d6, menu_string)

    if no_2player:
        patch.write_token(APTokenTypes.WRITE, 0x00011218, read_bin("main_loop_disable_coop_join"))

def patch_starting_presents(world, patch) -> None:
    if world.options.starting_presents == StartingPresentOption.NONE:
        presents = [EMPTY_PRESENT]*8
    else:
        presents = [struct.pack(">B", ITEM_ID_TO_CODE[p]) for p in world.starting_presents]

    for i in range(8):
        patch.write_token(APTokenTypes.WRITE, INITIAL_PRESENT_ADDRS[i], presents[i])

def patch_expanded_inv(world, patch) -> None:
    if world.options.expanded_inventory:
        for addr in INV_REF_ADDRS:
            patch.write_token(APTokenTypes.WRITE, addr, b"\x00\xff\xf2\x80")
        for addr in INV_SIZE_ADDRS:
            patch.write_token(APTokenTypes.WRITE, addr, b"\x40")
        for i, addr in enumerate(INV_SIZE_ADDRS_INITIAL):
            patch.write_token(APTokenTypes.WRITE, addr, (0x40+i).to_bytes(1))

        if world.options.max_rank_check.value > 0:
            inv_size_addrs_asl_d0 = copy.copy(INV_SIZE_ADDRS_ASL_D0)
            # The ASL at 0x00022042 has been relocated to 0x0010bb04 in our custom code
            inv_size_addrs_asl_d0.remove(0x00022042)
            inv_size_addrs_asl_d0.append(0x0010bb04)
        else:
            inv_size_addrs_asl_d0 = INV_SIZE_ADDRS_ASL_D0

        for addr in inv_size_addrs_asl_d0:
            patch.write_token(APTokenTypes.WRITE, addr, b"\xED\x80")
        patch.write_token(APTokenTypes.WRITE, 0x000099a6, b"\xED\x81") # using D1
        patch.write_token(APTokenTypes.WRITE, 0x00022068, b"\xED\x82") # using D2

        # Make presents scooch up properly on opening and dropping (expand range)
        patch.write_token(APTokenTypes.WRITE, 0x00009ab2+3, b"\x3F")
        patch.write_token(APTokenTypes.WRITE, 0x00009ba0+3, b"\x3F")

        # Patch menu handler to allow extra scrolling (size/2 - 3)
        patch.write_token(APTokenTypes.WRITE, 0x0000979c+3, b"\x1D")

def patch_misc_qol(world, patch) -> None:
    if not world.options.sleep_when_idle:
        patch.write_token(APTokenTypes.WRITE, 0x0001262a, read_bin("no_idle_sleeping"))

    if world.options.fast_loads:
        patch.write_token(APTokenTypes.WRITE, 0x00013710, read_bin("elev_fast_loads"))

    if world.options.free_earthling_services:
        patch.write_token(APTokenTypes.WRITE, 0x00021a70, read_bin("earthling_opera_free1"))
        patch.write_token(APTokenTypes.WRITE, 0x00021a8a, read_bin("earthling_opera_free2"))
        patch.write_token(APTokenTypes.WRITE, 0x00021c04, read_bin("earthling_opera_free_text"))
        patch.write_token(APTokenTypes.WRITE, 0x000215dc, read_bin("earthling_wizard_free1"))
        patch.write_token(APTokenTypes.WRITE, 0x000215f4, read_bin("earthling_wizard_free2"))
        patch.write_token(APTokenTypes.WRITE, 0x000216f2, read_bin("earthling_wizard_free_text"))
        patch.write_token(APTokenTypes.WRITE, 0x00009d96, read_bin("earthling_wiseman_free1"))
        patch.write_token(APTokenTypes.WRITE, 0x00009e10, read_bin("earthling_wiseman_free2"))
        patch.write_token(APTokenTypes.WRITE, 0x000218ea, read_bin("earthling_wiseman_free_text"))

    if world.options.present_timers.value != world.options.present_timers.default:
        base_timer = ceil(1000*(world.options.present_timers.value/100))
        hitops_timer = ceil(0.75*base_timer)
        patch.write_token(APTokenTypes.WRITE, 0x00017334, struct.pack(">H", base_timer))
        patch.write_token(APTokenTypes.WRITE, 0x00017410, struct.pack(">H", hitops_timer))

    if world.options.walk_speed.value != world.options.walk_speed.default:
        orthog_land_speed = ceil(320*(world.options.walk_speed.value/100))
        diag_land_speed = ceil(orthog_land_speed/sqrt(2))
        patch.write_token(APTokenTypes.WRITE, 0x000f028, struct.pack(">H", orthog_land_speed))
        patch.write_token(APTokenTypes.WRITE, 0x000f02c, struct.pack(">H", diag_land_speed))

        orthog_road_speed, diag_road_speed = ceil(1.25*orthog_land_speed), ceil(1.25*diag_land_speed)
        patch.write_token(APTokenTypes.WRITE, 0x000f038, struct.pack(">H", orthog_road_speed))
        patch.write_token(APTokenTypes.WRITE, 0x000f03c, struct.pack(">H", diag_road_speed))

def patch_upwarp_present(world, patch) -> None:
    if world.options.upwarp_present:
        patch.write_token(APTokenTypes.WRITE, 0x00010b06, read_bin("upwarp_handler_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010b900, read_bin("upwarp_handler"))
        patch.write_token(APTokenTypes.WRITE, 0x000abc34, read_bin("upwarp_name_inv"))
        patch.write_token(APTokenTypes.WRITE, 0x0000a750, read_bin("upwarp_name_mailbox"))
        patch.write_token(APTokenTypes.WRITE, 0x00017be6, read_bin("ship_piece_hint_always_show"))

def patch_death_link(world, patch) -> None:
    if world.options.death_link:
        patch.write_token(APTokenTypes.WRITE, 0x0000bcc6, read_bin("on_death_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010a400, read_bin("on_death"))

def patch_game_overs(world, patch) -> None:
    if world.options.game_overs == GameOverOption.DISABLE:
        patch.write_token(APTokenTypes.WRITE, 0x0000bcd0, read_bin("skip_life_subtraction"))
    elif world.options.game_overs == GameOverOption.DROP_DOWN:
        patch.write_token(APTokenTypes.WRITE, 0x000111ac, read_bin("dropdown_on_death_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010a300, read_bin("dropdown_on_death"))

def patch_ranks(world, patch) -> None:
    if world.options.max_rank_check.value > 0:
        patch.write_token(APTokenTypes.WRITE, 0x001a0310, struct.pack(">8H", *world.rank_thresholds[1:]))
        patch.write_token(APTokenTypes.WRITE, 0x0000b898, read_bin("scaled_rank_points_handler"))

        patch.write_token(APTokenTypes.WRITE, 0x0002203e, read_bin("mole_steal_additions_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010bb00, read_bin("mole_steal_additions"))

def patch_level_gen(world, patch) -> None:
    if world.options.islandless:
        patch.write_token(APTokenTypes.WRITE, 0x00003e80, read_bin("level_gen_islandless"))

def patch_last_level(world, patch) -> None:
    if world.options.last_level != world.options.last_level.default:
        for addr in (0x000127e0+3, 0x0010bf20+3, 0x0010b908+1, 0x0010a738+1):
            patch.write_token(APTokenTypes.WRITE, addr, struct.pack(">B", world.options.last_level.value))
        for addr in (0x0010bd3a+3, 0x0010b900+1):
            patch.write_token(APTokenTypes.WRITE, addr, struct.pack(">B", world.options.last_level.value-1))

def patch_map_reveals(world, patch) -> None:
    patch.write_token(APTokenTypes.WRITE, 0x001a0300, struct.pack(">5B", *world.map_reveal_potencies))
    if world.options.last_level != world.options.last_level.default:
        map_reveal_dialogue = map_reveal_text(world.map_reveal_potencies)
        for addr, string in zip(MAP_REVEAL_DIALOGUE_ADDRS, map_reveal_dialogue):
            patch.write_token(APTokenTypes.WRITE, addr, string.encode("ascii") + b"\x00")

def patch_min_max_items(world, patch) -> None:
    if world.options.min_items != world.options.min_items.default:
        patch.write_token(APTokenTypes.WRITE, 0x00014c1a+1, struct.pack(">B", world.options.min_items.value))
        patch.write_token(APTokenTypes.WRITE, 0x00014c1e+1, struct.pack(">B", world.options.min_items.value))

    if world.options.max_items != world.options.max_items.default:
        patch.write_token(APTokenTypes.WRITE, 0x00014c2c+3, struct.pack(">B", world.options.max_items.value))
        patch.write_token(APTokenTypes.WRITE, 0x00014c32+1, struct.pack(">B", world.options.max_items.value))

def patch_earthling_rando(world, patch) -> None:
    if world.options.earthling_rando != world.options.earthling_rando.default:
        patch.write_token(APTokenTypes.WRITE, 0x0002646e, struct.pack(f">480B", *chain(*world.earthling_list)))

def patch_sound_rando(world, patch) -> None:
    if world.options.sound_rando != world.options.sound_rando.default:
        if world.options.sound_rando == SoundRandoOption.ALL:
            pcm_sfx_addrs = PCM_SFX_ADDRS + PCM_SFX_ADDRS_MUSIC
            pcm_sfx_usage_addrs = PCM_SFX_USAGE_ADDRS + PCM_SFX_USAGE_ADDRS_MUSIC
        else:
            pcm_sfx_addrs = PCM_SFX_ADDRS
            pcm_sfx_usage_addrs = PCM_SFX_USAGE_ADDRS

        world.random.shuffle(pcm_sfx_addrs)
        for i, sfx_addr in enumerate(pcm_sfx_addrs):
            for rom_addr in pcm_sfx_usage_addrs[i]:
                patch.write_token(APTokenTypes.WRITE, rom_addr + 2, struct.pack(">L", sfx_addr))

        world.random.shuffle(PSG_SFX)
        for i, sfx_addr in enumerate(PSG_SFX):
            for rom_addr in PSG_SFX_USAGE_ADDRS[i]:
                patch.write_token(APTokenTypes.WRITE, rom_addr + 3, struct.pack(">B", sfx_addr))

def patch_map_rando(world, patch) -> None:
    if world.options.map_rando != world.options.map_rando.default:
        level_types, new_params = None, None

        match world.options.map_rando:
            case MapRandomizationOption.BASE_SHUFFLE:
                add_failsafe = True
                level_types = BASE_LEVEL_TYPES
                world.random.shuffle(level_types)
            case MapRandomizationOption.BASE_RANDOM:
                add_failsafe = True
                level_types = world.random.choices(range(8), k=24)
            case MapRandomizationOption.FULL_RANDOM | MapRandomizationOption.MAPSANITY:
                add_failsafe = False
                new_params = read_bin("level_gen_mapsanity_parameter_ranges")
                level_types = [0]*24

        if level_types:
            patch.write_token(APTokenTypes.WRITE, 0x0008c00e, struct.pack(">24B", *level_types))
        if new_params:
            patch.write_token(APTokenTypes.WRITE, 0x0008beca, new_params)
        if add_failsafe:
            for addr in [0x0008bef6, 0x0008bf06, 0x0008bf16, 0x0008bf26, 0x0008bf36, 0x0008bf46]:
                patch.write_token(APTokenTypes.WRITE, addr, read_bin("level_gen_parameter_failsafe"))

        if world.options.map_rando == MapRandomizationOption.MAPSANITY:
            patch.write_token(APTokenTypes.WRITE, 0x00004a4c, read_bin("level_gen_skip_seed_setting"))
            patch.write_token(APTokenTypes.WRITE, 0x00004506, read_bin("level_gen_skip_mapdata_storage"))

#endregion

def write_tokens(world: "TJEWorld", patch: TJEProcedurePatch) -> None:
    set_bin_paths(Path("./worlds/tje/data/asm_bin/"), Path("./worlds/tje/data/sprite_bin/"))
    patch_slot_data(world, patch)
    patch_item_list(world, patch)
    patch_main_menu(world, patch)
    patch_starting_presents(world, patch)
    patch_misc_qol(world, patch)
    patch_upwarp_present(world, patch)
    patch_death_link(world, patch)
    patch_game_overs(world, patch)
    patch_ranks(world, patch)
    patch_level_gen(world, patch)
    patch_min_max_items(world, patch)
    patch_last_level(world, patch)
    patch_map_reveals(world, patch)
    patch_earthling_rando(world, patch)
    patch_sound_rando(world, patch)
    patch_map_rando(world, patch)
    patch_expanded_inv(world, patch)

    patch.write_file("token_data.bin", patch.get_token_binary())
    