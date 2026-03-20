;00106000

;relocated from original at 000aafa4

    dc.l $000aa110 ; Present sprite $0
    dc.l $000aa18e
    dc.l $000aa210
    dc.l $000aa2a4
    dc.l $000aa302
    dc.l $000aa342
    dc.l $000aa3ac
    dc.l $000aa404
    dc.l $000aa4be
    dc.l $000aa520
    dc.l $000aa5aa
    dc.l $000aa634
    dc.l $000aa69c
    dc.l $000aa718
    dc.l $000aa7da
    dc.l $000aa858
    dc.l $000aa95e
    dc.l $000aa9ea
    dc.l $000aaa22
    dc.l $000aaac4
    dc.l $000aab58
    dc.l $000aabea
    dc.l $000aac4c
    dc.l $000aad06
    dc.l $000aad68
    dc.l $000aadd0
    dc.l $000aa8de ; Present sprite $1a (always mystery present)
    dc.l $000aae4a ; Present sprite $1b (always bonus hitops)

DYNRP_custom_present_1:
    dc.l $ffffffff ; $1c / beginning of blank entries
    dc.l $ffffffff ; $1d
    dc.l $ffffffff ; $1e
    dc.l $ffffffff ; $1f
    dc.l $ffffffff ; $20
    dc.l $ffffffff ; $21 
    dc.l $ffffffff ; $22
    dc.l $ffffffff ; $23
    dc.l $ffffffff ; $24
    dc.l $ffffffff ; $25
    dc.l $ffffffff ; $26
    dc.l $ffffffff ; $27
    dc.l $ffffffff ; $28
    dc.l $ffffffff ; $29
    dc.l $ffffffff ; $2a
    dc.l $ffffffff ; $2b
    dc.l $ffffffff ; $2c
    dc.l $ffffffff ; $2d
    dc.l $ffffffff ; $2e
    dc.l $ffffffff ; $2f
    dc.l $ffffffff ; $30
    dc.l $ffffffff ; $31
    dc.l $ffffffff ; $32
    dc.l $ffffffff ; $33
    dc.l $ffffffff ; $34
    dc.l $ffffffff ; $35
    dc.l $ffffffff ; $36
    dc.l $ffffffff ; $37
    dc.l $ffffffff ; $38
    dc.l $ffffffff ; $39
    dc.l $ffffffff ; $3a
    dc.l $ffffffff ; $3b
    dc.l $ffffffff ; $3c
    dc.l $ffffffff ; $3d
    dc.l $ffffffff ; $3e
    dc.l $ffffffff ; $3f

    ; beginning of other pickup sprites, inserted to allow rendering in mailbox
    dc.l $000ab068 ; $40 / burger
    dc.l $000ab0be ; $41 / fudge sundae
    dc.l $000ab14a ; $42 / fudge cake
    dc.l $000ab184 ; $43 / candy cane
    dc.l $000ab1ce ; $44 / fries
    dc.l $000ab21a ; $45 / pancakes
    dc.l $000ab27c ; $46 / watermelon
    dc.l $000ab2ee ; $47 / bacon'n eggs
    dc.l $000ab344 ; $48 / cherry pie
    dc.l $000ab3b4 ; $49 / pizza
    dc.l $000ab408 ; $4a / cereal
    dc.l $000ab466 ; $4b / fish bones
    dc.l $000ab4ba ; $4c / moldy cheese
    dc.l $000ab528 ; $4d / moldy bread
    dc.l $000ab592 ; $4e / slimy fungus
    dc.l $000ab602 ; $4f / cabbage
    dc.l $000ab678 ; $50 / a buck

    dc.l $ffffffff ; $51 / beginning of blank entries for trees
    dc.l $ffffffff ; $52
    dc.l $ffffffff ; $53

    ; extra ground items
    dc.l $00107500 ; $54 / AP item
    dc.l $0010750e ; $55 / AP item (important)
    dc.l $0010751c ; $56 / elevator key
    dc.l $0010752a ; $57 / map reveal
    dc.l $00107538 ; $58 / ship item on ground