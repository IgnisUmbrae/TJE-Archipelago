;0010b100
;handles: (1) present opening (2) trap activating (3) dialogue emitting
;         (4) ground item collecting (5) present dropping (6) ship piece collecting

ReturnPoint equ $00001518

    include "common.inc"

    ;-- begin original function block --
    jsr        $0000219C
    ;-- end original function block --

CheckAutoPresent:
    ; check for activation (non-$FF)
    movea.l    #AP_OPEN_PRES,A1
    cmpi.b     #-1,(A1)
    beq.w      CheckAutoTrap

    ; special handling if present is randomizer
    cmpi.b     #$12,(A1)
    beq.b      OpenRandomizerPresent
    ; otherwise go via the standard present-opening routine
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_OpenPresent
    addq.l     #$8,SP
    bra.b      ResetFlagAndContinue
OpenRandomizerPresent:
    ; force-open inventory and then activate the randomizer
    pea        ($1).l
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_OpenOrCloseMenu
    addq.l     #$8,SP
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_OpenRandomizerPresent
    addq.l     #$4,SP
ResetFlagAndContinue:
    move.b     #-1,(AP_OPEN_PRES)
    ; *zero* return value indicates success
    tst.b      D0
    bne.b      CheckAutoTrap
    addi.w     #$1,(AP_ITEM_RECEIVED)

CheckAutoTrap:
    ; check for activation (non-$FF), get active char & call trap handler with trap ID & player args
    movea.l    #AP_GIVE_TRAP,A1
    cmpi.b     #-1,(A1)
    beq.b      CheckAutoDialogue
    
    ; trap type arg
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)

    ; player arg
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)

    jsr        AP_TRAP_HANDLER
    addq.l     #$8,SP
    ; reset activation flag
    move.b     #-1,(AP_GIVE_TRAP)
    ; always assume trap is successfully received (no logic issues if not)
    addi.w     #$1,(AP_ITEM_RECEIVED)

CheckAutoDialogue:
    ; check for activation (non-zero), get active char & output requested dialogue (via entry $3a, which points to RAM)
    ; the AP client is expected to write the dialogue into RAM before triggering this
    tst.b      (AP_DIALOGUE_TRIGGER)
    beq.b      CheckAutoGroundItem
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    pea        ($3a).w
    jsr        Fn_QueueDialogueSequence
    addq.l     #$8,SP
    clr.b      (AP_DIALOGUE_TRIGGER)

CheckAutoGroundItem:
    ; check for activation (non-$FF)
    movea.l    #AP_GIVE_ITEM,A1
    cmpi.b     #-1,(A1)
    beq.b      CheckAutoDropPres
    ; create simplified phantom ground item entry in RAM
    movea.l    #AP_PHANTOM_ITEM,A2
    move.b     (A1),(A2) ; object type → specified type
    move.b     (VAN_LEVEL_LOADED),($1,A2) ; level → receiving player's current level
    move.b     #-1,($2,A2) ; entity id → $FF
    move.b     #$aa,($3,A2) ; z sort → $aa, magic value used to signify an auto-awarded item
    movea.l    #VAN_ENTITY_INFO_TABLE,A3
    clr.l      D1
    move.b     (AP_ACTIVE_CHAR).l,D1
    mulu.w     #$80,D1
    adda.w     D1,A3
    move.l     (A3),($4,A2) ; item (x,y) position → player (x,y) position
    ; reset flag
    move.b     #-1,(A1)
    ; force pickup
    pea        ($0).w ; not dropped present
    pea        ($1).w ; table size = 1, i.e. only check this singular item
    pea        (AP_PHANTOM_ITEM).l
    move.b     (AP_ACTIVE_CHAR).l,D0
    ext.w      D0
    ext.l      D0
    move.l     D0,-(SP)
    jsr        Fn_PickupItem
    ;tst.b      D0
    ;beq.b      CheckAutoDropPres

    ; these items are always successfully received
    addi.w     #$1,(AP_ITEM_RECEIVED)

CheckAutoDropPres:
    ; check for activation (non-$FF)
    movea.l    #AP_DROP_PRES,A1
    cmpi.b     #-1,(A1)
    beq.b      CheckAutoShipPiece
    ; get active character, output "oops..."" / "too many" dialogue & drop specified present for character
    move.b     (AP_ACTIVE_CHAR).l,D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    pea        ($19).w
    jsr        Fn_QueueDialogueSequence
    addq.l     #$8,SP
    movea.l    #AP_DROP_PRES,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    move.b     (AP_ACTIVE_CHAR).l,D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_DropPresent
    addq.l     #$8,SP
    ; reset flag
    move.b     #-1,(AP_DROP_PRES)
    ; nonzero return value indicates success
    tst.b      D0
    beq.b      CheckAutoShipPiece
    addi.w     #$1,(AP_ITEM_RECEIVED)

CheckAutoShipPiece:
    movea.l    #AP_GIVE_SHIPPIECE,A1
    cmpi.b     #-1,(A1)
    beq.b      Return
    ; Zero out relevant ship piece
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    movea.l    #AP_SHIP_PIECES_GOT,A1
    clr.b      (A1,D1)
    ; output dialogue (entries begin at 0x3b)
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    move.b     #$3b,D1
    add.b      (AP_GIVE_SHIPPIECE),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_QueueDialogueSequence
    addq.l     #$8,SP
    ; reset flag
    move.b     #-1,(AP_GIVE_SHIPPIECE)
    ; this item is always successfully received
    addi.w     #$1,(AP_ITEM_RECEIVED)

Return:  
    jmp        ReturnPoint