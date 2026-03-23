from enum import IntEnum
from typing import NamedTuple
from base64 import b64encode, b64decode

BASE_TJE_ID = 25101991

#region Deathlink-related

DEATHLINK_MESSAGES = {
    0x1 : [
        "{player} got poked by a devil"
    ],
    0x2 : [
        "{player} got squished by a hamster"
    ],
    0x3 : [
        "{player} got shunted by a shopping cart"
    ],
    0x4 : [
        "{player} got drilled by a dentist"
    ],
    0x6 : [
        "{player} got stung all over by a swarm of bees"
    ],
    0x9 : [
        "{player} got mauled by a mailbox"
    ],
    0xC : [
        "{player} got squished by a herd of nerds"
    ],
    0xD : [
        "{player} got run over by a lawnmower"
    ],
    0xE : [
        "{player} got chomped by a shark"
    ],
    0xF : [
        "{player} got rammed by a gang of chickens"
    ],
    0x10 : [
        "{player} got boogied to death by a boogie man"
    ],
    0x13 : [
        "{player} got squished by an ice cream truck"
    ],
    0x15 : [
        "{player} got drilled by a very angry dentist"
    ],
    0x16 : [
        "{player} got stung all over by a swarm of very angry bees"
    ],
    0x19 : [
        "{player} got spined to death by a cactus"
    ],
    0x1A : [
        "{player} got spiked to death by their own rosebushes"
    ],
    0x1B : [
        "{player} got smacked in the face by a tomato"
    ],
    0x1C : [
        "{player} got zapped by lightning"
    ],
    0x1D : [
        "{player} had a total bummer"
    ],
    0x1E : [
        "{player} drowned in the sea",
    ],
    0x4A : [
        "{player} gambled with mystery food and lost",
    ],
    0x4B : [
        "{player} choked on some fish bones",
    ],
    0x4C : [
        "{player} got ill from moldy cheese",
    ],
    0x4D : [
        "{player} got ill from moldy bread",
    ],
    0x4E : [
        "{player} tried eating a weird-looking mushroom",
    ],
    0x4F : [
        "{player} got cabbaged",
    ]
}

#endregion

#region Sound effects

PCM_SFX_ADDRS = [0x00044d8a, 0x000491c8, 0x0004c276, 0x0004d75a, 0x0004dfa0, 0x0004f79a, 0x00051472, 0x00053920,
                 0x00054626, 0x00055a9a, 0x0005747c, 0x0005a02e, 0x0005d7a0, 0x0005f5e2, 0x000601b4, 0x00061bd6,
                 0x00064178, 0x00067cba, 0x0006a13c, 0x0006ac3e, 0x0006b4a8, 0x0006f5aa, 0x0007177c, 0x000730de,
                 0x000741f0, 0x000752ba, 0x00076ecc, 0x0007763e, 0x00079170, 0x0007a2e2, 0x0007be44, 0x0007ccc6,
                 0x0007de38, 0x0007e8ba, 0x0008233c, 0x0008381e, 0x00088060]

# These four sounds are also used as part of the music
PCM_SFX_ADDRS_MUSIC = [0x00089a42, 0x0008a4ac, 0x0008addc, 0x0008b104]

# Excluding in Jam Out
# Dynamically repatched: indices 3 and 34
PCM_SFX_USAGE_ADDRS = [
    (0x0002009c, 0x0002160c), (0x0000f8c0, 0x0002b3fa), (0x0001b2e6,), (0x0001553e, 0x0001556a), (0x0001070c,),
    (0x0001663a, 0x000166f6), (0x0001015c, 0x0001059c, 0x0001089e, 0x00011cbe, 0x00023f8c), (0x0000fcda, 0x0001b3cc),
    (0x0000f3ca, 0x0002ad16, 0x0002ad42, 0x0002b1b2, 0x0002b200, 0x000378ea), (0x0001e600, 0x0003a658), (0x0001bdba,),
    (0x00019824,), (0x0001d420,), (0x0001b2f4,), (0x0002185e,), (0x00021b08,), (0x00022c92,), (0x0001a30e,),
    (0x000169c6, 0x00023daa), (0x0001c510,), (0x0000943c,), (0x0001b53c,), (), (0x00019d88, 0x00019e6c), (0x000200b6,),
    (0x0002135a,), (0x000120d2, 0x000120fa), (0x0001661e, 0x0001683c), (), (), (0x0000fa0c,), (0x0000fa1c,),
    (0x0000fa7e,), (0x00012598,), (0x000154d8,), (0x000125c6,), (0x00012580,)
]

