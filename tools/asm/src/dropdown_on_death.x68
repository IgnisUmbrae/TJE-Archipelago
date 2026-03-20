;0010a300

    include "common.inc"

    ; A2 contains address of player info
    ; D4 contains player

    ; set downward motion
    ;movea.l #VAN_FALLING_STATE,A1
    ;move.b #$1,(A1,D4.l)

    ; set lives to 4
    movea.l #VAN_PLAYER_LIVES,A1
    move.b #$4,(A1,D4.l)

    ; unset game over flag
    andi.b #$7f,($4d,A2)

    ; unset movement-locking flag in case drop occurs in elevator or similar
    movea.l #VAN_LOCK_IN_ELEV_FLAG,A1
    clr.b (A1,D4.l)

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
;DYNRP_level_0_dropdown_check:
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
    rts