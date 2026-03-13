;0010bb00

ReturnPointSteal    equ $00022052
ReturnPointNoSteal  equ $0002217c

    include "common.inc"

    ; --begin original function block--
    move.w  D3,D0
    ext.l   D0
DYNRP_inventory_asl:
    asl.l   #$4,D0
    movea.l D5,A1
    movea.l A1,A0
    move.w  D2,D1
    adda.l  D0,A0
    move.b  (A0,D1.w),D6
    ext.w   D6
    ; --end original function block--

    ; disallow stealing of various present types
DYNRP_promotion_present_steal: ; left intact rank checks are off; compiles to 6 bytes
    cmpi.b  #$b,D6 ; Promotion
    beq     RetNoSteal
DYNRP_buck_present_steal: ; left intact unless mailbox checks are off
    cmpi.b  #$14,D6 ; Extra Buck
    beq     RetNoSteal
DYNRP_jackpot_present_steal: ; left intact unless mailbox checks are off
    cmpi.b  #$15,D6 ; Jackpot
    beq     RetNoSteal

    ; add points for stolen present
    ; D3 contains player

    move.w  D3,D0
    movea.l #VAN_PLAYER_POINTS,A0
    addq.w  #$2,(A0,D0.w)

    jmp     ReturnPointSteal
RetNoSteal:
    jmp     ReturnPointNoSteal