PCM_SFX_USAGE_ADDRS_MUSIC = [
    (0x00012182, 0x0002002a, 0x00020076, 0x0003779c, 0x0003efe6), (0x0003effe,), (0x0003efce,), (0x0001677a, 0x0003f01e)
]

# Not included: the menu blip 0x7, rocket skates sound 0x5
PSG_SFX = [0x1, 0x2, 0x3, 0x4, 0x8, 0xA, 0xC, 0xE, 0xF, 0x10, 0x11, 0x12, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A]

# Not included: menu blips @ (0x00009482, 0x000095ae, 0x000097f6, 0x00013d8a, 0x000239bc, 0x000239ea)
#               rocket skates @ (0001738a, 000224f6)
# Dynamically repatched: indices 0 and 11
PSG_SFX_USAGE_ADDRS = [
    [], (0x0001cd8c,), (0x00013db4,), (), (0x0002b6ba,), (0x0002b240,),
    (0x000206ec,), (0x0001be8e,), (0x00014024,), (0x00015c0c, 0x0001f18c), (0x00013b38, 0x00013d36),
    [0x000165ca, 0x000166ce, 0x00016c34], (0x0001db66, 0x0001dd80, 0x0001de9c),
    (0x0002aede, 0x0002af76, 0x0003a690), (0x0002af36,), (0x00011c56,), (0x00013eb2, 0x00014134), (),
    [0x00009a4e, 0x00009b1c, 0x00009da2, 0x00009e1a, 0x00021622, 0x00021b1e, 0x0002398a]
]

# Not included: the cancel sound 0x0, various unused sounds
SIMPLE_SFX = [0x2, 0x4, 0x9, 0xB, 0xD, 0xE, 0xF, 0x13, 0x14, 0x15, 0x16]

SIMPLE_SFX_USAGE_ADDRS = (
    (0x0001c732,), (0x0001ca52,), (0x0001b094,), (0x0001c0be,), (0x0001cf54, 0x0001d072), (0x0001691e,),
    (0x0001c628,), (0x0003ae80,), (0x0003ae6c,), (0x0003aea2,), (0x0003ae48,)
)

#endregion

#region Inventory-related ROM addresses

INV_REF_ADDRS_VANILLA = [0x0000934a+2, 0x000097aa+2, 0x000099a8+2, 0x000099ca+2, 0x00009b02+2, 
                         0x00009d76+2, 0x00009dcc+2, 0x0000a23a+2, 0x0000a460+2, #0x00014310+2,
                         0x0001542a+2, 0x00015442+2, 0x0001ac24+4, 0x00021fba+2, 0x0002227a+2]

INV_SIZE_ADDRS_VANILLA = [0x00009396+3, 0x00014320+5, 0x00014328+3, 0x00015474+3, 0x0001547a+3, 0x00021fd8+3]

INV_SIZE_ADDRS_INITIAL = (0x000143c2+5, 0x000143c8+5, 0x000143d6+5, 0x000143dc+5)

INV_SIZE_ADDRS_ASL_D0_VANILLA = [0x00009358, 0x0000936c, 0x00009380, 0x000097a8, 0x00009a0c, 0x00009a64, 0x00009a8e,
                                 0x00009a9c, 0x00009abc, 0x00009ad6, 0x00009b68, 0x00009b7c, 0x00009b8a, 0x00009baa,
                                 0x00009bc4, 0x00009d74, 0x00009dca, 0x0000a238, 0x0000a45e, 0x00015428, 0x00015440,
                                 0x00021fc6, 0x0002205a, 0x0002207e, 0x00022278]

INITIAL_PRESENT_ADDRS = (0x00014393, 0x00014397, 0x000143a5, 0x000143ab,
                         0x000143c5, 0x000143cb, 0x000143d9, 0x000143df)

#endregion

#region Custom present–related ROM addresses

TOTAL_PRES_TYPES_PLUS_ONE_ADDRS = (0x00014298 + 3, 0x000142ba + 1, 0x000142d8 + 1)

#endregion

#region Earthling-related

