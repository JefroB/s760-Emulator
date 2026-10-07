"""
mcs96_disasm.py - authoritative MCS-96 disassembly of the S-760 OS payload.

Uses pypcode (Ghidra's SLEIGH engine) with the bundled 'MCS96:LE:16:default'
language, so instruction decoding is authoritative (no hand-coded opcode
guessing). This replaces the earlier heuristic approaches.

Usage:
  python mcs96_disasm.py <image> --off 0x4800 --len 0x100 [--base 0x0000]

--off / --len are FILE offsets/length to read.
--base is the ADDRESS the first byte is assumed to live at in the MCS-96
        address space (affects displayed addresses + relative branch targets).
        Default 0 = show payload-relative addresses.

Because SLEIGH tracks each instruction length correctly, this also gives us a
clean linear-sweep disassembly we can trust for reading the reset/init code.
"""
import sys, argparse
import pypcode

def parse_num(s):
    s = str(s).strip()
    return int(s, 16) if s.lower().startswith("0x") else int(s, 10)

ap = argparse.ArgumentParser()
ap.add_argument("image")
ap.add_argument("--off", default="0x4800")
ap.add_argument("--len", default="0x100")
ap.add_argument("--base", default="0x0000")
args = ap.parse_args()

off = parse_num(args.off)
length = parse_num(args.len)
base = parse_num(args.base)

data = open(args.image, "rb").read()
code = data[off:off+length]

ctx = pypcode.Context("MCS96:LE:16:default")

addr = 0
out = []
while addr < len(code):
    try:
        tx = ctx.disassemble(code[addr:], base_address=base + addr, offset=0)
    except Exception as e:
        out.append(f"{base+addr:04X}: {code[addr]:02X}            <decode error: {e}>")
        addr += 1
        continue
    if not tx.instructions:
        out.append(f"{base+addr:04X}: {code[addr]:02X}            <no insn>")
        addr += 1
        continue
    ins = tx.instructions[0]
    raw = code[addr:addr+ins.length]
    hexbytes = ' '.join(f'{b:02X}' for b in raw)
    out.append(f"{base+addr:04X}: {hexbytes:<20} {ins.mnem} {ins.body}")
    addr += ins.length

print('\n'.join(out))
