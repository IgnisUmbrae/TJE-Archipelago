; 0010d100

ReturnOpenTelephone equ $0001715e
ReturnOpenOtherPresent equ $00017178
ReturnOpenActionPresent equ $00017224

    include "common.inc"

    ; D2 contains present id
    ; D3 contains player

    ; check if telephone present (excised & modified from original function)
    cmpi.w #$13,D2
    beq.b RetTelephone

    cmpi.w #POINT_PRESENT,D2
    beq.b OpenPointPresent

    jmp ReturnOpenOtherPresent
OpenPointPresent:
    move.w D3,-(SP)
    jsr AP_OPEN_POINT_PRES
    addq #$2,SP
    ;bra.b RetActionPres

RetActionPres:
    jmp ReturnOpenActionPresent
RetTelephone:
    jmp ReturnOpenTelephone