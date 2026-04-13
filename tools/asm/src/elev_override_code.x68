;0001de32

    include "common.inc"

    movea.l #AP_KEY_OVERRIDE_LV,A1
    move.b #$18,(A1)
    jmp $0001de98