;0010a400

    include "common.inc"

    ; -- begin original function block --
    move.w D3,D0
    ext.l D0
    movea.l #VAN_PLAYER_LIVES,A0
    ; -- end original function block --

    ; set death triggered flag
    ; if dropdown and deathlink are both enabled, this check is kept to avoid triggering deathlink twice on game over
    ; otherwise it is patched out entirely
DYNRP_dropdown_life_check:
    cmpi.b #$1,(A0)
    blt.b Return
    move.b #$1,(AP_DEATH_TRIGGERED)
Return:
    rts