class Earthling(IntEnum):
    SHIPPIECE = 0x00
    DEVIL = 0x01
    HAMSTER = 0x02
    SHOPPER = 0x03
    DENTIST = 0x04
    WAHINI = 0x05
    BEES = 0x06
    CUPID = 0x07
    TORNADO = 0x08
    MAILBOX = 0x09
    WIZARD = 0x0A
    WISEMAN = 0x0B
    NERDS = 0x0C
    LAWNMOWER = 0x0D
    SHARK = 0x0E
    CHICKENS = 0x0F
    BOOGIE = 0x10
    OPERA = 0x11
    MOLE = 0x12
    ICECREAM = 0x13
    SANTA = 0x14
    DENTIST_ANGRY = 0x15
    BEES_ANGRY = 0x16
    LEMONADE = 0x17
    HOTTUB = 0x18

    NONE = 0xFF

def earthling_value(e: int) -> int:
    match e:
        case Earthling.SANTA:
            return -2
        case e if e in (Earthling.WISEMAN, Earthling.WIZARD, Earthling.OPERA):
            return -1
        case e if e in (Earthling.DEVIL, Earthling.HAMSTER, Earthling.CUPID, Earthling.SHARK):
            return 1
        case e if e in (Earthling.SHOPPER, Earthling.DENTIST, Earthling.BEES, Earthling.WAHINI, Earthling.BOOGIE, Earthling.MOLE):
            return 2
        case e if e in (Earthling.LAWNMOWER, Earthling.CHICKENS, Earthling.BEES_ANGRY, Earthling.DENTIST_ANGRY):
            return 3
        case e if e in (Earthling.NERDS, Earthling.TORNADO):
            return 4
        case e if e in (Earthling.ICECREAM, Earthling.MAILBOX):
            return 5
        case _:
            return 0

LEVEL_TO_VANILLA_EARTHLINGS = (
    [Earthling.LEMONADE, Earthling.HOTTUB, Earthling.WAHINI],
    [],
    [Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL],
    [Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.HAMSTER, Earthling.HAMSTER, Earthling.HAMSTER, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WIZARD],
    [Earthling.BEES, Earthling.BEES, Earthling.HAMSTER, Earthling.HAMSTER, Earthling.HAMSTER, Earthling.HAMSTER, Earthling.HAMSTER, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.CUPID, Earthling.CUPID, Earthling.SHARK, Earthling.SHARK, Earthling.WISEMAN, Earthling.SANTA],
    [Earthling.BEES, Earthling.BEES, Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.HAMSTER, Earthling.SHOPPER, Earthling.SHOPPER, Earthling.SHOPPER, Earthling.SHOPPER, Earthling.DENTIST, Earthling.DENTIST, Earthling.DENTIST, Earthling.DENTIST, Earthling.WISEMAN],
    [Earthling.BOOGIE, Earthling.BOOGIE, Earthling.MOLE, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.DEVIL, Earthling.WAHINI, Earthling.WAHINI, Earthling.CUPID, Earthling.CUPID, Earthling.BEES, Earthling.BEES, Earthling.WIZARD],
    [Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.BEES, Earthling.BEES, Earthling.TORNADO, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.DENTIST, Earthling.DENTIST, Earthling.WISEMAN, Earthling.SANTA],
    [Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.SHOPPER, Earthling.SHOPPER, Earthling.DENTIST, Earthling.DENTIST, Earthling.DENTIST, Earthling.NERDS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.WISEMAN, Earthling.MOLE],
    [Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.SHOPPER, Earthling.SHOPPER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.OPERA, Earthling.MOLE],
    [Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.WIZARD, Earthling.SANTA],
    [Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.WIZARD, Earthling.WISEMAN, Earthling.OPERA, Earthling.SANTA],
    [Earthling.NERDS, Earthling.NERDS, Earthling.NERDS, Earthling.NERDS, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.WAHINI, Earthling.WAHINI, Earthling.CUPID, Earthling.CUPID, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS],
    [Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.MOLE, Earthling.MOLE, Earthling.OPERA],
    [Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.WIZARD, Earthling.SANTA],
    [Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.CUPID, Earthling.CUPID, Earthling.CUPID, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.NERDS, Earthling.NERDS, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.WISEMAN, Earthling.OPERA],
    [Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.MOLE, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.NERDS, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE],
    [Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.ICECREAM, Earthling.WIZARD, Earthling.OPERA],
    [Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.CUPID, Earthling.CUPID, Earthling.WAHINI, Earthling.WAHINI, Earthling.BEES, Earthling.BEES, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.WISEMAN],
    [Earthling.SANTA, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.CHICKENS, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.MOLE, Earthling.MOLE],
    [Earthling.OPERA, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.NERDS, Earthling.NERDS, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM],
    [Earthling.ICECREAM, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.BEES, Earthling.TORNADO],
    [Earthling.CUPID, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.ICECREAM, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO, Earthling.TORNADO],
    [Earthling.WIZARD, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.SHARK, Earthling.CHICKENS, Earthling.BEES_ANGRY],
    [Earthling.BEES_ANGRY, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.WAHINI, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER, Earthling.LAWNMOWER],
    [Earthling.MOLE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.BOOGIE, Earthling.DENTIST_ANGRY, Earthling.DENTIST_ANGRY, Earthling.TORNADO, Earthling.TORNADO, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.BEES_ANGRY, Earthling.OPERA]
)

