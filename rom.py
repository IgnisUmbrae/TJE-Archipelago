import copy
import struct
import json
import pkgutil
from itertools import chain
from math import sqrt, ceil

from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from .constants import EMPTY_PRESENT, INITIAL_PRESENT_ADDRS, BASE_LEVEL_TYPES, INV_REF_ADDRS_VANILLA, \
                       INV_SIZE_ADDRS_VANILLA, INV_SIZE_ADDRS_ASL_D0_VANILLA, INV_SIZE_ADDRS_INITIAL, \
                       MAP_REVEAL_DIALOGUE_ADDRS, PCM_SFX_ADDRS, PCM_SFX_ADDRS_MUSIC, PCM_SFX_USAGE_ADDRS, \
                       PCM_SFX_USAGE_ADDRS_MUSIC, PSG_SFX, PSG_SFX_USAGE_ADDRS, SIMPLE_SFX, SIMPLE_SFX_USAGE_ADDRS
from .generators import map_reveal_text
from .items import ITEM_ID_TO_CODE
from .options import CharacterOption, SoundRandoOption, StartingPresentOption, GameOverOption, MapRandomizationOption, \
                     LocalShipPiecesOption

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

def read_bin(filename: str, sprite: bool = False) -> bytes | None:
    dir = "data/sprites_bin/" if sprite else "data/asm_bin/"
    return pkgutil.get_data(__name__, dir + filename + ".bin")

def read_json(filename: str) -> str | None:
    return pkgutil.get_data(__name__, "data/json/" + filename + ".json").decode("utf-8")

#region Individual patching sections

def patch_slot_data(world, patch, dro) -> None:
    patch.write_token(APTokenTypes.WRITE, 0x00097704, struct.pack(">26H", *world.seeds))
    patch.write_token(APTokenTypes.WRITE, 0x00097738, struct.pack(">10B", *world.ship_item_levels))

    key_gap = world.options.key_gap.value if world.options.elevator_keys else 0
    patch.write_token(APTokenTypes.WRITE, 0x001f0000, struct.pack(">B", key_gap))
    patch.write_token(APTokenTypes.WRITE, 0x001f0001, struct.pack(">B", world.options.death_link.value))
    patch.write_token(APTokenTypes.WRITE, 0x001f0005, struct.pack(">B", world.options.auto_bad_presents.value))
    num_key_levels = len(world.key_levels)
    patch.write_token(APTokenTypes.WRITE, 0x001f0010, struct.pack(">B", num_key_levels))
    patch.write_token(APTokenTypes.WRITE, 0x001f0011, struct.pack(f">{num_key_levels}B", *world.key_levels))

def patch_item_list(world, patch, dro) -> None:
    patch.write_token(APTokenTypes.WRITE, 0x001a0000, struct.pack(f">{(world.options.last_level.value+1)*28}B",
                                                                  *world.patchable_item_list))
def patch_main_menu(world, patch, dro) -> None:
    # Menu return options: 0 for 2-player, 1 for TJ only, 2 for Earl only
    match world.options.character:
        case CharacterOption.TOEJAM:
            ret_val = 1
            char_init = 0
            menu_string_fn = "who_menu_toejam_string"
            no_2player = True
        case CharacterOption.EARL:
            ret_val = 2
            char_init = 1
            menu_string_fn = "who_menu_earl_string"
            no_2player = True
        case CharacterOption.BOTH:
            ret_val = 0
            char_init = world.random.randint(0, 1)
            menu_string_fn = None
            no_2player = False

    patch.write_token(APTokenTypes.WRITE,
                      0x0010b400 + dro["init_extra"]["player_char"] + 3,
                      struct.pack(">B", char_init))

    if menu_string_fn:
        patch.write_token(APTokenTypes.WRITE, 0x000242c5, struct.pack(">B", ret_val))
        patch.write_token(APTokenTypes.WRITE, 0x000242d6, read_bin(menu_string_fn))

    if no_2player:
        patch.write_token(APTokenTypes.WRITE, 0x00011218, read_bin("main_loop_disable_coop_join"))

def patch_starting_presents(world, patch, dro) -> None:
    if world.options.starting_presents == StartingPresentOption.NONE:
        presents = [EMPTY_PRESENT]*8
    else:
        presents = [struct.pack(">B", ITEM_ID_TO_CODE[p]) for p in world.starting_presents]

    for i in range(8):
        patch.write_token(APTokenTypes.WRITE, INITIAL_PRESENT_ADDRS[i], presents[i])

