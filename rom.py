import hashlib
import struct
import os
from typing import TYPE_CHECKING

import Utils
from settings import get_settings
from worlds.Files import APProcedurePatch, APTokenMixin, APTokenTypes

from .constants import EMPTY_PRESENT, INITIAL_PRESENT_ADDRS
from .items import ITEM_ID_TO_CODE
from .options import StartingPresentOption, GameOverOption

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
    # Add starting presents
    if world.options.starting_presents == StartingPresentOption.NONE:
        presents = [EMPTY_PRESENT]*8
    else:
        presents = [struct.pack(">B", ITEM_ID_TO_CODE[p]) for p in world.starting_presents]

    for i in range(8):
        patch.write_token(APTokenTypes.WRITE, INITIAL_PRESENT_ADDRS[i], presents[i])

    # Add seeds
    patch.write_token(APTokenTypes.WRITE, 0x00097704, struct.pack(">26H", *world.seeds))

    # Add ship piece levels
    patch.write_token(APTokenTypes.WRITE, 0x00097738, struct.pack(">10B", *world.ship_piece_levels))

    # Add Upwarp Present if desired
    if world.options.upwarp_present:
        patch.write_token(APTokenTypes.WRITE, 0x00010b06, b"\x10\x3C\x00\x19\x4E\x71") # Always up unless on level 25
        patch.write_token(APTokenTypes.WRITE, 0x00017be6, b"\x4e\x71\x4e\x71") # Always show "item here" hint signs
        patch.write_token(APTokenTypes.WRITE, 0x000abc34, b"\x15\x10\x22\x17\x01\x12\x10") # Change name to Up-Warp
    
    if world.options.game_overs == GameOverOption.DISABLE:
        patch.write_token(APTokenTypes.WRITE, 0x0000bcd0, b"\x4E\x71\x4E\x71") # Skip life subtraction
    elif world.options.game_overs == GameOverOption.DROP_DOWN:
        patch.write_token(APTokenTypes.WRITE, 0x000111ac, b"\x4E\xB9\x00\x10\xA5\x00")
        patch.write_token(APTokenTypes.WRITE, 0x0010a500, b"\x24\x7C\x00\xFF\xDA\x22\x14\xBC\x00\x01\x24\x7C\x00\xFF"
                                                          b"\xA2\x48\x14\xBC\x00\x04\x24\x7C\x00\xFF\xA2\xA7\x02\x12"
                                                          b"\x00\x7F\x4E\x75")

    patch.write_file("token_data.bin", patch.get_token_binary())