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
- Configurable starting presents, game over handling (soon), and more
- Elevator keys: new items that unlock elevators when found
- Optionally change Un-Fall presents into Up-Warps, which _always_ send you up one level

## Caveats

- Game overs are not currently handled and will reset your progress. It's recommended to play with infinite lives for the time being.
- Item handling is (currently) entirely remote except for starting presents. In particular this means that every item in the game appears as an AP logo.
- Neither Earl nor 2-player mode is currently supported.
- Hints are yet to be implemented and locations are generically-named, so in multiworlds it's recommended to play with `restrict_prog_items: yes` to avoid having to scour the map for a singular progression item.

## Setup

### Requirements

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 5.0.0+
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.9.1+
- The latest [Toejam & Earl AP World](https://github.com/IgnisUmbrae/TJE-Archipelago/releases)
- A legally-obtained copy of **REV 02** Toejam & Earl ROM, the easiest source of which is [the Steam release](https://store.steampowered.com/app/71166/ToeJam__Earl/). **REV 00 is not supported.**

### Instructions

Place the downloaded `.apworld` file into the `worlds` subfolder of your Archipelago installation. Now you're ready to generate a world.

Generating a world will also generate a patch. You can use the Patch function in the launcher to apply the patch to the ROM and automatically launch BizHawk along with the client. BizHawk will also pop up its Lua scripting window, in which you'll need to enable the connector script by double clicking it.

## Configuration

See the [Options readme](https://github.com/IgnisUmbrae/TJE-Archipelago/docs/yaml-options.md) (TBC).

## Credits

I owe a great debt of gratitude to, in no particular order:

- **slab**, whose hand-labelled disassembly and knowledge of the game's internal workings has been invaluable
- **DrKelexo**, for being the first to brave the very first release, reams of early feedback, and some stellar spritework
- **Everyone** in the ToeJam & Earl section of the Archipelago Discord for their frequent testing, feedback and suggestions