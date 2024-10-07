import hashlib
import struct
import os
from math import sqrt, ceil
from typing import TYPE_CHECKING

import Utils
from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from .constants import EMPTY_PRESENT, INITIAL_PRESENT_ADDRS, BASE_LEVEL_TYPES, INV_REF_ADDRS, INV_SIZE_ADDRS, INV_SIZE_ADDRS_ASL_D0, INV_SIZE_ADDRS_INITIAL, PCM_SFX_ADDRS, PCM_SFX_ADDRS_MUSIC, \
                       PCM_SFX_USAGE_ADDRS, PCM_SFX_USAGE_ADDRS_MUSIC, PSG_SFX, PSG_SFX_USAGE_ADDRS
from .items import ITEM_ID_TO_CODE
from .options import CharacterOption, SoundRandoOption, StartingPresentOption, GameOverOption, MapRandomizationOption

if TYPE_CHECKING:
    from . import TJEWorld

REV00_MD5 = "0a6af20d9c5b3ec4e23c683f083b92cd"
REV02_MD5 = "72dc91fd2c5528b384f082a38db9ddda"

class TJEProcedurePatch(APProcedurePatch, APTokenMixin):
    game = "ToeJam and Earl"
    hash = REV02_MD5
    patch_file_ending = ".aptje"
    result_file_ending = ".bin"

    procedure = [
        ("apply_bsdiff4", ["base_patch.bsdiff4"]),
        ("apply_tokens", ["token_data.bin"])
    ]

    @classmethod
    def get_source_data(cls) -> bytes:

        try:
            filename = get_settings().tje_options["rom_file"]
        except AttributeError:
            filename = None
        if not filename or not os.path.exists(filename):
            filename = Utils.user_path(filename)

        with open(filename, "rb") as f:
            base_rom_bytes = bytes(f.read())

        base_md5 = hashlib.md5()
        base_md5.update(base_rom_bytes)
        md5_hash = base_md5.hexdigest()

        if md5_hash == REV02_MD5:
            return base_rom_bytes
        elif md5_hash == REV00_MD5:
            raise ValueError("This appears to be REV00. Please supply a valid REV02 ROM.")
        else:
            raise ValueError("This doesn't appear to be a ToeJam & Earl ROM.")

