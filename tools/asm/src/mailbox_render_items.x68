; 0000a6c0

    include "common.inc"

    ; D2 contains player
    ; D4 is loop var for containing loop
    movea.l #AP_MAILBOX_INFO_INDEX,A0
    move.b (A0,D2),D1

    ; calc source addr
    movea.l #AP_MAILBOX_ITEM_STRS,A0
    ; mailbox
    move.b D1,D0
    mulu.w #$60,D0
    adda.l D0,A0
    ; item
    move.w D4,D0
    mulu.w #$20,D0
    adda.l D0,A0

    ; push string addr as arg to string-drawing function
    move.l A0,-(SP)
    jsr (A3)
    jmp $0000a718