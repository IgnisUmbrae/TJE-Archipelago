;0010a400

    include "common.inc"

    ; -- begin original function block --
    move.w D3,D0
    ext.l D0
    movea.l #VAN_PLAYER_LIVES,A0
    ; -- end original function block --

    ; set death triggered flag
    move.b #$1,(AP_DEATH_TRIGGERED)
    rts