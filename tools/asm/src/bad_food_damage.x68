; 0010c300

ReturnPoint equ $0001557c

    include "common.inc"

    move.b      (A2),AP_LAST_DMG_SOURCE
    pea         ($28).w
DYNRP_PSG_SFX:
    pea         ($12).w ; bad food sound
    jmp         ReturnPoint