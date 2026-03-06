; 0010c600

ReturnPoint equ $00017030

    include "common.inc"

    ; -- begin original function block --
    jsr $000152f6
    ; -- end original function block --

    ; register 'opening bad food present' as last source of damage
    move.b #$4a,AP_LAST_DMG_SOURCE

    jmp ReturnPoint