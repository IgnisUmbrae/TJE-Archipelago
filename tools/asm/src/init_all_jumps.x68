;0001f9a6

    include "common.inc"

    jsr AP_EXTRA_INIT
    jsr AP_SHIP_PIECE_INIT
    jsr AP_PRES_ID_INIT
    move.b #1,(AP_INIT_COMPLETE).l