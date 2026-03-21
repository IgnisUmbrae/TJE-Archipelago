; 0010e000

ReturnPoint equ $00014282

    include "common.inc"

    ; set consistent random seed so the present wrapping is consistent between reloads
    movea.l #VAN_FIXED_WORLD_SEEDS,A2
    move.l (A2),-(SP)
    jsr Fn_SetRandomSeed
    addq.l #$4,SP

    movea.l #AP_PRES_WRAPPING,A2

    jmp ReturnPoint