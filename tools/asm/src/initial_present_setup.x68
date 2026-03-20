; 0010d700

    include "common.inc"

ReturnPointLoop equ $000142b2
ReturnPointExitLoop equ $00014308

    cmpi.w #$1a,D3
    bne.b BaseLoopCondition
    addi.w #$2,D3 ; to skip over the 2 fixed ones (Mystery / Bonus Hitops)
DYNRP_total_pres_types:
BaseLoopCondition:
    cmpi.w #$1c,D3
    ble.b RetLoop
    jmp ReturnPointExitLoop
RetLoop:
    jmp ReturnPointLoop