;0001370e

    include "common.inc"

ElevatorAccelDecel:
    tst.w (VAN_ELEV_SPEED)
    nop ; only here to keep internal alignment
    blt.b ElevatorAccelDecel
    move.w #-$8000,(VAN_ELEV_ACCEL)