;0010a500

    include "common.inc"

   ; initialize collected ship pieces to all empty ($FF)
    movea.l    #AP_SHIP_PIECES_GOT,A3
    clr.w      D4
InitShipPiecesLoop:
    move.w     D4,D0
    move.w     D4,D1
    move.b     #-1,(A3,D0.w)
    addq.w     #$1,D4
    cmpi.w     #$a,D4
    blt.b      InitShipPiecesLoop

    ; copy ship item levels over to the appropriate vanilla location
    ; (the AP patch overwrites the fixed world ship pieces with the randomly-genned ones)
    movea.l    #VAN_SHIP_PIECE_LEVELS,A3
    clr.w      D4
CopyShipItemLevelsLoop:
    move.w     D4,D0
    move.w     D4,D1
    movea.l    #VAN_FIXED_WORLD_SHIP_PIECES,A1
    move.b     (A1,D1.w),(A3,D0.w)
    addq.w     #$1,D4
    cmpi.w     #$a,D4
    blt.b      CopyShipItemLevelsLoop

    rts