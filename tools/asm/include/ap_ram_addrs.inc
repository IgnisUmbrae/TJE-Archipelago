; Active character
AP_ACTIVE_CHAR          equ $00fff000

; Storage for inventory scroll position
; Earl's values are +1 from TJ's
AP_MENU_ROW_TJ          equ $00fff100
AP_MENU_COL_TJ          equ $00fff102
AP_MENU_INV_POS_TJ      equ $00fff104

; Expanded and relocated data
AP_INVENTORIES          equ $00fff280
AP_PRES_WRAPPING        equ $00fff300

; AP-specific information

AP_SHIP_PIECES_GOT      equ $00fff444 ; not the same as ship items triggered, which is at e212

AP_NUM_KEYS             equ $00fff455
AP_NUM_MAP_REVS         equ $00fff456
AP_LAST_MAP_REV_LV      equ $00fff457

; Flags written to by the AP client to trigger events in-game
;; Client writes ID, game resets to FF after use
AP_DROP_PRES            equ $00fff553
AP_GIVE_ITEM            equ $00fff554
AP_OPEN_PRES            equ $00fff555
;; Client writes 1, game resets to 0 after use
AP_NO_PRES_POINTS_FLAG  equ $00fff556
AP_CUPID_TRAP           equ $00fff557
AP_DIALOGUE_TRIGGER     equ $00fff558

; Dialogue lines, for use with dialogue trigger above
AP_DIALOGUE_LINE1       equ $00fff600
AP_DIALOGUE_LINE2       equ $00fff60c

; Flags written to by the game to trigger events in the client
;; Game writes 1, client resets to 0 after use
AP_INIT_COMPLETE        equ $00fff6a0
AP_LEVEL_ITEMS_SET      equ $00fff6a1
AP_DEATH_TRIGGERED      equ $00fff6a2

; Addresses for communicating data from game to client
;; Game writes a value, client optionally resets to 0 after use
AP_BIG_ITEM_LV          equ $00fff6b0

; Phantom item entry for remote item awarding
AP_PHANTOM_ITEM         equ $00fff700
