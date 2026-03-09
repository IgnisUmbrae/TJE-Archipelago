; 00009bf6

    include "common.inc"

    ; -- begin original function block --
    movem.l A2/D5/D4/D3/D2,-(SP)
    move.w ($1a,SP),D3 ; player arg
    ; -- end original function block --

    ; get menu row for player in D5
    movea.l #VAN_MENU_ROW,A0
    move.b (A0,D3.l),D5

    ; get price of selected item in D0
    movea.l #VAN_MAILBOX_PRICES,A0
    move.b D3,D1
    mulu.w #$3,D1
    adda.l D1,A0
    move.b (A0,D5.w),D0

    ; fail if item is sold out (price = $FF)
    cmpi.b #-1,D0
    beq.b ItemSoldOut

    ; fail if we don't have enough
    movea.l #VAN_PLAYER_BUCKS,A0
    cmp.b (A0,D3.w),D0
    bgt.b NotEnoughBucks

GetItem:
    ; otherwise subtract price
    sub.b D0,(A0,D3.w)
    ; write row number and level to special addresses for AP client to pick up
    move.b D5,(AP_MAILBOX_ITEM_BOUGHT).l
    movea.l #VAN_LEVEL_LOADED,A0
    move.b (A0,D3.l),(AP_MAILBOX_ITEM_LEVEL).l

    ; mark item as already bought
    movea.l #AP_MAILBOX_INFO_INDEX,A0
    move.b (A0,D2),D1
    mulu.w #$3,D1
    add.w D5,D1
    movea.l #AP_MAILBOX_ITEMS_BOUGHT,A0
    move.b #-1,(A0,D1)

BuySuccess:
    ; success text
    pea ($1).w
    pea (Str_GotIt,PC)
    bra.b SayTextAndReturn

NotEnoughBucks:
    pea ($32).w
DYNRP_PSG_SFX_1:
    pea ($1a).w ; super-denied sound
    jsr Fn_PlayPSGSound
    addq.l #$8,SP

    ; failure text
    pea ($1).w
    pea (Str_NeedBucks,PC)
    bra.b SayTextAndReturn
ItemSoldOut:
    pea ($32).w
DYNRP_PSG_SFX_2:
    pea ($1a).w ; super-denied sound
    jsr Fn_PlayPSGSound
    addq.l #$8,SP
    pea ($1).w
    pea (Str_SoldOut,PC)

SayTextAndReturn:
    ; player arg
    move.w D3,D0
    ext.l D0
    move.l D0,-(SP)
    jsr Fn_SayText

    ; -- begin original function block --
    lea ($c,SP),SP
    movem.l (SP)+,D2/D3/D4/D5/A2
    rts
    ; -- end original function block --

Str_GotIt:
    dc.b "Got it!",0
Str_NeedBucks:
    dc.b "Need Bucks",0
Str_SoldOut:
    dc.b "sold out..",0