import bsdiff4
import copy
from pathlib import Path

# The extended ROM is split as follows:

SPRITE_PATH = Path("../data/sprites")

def read_bin(filename: Path) -> bytes:
    with filename.open("rb") as f:
        return f.read()

STATIC_ROM_PATCHES: list[tuple[int, bytes]] = [
    # Expand cartridge to 2 MB
    (0x000001a5, b"\x1f"),

    ### Present-related ###

    # Add new AP present sprite
    (0x00100000, read_bin(SPRITE_PATH / "apitem-v2.bin")),

    # # Replace Bonus Hi-Tops sprite metadata to point to AP sprite
    (0x000aae4e, b"\x03\x03\xf6\xef\xf2\x42\x00\x10\x00\x00"),

    # Patch object-adding routine to generate present 1B only, without removing/altering any RNG calls
    (0x00014cb6, b"\x76\x1b\x4e\x71\x4e\x71\x4e\x71\x4e\x71\x4e\x71\x4e"
                 b"\x71\x4e\x71\x4e\x71\x4e\x71\x4e\x71\x4e\x71\x4e\x71"),
    (0x00014d24, b"\x76\x1b\x4e\x71\x4e\x71"),
    (0x00014d2c, b"\x76\x1b"),
    
    # "Collect" but do not add to inventory any presents ≥ 1B
    (0x00015352, b"\x4e\xf9\x00\x10\xa0\x00"),
    (0x0010a000, b"\x4E\x56\xFF\xF8\x48\xE7\x3E\x30\x36\x2E\x00\x0A\x2A\x2E\x00\x0C\x38\x2E\x00\x12\x30\x03\xEF"
                 b"\x40\x20\x7C\x00\xFF\xA2\x5A\xD0\xC0\x26\x48\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x48\x4A\x30"
                 b"\x08\x00\x6D\x30\x0C\x6B\x00\x04\x00\x04\x6C\x28\x0C\x2B\x00\x03\x00\x4B\x67\x20\x0C\x2B\x00"
                 b"\x07\x00\x4B\x67\x18\x0C\x2B\x00\x4D\x00\x4B\x67\x10\x20\x6B\x00\x52\xC1\x88\x02\x80\x00\x04"
                 b"\x18\x00\xC1\x88\x67\x04\x60\x00\x02\x2A\x42\x6E\xFF\xFC\x60\x00\x02\x18\x30\x6E\xFF\xFC\x20"
                 b"\x08\x48\xC0\xE7\x80\x20\x40\xD1\xC5\x24\x48\x4A\x2A\x00\x02\x67\x00\x01\xFC\x42\x2E\xFF\xFF"
                 b"\x34\x2A\x00\x04\x48\xC2\x30\x13\x48\xC0\x94\x80\x2F\x02\x4E\xB9\x00\x02\x71\x4A\x58\x8F\x74"
                 b"\x10\xB4\x80\x6F\x00\x01\xAC\x34\x2A\x00\x06\x48\xC2\x30\x2B\x00\x02\x48\xC0\x94\x80\x2F\x02"
                 b"\x4E\xB9\x00\x02\x71\x4A\x58\x8F\x74\x08\xB4\x80\x6F\x00\x01\x8C\x0C\x12\x00\x40\x6C\x00\x00"
                 b"\x8C\x42\x46\x0C\x12\x00\x1B\x6C\x00\x00\x30\x30\x03\x48\xC0\xE9\x80\x20\x7C\x00\xFF\xDA\xC2"
                 b"\x32\x06\xD1\xC0\x0C\x30\x00\xFF\x10\x00\x66\x36\x30\x03\x48\xC0\xE9\x80\x20\x7C\x00\xFF\xDA"
                 b"\xC2\x32\x06\xD1\xC0\x11\x92\x10\x00\x74\x01\x1D\x42\xFF\xFF\x48\x78\x00\x32\x48\x78\x00\x01"
                 b"\x4E\xB9\x00\x03\xF7\x70\x2F\x0B\x4E\xB9\x00\x01\x90\x86\x4F\xEF\x00\x0C\x60\x08\x52\x46\x0C"
                 b"\x46\x00\x10\x6D\xAA\x0C\x46\x00\x10\x66\x00\x01\x1C\x34\x03\x48\xC2\x2F\x02\x4E\xB9\x00\x01"
                 b"\xE3\x12\x58\x8F\x4A\x80\x66\x00\x01\x08\x34\x03\x48\xC2\x2F\x02\x48\x78\x00\x19\x60\x00\x00"
                 b"\xF2\x70\x01\x1D\x40\xFF\xFF\x1D\x52\xFF\xFB\x30\x2E\xFF\xFA\x48\x80\x3D\x40\xFF\xFA\x04\x6E"
                 b"\x00\x40\xFF\xFA\x0C\x12\x00\x50\x66\x28\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x4A\x52\x30\x08"
                 b"\x00\x42\xA7\x48\x78\x00\x32\x2F\x3C\x00\x08\x23\x3C\x4E\xB9\x00\x03\xF5\xDC\x4F\xEF\x00\x0C"
                 b"\x60\x00\x00\x9A\x30\x2E\xFF\xFA\x20\x7C\x00\x0A\xBE\x98\x1C\x30\x00\x00\x48\x86\x6F\x52\x30"
                 b"\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x52\x14\x30\x08\x00\x48\x82\x48\xC2\x30\x03\x48\xC0\x2F\x00"
                 b"\x4E\xB9\x00\x00\xAE\x90\x58\x8F\xB4\x80\x6D\x2E\x48\x78\x00\x01\x48\x7A\x00\xBA\x4E\x71\x34"
                 b"\x03\x48\xC2\x2F\x02\x4E\xB9\x00\x01\xE0\x1E\x42\xA7\x48\x78\x00\x32\x2F\x3C\x00\x04\xD7\x5A"
                 b"\x4E\xB9\x00\x03\xF5\xDC\x4F\xEF\x00\x18\x60\x4C\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x52\x12"
                 b"\x06\xD3\x30\x08\x00\x4A\x46\x6F\x10\x42\xA7\x48\x78\x00\x32\x2F\x3C\x00\x04\xD7\x5A\x60\x00"
                 b"\xFF\x6C\x48\x78\x00\x28\x48\x78\x00\x12\x4E\xB9\x00\x03\xF7\x70\x50\x8F\x34\x03\x48\xC2\x2F"
                 b"\x02\x30\x2E\xFF\xFA\x48\xC0\x5A\x80\x2F\x00\x4E\xB9\x00\x01\xE3\x8E\x50\x8F\x4A\x2E\xFF\xFF"
                 b"\x67\x28\x14\xBC\x00\xFF\x4A\x2E\x00\x17\x67\x1E\x10\x2A\x00\x01\x48\x80\xE5\x40\x20\x7C\x00"
                 b"\xFF\xDD\xE8\x24\x3C\x80\x00\x00\x00\x12\x2E\xFF\xFD\xE2\xAA\x85\xB0\x00\x00\x52\x6E\xFF\xFC"
                 b"\x30\x2E\xFF\xFC\xB0\x44\x6D\x00\xFD\xE2\x4C\xEE\x0C\x7C\xFF\xDC\x4E\x5E\x4E\x75\x49\x27\x6D"
                 b"\x20\x73\x74\x75\x66\x66\x65\x64\x00"), 

    ### Ship piece–related ###

    # Ship piece display routine will now use a copy of the collected ship pieces
    # Copy is located at 0xFFF444 and will track collection of actual ship pieces
    # Original is at 0xFFE212 will track which ship piece *overworld items* have been triggered
    (0x00020906, b"\x26\x7c\x00\xff\xf4\x44"),

    # Ship pieces not marked as collected when collected, skip animation
    # Patch 4e ba fb ea back in here to return to normal behaviour on Level 25
    (0x00020cf8, b"\x4e\x71\x4e\x71"),

    # Alter various ship piece–related strings
    (0x000205e8, b"\x42\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6d\x20\x6f\x6e\x20\x74\x68\x69\x73\x20\x6c\x65\x76\x65"
                 b"\x6c\x21\x00\x00\x00\x00\x00\x00\x42\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6d\x20\x6f\x6e\x20\x74"
                 b"\x6f\x65\x6a\x61\x6d\x27\x73\x20\x6c\x65\x76\x65\x6c\x21\x00\x00\x00\x00\x00\x00\x42\x69\x67\x20"
                 b"\x41\x50\x20\x69\x74\x65\x6d\x20\x6f\x6e\x20\x65\x61\x72\x6c\x27\x73\x20\x6c\x65\x76\x65\x6c\x21"
                 b"\x00\x00\x00\x00\x00\x00\x6e\x6f\x20\x62\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6d\x73\x20\x68\x65"
                 b"\x72\x65\x00\x00\x00\x00\x6e\x6f\x20\x62\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6d\x73\x20\x77\x69"
                 b"\x74\x68\x20\x74\x6f\x65\x6a\x61\x6d\x00\x6e\x6f\x20\x62\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6d"
                 b"\x73\x20\x77\x69\x74\x68\x20\x65\x61\x72\x6c\x00"),

    # Add in new ship piece hint sprites: compression flags

    (0x000e13fd, b"\x40"),
    (0x000e1407, b"\x40"),
    (0x000e1411, b"\x40"),

    # Add in new ship piece hint sprites: pointers

    (0x000e13fe, b"\x00\x10\x01\x20"),
    (0x000e1408, b"\x00\x10\x03\x20"),
    (0x000e1412, b"\x00\x10\x05\x20"),

    # Add in new ship piece hint sprites: sprite data

    (0x00100120, read_bin(SPRITE_PATH / "apitemhere0.bin") +
                 read_bin(SPRITE_PATH / "apitemhere1.bin") +
                 read_bin(SPRITE_PATH / "apitemhere2.bin")),

    # Add in new ship piece sign/plinth sprites: compression flags

    (0x000e0e81, b"\x42"),
    (0x000e0e8b, b"\x42"),
    (0x000e116d, b"\x42"),
    (0x000e1177, b"\x42"),

    (0x000e0e82, b"\x00\x10\x07\x20"),
    (0x000e0e8c, b"\x00\x10\x09\x20"),
    (0x000e116e, b"\x00\x10\x0B\x20"),
    (0x000e1178, b"\x00\x10\x0D\x20"),

    # Add in new ship piece sign/plinth sprites: sprite data

    (0x00100720, read_bin(SPRITE_PATH / "shippiece0tile0.bin") +
                 read_bin(SPRITE_PATH / "shippiece0tile1.bin") +
                 read_bin(SPRITE_PATH / "shippiece1tile0.bin") +
                 read_bin(SPRITE_PATH / "shippiece1tile1.bin")),
     
    # Patch miscellaneous strings

    (0x0000b732, b"\x20\x61\x74\x00"),
    (0x0000b736, b"\x42\x2e\x4b\x2e\x00\x00\x00\x00\x00"),
    (0x0000b740, b"\x20\x61\x74\x00"),
    (0x0000b744, b"\x42\x2e\x4b\x2e\x00\x00\x00\x00\x00"),

    ### Menu modifications ###

    # "Who" menu: only one item / Toejam only / text change
    (0x00024326, b"\x00\x01"),
    (0x000242c4, b"\x00\x01"),
    (0x000242d6, b"\x4F\x6E\x65\x20\x50\x6C\x61\x79\x65\x72\x20\x2D\x2D\x20\x6A"
                 b"\x75\x73\x27\x20\x54\x6F\x65\x6A\x61\x6D\x00"),

    # "What" menu: remove Fixed World option / rename Random World to AP World / AP World uses Fixed World seeds
    (0x000243b8, b"\x00\x04"),
    (0x00024350, b"\x50\x6C\x61\x79\x20\x4E\x65\x77\x20\x47\x61\x6D\x65\x20\x2D\x2D\x20"
                 b"\x41\x50\x20\x57\x6F\x72\x6C\x64\x00\x00\x00\x00\x00"),
    (0x0002432e, b"\x00\x04")
]

with open("TJEREV02-orig.bin", "rb") as f:
    original_rom = bytearray(f.read())
    patched_rom = copy.copy(original_rom) + b"\x00"*len(original_rom)

for addr, val in STATIC_ROM_PATCHES:
    patched_rom[addr:addr+len(val)] = val

diff = bsdiff4.diff(bytes(original_rom), bytes(patched_rom))
with open("../data/base_patch.bsdiff4", "wb") as f:
    f.write(diff)