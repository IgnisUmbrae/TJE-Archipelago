;0010b500

    include "common.inc"

    ; check if "do not award points for present opening" flag is set
    movea.l    #AP_NO_PRES_POINTS_FLAG,A1
    cmpi.b     #$1,(A1)
    beq.b      ReturnFromCheck
    ; add 2 points if not set
    movea.l    #VAN_PLAYER_POINTS,A0
    addq.w     #$2,(A0,D0.l)
ReturnFromCheck:
    rts
