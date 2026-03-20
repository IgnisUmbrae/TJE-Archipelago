; 0010c600

ReturnPoint equ $00017030

    include "common.inc"

    ; -- begin original function block --
    jsr $000152f6
    ; -- end original function block --

    move.b #DMG_SRC_FOOD_PRESENT,AP_LAST_DMG_SOURCE

    jmp ReturnPoint