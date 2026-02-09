;0010a000
;relocated & modified from original at 00015352

    include "common.inc"
    
    ; --begin original function block--
    link.w     A6,#-8
    movem.l    A3/A2/D6/D5/D4/D3/D2,-(SP)
    ; various sanity checks on player state to ensure it's sensible to pick up an item
    move.w     ($a,A6),D3
    move.l     ($c,A6),D5
    move.w     ($12,A6),D4
    move.w     D3,D0
    asl.w      #$7,D0
    movea.l    #VAN_ENTITY_INFO_TABLE,A0
    adda.w     D0,A0
    movea.l    A0,A3
    move.w     D3,D0
    ext.l      D0
    movea.l    #VAN_PLAYER_LIVES,A0
    tst.b      (A0,D0.l)
    blt.b      DoNotPickup
    cmpi.w     #$4,($4,A3)
    bge.b      DoNotPickup
    cmpi.b     #$3,($4b,A3)
    beq.b      DoNotPickup
    cmpi.b     #$7,($4b,A3)
    beq.b      DoNotPickup
    cmpi.b     #$4d,($4b,A3)
    beq.b      DoNotPickup
    movea.l    ($52,A3),A0
    exg        D0,A0
    andi.l     #$41800,D0
    exg        D0,A0
    beq.b      FindCloseMapObject
DoNotPickup:
    bra.w      ReturnPoint
FindCloseMapObject: ; loop through all nonempty map objects and find which ones are close to the player
    clr.w      -$4(A6)
    bra.w      FindCloseMapObject_LoopCondition
CheckDistanceToObject:
    ; check if map object has nonzero ID (i.e. it exists)
    movea.w    -$4(A6),A0
    move.l     A0,D0
    ext.l      D0
    asl.l      #$3,D0
    movea.l    D0,A0
    adda.l     D5,A0
    movea.l    A0,A2
    tst.b      ($2,A2)
    beq.w      FindCloseMapObject_CounterIncrement

    ; if so, check distance to map object
    ; x distance < 16?
    clr.b      -$1(A6)
    move.w     ($4,A2),D2
    ext.l      D2
    move.w     (A3),D0
    ext.l      D0
    sub.l      D0,D2
    move.l     D2,-(SP)
    jsr        Fn_MathAbs.l
    addq.l     #$4,SP
    moveq      #$10,D2
    cmp.l      D0,D2
    ble.w      MarkAsCollected

    ; y distance < 8?
    move.w     ($6,A2),D2
    ext.l      D2
    move.w     ($2,A3),D0
    ext.l      D0
    sub.l      D0,D2
    move.l     D2,-(SP)
    jsr        Fn_MathAbs.l
    addq.l     #$4,SP
    moveq      #$8,D2
    cmp.l      D0,D2
    ble.w      MarkAsCollected
    ; check if object is a present or AP item (type < $40)
    cmpi.b     #$40,(A2)
    bge.w      PickupNonPresent
    clr.w      D6
    ; -- end original function block --

    ; check if object is AP item, skip adding to inv if so
    cmpi.b     #$1c,(A2)
    bge.w      SetMarkCollectedFlag
    ; otherwise it's a normal present
FindEmptyInvSlot:
    move.w     D3,D0
    ext.l      D0
    asl.l      #$4,D0 ; repatched to #$6 if expanded_inventory enabled
    movea.l    #AP_INVENTORIES,A0
    move.w     D6,D1
    adda.l     D0,A0
    ; is this inv slot empty?
    cmpi.b     #-1,(A0,D1.w)
    bne.b      FindEmptyInvSlot_LoopCondition
    ; put present in player inventory
    move.w     D3,D0
    ext.l      D0
    asl.l      #$4,D0 ; repatched to #$6 if expanded_inventory enabled
    movea.l    #AP_INVENTORIES,A0
    move.w     D6,D1
    adda.l     D0,A0
    move.b     (A2),(A0,D1.w)
    moveq      #$1,D2
SetMarkCollectedFlag:
    move.b     D2,-$1(A6)
    bra.w      CheckIfElevKey
APItemPostAwardCleanup:
    ; because the AP items are technically 'presents', the game expects an inventory slot index (D6) of less than
    ; the inventory size in order to correctly mark it as collected, so 1 has been chosen arbitrarily
    ; this value is only used to pass the check in CheckForFullInventory
    nop
    nop
    moveq      #$1,D6
    bra.w      AutoIdentifyPresent
ExtraUnknownCheck:
    move.l     A3,-(SP)
    jsr        $00019086.l ; unknown Earthling-related check
    lea        ($c,SP),SP
    bra.b      CheckForFullInventory
FindEmptyInvSlot_LoopCondition:
    addq.w     #$1,D6
    cmpi.w     #$10,D6 ; repatched to AP_INVENTORY_SIZE if expanded_inventory enabled
    blt.b      FindEmptyInvSlot