EARTHLING_LIST = [e for e in Earthling if e != Earthling.MAILBOX and e.value in range(1, 0x17)]
PER_LEVEL_UNIQUE_EARTHLINGS = (Earthling.WIZARD, Earthling.WISEMAN, Earthling.OPERA, Earthling.SANTA)
# Actual number of Earthlings per level in the vanilla game
EARTHLING_MAX_PER_LEVEL = (0, 0, 6, 16, 18, 18, 18, 17, 16, 16, 18, 17, 16, 16, 16, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20)

PER_LEVEL_EARTHLING_WEIGHTS = [
    [0, 0, 11.5, 23.0, 11.5, 7.75, 5.75, 4.5, 3.75, 3.25, 3.0, 2.5, 2.25, 2.0, 2.0, 1.75, 1.75, 1.5, 1.5, 1.25, 1.25, 1.25, 1.25, 1.0, 1.0, 1.0],
    [0, 0, 7.25, 11.0, 22.0, 11.0, 7.25, 5.5, 4.5, 3.75, 3.25, 2.75, 2.5, 2.25, 2.0, 1.75, 1.75, 1.5, 1.5, 1.5, 1.25, 1.25, 1.25, 1.0, 1.0, 1.0],
    [0, 0, 2.5, 3.0, 3.5, 4.5, 6.0, 9.0, 18.0, 9.0, 6.0, 4.5, 3.5, 3.0, 2.5, 2.25, 2.0, 1.75, 1.75, 1.5, 1.5, 1.25, 1.25, 1.0, 1.0, 1.0],
    [0, 0, 3.25, 3.75, 4.75, 6.25, 9.5, 19.0, 9.5, 6.25, 4.75, 3.75, 3.25, 2.75, 2.5, 2.0, 2.0, 1.75, 1.5, 1.5, 1.25, 1.25, 1.25, 1.0, 1.0, 1.0],
    [0, 0, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.75, 5.0, 7.5, 15.0, 7.5, 5.0, 3.75, 3.0, 2.5, 2.25, 2.0, 1.75, 1.5, 1.25, 1.25, 1.25, 1.0, 1.0],
    [0, 0, 2.5, 3.0, 3.5, 4.5, 6.0, 9.0, 18.0, 9.0, 6.0, 4.5, 3.5, 3.0, 2.5, 2.25, 2.0, 1.75, 1.75, 1.5, 1.5, 1.25, 1.25, 1.0, 1.0, 1.0],
    [0, 0, 2.0, 2.25, 2.5, 3.0, 3.75, 4.75, 6.5, 11.0, 11.0, 6.5, 4.75, 3.75, 3.0, 2.5, 2.25, 2.0, 1.75, 1.5, 1.5, 1.25, 1.25, 1.25, 1.0, 1.0],
    [0, 0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.5, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.75, 4.75, 6.5, 11.0, 11.0, 6.5, 4.75, 3.75, 3.0, 2.5, 2.25, 2.0],
    [0, 0, 1.5, 1.75, 2.0, 2.25, 2.5, 3.0, 3.75, 5.0, 7.5, 15.0, 7.5, 5.0, 3.75, 3.0, 2.5, 2.25, 2.0, 1.75, 1.5, 1.25, 1.25, 1.25, 1.0, 1.0],
    [0, 0, 2.5, 3.0, 3.5, 4.5, 6.0, 9.0, 18.0, 9.0, 6.0, 4.5, 3.5, 3.0, 2.5, 2.25, 2.0, 1.75, 1.75, 1.5, 1.5, 1.25, 1.25, 1.0, 1.0, 1.0],
    [0, 0, 1.0, 1.0, 1.25, 1.25, 1.5, 1.5, 1.75, 2.0, 2.25, 2.75, 3.5, 4.75, 7.0, 14.0, 7.0, 4.75, 3.5, 2.75, 2.25, 2.0, 1.75, 1.5, 1.5, 1.25],
    [0, 0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.5, 1.5, 1.75, 2.0, 2.0, 2.5, 2.75, 3.5, 4.25, 5.75, 8.5, 17.0, 8.5, 5.75, 4.25, 3.5, 2.75, 2.5, 2.0],
    [0, 0, 1.25, 1.5, 1.5, 1.75, 2.0, 2.25, 2.75, 3.5, 4.75, 7.0, 14.0, 7.0, 4.75, 3.5, 2.75, 2.25, 2.0, 1.75, 1.5, 1.5, 1.25, 1.25, 1.0, 1.0],
    [0, 0, 1.0, 1.0, 1.25, 1.25, 1.5, 1.5, 1.75, 2.25, 2.5, 3.25, 4.25, 6.5, 13.0, 6.5, 4.25, 3.25, 2.5, 2.25, 1.75, 1.5, 1.5, 1.25, 1.25, 1.0],
    [0, 0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.5, 1.5, 1.75, 1.75, 2.0, 2.25, 2.75, 3.25, 4.0, 5.0, 7.0, 11.75, 11.75, 7.0, 5.0, 4.0, 3.25, 2.75, 2.25],
    [0, 0, 1.0, 1.0, 1.25, 1.25, 1.5, 1.5, 1.75, 2.0, 2.25, 2.75, 3.5, 4.75, 7.0, 14.0, 7.0, 4.75, 3.5, 2.75, 2.25, 2.0, 1.75, 1.5, 1.5, 1.25],
    [0, 0, 1.25, 1.5, 1.5, 1.75, 2.0, 2.25, 2.75, 3.5, 4.75, 7.0, 14.0, 7.0, 4.75, 3.5, 2.75, 2.25, 2.0, 1.75, 1.5, 1.5, 1.25, 1.25, 1.0, 1.0],
    [0, 0, 1.0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.5, 1.5, 1.75, 2.0, 2.25, 2.5, 2.75, 3.25, 4.0, 5.25, 7.5, 12.25, 12.25, 7.5, 5.25, 4.0, 3.25, 2.75],
    [0, 0, 1.75, 1.75, 2.0, 2.5, 2.75, 3.5, 4.5, 6.25, 10.25, 10.25, 6.25, 4.5, 3.5, 2.75, 2.5, 2.0, 1.75, 1.75, 1.5, 1.25, 1.25, 1.25, 1.0, 1.0],
    [0, 0, 1.0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.25, 1.5, 1.5, 1.75, 1.75, 2.0, 2.0, 2.25, 2.5, 3.0, 3.25, 3.75, 4.5, 5.75, 7.75, 11.5, 23.0, 11.5],
    [0, 0, 1.0, 1.0, 1.0, 1.25, 1.25, 1.25, 1.25, 1.5, 1.5, 1.75, 1.75, 2.0, 2.25, 2.25, 2.75, 3.0, 3.5, 4.0, 5.0, 6.5, 9.0, 15.0, 15.0, 9.0]
]
    
