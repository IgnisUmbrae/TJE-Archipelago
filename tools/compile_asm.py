import subprocess
from pathlib import Path

IN_DIR, OUT_DIR = Path("./asm/src/"), Path("../data/asm_bin")
IN_EXT, OUT_EXT = ".x68", ".bin"
BASE_CMD = f"vasmm68k_mot -I./asm/include -Fbin -o"

in_files = tuple(IN_DIR.glob(f"*{IN_EXT}"))

if not OUT_DIR.exists():
    OUT_DIR.mkdir()
for i, f in enumerate(in_files):
    basename = f.name.removesuffix(".x68")
    cmd = " ".join((BASE_CMD, OUT_DIR.joinpath(basename + OUT_EXT).as_posix(), IN_DIR.joinpath(basename + IN_EXT).as_posix()))
    print(f"({i+1}/{len(in_files)}) Assembling {basename}…")
    subprocess.Popen(cmd, stdout=subprocess.DEVNULL)
print("Done!")