"""
make_blank.py - create blank 1.44MB (0x168000-byte) floppy image(s) to use as
Gotek dump/save targets. Size-exact to a real 2880x512 HD floppy.

Single:
  python make_blank.py <out.img> [--fill 00|FF|0F]

Batch (make a folder full of ready-to-use blanks):
  python make_blank.py --batch <count> [--dir temp/blanks] [--fill 00]
                       [--name blank] [--start 1]
  e.g. python make_blank.py --batch 10 --dir temp/blanks
       -> temp/blanks/blank_01.IMG .. blank_10.IMG

NOTE: raw blank (no S-760 filesystem). The S-760 "Save System"/format writes its
own format, so a raw 0x00 blank is a fine target. Default fill 0x00.
"""
import os, argparse
SIZE = 0x168000  # 1,474,560 bytes

ap = argparse.ArgumentParser()
ap.add_argument("out", nargs="?", help="output path (single-file mode)")
ap.add_argument("--fill", default="00", help="fill byte in hex (e.g. 00, FF, 0F)")
ap.add_argument("--batch", type=int, help="make N blanks in a folder")
ap.add_argument("--dir", default="temp/blanks", help="output folder for --batch")
ap.add_argument("--name", default="blank", help="base name for --batch files")
ap.add_argument("--start", type=int, default=1, help="starting index for --batch")
args = ap.parse_args()

fill = int(args.fill, 16) & 0xFF
data = bytes([fill]) * SIZE
assert len(data) == SIZE

def write(path):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    print(f"Wrote {path} ({len(data)} bytes, fill=0x{fill:02X})")

if args.batch:
    for i in range(args.start, args.start + args.batch):
        write(os.path.join(args.dir, f"{args.name}_{i:02d}.IMG"))
    print(f"Done: {args.batch} blanks in {args.dir}")
elif args.out:
    write(args.out)
else:
    ap.error("provide <out> for single mode, or --batch N for batch mode")