def patch_unused_present_sprites(world, patch, dro) -> None:
    # replace two random present sprites with the unused ones
    if world.options.unused_present_sprites:
        excl1, excl2 = world.random.sample(range(0, 30), k=2)
        if excl1 < 28:
            patch.write_token(APTokenTypes.WRITE, 0x00105000 + 4*excl1, struct.pack(">L", 0x000aaee4))
        if excl2 < 28:
            patch.write_token(APTokenTypes.WRITE, 0x00105000 + 4*excl2, struct.pack(">L", 0x000aaf92))

def patch_expanded_inv(world, patch, dro) -> None:

    if world.options.expanded_inventory:
        inv_ref_addrs = copy.copy(INV_REF_ADDRS_VANILLA)
        inv_ref_addrs.extend([
            0x0010a000 + dro["pickup_item"]["inventory_addr_1"] + 2,
            0x0010a000 + dro["pickup_item"]["inventory_addr_2"] + 2,
            0x0010a900 + dro["init_id_presents"]["inventory_addr"] + 2,
        ])

        inv_size_addrs = copy.copy(INV_SIZE_ADDRS_VANILLA)
        inv_size_addrs.extend([
            0x0010a000 + dro["pickup_item"]["inventory_size_1"] + 3,
            0x0010a000 + dro["pickup_item"]["inventory_size_2"] + 3,
            0x0010a900 + dro["init_id_presents"]["inventory_size_1"] + 3,
            0x0010a900 + dro["init_id_presents"]["inventory_size_2"] + 3,
        ])

        for addr in inv_ref_addrs:
            patch.write_token(APTokenTypes.WRITE, addr, struct.pack(">L", 0x00fff280))
        for addr in inv_size_addrs:
            patch.write_token(APTokenTypes.WRITE, addr, struct.pack(">B", 64))
        for i, addr in enumerate(INV_SIZE_ADDRS_INITIAL):
            patch.write_token(APTokenTypes.WRITE, addr, (0x40+i).to_bytes(1))

        inv_size_addrs_asl_d0 = copy.copy(INV_SIZE_ADDRS_ASL_D0_VANILLA)
        inv_size_addrs_asl_d0.extend([
            0x0010a000 + dro["pickup_item"]["inventory_asl_1"],
            0x0010a000 + dro["pickup_item"]["inventory_asl_2"],
        ])

        if world.options.max_rank_check.value > 0:
            inv_size_addrs_asl_d0.remove(0x00022042)
            inv_size_addrs_asl_d0.append(0x0010bb00 + dro["mole_steal_additions"]["inventory_asl"])

        for addr in inv_size_addrs_asl_d0:
            patch.write_token(APTokenTypes.WRITE, addr, b"\xED\x80")
        patch.write_token(APTokenTypes.WRITE, 0x000099a6, b"\xED\x81") # using D1
        patch.write_token(APTokenTypes.WRITE, 0x00022068, b"\xED\x82") # using D2

        # Make presents scooch up properly on opening and dropping (expand range)
        patch.write_token(APTokenTypes.WRITE, 0x00009ab2+3, struct.pack(">B", 39))
        patch.write_token(APTokenTypes.WRITE, 0x00009ba0+3, struct.pack(">B", 39))

        # Patch menu handler to allow extra scrolling (size/2 - 3)
        patch.write_token(APTokenTypes.WRITE, 0x0000979c+3, b"\x1D")

def patch_misc_qol(world, patch, dro) -> None:
    if not world.options.sleep_when_idle:
        patch.write_token(APTokenTypes.WRITE, 0x0001262a, read_bin("no_idle_sleeping"))

    if world.options.fast_loads:
        patch.write_token(APTokenTypes.WRITE, 0x0001370e, read_bin("elev_fast_loads"))

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

