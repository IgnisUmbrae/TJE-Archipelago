import copy
from pathlib import Path

import bsdiff4
import pyjson5

from patch_util import extract_patches, BinType, set_bin_paths

set_bin_paths(Path("../data/asm_bin"), Path("../data/sprites_bin"))

# collect and assemble base patches
with open("./asm/base_code_patches.json5", "r") as f:
    code_patches = pyjson5.decode(f.read())
with open("./asm/base_sprite_patches.json5", "r") as f:
    sprite_patches = pyjson5.decode(f.read())

static_rom_patches = extract_patches(code_patches, BinType.ASM) + extract_patches(sprite_patches, BinType.SPRITE)

with open("./rom_data/TJEREV02-orig.bin", "rb") as f:
    original_rom = bytearray(f.read())
    patched_rom = copy.copy(original_rom) + b"\x00"*len(original_rom)

for addr, val in static_rom_patches:
    patched_rom[addr:addr+len(val)] = val

diff = bsdiff4.diff(bytes(original_rom), bytes(patched_rom))
with open("../data/base_patch.bsdiff4", "wb") as f:
    f.write(diff)

# create json-formatted optional patches for use in rom.py

