; 0010c700

ReturnPoint equ $00016c6e

    include "common.inc"
; -- begin original function block --
    subq.b #$2,(A0,D0.l)
; -- end original function block --

    move.b #$1c,AP_LAST_DMG_SOURCE

    jmp ReturnPoint