# TJE-Archipelago

## What is this?

This lets you play the classic Sega Mega Drive/Genesis game _Toejam & Earl_ in [Archipelago](https://archipelago.gg) as part of a multiworld.

## Features

### Base

- Checks for all collectible items and ship pieces, plus extra checks for ranks
- _Seeded_ random world, unchanged on reset

### Extra

Additions over the base game include:

- Server-side saving & loading
- New sprites for AP items, ship pieces and extra items
- Configurable starting presents, game over handling, and more
- Customize details of level randomization, number of levels, numbers of items, and much more
- New items:
  - Elevator keys, which are required to unlock elevators
  - Map revealers, which uncover the map five levels at a time
  - The Up-Warp present, which replaces Un-Fall and _always_ sends you up one level
  - Traps that spawn Earthlings, instantly give you Rocket Skates, scramble your controls, and more

## Caveats

- 2-player mode is not currently supported.
- Hints are yet to be implemented and locations are generically-named.

## Tracker

A tracker developed by GrayGooGlitch is available [on GitHub here](https://github.com/graygooglitch/Toejam-and-Earl-AP-Tracker/) and requires TJE-AP version 0.2.4c or higher.

## Setup

### Requirements

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 5.0.0+
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.9.1+
- The latest [Toejam & Earl AP World](https://github.com/IgnisUmbrae/TJE-Archipelago/releases)
- A legally-obtained **REV 02** Toejam & Earl ROM, the easiest source of which is [the Steam release](https://store.steampowered.com/app/71166/ToeJam__Earl/). **REV 00 is not supported.**

### Instructions

0. Install BizHawk, install Archipelago, and obtain a ROM file.

1. Place the downloaded `tje.apworld` file into the `custom_worlds` subfolder of your Archipelago installation.

2. Create a YAML with the settings of your choice. You can also use [the example](https://github.com/IgnisUmbrae/TJE-Archipelago/blob/main/docs/example.yaml) as a quickstart. Add this to the `Players` subfolder if you're hosting locally, upload it to the host otherwise.

3. Now you or the host can generate a world; Archipelago will also generate a patch with the extension `.aptje`. Use the Patch function in the launcher to apply the patch to the ROM and automatically launch BizHawk along with the client. If this is your first time, you will be prompted to locate one or both of BizHawk and the ROM file.

4. Now BizHawk will pop up its Lua scripting window. If the `connector_bizhawk_generic` script isn't already enabled, enable it by double clicking it and everything will connect together.

5. To avoid issues with items and/or save data desyncing, wait until the client has successfully connected to _both_ BizHawk _and_ the AP host before selecting "Play new game -- AP World" from the menu to actually start playing.

## Questions, feedback, etc

Come and visit us in [our corner of the Archipelago Discord](https://discord.com/channels/731205301247803413/1204326236415856671).

## Credits

I owe a great debt of gratitude to:

- **slab**, whose hand-labelled disassembly and knowledge of the game's internal workings has been invaluable
- **DrKelexo**, for being the first to brave the very first release, reams of early feedback, and some stellar spritework
- **GrayGooGlitch**, for creating the most lovely tracker in apparently no time at all
- **Everyone** in the ToeJam & Earl section of the Archipelago Discord for their frequent testing, feedback and suggestions
