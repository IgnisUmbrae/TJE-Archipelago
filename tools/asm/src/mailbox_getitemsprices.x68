; 00008e54

    include "common.inc"

    ; -- begin original function block --
    movem.l A3/A2/D6/D5/D4/D3/D2,-(SP)
    move.w ($22,SP),D3 ; player arg
    move.w ($26,SP),D0 ; level arg
    ; -- end original function block --

    ; find where current level falls in list of mailbox levels

    movea.l #AP_MAILBOX_LEVEL_LIST,A2
    clr.w D5
FindMailboxLevelIndexLoop:
    move.b (A2,D5.w),D1
    cmp.b D1,D0
    beq.b ReadMailboxInfoLoopPre
    addq.w #$1,D5
    bra.b FindMailboxLevelIndexLoop
    ; hereafter D5 contains index of current mailbox

ReadMailboxInfoLoopPre:
    clr.w D2
ReadMailboxInfoLoop:
    ; calc destination addrs into A1 & A2
    movea.l #VAN_MAILBOX_PRICES,A1
    movea.l #VAN_MAILBOX_ITEMS,A2
    move.b D3,D4
    mulu.w #$3,D4
    adda.l D4,A2
    adda.l D4,A1

    ; calc source addrs into A3 & A4
    movea.l #AP_MAILBOX_ITEM_PRICES,A3
    movea.l #AP_MAILBOX_ITEM_TYPES,A4
    move.b D5,D4
    mulu.w #$3,D4
    adda.l D4,A4
    adda.l D4,A3

    ; check if item is sold out
    movea.l #AP_MAILBOX_ITEMS_BOUGHT,A0
    move.b D5,D4
    mulu.w #$3,D4
    add.w D2,D4
    cmpi.b #-1,(A0,D4)
    beq.b CopySoldOutPrice

CopyNormalPrice:
    move.b (A3,D2),(A1,D2) ; normal price
    bra.b CopyType
CopySoldOutPrice:
    move.b #-1,(A1,D2) ; sold out price
CopyType:
    move.b (A4,D2),(A2,D2) ; item type

    addq.w #$1,D2
    cmpi.w #$3,D2
    blt.b ReadMailboxInfoLoop

    ; finally, store the index for later use by the mailbox menu renderer (per-player)
    movea.l #AP_MAILBOX_INFO_INDEX,A2
    move.b D5,(A2,D3)

    ; -- begin original function block --
    movem.l (SP)+,D2/D3/D4/D5/D6/A2/A3
    rts
    ; -- end original function block --