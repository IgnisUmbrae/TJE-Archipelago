; 0010e000

ReturnPoint equ $00014316

    include "common.inc"

    ; set consistent random seed (concatenation of first two level seeds)
    ; so the present wrapping is consistent between reloads
    move.l (VAN_FIXED_WORLD_SEEDS),-(SP)
    jsr Fn_SetRandomSeed
    addq.l #$4,SP

    ; -- begin original function block --
DYNRP_inventory_addr:
    movea.l #VAN_INVENTORIES,A2
    ; -- end original function block --

    jmp ReturnPoint