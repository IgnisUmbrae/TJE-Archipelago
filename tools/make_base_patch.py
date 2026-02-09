from pathlib import Path
from enum import IntEnum, auto
import copy

import bsdiff4
import pyjson5

SPRITE_PATH = Path("../data/sprites_bin")
CODE_PATH = Path("../data/asm_bin")

class BinType(IntEnum):
    SPRITE = auto()
    CODE = auto()

def read_bin(filename: Path, type: BinType) -> bytes:
    match type:
        case BinType.SPRITE:
            filename = (SPRITE_PATH / filename).with_suffix(".bin")
        case BinType.CODE:
            filename = (CODE_PATH / filename).with_suffix(".bin")
    with filename.open("rb") as file:
        return file.read()

def extract_patches(parsed_json5: str, type: BinType):
    return tuple(
        (addr, read_bin(patch.get("filename"), type))
        for patch in parsed_json5.get("patches")
        for addr in patch.get("addresses")
    )

with open("./asm/code_patches.json5", "r") as f:
    code_patches = pyjson5.decode(f.read())
with open("./asm/sprite_patches.json5", "r") as f:
    sprite_patches = pyjson5.decode(f.read())

static_rom_patches = extract_patches(code_patches, BinType.CODE) + extract_patches(sprite_patches, BinType.SPRITE)

with open("./rom_data/TJEREV02-orig.bin", "rb") as f:
    original_rom = bytearray(f.read())
    patched_rom = copy.copy(original_rom) + b"\x00"*len(original_rom)

for addr, val in static_rom_patches:
    patched_rom[addr:addr+len(val)] = val

diff = bsdiff4.diff(bytes(original_rom), bytes(patched_rom))
with open("../data/base_patch.bsdiff4", "wb") as f:
    f.write(diff)