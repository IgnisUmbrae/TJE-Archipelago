; 00111200

ReturnPoint equ $00015000

    include "common.inc"

; -- begin original function block --

    move.b D1,(VAN_DROP_PRES_TBL_IDX)

; -- end original function block --

    moveq #$1,D0 ; retval to indicate success

    jmp ReturnPoint