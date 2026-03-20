; 0010cd00

ReturnDrawNumber equ $0000a718
ReturnNoNumber equ $0000a73c

    include "common.inc"

    ; D2 contains player
    ; D4 is loop var for the containing loop
    movea.l #AP_MAILBOX_INFO_INDEX,A0
    move.b (A0,D2),D1

    ; check price of item; if sold out ($FF), render special string + no number
    movea.l #VAN_MAILBOX_PRICES,A0
    ; correct char
    move.b D2,D0
    mulu.w #$3,D0
    adda.l D0,A0
    ; correct item
    cmpi.b #-1,(A0,D4)
    beq.b SoldOutItem

    ; calc source addr for item name into A0
    movea.l #AP_MAILBOX_ITEM_STRS,A0
    ; correct mailbox
    move.b D1,D0
    mulu.w #$60,D0
    adda.l D0,A0
    ; correct item
    move.w D4,D0
    mulu.w #$20,D0
    adda.l D0,A0

InStockItem:
    ; push string addr as arg to string-drawing function
    move.l A0,-(SP)
    jsr Fn_MenuDrawString
    ; jump to number-drawing routine
    jmp ReturnDrawNumber
SoldOutItem:
    pea (Str_SoldOut,PC)
    jsr Fn_MenuDrawString
    addq.l #$4,SP ; not sure why this stack realignment is needed, but it is
    ; skip over number-drawing routine
    jmp ReturnNoNumber

Str_SoldOut:
    dc.b "         --SOLD OUT!--         ",0