#endregion

#region Dialogue-related

MAP_REVEAL_DIALOGUE_ADDRS = (0x00105b73, 0x00105b7e, 0x00105b8a, 0x00105b97, 0x00105ba4)

MAP_REVEAL_DIALOGUE_TEMPLATE = "Lv{}-{} map!"
MAP_REVEAL_DIALOGUE_TEMPLATE_DEGEN = "Lv{} map!"

POINT_PRESENT_DIALOGUE_TEMPLATE = "{} points"

STATIC_DIALOGUE_LIST: dict[str, tuple[str,str]] = {
    "Ship Piece: Rocketship Windshield": ("Windshield!", "jammin'"),
    "Ship Piece: Left Megawatt Speaker": ("L. speaker!", "jammin'"),
    "Ship Piece: Super Funkomatic Amplamator": ("Amp!", "jammin'"),
    "Ship Piece: Amplamator Connector Fin": ("Amp fin!", "jammin'"),
    "Ship Piece: Forward Stabilizing Unit": ("Front leg!", "jammin'"),
    "Ship Piece: Rear Leg": ("Rear leg!", "jammin'"),
    "Ship Piece: Awesome Snowboard": ("Snowboard!", "jammin'"),
    "Ship Piece: Righteous Rapmaster Capsule": ("Capsule!", "jammin'"),
    "Ship Piece: Right Megawatt Speaker": ("R. speaker!", "jammin'"),
    "Ship Piece: Hyperfunk Thruster": ("Thruster!", "jammin'"),
    "Cupid Trap": ("Uh-oh...", "cupid trap!"),
    "Burp Trap": ("Uh-oh...", "burp trap!"),
    "Sleep Trap": ("Uh-oh...", "study time!"),
    "Earthling Trap": ("Uh-oh...", "earthling!!"),
    "Rocket Skates Trap": ("Uh-oh...", "skates trap!"),
    "Randomizer Trap": ("Uh-oh...", "randomizer!!"),
}

