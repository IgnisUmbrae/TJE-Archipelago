;00016fb8

OpenActionPresent equ $00017224

    include "common.inc"

    ; D3 contains player

    ; -- begin original function block --
    move.w D3,D4
	ext.l D4
	add.l D4,D4
    ; -- end original function block --
    ; award points
	movea.l #VAN_PLAYER_POINTS,A2
	move.w (A2,D4),D0
DYNRP_promotion_point_value_minus_two:
	addi.w #$32,D0
	move.w D0,(A2,D4)

    ; output dialogue
    move.w D3,D0
    ext.l D0
    move.l D0,-(SP)
    pea ($63).w
    jsr Fn_QueueDialogueSequence
    addq.l #$8,SP

    ; continue function as normal
    jmp OpenActionPresent