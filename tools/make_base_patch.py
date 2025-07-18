from pathlib import Path
import copy

import bsdiff4

SPRITE_PATH = Path("../data/sprites")

def read_bin(filename: Path) -> bytes:
    with filename.open("rb") as file:
        return file.read()

STATIC_ROM_PATCHES: list[tuple[int, bytes]] = [
    # Expand cartridge to 2 MB
    (0x000001a5, b"\x1f"),

    ### Initialization setup ###

    # Add jumps to all new initialization routines
    (0x0001f9a6, b"\x4E\xB9\x00\x10\xA5\x00\x4E\xB9\x00\x10\xA9\x00\x4E\xB9\x00\x10\xB3\x00\x13\xFC\x00\x01\x00\xFF\xF6\xA0"),

    # Initialize various special RAM addresses (used for remote activation, key/map collection states, etc)
    (0x0010b300, b"\x13\xFC\x00\x00\x00\xFF\xF0\x00\x13\xFC\x00\xFF\x00\xFF\xF5\x54\x13\xFC\x00\xFF\x00\xFF\xF5\x55\x42\x44\x20\x7C\x00\xFF\xF5\x56\x42\x30\x41\x10\x52\x44\xB8\x7C\x00\x02\x6F\xF4\x42\x44\x20\x7C\x00\xFF\xF4\x55\x42\x30\x41\x10\x52\x44\xB8\x7C\x00\x02\x6F\xF4\x13\xFC\x00\x00\x00\xFF\xF6\xA1\x4E\x75"),

    ### Mailbox/present menu–related ###

    # New functions to always remember inventory cursor position
    (0x0010c100, b"\x2F\x02\x34\x2F\x00\x0A\x3A\x02\x48\xC5\x20\x7C\x00\xFF\x93\x68\x22\x7C\x00\xFF\xF1\x00\x13\xB0\x58\x00\x58\x00\x20\x7C\x00\xFF\x93\x6A\x22\x7C\x00\xFF\xF1\x02\x13\xB0\x58\x00\x58\x00\x20\x7C\x00\xFF\x93\x66\x22\x7C\x00\xFF\xF1\x04\x13\xB0\x58\x00\x58\x00\x48\x78\x00\x02\x30\x02\x48\xC0\x2F\x00\x4E\xB9\x00\x00\x8F\x3A\x30\x02\x48\xC0\x20\x7C\x00\xFF\x80\x1E\x50\x8F\x11\xBC\x00\x40\x08\x00\x30\x02\x48\xC0\x20\x7C\x00\xFF\x80\x20\x11\xBC\x00\x40\x08\x00\x4E\xB9\x00\x00\x98\x88\x20\x7C\x00\xFF\x93\x68\x22\x7C\x00\xFF\xF1\x00\x11\xB1\x58\x00\x58\x00\x20\x7C\x00\xFF\x93\x6A\x22\x7C\x00\xFF\xF1\x02\x11\xB1\x58\x00\x58\x00\x20\x7C\x00\xFF\x93\x66\x22\x7C\x00\xFF\xF1\x04\x11\xB1\x58\x00\x58\x00\x24\x1F\x4E\x75\x0C\x02\x00\x02\x66\x34\x34\x2F\x00\x1E\x30\x02\x48\xC0\x20\x7C\x00\xFF\x93\x68\x42\x30\x08\x00\x30\x02\x48\xC0\x20\x7C\x00\xFF\x93\x6A\x42\x30\x08\x00\x30\x02\x48\xC0\x20\x7C\x00\xFF\x93\x66\x42\x30\x08\x00\x4E\xF9\x00\x00\xA3\x12\x34\x2F\x00\x1E\x30\x02\x60\xF2"),
    # Add jumps to these functions
    (0x000098f6, b"\x4E\xF9\x00\x10\xC1\x00"),
    (0x0000a2e4, b"\x4E\xF9\x00\x10\xC1\xB2"),

    ### Present-related ###

    # Identify all starting presents at game initialization
    (0x0010a900, b"\x42\x41\x22\x7C\x00\xFF\xDA\xC2\x24\x7C\x00\xFF\xF3\x00\x14\x31\x10\x00\x0C\x02\x00\xFF\x67\x0A"
                 b"\x48\x82\xD4\x42\x15\xBC\x00\x01\x20\x01\x14\x31\x10\x10\x0C\x02\x00\xFF\x67\x0A\x48\x82\xD4\x42"
                 b"\x15\xBC\x00\x01\x20\x01\x06\x41\x00\x01\xB2\x7C\x00\x10\x6D\xCE\x13\xFC\x00\x1C\x00\xFF\xF3\x38"
                 b"\x13\xFC\x00\x1D\x00\xFF\xF3\x3A\x13\xFC\x00\x1E\x00\xFF\xF3\x3C\x13\xFC\x00\x1F\x00\xFF\xF3\x3E"
                 b"\x13\xFC\x00\x20\x00\xFF\xF3\x40\x4E\x75"),

    # Add new AP present sprites
    (0x00100000, read_bin(SPRITE_PATH / "apitem-v2.bin")),
    (0x00100f20, read_bin(SPRITE_PATH / "apitem-important.bin")),
    (0x00101040, read_bin(SPRITE_PATH / "elevatorkeycard-arrow-v2.bin")),
    (0x00101160, read_bin(SPRITE_PATH / "map.bin")),
    (0x00101280, read_bin(SPRITE_PATH / "shippiece-v2.bin")),

    # Relocate present sprite table
    (0x00105000, b"\x00\x0A\xA1\x10\x00\x0A\xA1\x8E\x00\x0A\xA2\x10\x00\x0A\xA2\xA4\x00\x0A\xA3\x02\x00\x0A\xA3"
                 b"\x42\x00\x0A\xA3\xAC\x00\x0A\xA4\x04\x00\x0A\xA4\xBE\x00\x0A\xA5\x20\x00\x0A\xA5\xAA\x00\x0A"
                 b"\xA6\x34\x00\x0A\xA6\x9C\x00\x0A\xA7\x18\x00\x0A\xA7\xDA\x00\x0A\xA8\x58\x00\x0A\xA9\x5E\x00"
                 b"\x0A\xA9\xEA\x00\x0A\xAA\x22\x00\x0A\xAA\xC4\x00\x0A\xAB\x58\x00\x0A\xAB\xEA\x00\x0A\xAC\x4C"
                 b"\x00\x0A\xAD\x06\x00\x0A\xAD\x68\x00\x0A\xAD\xD0\x00\x0A\xA8\xDE\x00\x0A\xAE\x4A"),

    # Add new entries to sprite table
    (0x00105070, b"\x00\x10\x51\x80"),
    (0x00105074, b"\x00\x10\x51\x8e"),
    (0x00105078, b"\x00\x10\x51\x9c"),
    (0x0010507c, b"\x00\x10\x51\xaa"),
    (0x00105080, b"\x00\x10\x51\xb8"),

    # Add new sprite headers
    (0x00105180, b"\x01\x00\x00\x00\x03\x03\xF6\xEF\xF2\x42\x00\x10\x00\x00"),
    (0x0010518e, b"\x01\x00\x00\x00\x03\x03\xF6\xEF\xF2\x42\x00\x10\x0f\x20"),
    (0x0010519c, b"\x01\x00\x00\x00\x03\x03\xF6\xEF\xF2\x42\x00\x10\x10\x40"),
    (0x001051aa, b"\x01\x00\x00\x00\x03\x03\xF6\xEF\xF2\x42\x00\x10\x11\x60"),
    (0x001051b8, b"\x01\x00\x00\x00\x03\x03\xF6\xEF\xF2\x43\x00\x10\x12\x80"),

    # Patch all references to sprite table
    (0x0000a48c+2, b"\x00\x10\x50\x00"),
    (0x0000a668+2, b"\x00\x10\x50\x00"),
    (0x0000d3ac+2, b"\x00\x10\x50\x00"),
    (0x0001506e+2, b"\x00\x10\x50\x00"),
    (0x00022148+2, b"\x00\x10\x50\x00"),

    # Relocate present wrapping table in memory

    (0x00009a7c+2, b"\x00\xFF\xF3\x00"),
    (0x00009de2+2, b"\x00\xFF\xF3\x00"),
    (0x00009df4+2, b"\x00\xFF\xF3\x00"),
    (0x0000a47c+2, b"\x00\xFF\xF3\x00"),
    (0x0000a518+2, b"\x00\xFF\xF3\x00"),
    (0x0000a658+2, b"\x00\xFF\xF3\x00"),
    (0x0000a6c6+2, b"\x00\xFF\xF3\x00"),
    (0x0001427c+2, b"\x00\xFF\xF3\x00"),
    (0x00015060+2, b"\x00\xFF\xF3\x00"),
    (0x0002213a+2, b"\x00\xFF\xF3\x00"),

    # Jump to item override code to load data generated by AP
    (0x00014e04, b"\x4E\xF9\x00\x10\xB7\x00\x4E\x71"),
    (0x0010b700, b"\x4E\xB9\x00\x00\x4E\xE8\x58\x8F\x42\x81\x4E\x71\x4E\x71\x20\x7C\x00\x1A\x00\x00\x76\x1C\xC6\xC2\xD0\xC3\x18\x30\x18\x00\x20\x7C\x00\xFF\xDA\xE2\x20\x01\xC0\xFC\x00\x08\xD1\xC0\x30\x05\x48\xC0\xE1\x80\x0C\x30\x00\xFF\x08\x00\x67\x04\x11\x84\x08\x00\xD2\x7C\x00\x01\x0C\x41\x00\x1C\x6D\xC6\x20\x7C\x00\xFF\xF6\xA1\x10\xBC\x00\x01\x4E\xF9\x00\x01\x4E\x0A"),

    # New pickup routine: collects but doesn't add to inventory anything ≥ 1C, handles elevator keys/map reveals,
    # auto-identifies all presents on pickup
    (0x00015352, b"\x4e\xf9\x00\x10\xa0\x00"),
    (0x0010a000, b"\x4E\x56\xFF\xF8\x48\xE7\x3E\x30\x36\x2E\x00\x0A\x2A\x2E\x00\x0C\x38\x2E\x00\x12\x30\x03\xEF\x40\x20\x7C\x00\xFF\xA2\x5A\xD0\xC0\x26\x48\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x48\x4A\x30\x08\x00\x6D\x30\x0C\x6B\x00\x04\x00\x04\x6C\x28\x0C\x2B\x00\x03\x00\x4B\x67\x20\x0C\x2B\x00\x07\x00\x4B\x67\x18\x0C\x2B\x00\x4D\x00\x4B\x67\x10\x20\x6B\x00\x52\xC1\x88\x02\x80\x00\x04\x18\x00\xC1\x88\x67\x04\x60\x00\x02\x2A\x42\x6E\xFF\xFC\x60\x00\x02\x18\x30\x6E\xFF\xFC\x20\x08\x48\xC0\xE7\x80\x20\x40\xD1\xC5\x24\x48\x4A\x2A\x00\x02\x67\x00\x01\xFC\x42\x2E\xFF\xFF\x34\x2A\x00\x04\x48\xC2\x30\x13\x48\xC0\x94\x80\x2F\x02\x4E\xB9\x00\x02\x71\x4A\x58\x8F\x74\x10\xB4\x80\x6F\x00\x01\xAC\x34\x2A\x00\x06\x48\xC2\x30\x2B\x00\x02\x48\xC0\x94\x80\x2F\x02\x4E\xB9\x00\x02\x71\x4A\x58\x8F\x74\x08\xB4\x80\x6F\x00\x01\x8C\x0C\x12\x00\x40\x6C\x00\x00\x8C\x42\x46\x0C\x12\x00\x1C\x6C\x00\x00\x30\x30\x03\x48\xC0\xED\x80\x20\x7C\x00\xFF\xF2\x80\x32\x06\xD1\xC0\x0C\x30\x00\xFF\x10\x00\x66\x36\x30\x03\x48\xC0\xED\x80\x20\x7C\x00\xFF\xF2\x80\x32\x06\xD1\xC0\x11\x92\x10\x00\x74\x01\x1D\x42\xFF\xFF\x60\x00\x01\xB8\x4E\x71\x4E\x71\x7C\x01\x4E\xFA\x01\x8C\x2F\x0B\x4E\xB9\x00\x01\x90\x86\x4F\xEF\x00\x0C\x60\x08\x52\x46\x0C\x46\x00\x40\x6D\xAA\x0C\x46\x00\x40\x66\x00\x01\x1C\x34\x03\x48\xC2\x2F\x02\x4E\xB9\x00\x01\xE3\x12\x58\x8F\x4A\x80\x66\x00\x01\x08\x34\x03\x48\xC2\x2F\x02\x48\x78\x00\x19\x60\x00\x00\xF2\x70\x01\x1D\x40\xFF\xFF\x1D\x52\xFF\xFB\x30\x2E\xFF\xFA\x48\x80\x3D\x40\xFF\xFA\x04\x6E\x00\x40\xFF\xFA\x0C\x12\x00\x50\x66\x28\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x4A\x52\x30\x08\x00\x42\xA7\x48\x78\x00\x32\x2F\x3C\x00\x08\x23\x3C\x4E\xB9\x00\x03\xF5\xDC\x4F\xEF\x00\x0C\x60\x00\x00\x9A\x30\x2E\xFF\xFA\x20\x7C\x00\x0A\xBE\x98\x1C\x30\x00\x00\x48\x86\x6F\x52\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x52\x14\x30\x08\x00\x48\x82\x48\xC2\x30\x03\x48\xC0\x2F\x00\x4E\xB9\x00\x00\xAE\x90\x58\x8F\xB4\x80\x6D\x2E\x48\x78\x00\x01\x48\x7A\x00\xBA\x4E\x71\x34\x03\x48\xC2\x2F\x02\x4E\xB9\x00\x01\xE0\x1E\x42\xA7\x48\x78\x00\x32\x2F\x3C\x00\x04\xD7\x5A\x4E\xB9\x00\x03\xF5\xDC\x4F\xEF\x00\x18\x60\x4C\x30\x03\x48\xC0\x20\x7C\x00\xFF\xA2\x52\x12\x06\xD3\x30\x08\x00\x4A\x46\x6F\x10\x42\xA7\x48\x78\x00\x32\x2F\x3C\x00\x04\xD7\x5A\x60\x00\xFF\x6C\x48\x78\x00\x28\x48\x78\x00\x12\x4E\xB9\x00\x03\xF7\x70\x50\x8F\x34\x03\x48\xC2\x2F\x02\x30\x2E\xFF\xFA\x48\xC0\x5A\x80\x2F\x00\x4E\xB9\x00\x01\xE3\x8E\x50\x8F\x4A\x2E\xFF\xFF\x67\x28\x14\xBC\x00\xFF\x4A\x2E\x00\x17\x67\x1E\x10\x2A\x00\x01\x48\x80\xE5\x40\x20\x7C\x00\xFF\xDD\xE8\x24\x3C\x80\x00\x00\x00\x12\x2E\xFF\xFD\xE2\xAA\x85\xB0\x00\x00\x52\x6E\xFF\xFC\x30\x2E\xFF\xFC\xB0\x44\x6D\x00\xFD\xE2\x4C\xEE\x0C\x7C\xFF\xDC\x4E\x5E\x4E\x75\x49\x27\x6D\x20\x73\x74\x75\x66\x66\x65\x64\x00\x18\x12\xD8\x04\x20\x7C\x00\xFF\xF3\x00\x11\xBC\x00\x01\x48\x01\x48\x78\x00\x32\x48\x78\x00\x01\x4E\xB9\x00\x03\xF7\x70\x4E\xFA\xFE\x56\x0C\x12\x00\x1E\x66\x06\x4E\xB9\x00\x10\xBF\x00\x0C\x12\x00\x1F\x66\x06\x4E\xB9\x00\x10\xBF\x50\x4E\xFA\xFE\x30"),
    
    ### Elevator key– and map reveal–related ###

    # Override elevator door opening with jump to custom key-checking code
    (0x00013e96, b"\x4E\xF9\x00\x10\xBD\x00\x4E\x71\x4E\x71"),
    # Main key-checking code
    (0x0010bd00, b"\x0C\x03\x00\x02\x67\x50\x20\x7C\x00\x1F\x00\x00\x0C\x10\x00\x00\x67\x40\x10\x10\x12\x2A\x00\x04\x48\x81\x48\xC1\x82\xC0\x42\x41\x48\x41\x0C\x01\x00\x00\x66\x2A\x12\x39\x00\xFF\xF4\x55\x0C\x00\x00\x01\x66\x04\x06\x01\x00\x01\xC2\xC0\xB2\x2A\x00\x04\x6D\x0E\x0C\x2A\x00\x18\x00\x04\x67\x1A\x60\x08\x4E\x71\x4E\x71\x78\x00\x60\x04\x78\x02\x60\x06\x4E\xF9\x00\x01\x3E\xBE\x4E\xF9\x00\x01\x3E\xAE\x20\x7C\x00\xFF\xF4\x44\x42\x40\x12\x30\x00\x00\xB2\x3C\x00\xFF\x67\xDA\x52\x40\x0C\x40\x00\x09\x6D\xEE\x60\xD4"),

    # Key pickup code
    (0x0010bf00, b"\x20\x7C\x00\x1F\x00\x00\x0C\x10\x00\x00\x67\x3A\x22\x7C\x00\xFF\xF4\x55\x06\x11\x00\x01\x4E\x71\x12\x10\x14\x11\x4E\x71\x0C\x01\x00\x01\x66\x04\x06\x02\x00\x01\xC4\xC1\x0C\x42\x00\x19\x6C\x16\x12\x03\x48\x81\x48\xC1\x2F\x01\x06\x42\x00\x43\x2F\x02\x4E\xB9\x00\x01\xE3\x8E\x50\x8F\x4E\x75"),
    # Map reveal pickup code
    (0x0010bf50, b"\x20\x7C\x00\xFF\xF4\x56\x06\x10\x00\x01\x12\x10\x0C\x01\x00\x05\x6E\x00\x00\x86\x12\x39\x00\xFF\xF4\x57\xC2\xFC\x00\x07\x28\x7C\x00\xFF\x91\xF4\x2A\x7C\x00\xFF\x92\xAA\xD9\xC1\xDB\xC1\x42\x84\x42\x81\x20\x4C\x22\x4D\xD1\xC1\xD3\xC1\x3C\x04\xCC\xFC\x00\x07\xD0\xC6\xD2\xC6\x14\x10\x0A\x02\x00\x7E\x12\x82\x06\x41\x00\x01\x0C\x41\x00\x05\x6D\xDC\x06\x44\x00\x01\x1C\x39\x00\xFF\xF4\x56\x04\x06\x00\x01\x26\x7C\x00\x1A\x03\x00\x1C\x33\x60\x00\x48\x86\xB8\x46\x6D\xBC\xD9\x39\x00\xFF\xF4\x57\x12\x03\x48\x81\x48\xC1\x2F\x01\x20\x7C\x00\xFF\xF4\x56\x16\x10\xD6\x7C\x00\x5B\x2F\x03\x4E\xB9\x00\x01\xE3\x8E\x50\x8F\x4E\x75"),

    ### Ship piece–related ###

    # Ship piece display routine will now use a copy of the collected ship pieces
    # Copy is located at F444 in RAM and will track collection of actual ship pieces
    # Original is at E212 will track which ship piece overworld items have been triggered
    (0x00020906, b"\x26\x7c\x00\xff\xf4\x44"),

    # New function to FF out the copy at 0xF444 in RAM at initialization time
    (0x0010a500, b"\x26\x7C\x00\xFF\xF4\x44\x42\x44\x30\x04\x32\x04\x22\x7C\x00\x09\x77\x38\x17\xBC\x00\xFF\x00"
                 b"\x00\x52\x44\x0C\x44\x00\x0A\x6D\xE8\x26\x7C\x00\xFF\xE2\x12\x42\x44\x30\x04\x32\x04\x22\x7C"
                 b"\x00\x09\x77\x38\x17\xB1\x10\x00\x00\x00\x52\x44\x0C\x44\x00\x0A\x6D\xE8\x4E\x75"),

    # 1. Patch in new part of ship piece touch routine to auto-trigger ending on 10th piece collected on level 25
    # 2. Safely jump to new part of ship touch routine
    # 3. Skip vanilla ship item collection text
    (0x0010a700, b"\x20\x7C\x00\xFF\xF4\x44\x42\x44\x4E\x71\x20\x7C\x00\xFF\xF4\x44\x10\x30\x40\x00\xB0\x3C\x00"
                 b"\xFF\x67\x46\x52\x44\x0C\x44\x00\x09\x6D\xE6\x24\x7C\x00\xFF\xA2\x5A\x10\x02\xEF\x80\xD5\xC0"
                 b"\x70\x19\xB0\x2A\x00\x4C\x66\x2A\x42\x30\x40\x00\x20\x7C\x00\xFF\xE2\x12\x42\x30\x40\x00\x30"
                 b"\x02\x48\xC0\x2F\x00\x36\x03\x48\xC3\x2F\x03\x4E\xB9\x00\x02\x08\xE4\x50\x8F\x4E\x71\x4E\xF9"
                 b"\x00\x02\x0C\xFC\x20\x7C\x00\xFF\xE2\x12\x42\x30\x30\x00\x4E\xF9\x00\x02\x0C\xFC"),
    (0x00020cec, b"\x4E\xF9\x00\x10\xA7\x00\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4A\x42\x4E\x71"),
    (0x00020d00, b"\x60\x2e"),

    # Alter various ship piece–related strings
    (0x000205e8, b"\x42\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6D\x20\x6F\x6E\x20\x74\x68\x69\x73\x20\x6C\x65\x76"
                 b"\x65\x6C\x21\x00\x00\x00\x00\x00\x00\x42\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6D\x20\x6F\x6E"
                 b"\x20\x74\x6F\x65\x6A\x61\x6D\x27\x73\x20\x6C\x65\x76\x65\x6C\x21\x00\x00\x00\x00\x00\x00\x42"
                 b"\x69\x67\x20\x41\x50\x20\x69\x74\x65\x6D\x20\x6F\x6E\x20\x65\x61\x72\x6C\x27\x73\x20\x6C\x65"
                 b"\x76\x65\x6C\x21\x00\x00\x00\x00\x00\x00\x6E\x6F\x20\x62\x69\x67\x20\x41\x50\x20\x69\x74\x65"
                 b"\x6D\x73\x20\x68\x65\x72\x65\x00\x00\x00\x00\x6E\x6F\x20\x62\x69\x67\x20\x41\x50\x20\x69\x74"
                 b"\x65\x6D\x73\x20\x77\x69\x74\x68\x20\x74\x6F\x65\x6A\x61\x6D\x00\x6E\x6F\x20\x62\x69\x67\x20"
                 b"\x41\x50\x20\x69\x74\x65\x6D\x73\x20\x77\x69\x74\x68\x20\x65\x61\x72\x6C\x00\x20\x62\x69\x67"
                 b"\x20\x41\x50\x20\x69\x74\x65\x6D\x73\x20\x72\x65\x6D\x61\x69\x6E\x69\x6E\x67\x00\x00\x00\x00"
                 b"\x00"),

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

    ### Main menu modifications ###

    # "What" menu: remove Fixed World option / rename Random World to AP World / AP World uses Fixed World seeds
    (0x000243b8, b"\x00\x04"),
    (0x00024350, b"\x50\x6C\x61\x79\x20\x4E\x65\x77\x20\x47\x61\x6D\x65\x20\x2D\x2D\x20"
                 b"\x41\x50\x20\x57\x6F\x72\x6C\x64\x00\x00\x00\x00\x00"),
    (0x0002432e, b"\x00\x04"),

    ### Remote activation–related ###

    # Jump to remote activation function

    (0x00001536, b"\x4E\xF9\x00\x10\xB1\x00"),

    # Main remote activation function

    (0x0010b100, b"\x4E\xB9\x00\x01\xC5\x2A\x60\x00\x00\x26\x60\x00\x00\xDC\x60\x00\x01\x06\x60\x00\x01\x36\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\xF9\x00\x00\x15\x3C\x22\x7C\x00\xFF\xF5\x55\x0C\x11\x00\xFF\x67\x00\x00\xA4\x0C\x11\x00\x12\x67\x2C\x12\x11\x48\x81\x48\xC1\x2F\x01\x22\x7C\x00\xFF\xF0\x00\x12\x11\x48\x81\x48\xC1\x2F\x01\x4E\xB9\x00\x01\x6E\xF4\x50\x8F\x60\x3E\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x4E\x71\x48\x79\x00\x00\x00\x01\x22\x7C\x00\xFF\xF0\x00\x12\x11\x48\x81\x48\xC1\x2F\x01\x4E\xB9\x00\x00\x8F\x3A\x50\x8F\x22\x7C\x00\xFF\xF0\x00\x12\x11\x48\x81\x48\xC1\x2F\x01\x4E\xB9\x00\x00\x93\xAA\x58\x8F\x0C\x00\x00\x00\x67\x26\x22\x7C\x00\xFF\xF5\x56\x0C\x11\x00\x01\x67\x1A\x22\x7C\x00\xFF\xF0\x00\x12\x11\x4E\x71\x20\x7C\x00\xFF\xA2\x4C\x54\x70\x18\x00\x4E\x71\x4E\x71\x4E\x71\x22\x7C\x00\xFF\xF5\x55\x12\xBC\x00\xFF\x22\x7C\x00\xFF\xF5\x56\x42\x11\x60\x00\xFF\x2A\x4E\x71\x4E\x71\x4E\x71\x22\x7C\x00\xFF\xF5\x57\x0C\x11\x00\x00\x67\x1E\x12\xBC\x00\x00\x22\x7C\x00\xFF\xF0\x00\x12\x11\x48\x81\x48\xC1\x2F\x01\x4E\xB9\x00\x01\xCB\x86\x58\x8F\x4E\x71\x4E\x71\x60\x00\xFE\xFA\x22\x7C\x00\xFF\xF5\x58\x0C\x11\x00\x00\x67\x24\x4E\x71\x22\x7C\x00\xFF\xF0\x00\x12\x11\x48\x81\x48\xC1\x2F\x01\x48\x78\x00\x3A\x4E\xB9\x00\x01\xE3\x8E\x50\x8F\x22\x7C\x00\xFF\xF5\x58\x42\x11\x60\x00\xFE\xCA\x22\x7C\x00\xFF\xF5\x54\x0C\x11\x00\xFF\x67\x60\x24\x7C\x00\xFF\xF7\x00\x14\x91\x4E\x71\x15\x7C\x00\x00\x00\x01\x15\x7C\x00\xFF\x00\x02\x15\x7C\x00\xFF\x00\x03\x26\x7C\x00\xFF\xA2\x5A\x42\x81\x12\x39\x00\xFF\xF0\x00\xC2\xFC\x00\x80\xD6\xC1\x25\x53\x00\x04\x4E\x71\x4E\x71\x4E\x71\x12\xBC\x00\xFF\x4E\x71\x48\x78\x00\x00\x48\x78\x00\x01\x48\x79\x00\xFF\xF7\x00\x10\x39\x00\xFF\xF0\x00\x48\x80\x48\xC0\x2F\x00\x4E\xB9\x00\x10\xA0\x00\x60\x00\xFE\x62"),

    # Inject new code into present-opening routine

    (0x00017302, b"\x4E\xB9\x00\x10\xB5\x00\x4E\x71\x4E\x71"),
    (0x0010b500, b"\x22\x7C\x00\xFF\xF5\x56\x0C\x11\x00\x01\x67\x0A\x20\x7C\x00\xFF\xA2\x4C\x54\x70\x08\x00\x4E\x75"),

    # Disable cheat code

    (0x0001ddee, b"\x60\xCA\x4e\x71"),

    # Relocate dialogue table, add new entry pointing to RAM

    (0x00105500, b"\x03\x03\x00\x02\x69\x08\x00\x30\x00\x02\x69\x0E\x00\x01\x00\x02\x69\x19\x00\x30\x00\x02\x69\x21"
                 b"\x00\x01\x00\x02\x69\x29\x00\x30\x00\x02\x69\x31\x00\x01\x00\x02\x69\x3E\x00\x30\x00\x02\x69\x49"
                 b"\x01\x00\x00\x02\x69\x55\x00\x30\x00\x02\x69\x61\x03\x02\x00\x02\x69\x8D\x00\x20\x00\x02\x69\x93"
                 b"\x03\x02\x00\x02\x69\x8D\x00\x20\x00\x02\x69\x9F\x03\x02\x00\x02\x69\x8D\x00\x20\x00\x02\x69\xAC"
                 b"\x03\x02\x00\x02\x69\x7F\x00\x20\x00\x02\x69\xB7\x03\x02\x00\x02\x69\x87\x00\x20\x00\x02\x69\xC2"
                 b"\x03\x02\x00\x02\x69\x87\x00\x20\x00\x02\x69\xC8\x03\x02\x00\x02\x69\x7F\x00\x20\x00\x02\x69\xD1"
                 b"\x03\x02\x00\x02\x69\x7F\x00\x20\x00\x02\x69\xDC\x03\x02\x00\x02\x69\x87\x00\x20\x00\x02\x69\xE9"
                 b"\x03\x02\x00\x02\x69\x87\x00\x20\x00\x02\x69\xF4\x03\x02\x00\x02\x69\x7F\x00\x20\x00\x02\x69\xFA"
                 b"\x03\x02\x00\x02\x69\x71\x00\x20\x00\x02\x6A\x01\x03\x02\x00\x02\x69\x6D\x00\x20\x00\x02\x6A\x0C"
                 b"\x03\x02\x00\x02\x69\x6D\x00\x20\x00\x02\x6A\x19\x03\x02\x00\x02\x69\x71\x00\x20\x00\x02\x6A\x25"
                 b"\x03\x02\x00\x02\x69\x77\x00\x20\x00\x02\x6A\x32\x03\x02\x00\x02\x6A\x3E\x00\x20\x00\x02\x6A\x46"
                 b"\x00\x02\x00\x02\x6A\x54\x00\x20\x00\x02\x6A\x59\x01\x02\x00\x02\x6A\x4D\x00\x20\x00\x02\x6A\x59"
                 b"\x03\x02\x00\x02\x6A\x64\x00\x20\x00\x02\x6A\x69\x03\x02\x00\x02\x6A\x72\x00\x20\x00\x02\x6A\x7A"
                 b"\x03\x02\x00\x02\x6A\x83\x00\x20\x00\x02\x6A\x89\x03\x02\x00\x02\x6A\x92\x00\x20\x00\x02\x6A\x98"
                 b"\x03\x02\x00\x02\x69\x29\x00\x20\x00\x02\x6A\xA2\x03\x02\x00\x02\x6A\x3E\x00\x20\x00\x02\x6A\xAF"
                 b"\x03\x02\x00\x02\x6A\xBC\x00\x20\x00\x02\x6A\xC4\x03\x02\x00\x02\x6A\xDC\x00\x20\x00\x02\x6A\xE6"
                 b"\x03\x02\x00\x02\x6A\xF0\x00\x20\x00\x02\x6A\xFD\x03\x02\x00\x02\x6B\x09\x00\x20\x00\x00\x00\x00"
                 b"\x03\x02\x00\x02\x6B\x16\x00\x20\x00\x02\x6B\x1F\x03\x02\x00\x02\x6B\x28\x00\x20\x00\x00\x00\x00"
                 b"\x03\x02\x00\x02\x6B\x35\x00\x20\x00\x02\x6B\x3A\x03\x02\x00\x02\x6B\x46\x00\x20\x00\x02\x69\x21"
                 b"\x03\x02\x00\x02\x6B\x4D\x00\x20\x00\x02\x6B\x59\x03\x02\x00\x02\x6B\x64\x00\x20\x00\x02\x6B\x71"
                 b"\x03\x02\x00\x02\x6B\x7B\x00\x20\x00\x02\x6B\x85\x03\x02\x00\x02\x6B\x90\x00\x20\x00\x02\x6B\x99"
                 b"\x03\x02\x00\x02\x6B\xA0\x00\x20\x00\x02\x6B\xAD\x03\x02\x00\x02\x6B\xB8\x00\x20\x00\x00\x00\x00"
                 b"\x03\x02\x00\x02\x6B\xCF\x00\x20\x00\x02\x69\x29\x03\x02\x00\x02\x6B\xDA\x00\x20\x00\x00\x00\x00"
                 b"\x03\x02\x00\x02\x6B\xE7\x00\x20\x00\x02\x6B\xED\x03\x02\x00\x02\x6B\xF5\x00\x20\x00\x02\x6C\x00"
                 b"\x03\x02\x00\x02\x6C\x06\x00\x20\x00\x02\x6C\x13\x03\x02\x00\x02\x6A\xCF\x00\x20\x00\x00\x00\x00"
                 b"\x03\x02\x00\x02\x6C\x20\x00\x20\x00\x02\x6C\x20\x03\x02\x00\x02\x69\x21\x00\x20\x00\x00\x00\x00"
                 b"\x03\x02\x00\x02\x6C\x25\x00\x20\x00\x02\x6C\x2F\x03\x02\x00\x02\x6C\x35\x00\x20\x00\x02\x6A\x54"
                 b"\x03\x02\x00\x02\x6C\x40\x00\x20\x00\x02\x6A\x4D\x03\x02\x00\x02\x6C\x4C\x00\x20\x00\x00\x00\x00"
                 b"\x03\x00\x00\x02\x69\x08\x00\x20\x00\x02\x69\x0E\x03\x02\x00\x02\x6C\x58\x00\x20\x00\x02\x6C\x62"),

    (0x001057b8, b"\x03\x02\x00\xFF\xF6\x00\x00\x20\x00\xFF\xF6\x0C"),
    (0x0001e3c0+2, b"\x00\x10\x55\x00"),

    # Add custom dialogue: table entries + ASCII strings
    (0x001057c4, b"\x03\x02\x00\x10\x5A\x00\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x0C\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x18\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x22\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x2B\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x36\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x40\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x4B\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x54\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x60\x00\x20\x00\x10\x5A\x6A\x03\x02\x00\x10\x5A\x72\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\x7C\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\x86\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\x90\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\x9A\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xA4\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xAE\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xB8\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xC2\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xCD\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xD8\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xE3\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xEE\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5A\xF9\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x04\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x0F\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x1A\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x25\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x30\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x3B\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x46\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x51\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x5C\x00\x20\x00\x10\x5B\x67\x03\x02\x00\x10\x5B\x73\x00\x20\x00\x10\x5B\xB1\x03\x02\x00\x10\x5B\x7E\x00\x20\x00\x10\x5B\xB1\x03\x02\x00\x10\x5B\x8A\x00\x20\x00\x10\x5B\xB1\x03\x02\x00\x10\x5B\x97\x00\x20\x00\x10\x5B\xB1\x03\x02\x00\x10\x5B\xA4\x00\x20\x00\x10\x5B\xB1\x03\x02\x00\x10\x5B\xBA\x00\x20\x00\x10\x5B\xC4\x03\x02\x00\x10\x5B\xD1\x00\x20\x00\x10\x5B\xDD"),
    (0x00105a00, b"\x57\x69\x6E\x64\x73\x68\x69\x65\x6C\x64\x21\x00\x4C\x2E\x20\x73\x70\x65\x61\x6B\x65\x72\x21\x00\x46\x75\x6E\x6B\x20\x61\x6D\x70\x21\x00\x41\x6D\x70\x20\x66\x69\x6E\x21\x00\x46\x72\x6F\x6E\x74\x20\x6C\x65\x67\x21\x00\x52\x65\x61\x72\x20\x6C\x65\x67\x21\x00\x53\x6E\x6F\x77\x62\x6F\x61\x72\x64\x21\x00\x43\x61\x70\x73\x75\x6C\x65\x21\x00\x52\x2E\x20\x73\x70\x65\x61\x6B\x65\x72\x21\x00\x54\x68\x72\x75\x73\x74\x65\x72\x21\x00\x6A\x61\x6D\x6D\x69\x6E\x27\x00\x4C\x76\x20\x32\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x33\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x34\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x35\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x36\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x37\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x38\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x39\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x30\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x31\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x32\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x33\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x34\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x35\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x36\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x37\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x38\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x31\x39\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x32\x30\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x32\x31\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x32\x32\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x32\x33\x20\x6B\x65\x79\x21\x00\x4C\x76\x20\x32\x34\x20\x6B\x65\x79\x21\x00\x27\x76\x61\x74\x6F\x72\x20\x6F\x70\x65\x6E\x00\x4C\x76\x31\x2D\x35\x20\x6D\x61\x70\x21\x00\x4C\x76\x36\x2D\x31\x30\x20\x6D\x61\x70\x21\x00\x4C\x76\x31\x31\x2D\x31\x35\x20\x6D\x61\x70\x21\x00\x4C\x76\x31\x36\x2D\x32\x30\x20\x6D\x61\x70\x21\x00\x4C\x76\x32\x31\x2D\x32\x35\x20\x6D\x61\x70\x21\x00\x6C\x65\x74\x27\x73\x20\x67\x6F\x00\x6E\x6F\x20\x6B\x65\x79\x2E\x2E\x2E\x00\x77\x68\x65\x72\x65\x20\x69\x73\x20\x69\x74\x3F\x00\x6E\x65\x65\x64\x20\x39\x20\x73\x68\x69\x70\x00\x70\x69\x65\x63\x65\x73\x20\x66\x69\x72\x73\x74\x00"),
]

with open("TJEREV02-orig.bin", "rb") as f:
    original_rom = bytearray(f.read())
    patched_rom = copy.copy(original_rom) + b"\x00"*len(original_rom)

for addr, val in STATIC_ROM_PATCHES:
    patched_rom[addr:addr+len(val)] = val

diff = bsdiff4.diff(bytes(original_rom), bytes(patched_rom))
with open("../data/base_patch.bsdiff4", "wb") as f:
    f.write(diff)