;0010b900

ReturnPointWarp equ $00010b12
ReturnPointNoWarp equ $00010b24

    include "common.inc"

    ; A2 contains address of player data

    ; if current level is max-2 (default: 23) or lower, we can upwarp
DYNRP_last_level_minus_one:
    moveq #$18,D0
    cmp.b ($4c,A2),D0
    bgt.b RetWithWarp

    ; forbid upwarp if we're already on the max level (default: 25)
DYNRP_last_level:
    moveq #$19,D0
    cmp.b ($4c,A2),D0
    beq.b RetNoWarp

    ; otherwise we're 1 level from the top so prepare to check if we have all the ship pieces
    movea.l #AP_SHIP_PIECES_GOT,A0
    clr.w D4
CheckNumShipPiecesLoop:
    move.b (A0,D4.w),D1
    cmp.b #-1,D1
    beq.b RetNoWarp
    addq.w #$1,D4
    cmpi.w #$9,D4
    blt.b CheckNumShipPiecesLoop

RetWithWarp:
    jmp ReturnPointWarp
RetNoWarp:
    jmp ReturnPointNoWarp