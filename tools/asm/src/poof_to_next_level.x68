; 0010d900

ReturnPoint equ $00010a46

    include "common.inc"

    ; check for special flag that takes us to an arbitrary level
    movea.l #AP_POOF_DEST_LEVEL,A4
    cmpi.b #-1,(A4)
    beq.b PoofToNext

    ; set player level & reset flag
    move.b (A4),($4c,A2)
    move.b #-1,(A4)
    bra.b PoofToArbitrary

PoofToNext:
    addq.b #$1,($4c,A2)
PoofToArbitrary:
    move.b ($4c,A2),D0
    jmp ReturnPoint