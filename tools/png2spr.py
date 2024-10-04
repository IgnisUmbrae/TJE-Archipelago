import sys
from pathlib import Path

from PIL import Image
from PIL.ImageColor import getrgb as rgb

type Palette = dict[int, tuple[int]]

#region Palettes

PALETTE_00 : Palette = {
    0: rgb("#FFFFFF00"),
    1: rgb("#00AA00FF"),
    2: rgb("#008800FF"),
    3: rgb("#006600FF"),
    4: rgb("#EEAA00FF"),
    5: rgb("#EE8800FF"),
    6: rgb("#CC6600FF"),
    7: rgb("#AA4400FF"),
    8: rgb("#222222FF"),
    9: rgb("#EEEE00FF"),
    10: rgb("#AAAA00FF"),
    11: rgb("#EEAAEEFF"),
    12: rgb("#CC00CCFF"),
    13: rgb("#660066FF"),
    14: rgb("#220044FF"),
    15: rgb("#000022FF")
}

PALETTE_02 : Palette = {
    0: rgb("#FFFFFF00"),
    1: rgb("#E08080FF"),
    2: rgb("#E06060FF"),
    3: rgb("#C04000FF"),
    4: rgb("#802000FF"),
    5: rgb("#E0E000FF"),
    6: rgb("#E0A000FF"),
    7: rgb("#E06000FF"),
    8: rgb("#E00000FF"),
    9: rgb("#4040E0FF"),
    10: rgb("#0000E0FF"),
    11: rgb("#400080FF"),
    12: rgb("#200040FF"),
    13: rgb("#FFFFFFFF"),
    14: rgb("#606060FF"),
    15: rgb("#000000FF")
}

PALETTE_03 : Palette = {
    0: rgb("#FFFFFF00"),
    1: rgb("#00AA00FF"),
    2: rgb("#008800FF"),
    3: rgb("#006600FF"),
    4: rgb("#EEAA00FF"),
    5: rgb("#EE8800FF"),
    6: rgb("#CC6600FF"),
    7: rgb("#AA4400FF"),
    8: rgb("#222222FF"),
    9: rgb("#EEEE00FF"),
    10: rgb("#AAAA00FF"),
    11: rgb("#EEAAEEFF"),
    12: rgb("#CC00CCFF"),
    13: rgb("#660066FF"),
    14: rgb("#220044FF"),
    15: rgb("#000000FF")
}

#endregion

PALETTES : list[Palette] = [PALETTE_00, None, PALETTE_02, PALETTE_03]

def colour_to_code(palette, colour : tuple[int]) -> int:
    if colour[3] == 0: return 0

    reverse_palette = {v: k for k, v in palette.items()}
    try:
        return reverse_palette[colour]
    except KeyError:
        print(f"Colour out of palette: {colour}; defaulting to transparent")
        return 0

def groups_of_n(data: list, n : int):
    return [data[i:i+n] for i in range(0, len(data), n)]

def guess_palette(data: list[int]) -> int:
    scores = []
    for palette in PALETTES:
        if palette == None: score = 0
        else:
            # Only counts matching non-transparent colours
            matches = [1 if d in palette.values() and d[3] != 0 else 0 for d in data]
            score = sum(matches)
        scores.append(score)
    return scores.index(max(scores))

def png_to_data(filepath: Path) -> None:
    png = Image.open(filepath)
    rgba = png.convert("RGBA")
    data = list(rgba.getdata())

    # Work out palette
    maybe_palette = guess_palette(data)
    print(f"Converting with palette {maybe_palette} (best guess).")
    palette = PALETTES[maybe_palette]

    num_columns, num_rows = rgba.size
    num_tile_columns = num_columns//8

    print("Regrouping pixel data to match VDP alignment…")
    data_rows = groups_of_n(data, num_columns)
    
    regrouped = []

    for i in range(num_tile_columns):
        for row in data_rows:
            # In each column, take the eight elements of each row that fall into that column and serialize
            split_rows = groups_of_n(row, 8)
            regrouped.extend(split_rows[i])

    # Pair up consecutive colours (each will be a nibble eventually)
    paired_data = [regrouped[i:i+2] for i in range(0, len(regrouped), 2)]

    out_data = bytearray()
    for pair in paired_data:
        palette_index = (colour_to_code(palette, pair[0]) << 4) + colour_to_code(palette, pair[1])
        out_data.append(palette_index)

    print("Saving binary data…")
    out_path = (filepath.absolute().parents[2] / "data" / "sprites" / filepath.name).with_suffix(".bin")
    with out_path.open("wb") as f:
        f.write(out_data)
    print("Done!")

if __name__ == "__main__":
    png_to_data(Path(sys.argv[1]))