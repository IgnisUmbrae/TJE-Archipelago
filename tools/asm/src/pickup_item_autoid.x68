; 0010a100

ReturnPoint equ $00015464

    include "common.inc"

    move.b      (A2),D4
    add.b       D4,D4
    movea.l     #AP_PRES_WRAPPING,A0
    move.b      #$1,($1,A0,D4.l)
PlayPickupSound:
    pea        ($32).w
DYNRP_PSG_SFX:
    pea        ($1).w ; item pickup sound
    jsr        Fn_PlayPSGSound.l
    jmp        ReturnPoint