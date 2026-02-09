;0010bf00

    include "common.inc"

    ; D3 → player
    
    ; do nothing if elevator keys are disabled (set to 0)
    movea.l #AP_KEY_INTERVAL,A0
    cmpi.b #$0,(A0)
    beq.b ReturnFromPickupKey
    ; award 1 key
    movea.l #AP_NUM_KEYS,A1
    addi.b #$1,(A1)
    move.b (A0),D1 ; key gap
    move.b (A1),D2 ; keys owned
    ; key interval of 1 is special ⇒ start key counts from 1 instead of 0 to keep later calculations aligned
    cmpi.b #$1,D1
    bne.b OutputKeyDialogue
    addi.b #$1,D2

OutputKeyDialogue:
    ; check if level to unlock is > 24, nothing to unlock if so
    mulu.w D1,D2
    cmpi.w #$19,D2
    bge.b ReturnFromPickupKey
    ; otherwise output correct dialogue [dialogue table entry $45 is "Lv2 key!"]
    move.b D3,D1
    ext.w D1
    ext.l D1
    move.l D1,-(SP)
    addi.w #$43,D2
    move.l D2,-(SP)
    jsr Fn_QueueDialogueSequence
    addq.l #$8,SP
ReturnFromPickupKey:
    rts
