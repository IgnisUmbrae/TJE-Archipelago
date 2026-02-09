;0010bd00

ReturnPointEBE equ $00013ebe
ReturnPointEAE equ $00013eae

    include "common.inc"

    ; A2 → address to relevant elevator, ($4,A2) → elevator level
    ; D3 → previous elevator state
    ; D4 → used to configure new elevator state

    ; return without change if elevator state = $02 (doors opening)
    cmpi.b #$2,D3
    beq.b ReturnNoSound

    ; do nothing if elevator keys are disabled (set to 0)
    movea.l #AP_KEY_INTERVAL,A0
    cmpi.b #$0,(A0)
    beq.b OpenDoorsNormally

    ; calculate (elevator level % key interval)
    move.b (A0),D0 ; key interval
    move.b ($4,A2),D1 ; level of elevator interacted with
    ext.w D1
    ext.l D1
    divu.w D0,D1
    clr.w D1
    swap D1
    ; nonzero remainder indicates non-locked elevator so open doors
    cmpi.b #$0,D1
    bne.b OpenDoorsNormally

    ; prepare to check keys
    move.b (AP_NUM_KEYS),D1
    ; key interval of 1 is special ⇒ start key counts from 1 instead of 0 to keep later calculations aligned
    cmpi.b #$1,D0
    bne.b CheckSufficientKeys
    addi.b #$1,D1
CheckSufficientKeys:
    ; check if (num keys × interval) ≥ elevator level, keep doors closed if not
    ; if we have enough keys, open elevator unless on level 24, in which case check for 9 ship pieces first
    mulu.w D0,D1
    cmp.b ($4,A2),D1
    blt.b KeepDoorsClosed
    cmpi.b #$18,($4,A2)
    beq.b CheckNumShipPieces
    bra.b OpenDoorsNormally
KeepDoorsClosed:
    moveq #$0,D4
    bra.b ReturnNoSound
OpenDoorsNormally:
    moveq #$2,D4
    bra.b ReturnPlaySound
ReturnNoSound:
    jmp ReturnPointEBE
ReturnPlaySound:
    jmp ReturnPointEAE
CheckNumShipPieces:
    ; loop through ship pieces, ensure first 9 are collected ($FF)
    movea.l #AP_SHIP_PIECES_GOT,A0
    clr.w D0
LoopThroughShipPieces:
    move.b (A0,D0.w),D1
    cmp.b #-1,D1
    beq.b KeepDoorsClosed
    addq.w #$1,D0
    cmpi.w #$9,D0
    blt.b LoopThroughShipPieces
    ; we have the first 9, open the doors
    bra.b OpenDoorsNormally
