; 0010c900

ReturnPoint equ $000164a2

    include "common.inc"
; -- begin original function block --
    movea.l #$aefba,A0
; -- end original function block --

    move.b #$1d,AP_LAST_DMG_SOURCE

    jmp ReturnPoint