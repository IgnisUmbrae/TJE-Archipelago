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

    ; add extra AP items and ground items into present wrapping table (for mailbox rendering)
    movea.l #AP_PRES_WRAPPING_EXTRA,A1
    moveq #$1c,D0
IdentifyAllExtraPresentsLoop:
    move.b D0,(A1)
    adda.l #$2,A1
    addq #$1,D0
    cmpi.b #$51,D0 ; #$50 = A Buck, the last item in the game
    blt IdentifyAllExtraPresentsLoop
    rts
