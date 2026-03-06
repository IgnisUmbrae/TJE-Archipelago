; 0010c800

ReturnPoint equ $000165e4

    include "common.inc"
; -- begin original function block --
    addq.l #$8,SP
    clr.b (A0,D0.l)
; -- end original function block --

    move.b #$1d,AP_LAST_DMG_SOURCE

    jmp ReturnPoint