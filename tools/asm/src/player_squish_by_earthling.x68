; 0010cb00

ReturnPoint equ $0001b36a

    include "common.inc"

    ; -- begin original function block --
    move.b #$03,($15,A3)
    ; -- end original function block --

    ; store earthling type as last damage source
    move.b (A2),(AP_LAST_DMG_SOURCE)
    jmp ReturnPoint