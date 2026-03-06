; 0010cc00

ReturnPoint equ $0000bd92

    include "common.inc"
; -- begin original function block --
    subq.b #$1,(A4,D0.l)
; -- end original function block --

    move.b #$23,AP_LAST_DMG_SOURCE

    jmp ReturnPoint