#endregion

#region Floor item–related

EMPTY_ITEM = b"\xFF"
EMPTY_PRESENT = b"\xFF"

PRESENT_LIST_BASE = [0x0, 0x1, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xA, 0xB, 0xC, 0xD, 0xE, 0xF, 0x10, 0x11,
                     0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1A]
PRESENT_WEIGHTS_BASE = [4, 5, 3, 4, 3, 4, 4, 3, 4, 4, 4, 1, 5, 4, 4, 4, 3, 1, 2, 2, 2, 1, 2, 2, 2, 2, 5]
BAD_PRESENT_INDICES = set([13, 16, 18, 23, 24])
LV1_FORBIDDEN_PRESENT_INDICES = set([0, 2, 5, 16, 18, 26])

FOOD_LIST = (0x40, 0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x4B, 0x4C, 0x4D, 0x4E, 0x4F)
FOOD_WEIGHTS = (1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1)
BAD_FOOD_INDICES = set([11, 12, 13, 14, 15])
A_BUCK = 0x50

#endregion

#region Ship piece–related

COLLECTED_SHIP_ITEM = b"\x00"
EMPTY_SHIP_PIECE = b"\xFF"

SHIP_PIECE_RANGES = (
    [(2, 3), (4, 5), (6, 7), (8, 9), (10, 11)], # max level 12
    [(2, 3), (4, 5), (6, 8), (9, 10), (11, 12)],
    [(2, 3), (4, 5), (6, 8), (9, 10), (11, 13)],
    [(2, 4), (5, 6), (7, 8), (9, 11), (12, 14)],
    [(2, 4), (5, 7), (8, 9), (10, 12), (13, 15)],
    [(2, 4), (5, 7), (8, 10), (11, 13), (14, 16)],
    [(2, 4), (5, 8), (9, 11), (12, 14), (15, 17)],
    [(2, 4), (5, 8), (9, 12), (13, 15), (16, 18)],
    [(2, 4), (5, 8), (9, 13), (14, 16), (17, 19)],
    [(2, 5), (6, 9), (10, 13), (14, 16), (17, 20)],
    [(2, 5), (6, 9), (10, 13), (14, 17), (18, 21)],
    [(2, 5), (6, 10), (11, 14), (15, 18), (19, 22)],
    [(2, 5), (6, 10), (11, 14), (15, 19), (20, 23)],
    [(2, 5), (6, 10), (11, 15), (16, 20), (21, 24)] # max level 25
)

#endregion

#region Elevator and rank checks

VANILLA_RANK_THRESHOLDS = (0, 40, 100, 180, 280, 400, 540, 700, 880)
RANK_NAMES = ("Wiener", "Dufus", "Poindexter", "Peanut", "Dude", "Bro", "Homey", "Rapmaster", "Funk Lord")

#endregion

#region Misc

POINT_PRESENT_NAME = "{} points"

MAILBOX_ITEM_REFS = ("Top", "Middle", "Bottom")

DEAD_SPRITES = (0x5, 0x6)

TRAP_NAMES = ("cupid", "burp", "sleep", "earthling", "skates", "randomizer")

BASE_LEVEL_TYPES = [0, 1, 5, 2, 7, 3, 4, 2, 6, 7, 2, 3, 6, 2, 4, 7, 2, 4, 2, 7, 4, 5, 1, 7]

CHARACTERS = ("Toejam", "Earl")

REV00_MD5 = "0a6af20d9c5b3ec4e23c683f083b92cd"
REV02_MD5 = "72dc91fd2c5528b384f082a38db9ddda"

#endregion

# player = AP-internal character value
def get_max_health(player: int, rank: int) -> int:
    return [23, 31][player] + 4*rank

# ROM-internal menu return values → AP-internal character values
def ret_val_to_char(ret_val: int) -> int:
    match ret_val:
        # ToeJam only
        case 1:
            return 0
        # Earl only
        case 2:
            return 1
        # Both
        case 0:
            return 2

