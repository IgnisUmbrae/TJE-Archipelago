;00013710

    include "common.inc"

ElevatorAccelDecel:
    cmpi.w #$0,(VAN_ELEV_SPEED)
    nop ; only here to keep internal alignment when assembler optimizes the line above
    blt.b (ElevatorAccelDecel)
    move.w #-$8000,(VAN_ELEV_ACCEL)