def patch_upwarp_present(world, patch, dro) -> None:
    if world.options.upwarp_present:
        patch.write_token(APTokenTypes.WRITE, 0x00010b06, read_bin("upwarp_handler_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010b900, read_bin("upwarp_handler"))
        patch.write_token(APTokenTypes.WRITE, 0x000abc34, read_bin("upwarp_name_inv"))
        patch.write_token(APTokenTypes.WRITE, 0x0000a750, read_bin("upwarp_name_mailbox"))
        patch.write_token(APTokenTypes.WRITE, 0x00017be6, read_bin("ship_piece_hint_always_show"))

def patch_death_link(world, patch, dro) -> None:
    if world.options.death_link:
        patch.write_token(APTokenTypes.WRITE, 0x0000bcc6, read_bin("on_death_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010a400, read_bin("on_death"))
        if world.options.game_overs != GameOverOption.DROP_DOWN:
            patch.write_token(APTokenTypes.WRITE,
                              0x0010a400 + dro["on_death"]["dropdown_life_check"],
                              read_bin("on_death_remove_life_check"))

def patch_game_overs(world, patch, dro) -> None:
    if world.options.game_overs == GameOverOption.DISABLE:
        patch.write_token(APTokenTypes.WRITE, 0x0000bcd0, read_bin("skip_life_subtraction"))
    elif world.options.game_overs == GameOverOption.DROP_DOWN:
        patch.write_token(APTokenTypes.WRITE, 0x000111ac, read_bin("dropdown_on_death_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010a300, read_bin("dropdown_on_death"))

def patch_ranks(world, patch, dro) -> None:
    if world.options.max_rank_check.value > 0:
        patch.write_token(APTokenTypes.WRITE, 0x001a0310, struct.pack(">8H", *world.rank_thresholds[1:]))
        patch.write_token(APTokenTypes.WRITE, 0x0000b898, read_bin("scaled_rank_points_handler"))

        patch.write_token(APTokenTypes.WRITE, 0x0002203e, read_bin("mole_steal_additions_jump"))
        patch.write_token(APTokenTypes.WRITE, 0x0010bb00, read_bin("mole_steal_additions"))

def patch_level_gen(world, patch, dro) -> None:
    if world.options.islandless:
        patch.write_token(APTokenTypes.WRITE, 0x00003e80, read_bin("level_gen_islandless"))

def patch_last_level(world, patch, dro) -> None:
    if world.options.last_level != world.options.last_level.default:
        for addr in (0x0010bd00 + dro["elev_key_logic"]["last_level_minus_one"] + 3,
                     0x0010b900 + dro["upwarp_handler"]["last_level_minus_one"] + 1):
            patch.write_token(APTokenTypes.WRITE, addr, struct.pack(">B", world.options.last_level.value-1))
        for addr in (0x000127e0+3, 0x0010bf20+3,
                     0x0010b900 + dro["upwarp_handler"]["last_level"] + 1,
                     0x0010a700 + dro["ship_piece_touch"]["last_level"] + 1):
            patch.write_token(APTokenTypes.WRITE, addr, struct.pack(">B", world.options.last_level.value))

def patch_map_reveals(world, patch, dro) -> None:
    patch.write_token(APTokenTypes.WRITE, 0x001a0300, struct.pack(">5B", *world.map_reveal_potencies))
    if world.options.last_level != world.options.last_level.default:
        map_reveal_dialogue = map_reveal_text(world.map_reveal_potencies)
        for addr, string in zip(MAP_REVEAL_DIALOGUE_ADDRS, map_reveal_dialogue):
            patch.write_token(APTokenTypes.WRITE, addr, string.encode("ascii") + b"\x00")

def patch_min_max_items(world, patch, dro) -> None:
    if world.options.min_items != world.options.min_items.default:
        patch.write_token(APTokenTypes.WRITE, 0x00014c1a+1, struct.pack(">B", world.options.min_items.value))
        patch.write_token(APTokenTypes.WRITE, 0x00014c1e+1, struct.pack(">B", world.options.min_items.value))

    if world.options.max_items != world.options.max_items.default:
        patch.write_token(APTokenTypes.WRITE, 0x00014c2c+3, struct.pack(">B", world.options.max_items.value))
        patch.write_token(APTokenTypes.WRITE, 0x00014c32+1, struct.pack(">B", world.options.max_items.value))

def patch_earthling_rando(world, patch, dro) -> None:
    if world.options.earthling_rando != world.options.earthling_rando.default:
        patch.write_token(APTokenTypes.WRITE, 0x0002646e, struct.pack(f">480B", *chain(*world.earthling_list)))

def patch_sound_rando(world, patch, dro) -> None:
    if world.options.sound_rando != world.options.sound_rando.default:
        # Get base of static locations
        if world.options.sound_rando == SoundRandoOption.ALL:
            pcm_sfx_addrs = PCM_SFX_ADDRS + PCM_SFX_ADDRS_MUSIC
            pcm_sfx_usage_addrs = PCM_SFX_USAGE_ADDRS + PCM_SFX_USAGE_ADDRS_MUSIC
        else:
            pcm_sfx_addrs = PCM_SFX_ADDRS
            pcm_sfx_usage_addrs = PCM_SFX_USAGE_ADDRS
        psg_sfx_usage_addrs = copy.copy(PSG_SFX_USAGE_ADDRS)

        # Insert dynamic locations from DRO list
        pcm_sfx_usage_addrs[34] = (0x0010a000 + dro["pickup_item"]["PCM_SFX_1"],)
        pcm_sfx_usage_addrs[3] = (0x0010a000 + dro["pickup_item"]["PCM_SFX_2"],
                                  0x0010a000 + dro["pickup_item"]["PCM_SFX_3"])
        psg_sfx_usage_addrs[11].append(0x0010a000 + dro["pickup_item"]["PSG_SFX_1"])
        psg_sfx_usage_addrs[0] = (0x0010a000 + dro["pickup_item"]["PSG_SFX_2"],)

        world.random.shuffle(pcm_sfx_addrs)
        for i, sfx_addr in enumerate(pcm_sfx_addrs):
            for rom_addr in pcm_sfx_usage_addrs[i]:
                patch.write_token(APTokenTypes.WRITE, rom_addr + 2, struct.pack(">L", sfx_addr))

        world.random.shuffle(PSG_SFX)
        for i, sfx_num in enumerate(PSG_SFX):
            for rom_addr in psg_sfx_usage_addrs[i]:
                patch.write_token(APTokenTypes.WRITE, rom_addr + 3, struct.pack(">B", sfx_num))

        world.random.shuffle(SIMPLE_SFX)
        for i, sfx_num in enumerate(SIMPLE_SFX):
            for rom_addr in SIMPLE_SFX_USAGE_ADDRS[i]:
                patch.write_token(APTokenTypes.WRITE, rom_addr + 3, struct.pack(">B", sfx_num))

def patch_map_rando(world, patch, dro) -> None:
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

def patch_ship_piece_sprites(world, patch, dro) -> None:
    if world.options.local_ship_pieces != LocalShipPiecesOption.VANILLA:
        for addr in (0x000e13fd, 0x000e1407, 0x000e1411):
            patch.write_token(APTokenTypes.WRITE, addr, read_bin("ship_piece_hint_spr_flags"))
        patch.write_token(APTokenTypes.WRITE, 0x000e13fe, read_bin("ship_piece_hint_spr_pointer1"))
        patch.write_token(APTokenTypes.WRITE, 0x000e1408, read_bin("ship_piece_hint_spr_pointer2"))
        patch.write_token(APTokenTypes.WRITE, 0x000e1412, read_bin("ship_piece_hint_spr_pointer3"))

        for addr in (0x000e0e81, 0x000e0e8b, 0x000e116d, 0x000e1177):
            patch.write_token(APTokenTypes.WRITE, addr, read_bin("ship_piece_sign_plinth_spr_flags"))
        patch.write_token(APTokenTypes.WRITE, 0x000e0e82, read_bin("ship_piece_sign_plinth_spr_pointer1"))
        patch.write_token(APTokenTypes.WRITE, 0x000e0e8c, read_bin("ship_piece_sign_plinth_spr_pointer2"))
        patch.write_token(APTokenTypes.WRITE, 0x000e116e, read_bin("ship_piece_sign_plinth_spr_pointer3"))
        patch.write_token(APTokenTypes.WRITE, 0x000e1178, read_bin("ship_piece_sign_plinth_spr_pointer4"))

        for addr, spr_file in zip((0x00100120, 0x00100320, 0x00100520),
                                  ("apitemhere0", "apitemhere1", "apitemhere2")):
            patch.write_token(APTokenTypes.WRITE, addr, read_bin(spr_file, sprite = True))

        for addr, spr_file in zip((0x00100720, 0x00100920, 0x00100b20, 0x00100d20),
                                  ("shippiece0tile0", "shippiece0tile1", "shippiece1tile0", "shippiece1tile1")):
            patch.write_token(APTokenTypes.WRITE, addr, read_bin(spr_file, sprite = True))
        
        patch.write_token(APTokenTypes.WRITE, 0x000205e8, read_bin("ship_piece_strings"))

#endregion

def write_tokens(world: "TJEWorld", patch: TJEProcedurePatch) -> None:
    dro = json.loads(read_json("dynamic_repatch_offsets"))

    patch_slot_data(world, patch, dro)
    patch_item_list(world, patch, dro)
    patch_main_menu(world, patch, dro)
    patch_starting_presents(world, patch, dro)
    patch_unused_present_sprites(world, patch, dro)
    patch_expanded_inv(world, patch, dro)
    patch_misc_qol(world, patch, dro)
    patch_upwarp_present(world, patch, dro)
    patch_death_link(world, patch, dro)
    patch_game_overs(world, patch, dro)
    patch_ranks(world, patch, dro)
    patch_level_gen(world, patch, dro)
    patch_min_max_items(world, patch, dro)
    patch_last_level(world, patch, dro)
    patch_map_reveals(world, patch, dro)
    patch_earthling_rando(world, patch, dro)
    patch_sound_rando(world, patch, dro)
    patch_map_rando(world, patch, dro)
    patch_ship_piece_sprites(world, patch, dro)

    patch.write_file("token_data.bin", patch.get_token_binary())
