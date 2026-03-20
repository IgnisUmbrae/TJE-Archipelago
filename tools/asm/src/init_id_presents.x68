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

    ; add all other items into present wrapping table for mailbox rendering purposes
    movea.l #AP_PRES_WRAPPING,A1
DYNRP_total_pres_types:
    moveq #POINT_PRESENT,D0
    addq #$1,D0
    ; align just past end of used present wrapping area
    adda.l D0,A1
    adda.l D0,A1
IdentifyAllExtraPresentsLoop:
    move.b D0,(A1)
    adda.l #$2,A1
    addq #$1,D0
    cmpi.b #GROUND_SHIP_PIECE,D0
    ble.b IdentifyAllExtraPresentsLoop
    rts
