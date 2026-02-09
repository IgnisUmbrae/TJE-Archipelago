;0010c100
;modified from original function at 0000a2e0

InjectionPoint equ $0000a312

    include "common.inc"

    ; restore state if in mailbox menu
    cmpi.b #2,D2
    bne.b RestoreState
    ; --begin original function block--
    move.w ($1e,SP),D2
    move.w D2,D0 ; D0 now contains player
    ext.l D0
    movea.l #VAN_MENU_ROW_TJ,A0
    clr.b (A0,D0.l)
    move.w D2,D0
    ext.l D0
    movea.l #VAN_MENU_COL_TJ,A0
    clr.b (A0,D0.l)
    move.w D2,D0
    ext.l D0
    movea.l #VAN_MENU_INV_POS_TJ,A0
    clr.b (A0,D0.l)
    ; --end original function block--
ReturnPoint:
    jmp InjectionPoint
RestoreState:
    move.w ($1e,SP),D2
    move.w D2,D0
    bra.b ReturnPoint