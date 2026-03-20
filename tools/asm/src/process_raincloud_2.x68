; 0010c800

ReturnPoint equ $00016c14

    include "common.inc"
; -- begin original function block --
    move.b #$2,(A0,D0.l)
; -- end original function block --

    move.b #DMG_SRC_RAINCLOUD,AP_LAST_DMG_SOURCE

    jmp ReturnPoint