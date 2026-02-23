;0010a700

ReturnPoint equ $00020cfc

    include "common.inc"

    ; D2 contains player
    ; D3 contains index of which ship piece has just been collected

    ; write triggered ship piece level to memory
    movea.l #VAN_SHIP_PIECE_LEVELS,A0
    move.b (A0,D3),D4
    movea.l #AP_BIG_ITEM_LV,A0
    move.b D4,(A0)

    ; check if player already has 9 ship pieces
    clr.w      D4
Check9ShipPiecesLoop:
    movea.l    #AP_SHIP_PIECES_GOT,A0
    move.b     (A0,D4.w),D0
    cmp.b      #-$1,D0
    beq.b      AwardNoDisplay
    addq.w     #$1,D4
    cmpi.w     #$9,D4
    blt.b      Check9ShipPiecesLoop

    ; check if player is on level 25
    movea.l    #VAN_ENTITY_INFO_TABLE,A2
    move.b     D2,D0
    asl.l      #$7,D0
    adda.l     D0,A2
    moveq      #$19,D0 ; ⚠ this is repatched elsewhere if max_level is changed
    cmp.b      ($4c,A2),D0
    bne.b      AwardNoDisplay

    ; this is level 25 → clear ship piece and ship item then call CollectedShipPieces to trigger ending transition
    clr.b      (A0,D4.w)
    movea.l    #VAN_SHIP_PIECE_LEVELS,A0
    clr.b      (A0,D4.w)
    ; push player arg
    move.w     D2,D0
    ext.l      D0
    move.l     D0,-(SP)
    ; push index arg
    move.w     D3,D3
    ext.l      D3
    move.l     D3,-(SP)
    jsr        Fn_ShowCollectedShipPieces
    addq.l     #$8,SP
    jmp        ReturnPoint
    ; award ship piece without displaying collection screen
AwardNoDisplay:
    movea.l    #VAN_SHIP_PIECE_LEVELS,A0
    clr.b      (A0,D3.w)
    jmp        ReturnPoint