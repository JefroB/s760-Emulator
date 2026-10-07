"""
mcs96_trace.py - recursive-descent control-flow tracer for the S-760 OS.

This is static "watch the code" infrastructure: instead of a full CPU emulator
(which we can't build reliably without the boot ROM + hardware model), we follow
the actual control flow from known entry points using the authoritative pypcode
MCS-96 decoder. It:
  - starts at one or more entry addresses,
  - decodes instructions (correct lengths via SLEIGH),
  - follows SCALL/LCALL/SJMP/LJMP/conditional-jump targets that stay inside the
    resident 64KB image,
  - stops at RET/unconditional-jump leaves,
  - records every distinct routine entry, and every memory-mapped I/O access
    (addresses >= IO_BASE), so we can see which peripherals a routine touches.

Because it follows real edges (not a linear sweep) the disassembly it prints is
trustworthy for reading. Targets outside the resident window are logged as
"far/banked" for later (they need emulation or the loader's segment table).

Usage:
  python mcs96_trace.py S760224.IMG --entry 0x2080 [--entry 0x2831] [--max 4000]
  python mcs96_trace.py S760224.IMG --entry 0x54e8 --io      # show I/O for a routine

Address model: runtime address A maps to file offset 0x4800 + (A - 0x2080),
valid for the resident image A in [0x2080, 0xFFFF].
"""
import sys, argparse
import pypcode

BASE = 0x2080
FILE_OFF = 0x4800
RESIDENT_LO = 0x2080
RESIDENT_HI = 0xFFFF
IO_BASE = 0xF000          # gate-array / peripheral window (see findings F24/F26)

def parse_num(s):
    s = str(s).strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s, 10)

def file_of(addr):
    return FILE_OFF + (addr - BASE)

def in_resident(addr):
    return RESIDENT_LO <= addr <= RESIDENT_HI

ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("--entry", action="append", required=True,
                help="entry address (hex). Repeatable.")
ap.add_argument("--max", default="20000", help="max instructions to trace")
ap.add_argument("--io", action="store_true", help="print I/O access summary")
ap.add_argument("--print", dest="do_print", action="store_true",
                help="print the decoded instructions as they are traced")
args = ap.parse_args()

data = open(args.image, "rb").read()
ctx = pypcode.Context("MCS96:LE:16:default")
maxi = parse_num(args.max)

# control-flow mnemonics
COND = {"JC","JNC","JE","JNE","JH","JNH","JGE","JLT","JGT","JLE","JV","JNV",
        "JVT","JNVT","JST","JNST","JBS","JBC","DJNZ","DJNZW"}
CALL = {"SCALL","LCALL"}
UJMP = {"SJMP","LJMP","BR"}

seen = set()          # addresses already decoded (avoid loops)
routines = set()      # discovered routine entries (call targets)
far_targets = set()   # targets outside resident window (banked/overlay)
io_accesses = []      # (from_addr, mnem, body, io_addr)
worklist = [parse_num(e) for e in args.entry]
routines.update(worklist)
count = 0

def decode_at(addr):
    fo = file_of(addr)
    if fo < 0 or fo + 8 > len(data):
        return None
    try:
        tx = ctx.disassemble(data[fo:fo+8], base_address=addr, offset=0)
        if tx.instructions and tx.instructions[0].length > 0:
            return tx.instructions[0]
    except Exception:
        return None
    return None

def target_of(ins, addr):
    tok = ins.body.strip().split()[-1].rstrip(",")
    try:
        t = int(tok, 16) if tok.lower().startswith("0x") else int(tok)
    except ValueError:
        return None
    if t < 0:
        t = (addr + ins.length + t) & 0xFFFF
    return t & 0xFFFF

import re
hex_re = re.compile(r"0x([0-9a-fA-F]{3,4})")

while worklist and count < maxi:
    addr = worklist.pop()
    # trace straight-line until a leaf
    while addr not in seen and count < maxi:
        ins = decode_at(addr)
        if ins is None:
            break
        seen.add(addr)
        count += 1
        m = ins.mnem.upper()
        if args.do_print:
            raw = data[file_of(addr):file_of(addr)+ins.length]
            hx = ' '.join(f'{b:02X}' for b in raw)
            print(f"{addr:04X}: {hx:<20} {m} {ins.body}")
        # record I/O accesses
        for mm in hex_re.finditer(ins.body):
            v = int(mm.group(1), 16)
            if v >= IO_BASE and m not in COND and m not in UJMP:
                io_accesses.append((addr, m, ins.body, v))
                break
        # control flow
        if m == "RET" or m == "RETI":
            break
        if m in CALL:
            t = target_of(ins, addr)
            if t is not None:
                if in_resident(t):
                    if t not in seen:
                        routines.add(t); worklist.append(t)
                else:
                    far_targets.add(t)
            addr += ins.length          # calls return -> continue after
            continue
        if m in UJMP:
            t = target_of(ins, addr)
            if t is not None:
                if in_resident(t):
                    addr = t
                    continue
                else:
                    far_targets.add(t)
                    break
            break
        if m in COND:
            t = target_of(ins, addr)
            if t is not None:
                if in_resident(t):
                    if t not in seen:
                        worklist.append(t)
                else:
                    far_targets.add(t)
            addr += ins.length          # fall-through
            continue
        addr += ins.length

print(f"\n=== trace summary ===")
print(f"instructions decoded: {count}")
print(f"distinct routine entries discovered: {len(routines)}")
print(f"far/banked targets (outside 0x{RESIDENT_LO:X}-0x{RESIDENT_HI:X}): {len(far_targets)}")
if far_targets:
    fs = sorted(far_targets)
    print("  " + " ".join(f"{t:04X}" for t in fs[:32]) + (" ..." if len(fs) > 32 else ""))

if args.io or io_accesses:
    from collections import Counter
    c = Counter(a[3] for a in io_accesses)
    print(f"\nI/O-window accesses (>=0x{IO_BASE:X}): {len(io_accesses)} total")
    for addr_io, cnt in sorted(c.items()):
        print(f"  0x{addr_io:04X}: {cnt}")
