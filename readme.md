# TJE-Archipelago

## What is this?

This lets you play the classic Sega ~~Genesis~~ Mega Drive game _Toejam & Earl_ in [Archipelago](https://archipelago.gg) as part of a multiworld.

## Features

### Base

- Checks for all collectible items and ship pieces, plus extra checks for ranks
- _Seeded_ random world, unchanged on reset

### Extra

Additions over the base game include:

- New sprites for AP items, ship pieces and hints
- Configurable starting presents, game over handling, and more
- Progress is saved when paused, when travelling between levels (both up and down), and on game over
- Customize level randomization, numbers of items, and more
- New items:
  - Elevator keys, which are required to unlock elevators
  - Map revealers, which uncover the map five levels at a time
  - The Up-Warp present, which replaces Un-Fall and _always_ sends you up one level

## Caveats

- Item handling is currently entirely remote except for starting presents. In particular this means that every item in the game appears as an AP logo.
- Neither Earl nor 2-player mode is currently supported.
- Hints are yet to be implemented and locations are generically-named, so in multiworlds it's recommended to play with `restrict_prog_items: yes` to avoid having to scour the map for a singular progression item in a weird location.

## Setup

### Requirements

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 5.0.0+
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.9.1+
- The latest [Toejam & Earl AP World](https://github.com/IgnisUmbrae/TJE-Archipelago/releases)
- A legally-obtained **REV 02** Toejam & Earl ROM, the easiest source of which is [the Steam release](https://store.steampowered.com/app/71166/ToeJam__Earl/). **REV 00 is not supported.**

### Instructions

1. Locate your Toejam & Earl REV 02 ROM. If you own the Steam version, you can right-click it in your library, select Manage → Browse Local Files and locate `ToeJamEarl.SGD` in the `uncompressed ROMs` folder. Copy that file to the root of your Archipelago directory.

2. Add these lines to `host.yaml` so the client knows where your ROM file is (changing the name if needed):

```
tje_options:
  rom_file: "ToeJamEarl.SGD"
```

3. Place the downloaded `tje.apworld` file into the `custom_worlds` subfolder of your Archipelago installation.

4. Create a YAML. You can use [the example](https://github.com/IgnisUmbrae/TJE-Archipelago/blob/main/docs/example.yaml) as a quickstart. Add this to the `Players` subfolder if you're hosting locally, or upload it to the host otherwise.

5. Now you or the host can generate a world. Archipelago will also generate a patch with the extension `.aptje`; the easiest way to use this is via the Patch function in the launcher, which will apply the patch to the ROM and automatically launch BizHawk along with the client. (You may be asked to locate one or both of these.)

6. BizHawk will also pop up its Lua scripting window, in which you'll need to enable the script `connector_bizhawk_generic` by double clicking it. Now everything will connect together. It's recommended not to begin the game until the client has successfully connected to both BizHawk and the AP host.

## Questions, feedback, etc

Come and visit us in [our corner of the Archipelago Discord](https://discord.com/channels/731205301247803413/1204326236415856671).

## Credits

I owe a great debt of gratitude to:

- **slab**, whose hand-labelled disassembly and knowledge of the game's internal workings has been invaluable
- **DrKelexo**, for being the first to brave the very first release, reams of early feedback, and some stellar spritework
- **Everyone** in the ToeJam & Earl section of the Archipelago Discord for their frequent testing, feedback and suggestions
