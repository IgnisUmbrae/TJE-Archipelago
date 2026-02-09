;0010b100

ReturnPoint equ $0000153c

    include "common.inc"

    ; relocated from injection point
    jsr        Fn_ProcessFallingTomatoes
    bra.w      AutoOpenPresents
BranchToCheckCupidTrap:
    bra.w      AutoCupidTrap
BranchToCheckDialogue:  
    bra.w      AutoDialogueOutput
BranchToCheckGroundItem:  
    bra.w      AutoAwardGroundItem
BranchToCheckDropPres:  
    bra.w      AutoDropPresent
JumpToReturnPoint:  
    jmp        ReturnPoint
AutoOpenPresents:
    ; check for activation (non-$FF)
    movea.l    #AP_OPEN_PRES,A1
    cmpi.b     #-1,(A1)
    beq.w      ReturnFromAutoPresentOpening
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
    bra.b      AddPointsIfNeeded
OpenRandomizerPresent:
    ; force-open inventory and then activate the randomizer
    pea        ($1).l
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_OpenPresentSelectionMenu
    addq.l     #$8,SP
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_OpenRandomizerPresent
    addq.l     #$4,SP
AddPointsIfNeeded:
    ; add points if no-points-flag is not set
    cmpi.b     #0,D0
    beq.b      ResetFlags
    movea.l    #AP_NO_PRES_POINTS_FLAG,A1
    cmpi.b     #1,(A1)
    beq.b      ResetFlags
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    movea.l    #VAN_PLAYER_POINTS,A0
    addq.w     #$2,(A0,D1.l)
ResetFlags:
    ; reset both open-present and no-points flags
    movea.l    #AP_OPEN_PRES,A1
    move.b     #-1,(A1)
    movea.l    #AP_NO_PRES_POINTS_FLAG,A1
    clr.b      (A1)
ReturnFromAutoPresentOpening:
    bra.w      BranchToCheckCupidTrap
AutoCupidTrap:
    ; check for activation (nonzero), get active char & give cupid effect
    movea.l    #AP_CUPID_TRAP,A1
    cmpi.b     #$0,(A1)
    beq.b      ReturnFromAutoCupidTrap
    move.b     #$0,(A1)
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    jsr        Fn_InitiateCupidHearts
    addq.l     #$4,SP
ReturnFromAutoCupidTrap:
    bra.w      BranchToCheckDialogue
AutoDialogueOutput:
    ; check for activation (non-$FF), get active char & output requested dialogue (via entry $3a, which points to RAM)
    ; the AP client is expected to write the dialogue into RAM before triggering this
    movea.l    #AP_DIALOGUE_TRIGGER,A1
    cmpi.b     #$0,(A1)
    beq.b      ReturnFromAutoDialogueOutput
    movea.l    #AP_ACTIVE_CHAR,A1
    move.b     (A1),D1
    ext.w      D1
    ext.l      D1
    move.l     D1,-(SP)
    pea        ($3a).w
    jsr        Fn_QueueDialogueSequence
    addq.l     #$8,SP
    movea.l    #AP_DIALOGUE_TRIGGER,A1
    clr.b      (A1)
ReturnFromAutoDialogueOutput:
    bra.w      BranchToCheckGroundItem
AutoAwardGroundItem:
    ; check for activation (non-$FF)
    movea.l    #AP_GIVE_ITEM,A1
    cmpi.b     #-1,(A1)
    beq.b      ReturnFromAutoAwardGroundItem
    ; create simplified phantom ground item entry in RAM
    movea.l    #AP_PHANTOM_ITEM,A2
    move.b     (A1),(A2) ; object type → specified type
    move.b     #$0,($1,A2) ; level → 0
    move.b     #-1,($2,A2) ; entity id → $FF
    move.b     #-1,($3,A2) ; z sort → $FF
    movea.l    #VAN_ENTITY_INFO_TABLE,A3
    clr.l      D1
    move.b     (AP_ACTIVE_CHAR).l,D1
    mulu.w     #$80,D1
    adda.w     D1,A3
    move.l     (A3),($4,A2) ; (x,y) position → player (x,y) position
    ; reset flag to $FF
    move.b     #-1,(A1)
    ; force pickup
    pea        ($0).w
    pea        ($1).w
    pea        (AP_PHANTOM_ITEM).l
    move.b     (AP_ACTIVE_CHAR).l,D0
    ext.w      D0
    ext.l      D0
    move.l     D0,-(SP)
    jsr        AP_PICKUP_ITEM
ReturnFromAutoAwardGroundItem:
    bra.w      BranchToCheckDropPres
AutoDropPresent:
    ; check for activation (non-$FF)
    movea.l    #AP_DROP_PRES,A1
    cmpi.b     #-1,(A1)
    beq.b      ReturnFromAutoDropPresent
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
    movea.l    #AP_DROP_PRES,A1
    move.b     #-1,(A1)
ReturnFromAutoDropPresent:
    bra.w      JumpToReturnPoint