; 0010d000

; overrides part of the function that creates entities from map object data to allow
; extra ground sprites to occupy IDs > 0x53

ReturnPointTree    equ $00015144
ReturnPointNotTree equ $0001512a

    include "common.inc"

    cmpi.b #$50,(A2)
    ble RetNotTree
    cmpi.b #AP_ITEM,(A2)
    bge RetNotTree

RetTree:
    jmp ReturnPointTree
RetNotTree:
    jmp ReturnPointNotTree