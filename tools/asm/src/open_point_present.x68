;0010d400

    include "common.inc"

    movem.l D0/D4/A2,-(SP)
    move.w ($10,SP),D4 ; player arg

    ext.l D4
    add.l D4,D4

    ; award points
	movea.l #VAN_PLAYER_POINTS,A2
	move.w (A2,D4),D0
DYNRP_point_present_value_minus_two:
	addi.w #$32,D0
	move.w D0,(A2,D4)

    ; output dialogue
    move.w D4,D0
    ext.l D0
    move.l D0,-(SP)
    pea ($63).w
    jsr Fn_QueueDialogueSequence
    addq.l #$8,SP

    movem.l (SP)+,A2/D4/D0

    rts