CheckForFullInventory:
    cmpi.w     #$10,D6 ; repatched to AP_INVENTORY_SIZE if expanded_inventory enabled
    bne.w      MarkAsCollected
    move.w     D3,D2
    ext.l      D2
    move.l     D2,-(SP)
    jsr        $0001e312.l ; unknown additional "full inventory" check 
    addq.l     #$4,SP
    tst.l      D0
    bne.w      MarkAsCollected
    move.w     D3,D2
    ext.l      D2
    move.l     D2,-(SP)
    pea        ($19).w ; "oops…" "too many"
    bra.w      OutputDialogue
PickupNonPresent:
    ; check if food or buck
    moveq      #$1,D0
    move.b     D0,-$1(A6)
    move.b     (A2),-$5(A6)
    move.w     -$6(A6),D0
    ext.w      D0
    move.w     D0,-$6(A6)
    subi.w     #$40,-$6(A6)
    cmpi.b     #$50,(A2)
    bne.b      PickupFood
    ; award buck
    move.w     D3,D0
    ext.l      D0
    movea.l    #VAN_PLAYER_BUCKS,A0
    addq.b     #$1,(A0,D0.l)
    clr.l      -(SP)
    pea        ($32).w
    move.l     #Sfx_Money,-(SP)
OutputSound:
    jsr        Fn_PlayPCMSound.l
    lea        ($c,SP),SP
    bra.w      PrepCorrectDialogue
PickupFood:
    move.w     -$6(A6),D0
    movea.l    #VAN_FOOD_TO_HP_TABLE,A0
    move.b     (A0,D0.w),D6
    ext.w      D6
    ble.b      EatFood
    move.w     D3,D0
    ext.l      D0
    movea.l    #VAN_PLAYER_HP,A0
    move.b     (A0,D0.l),D2
    ext.w      D2
    ext.l      D2
    move.w     D3,D0
    ext.l      D0
    move.l     D0,-(SP)
    jsr        Fn_GetMaxHP.l
    addq.l     #$4,SP
    cmp.l      D0,D2
    blt.b      EatFood
    ; already at max health
    pea        ($1).w
    pea        (Str_ImStuffed,PC)
    nop
    move.w     D3,D2
    ext.l      D2
    move.l     D2,-(SP)
    jsr        Fn_SayText.l
    clr.l      -(SP)
    pea        ($32).w
    move.l     #Sfx_Eat,-(SP)
    jsr        Fn_PlayPCMSound.l
    lea        ($18,SP),SP
    bra.b      MarkAsCollected
EatFood:
    move.w     D3,D0
    ext.l      D0
    movea.l    #VAN_PLAYER_HP,A0
    move.b     D6,D1
    add.b      D1,(A0,D0.l)
    tst.w      D6
    ble.b      EatBadFood
    clr.l      -(SP)
    pea        ($32).w
    move.l     #Sfx_Eat,-(SP)
    bra.w      OutputSound
EatBadFood:
    pea        ($28).w
    pea        ($12).w ; bad food sound
    jsr        Fn_PlayPSGSound.l
    addq.l     #$8,SP
PrepCorrectDialogue:
    move.w     D3,D2
    ext.l      D2
    move.l     D2,-(SP)
    move.w     -$6(A6),D0
    ext.l      D0
    addq.l     #$5,D0
    move.l     D0,-(SP)
OutputDialogue:
    jsr        Fn_QueueDialogueSequence.l
    addq.l     #$8,SP
MarkAsCollected:
    ; check if this present was dropped by the player, don't alter collected object table if so
    tst.b      -$1(A6)
    beq.b      FindCloseMapObject_CounterIncrement
    move.b     #-1,(A2)
    tst.b      ($17,A6)
    beq.b      FindCloseMapObject_CounterIncrement
    move.b     ($1,A2),D0
    ext.w      D0
    asl.w      #$2,D0
    movea.l    #VAN_COLLECTED_OBJ_TABLE,A0
    move.l     #$80000000,D2
    move.b     -$3(A6),D1
    lsr.l      D1,D2
    or.l       D2,(A0,D0.w)
FindCloseMapObject_CounterIncrement:
    addq.w     #$1,-$4(A6)
FindCloseMapObject_LoopCondition:
    move.w     -$4(A6),D0
    cmp.w      D4,D0
    blt.w      CheckDistanceToObject
ReturnPoint:
    movem.l    -$24(A6),D2/D3/D4/D5/D6/A2/A3
    unlk       A6
    rts
Str_ImStuffed:
    dc.b "I'm stuffed",0
AutoIdentifyPresent:
    move.b     (A2),D4
    add.b      D4,D4
    movea.l    #AP_PRES_WRAPPING,A0
    move.b     #$1,($1,A0,D4.l)
    pea        ($32).w
    pea        ($1).w ; item pickup sound
    jsr        Fn_PlayPSGSound.l
    bra.w      ExtraUnknownCheck
CheckIfElevKey:
    cmpi.b     #$1e,(A2)
    bne.b      CheckIfMapReveal
    jsr        AP_PICKUP_ELEV_KEY.l
CheckIfMapReveal:
    cmpi.b     #$1f,(A2)
    bne.b      ReturnFromAPItemChecks
    jsr        AP_PICKUP_MAP_REV.l
ReturnFromAPItemChecks:
    bra.w      APItemPostAwardCleanup