# 0 = Toejam, 1 = Earl
def get_ram_addr(name: str, player: int = 0) -> int:
    if name in GLOBAL_RAM_ADDRS:
        return GLOBAL_RAM_ADDRS[name]
    addr, earl_offset = PLAYER_RAM_ADDRS[name]
    return addr + player * earl_offset

def get_datastructure(name: str) -> "DataStructure":
    if name in GLOBAL_DATA_STRUCTURES:
        return GLOBAL_DATA_STRUCTURES[name]
    return PLAYER_DATA_STRUCTURES[name]

PLAYER_RAM_ADDRS: dict[tuple[int, int]] = {
    # Main data store (P2 = P1 + 0x80)
    "POSITION": (0xA25A, 0x80),
    "STATE": (0xA289, 0x80),
    "SPRITE": (0xA2A5, 0x80),
    "LEVEL": (0xA2A6, 0x80),
    "GAME_OVER_FLAG": (0xA2A7, 0x80),
    "SPRITE_SET": (0xA2AC, 0x80),

    # Sequential, variable offset for Earl
    "CURRENT_BUTTONS": (0x801E, 0x1),
    "PREV_BUTTONS": (0x8020, 0x1),
    "HIGHEST_LEVEL_REACHED": (0x9132, 0x1),
    "LIVES": (0xA248, 0x1),
    "BUCKS": (0xA24A, 0x1),
    "POINTS": (0xA24C, 0x2),
    "RANK": (0xA250, 0x1),
    "HEALTH": (0xA252, 0x1),
    "HP_DISPLAY": (0xA254, 0x1),
    "HP_RESTORE": (0xA258, 0x1),
    "TILE_BELOW": (0xD9F4, 0x19),
    "FALL_STATE": (0xDA22, 0x1),
    "SLEEP_TIMER": (0xDA44, 0x2),
    "GLOBAL_ELEVATOR_STATE": (0xDA6A, 0x1),
    "INVENTORY": (0xDAC2, 0x10),
    "BURPS_LEFT": (0xDE62, 0x1),
    "BURP_TIMER" : (0xDE64, 0x1),
    "CUPID_HEART_REF": (0xE1DC, 0x1),
    "CUPID_EFF_TIMER": (0xE1DF, 0x2),
    "CUPID_EFF_TYPE": (0xE1E2, 0x1),
    "LEMONADE_STATE": (0xE396, 0x1)
}

GLOBAL_RAM_ADDRS: dict[int] = {
    "REDRAW_FLAG": 0x8022,
    "UNFALL_FLAG": 0x936C,
    #UNFALL_FLAG_2 = 0x936D
    "FLOOR_ITEMS": 0xDAE2,
    "END_ELEVATOR_STATE": 0xDA4F,
    "PRESENTS_ALL_DATA": 0xF300, # vanilla: 0xDA8A
    "PRESENTS_WRAPPING": 0xF300, # vanilla: 0xDA8A
    "PRESENTS_IDENTIFIED": 0xF300, # vanilla: 0xDA8A
    "DROPPED_PRESENTS": 0xDCE6,
    "COLLECTED_ITEMS": 0xDDE8,
    "EARTHLINGS": 0xDE72,
    "TRIGGERED_SHIP_ITEMS": 0xE212,
    "COLLECTED_SHIP_PIECES": 0xF444,
    "UNCOVERED_MAP_MASK": 0x91EC,
    "TRANSP_MAP_MASK": 0x92A2,
    "CURRENT_LEVEL_DATA": 0x81AA,
    # Special AP addresses
    "AP_CHARACTER": 0xF000,
    "AP_MAILBOX_ITEMS_BOUGHT": 0xF106,
    "AP_NUM_KEYS": 0xF455,
    "AP_NUM_MAP_REVEALS": 0xF456,
    "AP_LAST_REVEALED_MAP": 0xF457,
    "AP_DROP_PRESENT" : 0xF553,
    "AP_GIVE_ITEM": 0xF554,
    "AP_AUTO_PRESENT": 0xF555,
    "AP_AUTO_NO_POINTS": 0xF556,
    "AP_CUPID_TRAP": 0xF557,
    "AP_DIALOGUE_TRIGGER": 0xF558,
    "AP_DIALOGUE_LINE1": 0xF600,
    "AP_DIALOGUE_LINE2": 0xF60C,
    "AP_INIT_COMPLETE": 0xF6A0,
    "AP_LEVEL_ITEMS_SET": 0xF6A1,
    "AP_DEATH": 0xF6A2,
    "AP_BIG_ITEM_LV": 0xF6B0,
    "AP_MAILBOX_ITEM_BOUGHT": 0xF6B1,
    "AP_MAILBOX_ITEM_LEVEL": 0xF6B2,
    "AP_LAST_DMG_SOURCE" : 0xF6C0,
}

