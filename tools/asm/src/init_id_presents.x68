;0010a900

    include "common.inc"

    clr.w D1
DYNRP_inventory_addr:
    movea.l #VAN_INVENTORIES,A1
    movea.l #AP_PRES_WRAPPING,A2
CheckTJInv:
    move.b (A1,D1.w),D2
    cmpi.b #-1,D2
    beq.b CheckEarlInv
    ext.w D2
    add.w D2,D2
    move.b #$1,($1,A2,D2.w)
CheckEarlInv:
DYNRP_inventory_size_1:
    move.b ($10,A1,D1.w),D2
    cmpi.b #-1,D2
    beq.b IncCounter
    ext.w D2
    add.w D2,D2
    move.b #$1,($1,A2,D2.w)
IncCounter:
    addq.w #$1,D1
DYNRP_inventory_size_2:
    cmpi.w #$10,D1
    blt.b CheckTJInv

    ; add extra AP items into present wrapping table
    move.b #$1c,($00fff338).l
    move.b #$1d,($00fff33a).l
    move.b #$1e,($00fff33c).l
    move.b #$1f,($00fff33e).l
    move.b #$20,($00fff340).l
    rts
