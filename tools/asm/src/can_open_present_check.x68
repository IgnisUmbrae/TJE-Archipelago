; 00111500
; recreates the check at the beginning of the vanilla Fn_OpenPresent
; returns 0 if player state allows present opening, 1 otherwise

    include "common.inc"

    movem.l A0,-(SP)

    move.l ($8,SP),D0 ; player arg

    ; check if player is in elevator
    movea.l #VAN_LOCK_IN_ELEV_FLAG,A0
    tst.b (A0,D0)
    bne.b Return1

    ; check if player is dead
    movea.l #VAN_ENTITY_INFO_TABLE,A0
    asl.l #$7,D0
    adda.l D0,A0
    ; ghost sprite
    cmpi.b #$5,($4b,A0)
    beq.b Return1
    ; waving ghost sprite
    cmpi.b #$6,($4b,A0)
    beq.b Return1

Return0:
    moveq #$0,D0
    bra.b Return
Return1:
    moveq #$1,D0
Return:
    movem.l (SP)+,A0
    rts