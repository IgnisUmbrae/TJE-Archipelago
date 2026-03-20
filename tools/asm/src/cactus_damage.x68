; 0001566c

; makes the fake Earthling entity used for cactus youches use 0x19 (nonexistent in vanilla) instead of 0x1 (Devil)

    include "common.inc"

    move.b #DMG_SRC_CACTUS,-$14(A6)