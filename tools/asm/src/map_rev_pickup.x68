;0010bf50

    include "common.inc"

    ; D3 → player
    ; A0 → revealed map tiles
    ; A1 → transparent map tiles

    ; award map reveal
    movea.l #AP_NUM_MAP_REVS,A0
    addi.b #$1,(A0)
    move.b (A0),D1
    ; do nothing if we already had 5 map reveals
    cmpi.b #$5,D1
    bgt.w ReturnFromPickupMapRev
    
    ; calculate offset based on level uncovered by last map reveal collected
    move.b (AP_LAST_MAP_REV_LV),D1
    mulu.w #$7,D1
    ; uncovered mask begins at 0x91EC for level 0 ⇒ start at 91F4 for level 1 with 1 byte offset
	; transparent mask begins at 0x92A2 for level 0 ⇒ start at 92AA for level 1 with 1 byte offset
    movea.l #$00ff91f4,A4
    movea.l #$00ff92aa,A5
    adda.l D1,A4
    adda.l D1,A5
    ; D4 → level whose transparency mask is being modified
    ; D1 → which byte (row) within the level's mask is being modified
    clr.l D4
LevelLoop:
    clr.l D1
MapRowLoop:
    ; calculate map row offset
    movea.l A4,A0
    movea.l A5,A1
    adda.l D1,A0
    adda.l D1,A1
    move.w D4,D6
    mulu.w #$7,D6
    adda.w D6,A0
    adda.w D6,A1
    move.b (A0),D2
    
    ; uncover all but edges of central map rows by XORing with 01111110
    eori.b #$7e,D2
    move.b D2,(A1)

    ; inner loop condition: continue until all 5 middle rows have been uncovered
    addi.w #$1,D1
    cmpi.w #$5,D1
    blt.b MapRowLoop
    
    ; inner loop code
    ; find how many maps should be uncovered, check if we've uncovered enough
    addi.w #$1,D4
    move.b (AP_NUM_MAP_REVS),D6
    subi.b #$1,D6
    movea.l #AP_MAP_REV_POTENCIES,A3
    move.b (A3,D6.w),D6
    ext.w D6
    cmp.w D6,D4
    blt.b LevelLoop

    ; end of loop, update last revealed level
    add.b D4,(AP_LAST_MAP_REV_LV)

    ; prepare to emit dialogue
    ; push player argument
    move.b D3,D1
    ext.w D1
    ext.l D1
    move.l D1,-(SP)
    ; push correct dialogue sequence argument
    ; first dialogue sequence is $5c ("Lv1-5 map!"), hence begin from $5b
    movea.l #AP_NUM_MAP_REVS,A0
    move.b (A0),D3
    add.w #$5b,D3
    move.l D3,-(SP)
    jsr Fn_QueueDialogueSequence
    addq.l #$8,SP
ReturnFromPickupMapRev:
    rts

