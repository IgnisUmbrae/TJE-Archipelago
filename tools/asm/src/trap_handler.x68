;0010f000

    include "common.inc"

    movem.l D0/D1/D2/D3/A1,-(SP)

    move.l ($18,SP),D2 ; player arg
    move.l ($1c,SP),D3 ; trap type arg
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
    move.b (A1,D2),D0
    add.b #$0F,D0
    move.b D0,(A1,D2)
    bra OutputDialogueAndReturn

CheckSleepTrap:
    cmpi.b #AP_TRAP_SLEEP,D3
    bne.b CheckSkatesTrap
GiveSleepTrap:
    move.b #$18,D0 ; school book present
    bra OpenPresentAsTrap

CheckSkatesTrap:
    cmpi.b #AP_TRAP_SKATES,D3
    bne.b CheckEarthlingTrap
GiveSkatesTrap:
    move.b #$05,D0 ; rocket skates present
    bra OpenPresentAsTrap

CheckEarthlingTrap:
    cmpi.b #AP_TRAP_EARTHLING,D3
    bne.b CheckRandomizerTrap
GiveEarthlingTrap:
    move.b #$17,D0 ; earthling present
    bra OpenPresentAsTrap

CheckRandomizerTrap:
    cmpi.b #AP_TRAP_RANDOMIZER,D3
    bne.b ReturnNoDialogue
GiveRandomizerTrap:
    ; force-open inventory
    pea ($1).l
    move.b D2,D0
    ext.w D0
    ext.l D0
    move.l D0,-(SP)
    jsr Fn_OpenOrCloseMenu
    addq.l #$8,SP

    ; open randomizer present in more direct manner
    move.b D2,D0
    ext.w D0
    ext.l D0
    move.l D0,-(SP)
    jsr Fn_OpenRandomizerPresent
    addq.l #$4,SP
    bra ReturnNoDialogue ; dialogue exists for this, but cannot be seen due to the menu

OpenPresentAsTrap:
    ; present type arg
    ext.w D0
    ext.l D0
    move.l D0,-(SP)
    ; player arg
    move.b D2,D0
    ext.w D0
    ext.l D0
    move.l D0,-(SP)
    
    jsr Fn_OpenPresent
    addq.l #$8,SP

    ; immediately subtract the 2 points given by the open present function
    movea.l #VAN_PLAYER_POINTS,A1
    sub.w #$2,(A1,D2)

OutputDialogueAndReturn:
    ; player arg
    move.b D2,D0
    ext.w D0
    ext.l D0
    move.l D0,-(SP)

    ; dialogue sequence id
    move.b #$64,D0 ; beginning of trap dialogue block
    add.b D3,D0
    ext.w D0
    ext.l D0
    move.l D0,-(SP)    
    jsr Fn_QueueDialogueSequence
    addq.l #$8,SP
ReturnNoDialogue:
    movem.l (SP)+,A1/D3/D2/D1/D0
    rts