def write_tokens(world: "TJEWorld", patch: TJEProcedurePatch) -> None:

    patch.write_token(APTokenTypes.WRITE, 0x00097704, struct.pack(">26H", *world.seeds))

    patch.write_token(APTokenTypes.WRITE, 0x00097738, struct.pack(">10B", *world.ship_item_levels))

    # "Who" menu: only one item / TJ or Earl only / text change
    # Menu return options: 0 for 2-player, 1 for TJ only, 2 for Earl only
    patch.write_token(APTokenTypes.WRITE, 0x00024327, b"\x01")
    match world.options.character:
        case CharacterOption.TOEJAM:
            ret_val = 1
            string = (b"\x4F\x6E\x65\x20\x50\x6C\x61\x79\x65\x72\x20\x2D\x2D\x20\x6A"
                      b"\x75\x73\x27\x20\x54\x6F\x65\x6A\x61\x6D\x00")
            
            char_init = 0
            no_2player = True
        case CharacterOption.EARL:
            ret_val = 2
            string = (b"\x4F\x6E\x65\x20\x50\x6C\x61\x79\x65\x72\x20\x2D\x2D\x20\x6A"
                      b"\x75\x73\x27\x20\x45\x61\x72\x6C\x00")
            char_init = 1
            no_2player = True
        case CharacterOption.BOTH:
            ret_val = 0
            string = None
            no_2player = False

    # Initializes special RAM address that keeps track of which character will receive traps
    patch.write_token(APTokenTypes.WRITE, 0x0010b314, (b"\x20\x7C\x00\xFF\xF0\x00\x10\xBC\x00"
                                                       + char_init.to_bytes(1) + b"\x4E\x75"))

    if string:
        patch.write_token(APTokenTypes.WRITE, 0x000242c5, struct.pack(">B", ret_val))
        patch.write_token(APTokenTypes.WRITE, 0x000242d6, string)

    if no_2player:
        patch.write_token(APTokenTypes.WRITE, 0x00011218, b"\x4E\x71\x4E\x71\x4E\x71")

    if world.options.starting_presents == StartingPresentOption.NONE:
        presents = [EMPTY_PRESENT]*8
    else:
        presents = [struct.pack(">B", ITEM_ID_TO_CODE[p]) for p in world.starting_presents]

    for i in range(8):
        patch.write_token(APTokenTypes.WRITE, INITIAL_PRESENT_ADDRS[i], presents[i])

    if world.options.max_rank_check.value > 0:
        # Stop moles stealing Promotion presents
        patch.write_token(APTokenTypes.WRITE, 0x0002203e, b"\x4E\xF9\x00\x10\xBB\x00\x4E\x71\x4E\x71\x4E\x71\x4E\x71"
                                                          b"\x4E\x71\x4E\x71\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x0010bb00, b"\x30\x03\x48\xC0\xE9\x80\x22\x45\x20\x49\x32\x02\xD1\xC0"
                                                          b"\x1C\x30\x10\x00\x48\x86\x0C\x46\x00\x0B\x67\x06\x4E\xF9"
                                                          b"\x00\x02\x20\x52\x4E\xF9\x00\x02\x21\x7C\x00")
    if world.options.upwarp_present:
        # Jump to new function
        patch.write_token(APTokenTypes.WRITE, 0x00010b06, b"\x4E\xF9\x00\x10\xB9\x00\x4e\x71\x4e\x71\x4e\x71")
        # New Up-Warp handling function
        patch.write_token(APTokenTypes.WRITE, 0x0010b900, b"\x70\x18\xB0\x2A\x00\x4C\x6E\x26\x70\x19\xB0\x2A\x00\x4C"
                                                          b"\x67\x24\x20\x7C\x00\xFF\xF4\x44\x42\x44\x12\x30\x40\x00"
                                                          b"\xB2\x3C\x00\xFF\x67\x12\x4E\x71\x4E\x71\x52\x44\x0C\x44"
                                                          b"\x00\x09\x6D\xEA\x4E\xF9\x00\x01\x0B\x12\x4E\xF9\x00\x01"
                                                          b"\x0B\x24")
        patch.write_token(APTokenTypes.WRITE, 0x00017be6, b"\x4e\x71\x4e\x71") # Always show "item here" hint signs
        patch.write_token(APTokenTypes.WRITE, 0x000abc34, b"\x15\x10\x22\x17\x01\x12\x10") # Change name to Up-Warp
        patch.write_token(APTokenTypes.WRITE, 0x0000a750, b"\x75\x70\x2D\x77\x61\x72\x70\x20") # And in mailbox

    if world.options.game_overs == GameOverOption.DISABLE:
        patch.write_token(APTokenTypes.WRITE, 0x0000bcd0, b"\x4E\x71\x4E\x71") # Skip life subtraction
    elif world.options.game_overs == GameOverOption.DROP_DOWN:
        patch.write_token(APTokenTypes.WRITE, 0x000111ac, b"\x4E\xB9\x00\x10\xA3\x00")
        patch.write_token(APTokenTypes.WRITE, 0x0010a300, b"\x22\x7C\x00\xFF\xDA\x22\x13\xBC\x00\x01\x48\x00\x22\x7C"
                                                          b"\x00\xFF\xA2\x48\x13\xBC\x00\x04\x48\x00\x22\x7C\x00\xFF"
                                                          b"\xA2\xA7\x02\x2A\x00\x7F\x00\x4D\x4E\x75")
    if not world.options.sleep_when_idle:
        patch.write_token(APTokenTypes.WRITE, 0x0001262a, b"\x4E\x71\x4E\x71")

    if world.options.free_earthling_services:
        # Opera singer
        patch.write_token(APTokenTypes.WRITE, 0x00021a70, b"\x4E\x71\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x00021a8a, b"\x4E\x71\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x00021c04, b"\x46\x72\x65\x65\x20\x73\x6F\x6E\x67\x3F\x00")

        # Wizard
        patch.write_token(APTokenTypes.WRITE, 0x000215dc, b"\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x000215f4, b"\x4E\x71\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x000216f2, b"\x46\x72\x65\x65\x20\x68\x65\x61\x6C\x3F\x00")

        # Wiseman
        patch.write_token(APTokenTypes.WRITE, 0x00009d96, b"\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x00009e10, b"\x4E\x71\x4E\x71")
        patch.write_token(APTokenTypes.WRITE, 0x000218ea, b"\x46\x72\x65\x65\x20\x49\x44\x3F\x00")

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

    if world.options.fast_loads:
        patch.write_token(APTokenTypes.WRITE, 0x00013710, b"\x00\x00")
        patch.write_token(APTokenTypes.WRITE, 0x0001371a, b"\x80\x00")

    if world.options.expanded_inventory:
        for addr in INV_REF_ADDRS:
            patch.write_token(APTokenTypes.WRITE, addr, b"\x00\xff\xf2\x80")
        for addr in INV_SIZE_ADDRS:
            patch.write_token(APTokenTypes.WRITE, addr, b"\x40")
        for i, addr in enumerate(INV_SIZE_ADDRS_INITIAL):
            patch.write_token(APTokenTypes.WRITE, addr, (0x40+i).to_bytes(1))
        for addr in INV_SIZE_ADDRS_ASL_D0:
            patch.write_token(APTokenTypes.WRITE, addr, b"\xED\x80")
        patch.write_token(APTokenTypes.WRITE, 0x000099a6, b"\xED\x81") # using D1
        patch.write_token(APTokenTypes.WRITE, 0x00022068, b"\xED\x82") # using D2

        # Make presents scooch up properly on opening and dropping
        patch.write_token(APTokenTypes.WRITE, 0x00009ab2+3, b"\x3F")
        patch.write_token(APTokenTypes.WRITE, 0x00009ba0+3, b"\x3F")

        # Patch menu handler to allow extra scrolling
        patch.write_token(APTokenTypes.WRITE, 0x0000979c+3, b"\x1D")

    if world.options.sound_rando != world.options.sound_rando.default:
        if world.options.sound_rando == SoundRandoOption.ALL:
            PCM_SFX_ADDRS.extend(PCM_SFX_ADDRS_MUSIC)
            PCM_SFX_USAGE_ADDRS.extend(PCM_SFX_USAGE_ADDRS_MUSIC)
        world.random.shuffle(PCM_SFX_ADDRS)
        for i, sfx_addr in enumerate(PCM_SFX_ADDRS):
            for rom_addr in PCM_SFX_USAGE_ADDRS[i]:
                # +2 to jump over the operation
                patch.write_token(APTokenTypes.WRITE, rom_addr + 2, sfx_addr.to_bytes(4))

        world.random.shuffle(PSG_SFX)
        for i, sfx_addr in enumerate(PSG_SFX):
            for rom_addr in PSG_SFX_USAGE_ADDRS[i]:
                patch.write_token(APTokenTypes.WRITE, rom_addr + 3, sfx_addr.to_bytes(1))

    if world.options.map_rando != world.options.map_rando.default:
        # add_failsafe alters the penultimate property of every level type to guarantee that
        # levels generate successfully; without it, elevator softlocks are possible
        add_failsafe = False
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
                new_params = b"\x01\x46\x00\x3C\x05\x50\x01\x46\x00\x64\x00\x64\x03\x04\x0F\x50"
                level_types = [0]*24

        if level_types:
            patch.write_token(APTokenTypes.WRITE, 0x0008c00e, struct.pack(">24B", *level_types))
        if new_params:
            patch.write_token(APTokenTypes.WRITE, 0x0008beca, new_params)
        if add_failsafe:
            for addr in [0x0008bef6, 0x0008bf06, 0x0008bf16, 0x0008bf26, 0x0008bf36, 0x0008bf46]:
                patch.write_token(APTokenTypes.WRITE, addr, b"\x03\x04")

        if world.options.map_rando == MapRandomizationOption.MAPSANITY:
            # Don't set level seed; current RNG value will be used instead
            patch.write_token(APTokenTypes.WRITE, 0x00004a4c, b"\x4e\x71\x4e\x71\x4e\x71\x4e\x71")
            # Prevent game from storing previous level data
            patch.write_token(APTokenTypes.WRITE, 0x00004506, b"\x4e\x71\x4e\x71\x4e\x71\x4e\x71\x4e\x71")
            patch.write_token(APTokenTypes.WRITE, 0x00004518, b"\x4e\x71\x4e\x71\x4e\x71")

    if world.options.min_items != world.options.min_items.default:
        patch.write_token(APTokenTypes.WRITE, 0x00014c1b, struct.pack(">B", world.options.min_items.value))
        patch.write_token(APTokenTypes.WRITE, 0x00014c1f, struct.pack(">B", world.options.min_items.value))

    if world.options.max_items != world.options.max_items.default:
        patch.write_token(APTokenTypes.WRITE, 0x00014c2f, struct.pack(">B", world.options.max_items.value))
        patch.write_token(APTokenTypes.WRITE, 0x00014c33, struct.pack(">B", world.options.max_items.value))

    # Store data required by client

    patch.write_token(APTokenTypes.WRITE, 0x001f0000, struct.pack(">B", world.options.key_type.value))
    patch.write_token(APTokenTypes.WRITE, 0x001f0001, struct.pack(">B", world.options.auto_trap_presents.value))

    num_key_levels = len(world.key_levels)
    patch.write_token(APTokenTypes.WRITE, 0x001f0010, struct.pack(">B", num_key_levels))
    patch.write_token(APTokenTypes.WRITE, 0x001f0011, struct.pack(f">{num_key_levels}B", *world.key_levels))

    # Store list of item types

    patch.write_token(APTokenTypes.WRITE, 0x001a0000, struct.pack(f">{26*28}B", *world.patchable_item_list))

    patch.write_file("token_data.bin", patch.get_token_binary())