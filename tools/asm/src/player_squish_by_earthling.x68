; 0010cb00

ReturnPoint equ $0001b36a

SquishedByHamster       equ $1e
SquishedByNerds         equ $1f
SquishedByIceCream      equ $20
SquishedByOther         equ $21

    include "common.inc"

    ; -- begin original function block --
    move.b #$03,($15,A3)
    ; -- end original function block --

    ; check type of Earthling that squished us
CheckHamsterSquish:
    cmpi.b #$2,(A2)
    bne.b CheckNerdsSquish
    move.b #SquishedByHamster,(AP_LAST_DMG_SOURCE)
    bra.b JumpBack
CheckNerdsSquish:
    cmpi.b #$0c,(A2)
    bne.b CheckIceCreamSquish
    move.b #SquishedByNerds,(AP_LAST_DMG_SOURCE)
    bra.b JumpBack
CheckIceCreamSquish:
    cmpi.b #$13,(A2)
    bne.b CheckSquishedByOther
    move.b #SquishedByIceCream,(AP_LAST_DMG_SOURCE)
    bra.b JumpBack
CheckSquishedByOther:
    move.b #SquishedByOther,(AP_LAST_DMG_SOURCE)
JumpBack:
    jmp ReturnPoint