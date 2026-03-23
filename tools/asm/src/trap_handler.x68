;0010f000

    include "common.inc"

    movem.l D1/D2/A1,-(SP)

    move.l ($10,SP),D2 ; player arg
    move.l ($14,SP),D1 ; trap type arg
CheckCupidTrap:
    cmpi.b #AP_TRAP_CUPID,D1
    bne.b CheckBurpTrap
GiveCupidTrap:
    move.l D2,-(SP)
    jsr Fn_InitiateCupidHearts
    addq.l #$4,SP
    bra Return

CheckBurpTrap:
    cmpi.b #AP_TRAP_BURP,D1
    bne.b CheckSleepTrap
GiveBurpTrap:
    ; not sure why this is needed, but the game internally sets this to $FF on opening rootbeer
    movea.l #VAN_BURP_TIMER,A1
    move.b #-1,(A1,D2)
    movea.l #VAN_BURPS_REMAINING,A1
    move.b (A1,D2),D1
    ; TODO: add random number of burps
    addi.b #$10,D1
    move.b D1,(A1,D2)
    bra Return

CheckSleepTrap:
    cmpi.b #AP_TRAP_SLEEP,D1
    bne.b CheckSkatesTrap
GiveSleepTrap:
    move.b #$18,D1 ; school book present
    bra OpenPresentAsTrap

CheckSkatesTrap:
    cmpi.b #AP_TRAP_SKATES,D1
    bne.b CheckEarthlingTrap
GiveSkatesTrap:
    move.b #$05,D1 ; rocket skates present
    bra OpenPresentAsTrap

CheckEarthlingTrap:
    cmpi.b #AP_TRAP_EARTHLING,D1
    bne.b CheckRandomizerTrap
GiveEarthlingTrap:
    move.b #$17,D1 ; earthling present
    bra OpenPresentAsTrap

CheckRandomizerTrap:
    cmpi.b #AP_TRAP_RANDOMIZER,D1
    bne.b Return
GiveRandomizerTrap:
    movea.l #AP_ACTIVE_CHAR,A1
    move.b (A1),D1

    ; force-open inventory
    pea ($1).l
    ext.w D1
    ext.l D1
    move.l D1,-(SP)
    jsr Fn_OpenOrCloseMenu
    addq.l #$8,SP

    ; open randomizer present in more direct manner
    movea.l #AP_ACTIVE_CHAR,A1
    move.b (A1),D1
    ext.w D1
    ext.l D1
    move.l D1,-(SP)
    jsr Fn_OpenRandomizerPresent
    addq.l #$4,SP
    ; jsr 0000A1CC
    bra Return

Return:
    movem.l (SP)+,A1/D2/D1
    rts

OpenPresentAsTrap:
    ext.w D1
    ext.l D1
    move.l D1,-(SP)
    movea.l #AP_ACTIVE_CHAR,A1
    move.b (A1),D1
    ext.w D1
    ext.l D1
    move.l D1,-(SP)
    jsr Fn_OpenPresent
    addq.l #$8,SP
    bra Return