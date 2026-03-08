import copy
from pathlib import Path

import bsdiff4
import pyjson5

from enum import IntEnum, auto
from pathlib import Path

CODE_PATH, SPRITE_PATH = Path("../data/asm_bin"), Path("../data/sprites_bin")

class BinType(IntEnum):
    SPRITE = auto()
    ASM = auto()

def read_bin(filename: Path | str, type: BinType = BinType.ASM) -> bytes:
    match type:
        case BinType.SPRITE:
            filename = (SPRITE_PATH / filename).with_suffix(".bin")
        case BinType.ASM:
            filename = (CODE_PATH / filename).with_suffix(".bin")
    with filename.open("rb") as file:
        return file.read()

def extract_patches(parsed_json5: str, type: BinType):
    return tuple(
        (addr, read_bin(patch.get("filename"), type))
        for patch in parsed_json5.get("patches")
        for addr in patch.get("addresses")
    )

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

