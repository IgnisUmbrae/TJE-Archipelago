from enum import IntEnum, auto
from pathlib import Path

class BinType(IntEnum):
    SPRITE = auto()
    ASM = auto()

def set_bin_paths(code_dir: Path, sprite_dir: Path) -> None:
    global CODE_PATH, SPRITE_PATH
    CODE_PATH, SPRITE_PATH = code_dir, sprite_dir

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