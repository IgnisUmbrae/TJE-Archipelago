;0010c100
;modified from original function at 000098f6

    include "common.inc"

    ; --begin original function block--
    move.l D2,-(SP)
    move.w ($0a,SP),D2
    ; --end original function block--

    ; temporarily store row/col/inv scroll pos for later restoration
    move.w D2,D5
    ext.l D5 ; contains player as long
    movea.l #VAN_MENU_ROW_TJ,A0
    movea.l #AP_MENU_ROW_TJ,A1
    move.b (A0,D5.l),(A1,D5.l)
    movea.l #VAN_MENU_COL_TJ,A0
    movea.l #AP_MENU_COL_TJ,A1
    move.b (A0,D5.l),(A1,D5.l)
    movea.l #VAN_MENU_INV_POS_TJ,A0
    movea.l #AP_MENU_INV_POS_TJ,A1
    move.b (A0,D5.l),(A1,D5.l)
    
    ; --begin original function block--
    pea ($2).w
    move.w D2,D0
    ext.l D0
    move.l D0,-(SP)
    jsr Fn_OpenPresentSelectionMenu
    move.w D2,D0
    ext.l D0
    movea.l #$00ff801e,A0
    addq.l #8,SP
    move.b #$40,(A0,D0.l)
    move.w D2,D0
    ext.l D0
    movea.l #$00ff8020,A0
    move.b #$40,(A0,D0.l)
    jsr Fn_MenuLoop
    ; --end original function block--
    
    ; restore temporarily stored row/col/inv scroll pos
    movea.l #VAN_MENU_ROW_TJ,A0
    movea.l #AP_MENU_ROW_TJ,A1
    move.b (A1,D5.l),(A0,D5.l)
    movea.l #VAN_MENU_COL_TJ,A0
    movea.l #AP_MENU_COL_TJ,A1
    move.b (A1,D5.l),(A0,D5.l)
    movea.l #VAN_MENU_INV_POS_TJ,A0
    movea.l #AP_MENU_INV_POS_TJ,A1
    move.b (A1,D5.l),(A0,D5.l)
    
    ; --begin original function block--
    move.l (SP)+,D2
    rts
    ; --end original function block--