; 00111000


    include "common.inc"

    movem.l D0/D4/A2,-(SP)

    move.l ($10,SP),A2 ; entity info for player arg
    move.l ($14,SP),D4 ; player arg

    ; poof to appropriate level
    move.b ($4c,A2),D0
    ; if the player's on level 1, check lemonade state; nonzero ⇒ already completed
    ; this check is patched out if the lemonade check is disabled
DYNRP_level_1_dropdown_check:
    cmpi.b #$1,D0
    bne.b CheckLevel0
    movea.l #VAN_LEMONADE_STATE,A2
    tst.b (A2,D4)
    beq.b StartPoof
CheckLevel0:
    ; if on level 0, poof "up" to highest level reached
    tst.b D0
    beq.b PoofToHighestReached
    ; otherwise poof to level - 1 as usual
    subq.b #$1,D0
    bra.b StartPoof
PoofToHighestReached:
    movea.l #VAN_MAX_LEVEL_REACHED,A2
    move.b (A2,D4),D0
StartPoof:
    move.b D0,(AP_POOF_DEST_LEVEL)
    ; push args & commence poof
    move.w D4,D0
    ext.l D0
    move.l D0,-(SP)
    jsr Fn_UnfallWarp
    addq.l #$4,SP

    movem.l (SP)+,A2/D4/D0
    rts