;0000b898

    include "common.inc"

    ; --begin original function block--
    movem.l D4/D3/D2,-(SP)
    move.w ($12,SP),D2 ; grab rank from args
    ; --end original function block--

    ; D3 will eventually be the return value
    clr.w D3
    ; if rank < 8, read from patched-in threshold list
    cmpi.w #$8,D2
    bge.b Return
    movea.l #AP_SCALED_RANK_PTS,A0
    adda.w D2,A0
    adda.w D2,A0
    move.w (A0),D3

Return:
    ; --begin original function block--
    move.w D3,D0
    ext.l D0
    movem.l (SP)+,D2/D3/D4
    rts
    ; --end original function block--