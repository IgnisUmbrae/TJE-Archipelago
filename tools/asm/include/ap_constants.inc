; damage sources (except earthlings / bad food)

DMG_SRC_CACTUS          equ $19
DMG_SRC_ROSEBUSHES      equ $1a
DMG_SRC_TOMATO          equ $1b
DMG_SRC_RAINCLOUD       equ $1c
DMG_SRC_TOTAL_BUMMER    equ $1d
DMG_SRC_DROWNED         equ $1e
DMG_SRC_FOOD_PRESENT    equ $4a

; misc just to make asm nicer to read

GROUND_ITEMS_PER_LEVEL  equ $1c

; new items: presents

POINT_PRESENT           equ $1c

; new items: ground items

AP_ITEM                 equ $54
AP_ITEM_PROG            equ $55
ELEV_KEY                equ $56
MAP_REVEAL              equ $57
GROUND_SHIP_PIECE       equ $58

; trap identifiers

AP_TRAP_CUPID           equ $00
AP_TRAP_BURP            equ $01
AP_TRAP_SLEEP           equ $02
AP_TRAP_SKATES          equ $03
AP_TRAP_EARTHLING       equ $04
AP_TRAP_RANDOMIZER      equ $05
AP_TRAP_DOWNFALL        equ $06