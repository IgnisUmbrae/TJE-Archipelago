;0010a000

ReturnPointPickupBuck     equ $000154c4
ReturnPointPickupFood     equ $000154ec
ReturnPointMarkCollected  equ $0001559c

    include "common.inc"

    cmpi.b     #AP_ITEM,(A2)
    bge.w      PickupAPItem
    cmpi.b     #$50,(A2)
    bne.b      RetPickupFood

RetPickupBuck:
    moveq     #$1,D0
    jmp       ReturnPointPickupBuck
RetPickupFood:
    moveq     #$1,D0
    jmp       ReturnPointPickupFood

PickupAPItem:
CheckIfElevKey:
    cmpi.b     #ELEV_KEY,(A2)
    bne.b      CheckIfMapReveal
    jsr        AP_PICKUP_ELEV_KEY.l
CheckIfMapReveal:
    cmpi.b     #MAP_REVEAL,(A2)
    bne.b      PlayPickupSoundForAPItem
    jsr        AP_PICKUP_MAP_REV.l
PlayPickupSoundForAPItem:
    pea        ($32).w
DYNRP_PSG_SFX:
    pea        ($1).w ; item pickup sound
    jsr        Fn_PlayPSGSound.l
    addq       #$4,SP ; must manually realign stack here due to the expectations of the external function
    moveq      #$1,D0 ; retval to indicate success
    jmp        ReturnPointMarkCollected