import subprocess
import re
import json
import time
from os.path import getmtime
from pathlib import Path
from collections import defaultdict

import yaml

# Printing constants

SECTION_SEP = ""

# Dirs & filenames

SRC_DIR, BIN_DIR, SYM_DIR, JSON_DIR = Path("./asm/src/"), Path("../data/asm_bin/"), Path("./asm/sym/"), \
                                      Path("../data/json/")
REPATCH_JSON_FN = "dynamic_repatch_offsets.json"
SRC_EXT, BIN_EXT, SYM_EXT = ".x68", ".bin", ".sym"
BASE_CMD = "vasmm68k_mot -I./asm/include -Fbin -L {} -o {} {}"
YAML_PATH = Path("./compile_asm.yaml")

# Read config

if not YAML_PATH.exists():
    YAML_PATH.touch()
with YAML_PATH.open() as f:
    yaml_data = yaml.load(f, Loader=yaml.Loader)
if yaml_data is None:
    yaml_data = dict()

# Compile x68 to raw binary

in_src_files = tuple(SRC_DIR.glob(f"*{SRC_EXT}"))

if not SYM_DIR.exists():
    SYM_DIR.mkdir()
if not BIN_DIR.exists():
    BIN_DIR.mkdir()

errored_files = []
error_log = []
print("Compiling modified source files", end=" ")
for i, f in enumerate(in_src_files):
    basename = f.name.removesuffix(SRC_EXT)
    retcode = None
    if getmtime(f) > yaml_data.get("last_compiled_time", 0):
        cmd = BASE_CMD.format(
            SYM_DIR.joinpath(basename + SYM_EXT).as_posix(),
            BIN_DIR.joinpath(basename + BIN_EXT).as_posix(),
            SRC_DIR.joinpath(basename + SRC_EXT).as_posix()
            )
        proc = subprocess.run(cmd, capture_output=True)
        retcode = proc.returncode
    match retcode:
        case None:
            out_str = "."
        case 0:
            out_str = "✔"
        case _:
            out_str = "✕"
            errored_files.append(f.name)
            error_log.append(proc.stderr.decode())
    print(out_str, end="")

if errored_files:
    print("⚠ The following files failed to compile (see log for details):")
    for file in errored_files:
        print(f"\t• {file}")
    with open("compile_errors.log", "w") as f:
        f.write(("-"*10+"\n\n").join(error_log))
else:
    print(SECTION_SEP)

# Process symbol tables and collect dynamic patches

in_sym_files = tuple(SYM_DIR.glob(f"*{SYM_EXT}"))
sym_regex = re.compile(r"([0-9A-F]{8})\s(DYNRP.*)$")
repatch_list = defaultdict(dict)

print("Extracting dynamic repatch information from symbol tables", end=" ")
for i, f in enumerate(in_sym_files):
    basename = f.name.removesuffix(SYM_EXT)
    with f.open() as file:
        contents = file.readlines()
        out_str = "."
        for line in contents:
            matches = sym_regex.findall(line)
            if matches:
                for offset, rpname in matches:
                    repatch_list[basename].update({
                            rpname.removeprefix("DYNRP_") : int(offset, base=16)
                        })
                out_str = "✔"
        print(out_str, end="")
print(SECTION_SEP)

print("All assembly complete.")

if not JSON_DIR.exists():
    JSON_DIR.mkdir()
with (JSON_DIR / REPATCH_JSON_FN).open("w") as f:
    json.dump(repatch_list, f, indent=2)

# Update config

yaml_data["last_compiled_time"] = time.time()
with YAML_PATH.open("w") as f:
    f.write(yaml.dump(yaml_data, Dumper=yaml.Dumper))