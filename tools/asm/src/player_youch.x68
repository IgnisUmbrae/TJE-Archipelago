; 0010c400

ReturnPoint equ $0001b282

    include "common.inc"

    move.b (A2),AP_LAST_DMG_SOURCE
    ; check if the Earthling is actually one of our fake cactus/rosebush values
    ; if so, use damage of 2 as in vanilla game
    cmpi.b #$18,(A2)
    bgt.b DamageTwo
    ; -- begin original function block --
    move.b ($1c,A1,D1.w),(A0,D0.l)
    ; -- end original function block --
    bra.b JumpBack
DamageTwo:
    move.b #$2,(A0,D0.l)
JumpBack:
    jmp ReturnPoint