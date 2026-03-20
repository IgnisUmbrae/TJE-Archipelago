; 0001d1a8

; makes the fake Earthling entity used for rosebush youches use 0x1A (nonexistent in vanilla) instead of 0x1 (Devil)

    include "common.inc"

    move.b #DMG_SRC_ROSEBUSHES,-$14(A6)