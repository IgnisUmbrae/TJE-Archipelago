;0010a300

    include "common.inc"

    ; A2 contains address of player info
    ; D4 contains player

    ; set lives to 4
    movea.l #VAN_PLAYER_LIVES,A1
    move.b #$4,(A1,D4.l)

    ; unset game over flag
    andi.b #$7f,($4d,A2)

    ; unset movement-locking flag in case drop occurs in elevator or similar
    movea.l #VAN_LOCK_IN_ELEV_FLAG,A1
    clr.b (A1,D4.l)

    move.l D4,-(SP)
    move.l A2,-(SP)
    jsr AP_POOF_DOWN_SAFE
    addq.l #$8,SP
    rts