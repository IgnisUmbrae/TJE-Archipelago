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
    beq.b ReadMailboxItemTypes
    addq.w #$1,D5
    bra.b FindMailboxLevelIndexLoop

    ; hereafter D5 contains index of current mailbox
ReadMailboxItemTypes:
    ; calc destination addr (per-player mailbox item list)
    movea.l #VAN_MAILBOX_ITEMS,A2
    move.b D3,D4
    mulu.w #$3,D4
    adda.l D4,A2

    ; calc source addr
    movea.l #AP_MAILBOX_ITEM_TYPES,A3
    move.b D5,D4
    mulu.w #$3,D4
    adda.l D4,A3

    ; copy data

    move.b (A3),(A2)
    move.b ($1,A3),($1,A2)
    move.b ($2,A3),($2,A2)

ReadMailboxItemPrices:
     ; calc destination addr (per-player mailbox price list)
    movea.l #VAN_MAILBOX_PRICES,A2
    move.b D3,D4
    mulu.w #$3,D4
    adda.l D4,A2

    ; calc source addr
    movea.l #AP_MAILBOX_ITEM_PRICES,A3
    move.b D5,D4
    mulu.w #$3,D4
    adda.l D4,A3

    ; copy data

    move.b (A3),(A2)
    move.b ($1,A3),($1,A2)
    move.b ($2,A3),($2,A2)   

    ; finally, store this index for later use by the mailbox menu renderer (per-player)
    movea.l #AP_MAILBOX_INFO_INDEX,A2
    move.b D5,(A2,D3)

    ; -- begin original function block --
    movem.l (SP)+,D2/D3/D4/D5/D6/A2/A3
    rts
    ; -- end original function block --