;0010f000

    include "common.inc"

    movem.l D1/D2/D3/D4/A1,-(SP)

    move.l ($18,SP),D2 ; player arg
    move.l ($1c,SP),D3 ; trap type arg

    ; check whether player is dead or in elevator; fail to activate if so
    move.l D2,-(SP)
    jsr AP_CAN_OPEN_PRESENT
    addq.l #$4,SP
    tst.b D0 ; zero indicates success
    bne ReturnFailure

CheckCupidTrap:
    cmpi.b #AP_TRAP_CUPID,D3
    bne.b CheckBurpTrap
GiveCupidTrap:
    move.l D2,-(SP)
    jsr Fn_InitiateCupidHearts
    addq.l #$4,SP
    bra OutputDialogueAndReturn

CheckBurpTrap:
    cmpi.b #AP_TRAP_BURP,D3
    bne.b CheckSleepTrap
GiveBurpTrap:
    movea.l #VAN_BURP_TIMER,A1
    move.b #$20,(A1,D2)
    movea.l #VAN_BURPS_REMAINING,A1
    move.b (A1,D2),D4
    add.b #$0f,D4
    move.b D4,(A1,D2)
    bra OutputDialogueAndReturn

CheckSleepTrap:
    cmpi.b #AP_TRAP_SLEEP,D3
    bne.b CheckSkatesTrap
GiveSleepTrap:
    move.b #$18,D4 ; school book present
    bra OpenPresentAsTrap

CheckSkatesTrap:
    cmpi.b #AP_TRAP_SKATES,D3
    bne.b CheckEarthlingTrap
GiveSkatesTrap:
    move.b #$05,D4 ; rocket skates present
    bra OpenPresentAsTrap

CheckEarthlingTrap:
    cmpi.b #AP_TRAP_EARTHLING,D3
    bne.b CheckRandomizerTrap
GiveEarthlingTrap:
    move.b #$17,D4 ; earthling present
    bra OpenPresentAsTrap

CheckRandomizerTrap:
    cmpi.b #AP_TRAP_RANDOMIZER,D3
    bne.b CheckDownfallTrap
GiveRandomizerTrap:
    ; force-open inventory
    pea ($1).l
    move.b D2,D4
    ext.w D4
    ext.l D4
    move.l D4,-(SP)
    jsr Fn_OpenOrCloseMenu
    addq.l #$8,SP

    ; open randomizer present in more direct manner
    move.b D2,D4
    ext.w D4
    ext.l D4
    move.l D4,-(SP)
    jsr Fn_OpenRandomizerPresent
    addq.l #$4,SP   
    bra ReturnSuccess ; dialogue exists for this, but cannot be seen due to the menu

CheckDownfallTrap:
    cmpi.b #AP_TRAP_DOWNFALL,D3
    bne.b ReturnFailure

    ; push player arg
    move.b D2,D4
    ext.w D4
    ext.l D4
    move.l D4,-(SP)

    ; calculate entity info table addr for player
    movea.l #VAN_ENTITY_INFO_TABLE,A1
    move.w D2,D4
    asl.w #$7,D4
    adda.w D4,A1
    ; push addr as arg
    move.l A1,-(SP)
    jsr AP_POOF_DOWN_SAFE
    addq.l #$8,SP
    bra OutputDialogueAndReturn

OutputDialogueAndReturn:
    ; player arg
    move.b D2,D4
    ext.w D4
    ext.l D4
    move.l D4,-(SP)

    ; dialogue sequence id
    move.b #$64,D4 ; beginning of trap dialogue block
    add.b D3,D4
    ext.w D4
    ext.l D4
    move.l D4,-(SP)    
    jsr Fn_QueueDialogueSequence
    addq.l #$8,SP
    bra ReturnSuccess

OpenPresentAsTrap:
    ; present type arg
    ext.w D4
    ext.l D4
    move.l D4,-(SP)
    ; player arg
    move.b D2,D4
    ext.w D4
    ext.l D4
    move.l D4,-(SP)
    
    jsr Fn_OpenPresent
    addq.l #$8,SP

    ; immediately subtract the 2 points given by the open present function if it was successful (return value = 0)
    tst.b D0
    bne.b SkipPointSubtraction
    movea.l #VAN_PLAYER_POINTS,A1
    sub.w #$2,(A1,D2)
SkipPointSubtraction:
    bra OutputDialogueAndReturn

ReturnSuccess:
    moveq.l #$0,D0
    bra Return
ReturnFailure:
    moveq.l #$1,D0
Return:
    movem.l (SP)+,A1/D4/D3/D2/D1
    rts