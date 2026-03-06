; 0010c500

ReturnPoint equ $0001c706

    include "common.inc"

    ; -- begin original function block --
    clr.w ($a,A2)
    clr.w ($10,A2)
    ; -- end original function block --

    ; register tomato as last damage source
    move.b #$1b,AP_LAST_DMG_SOURCE

    jmp ReturnPoint