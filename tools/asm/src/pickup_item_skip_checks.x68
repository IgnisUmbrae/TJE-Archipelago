;00111300

ReturnPointSkipChecks equ $000153b8
ReturnPointFailChecks equ $000153b4
ReturnPointContinueStateChecks equ $0001538c

    ; check if size of object table is 1; if so, this is remote item awarding
    ; so skip all internal checks on player state
    cmpi.w  #$1,D4
    beq.b   ReturnSkip
    ; -- begin original function block --
    cmpi.w  #$4,($4,A3)
    bge.b   ReturnFail
    ; -- end original function block --
    jmp     ReturnPointContinueStateChecks

    ReturnSkip:
    jmp     ReturnPointSkipChecks
    ReturnFail:
    jmp     ReturnPointFailChecks