; 0010d800

ReturnPoint equ $00010ab0

    include "common.inc"

    ; player is in D2, player info addr is in A2
    ; if we have zero lives, we will respawn at z=0 with no falling animation, so use $0 instead of $46 for poof height

    ; checks whether animation is 
    cmpi.b #$6,($4b,A2)
    beq.b SetZeroZPos
    move.w #$46,D2
    bra.b SetAndReturn
SetZeroZPos:
    clr.w D2
SetAndReturn:
    move.w D2,($4,A2)
    jmp ReturnPoint