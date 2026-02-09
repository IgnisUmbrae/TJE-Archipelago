;00105180

; AP item
    dc.b $01 ; sprite data count
    dc.b $00 ; x offset
    dc.b $00 ; y offset
    dc.b $00 ; next-is-same flag
    dc.b $03 ; width
    dc.b $03 ; height
    dc.b $f6 ; offset_x
    dc.b $ef ; offset_y
    dc.b $f2 ; offset_z
    dc.b $42 ; no compression ($40) + palette 2 ($02)
    dc.l $00100000 ; pointer to sprite data

; AP important item

    dc.b $01
    dc.b $00
    dc.b $00
    dc.b $00
    dc.b $03
    dc.b $03
    dc.b $f6
    dc.b $ef
    dc.b $f2
    dc.b $42
    dc.l $00100f20

; Elevator key

    dc.b $01
    dc.b $00
    dc.b $00
    dc.b $00
    dc.b $03
    dc.b $03
    dc.b $f6
    dc.b $ef
    dc.b $f2
    dc.b $42
    dc.l $00101040

; Map reveal

    dc.b $01
    dc.b $00
    dc.b $00
    dc.b $00
    dc.b $03
    dc.b $03
    dc.b $f6
    dc.b $ef
    dc.b $f2
    dc.b $42
    dc.l $00101160

; Ship item on ground

    dc.b $01
    dc.b $00
    dc.b $00
    dc.b $00
    dc.b $03
    dc.b $03
    dc.b $f6
    dc.b $ef
    dc.b $f2
    dc.b $43
    dc.l $00101280