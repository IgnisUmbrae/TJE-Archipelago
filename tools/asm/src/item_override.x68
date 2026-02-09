;0010b700

    include "common.inc"

InjectionReturnPoint equ $00014e0c

    ; --begin original function block (from Fn_AddObjectsToLevel @ $00014b90)--
    jsr Fn_SetRandomSeed.l
    addq.l #$4,SP
    ; --end original function block--

    clr.l D1
MainLoop:
    ;calculate address for item at index D1 inside AP item list
    ;D2 contains the level number
    movea.l #AP_ITEM_LIST,A0
    moveq #$1c,D3
    mulu.w D2,D3
    adda.w D3,A0
    move.b (A0,D1.l),D4
    
    ;calculate offset for coresponding object type byte inside map object table
    movea.l #VAN_MAP_OBJECT_TABLE,A0
    move.l D1,D0
    mulu.w #$8,D0
    adda.l D0,A0
    move.w D5,D0
    ext.l D0
    asl.l #$8,D0

    ;check if item is already collected
    cmpi.b #-1,(A0,D0.l)
    beq.b AlreadyCollected
    ;set object if not
    move.b D4,(A0,D0.l)
AlreadyCollected:
    ;loop until all 28 items set
    addq.w #$1,D1
    cmpi.w #$1c,D1
    blt.b MainLoop
    ;set flag for client to read
    movea.l #AP_LEVEL_ITEMS_SET,A0
    move.b #$1,(A0)
    jmp InjectionReturnPoint