def get_slot_addr(name: str, slot: int, player: int = 0) -> int | None:
    if name in GLOBAL_DATA_STRUCTURES:
        structure = GLOBAL_DATA_STRUCTURES[name]
        addr = GLOBAL_RAM_ADDRS[name]
    else:
        structure = PLAYER_DATA_STRUCTURES[name]
        addr = get_ram_addr(name, player)
    if slot < 0 or slot > structure.max_slot:
        return None
    return addr + slot * structure.slot_size + structure.fixed_offset

class DataStructure(NamedTuple):
    max_slot: int
    slot_size: int # bytes
    fixed_offset: int # bytes

    def size(self) -> int:
        return (self.max_slot+1)*self.slot_size

    def repr_for_saving(self, data: bytes) -> str:
        return b64encode(data).decode("ascii")

    def repr_for_loading(self, data: str) -> bytes:
        return b64decode(data)

GLOBAL_DATA_STRUCTURES: dict[str, DataStructure] = {
    "COLLECTED_ITEMS": DataStructure(25, 4, 0),
    "FLOOR_ITEMS": DataStructure(31, 8, 0),
    "DROPPED_PRESENTS": DataStructure(31, 8, 0),
    "EARTHLINGS": DataStructure(28, 18, 0),
    "TRIGGERED_SHIP_ITEMS": DataStructure(9, 1, 0),
    "COLLECTED_SHIP_PIECES": DataStructure(9, 1, 0),
    "PRESENTS_WRAPPING": DataStructure(0x1B, 2, 0),
    "PRESENTS_IDENTIFIED": DataStructure(0x1B, 2, 1),
    "PRESENTS_ALL_DATA": DataStructure(2*0x1B, 1, 0),
    "TRANSP_MAP_MASK": DataStructure(25, 7, 0),
    "UNCOVERED_MAP_MASK": DataStructure(25, 7, 0),
    "AP_CHARACTER": DataStructure(0, 1, 0),
    "AP_NUM_KEYS": DataStructure(0, 1, 0),
    "AP_NUM_MAP_REVEALS": DataStructure(0, 1, 0),
    "AP_LAST_REVEALED_MAP": DataStructure(0, 1, 0),
    "AP_MAILBOX_ITEMS_BOUGHT": DataStructure(71, 1, 0)
}

PLAYER_DATA_STRUCTURES: dict[str, DataStructure] = {
    "HIGHEST_LEVEL_REACHED": DataStructure(0, 1, 0),
    "LEMONADE_STATE": DataStructure(0, 1, 0),
    "POINTS": DataStructure(0, 2, 0),
    "RANK": DataStructure(0, 1, 0),
    "BUCKS": DataStructure(0, 1, 0),
    "LIVES": DataStructure(0, 1, 0),
    "INVENTORY": DataStructure(15, 1, 0),
}

def expand_inv_constants() -> None:
    PLAYER_DATA_STRUCTURES["INVENTORY"] = DataStructure(63, 1, 0)
    PLAYER_RAM_ADDRS["INVENTORY"] = (0xF280, 0x40)

#region Save data–related

SAVE_DATA_POINTS_GLOBAL: tuple[str] = (
    "COLLECTED_ITEMS",
    "DROPPED_PRESENTS",
    "COLLECTED_SHIP_PIECES",
    "TRIGGERED_SHIP_ITEMS",
    "UNCOVERED_MAP_MASK",
    "TRANSP_MAP_MASK",
    "PRESENTS_ALL_DATA",
    "AP_CHARACTER",
    "AP_NUM_KEYS",
    "AP_NUM_MAP_REVEALS",
    "AP_LAST_REVEALED_MAP",
    "AP_MAILBOX_ITEMS_BOUGHT",
)

SAVE_DATA_POINTS_PLAYER: tuple[str] = (
    "HIGHEST_LEVEL_REACHED",
    "LEMONADE_STATE",
    "RANK",
    "POINTS",
    "BUCKS",
    "LIVES",
    "INVENTORY",
)

SAVE_DATA_POINTS_ALL = SAVE_DATA_POINTS_GLOBAL + SAVE_DATA_POINTS_PLAYER

#endregion