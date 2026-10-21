"""Build the experimental OS2.24 local Sample Dump cleanup repair (BUG-122).

Includes BUG-118..121. Consolidate three native UI exit tails and release
the sender flag after parser/display cleanup. Preserve the current data bank
with one temporary 2-byte stack word; no new RAM/code region is allocated.
"""
import argparse
import hashlib
import json
from pathlib import Path

from patch_sds_sender_guard import (COMMANDS, IMAGE_SIZE, SOURCE_SHA256,
                                    TABLE_OFFSET, long_call,
                                    patches as sender_patches)


def jump(pc,target):
    delta=target-pc-2
    if not -1024<=delta<=1023:raise ValueError('Short jump out of range')
    return bytes((0x20|((delta&0x7FF)>>8),delta&255))


def patches():
    spans=sender_patches()
    common=bytes.fromhex('C7 01 BA 2B 00 B1 08 72 9B 01 76 24 00 DF 61 A1 32 F7 1E')
    common+=long_call(0x9AB3,0xCE62)+jump(0x9AB6,0x9BAA)+bytes([0xFD])*4
    second=jump(0x9B0B,0x9AA0)+bytes([0xFD])*3
    second+=jump(0x9B10,0x9BAA)+bytes([0xFD])*21
    third=jump(0x9BA8,0x9AA0)+bytes.fromhex(
        'CB 01 0C 01 A1 BE 02 1C C3 01 0C 01 1C '
        'B1 FF DA C7 01 AE B1 DA CF 01 0C 01 F0')
    before='C7 01 AE B1 00 C7 01 BA 2B 00 B1 08 72 9B 01 76 24 00 DF 07 A1 32 F7 1E EF '
    for offset,pc,tail,after in [(0x5FAA0,0x9AA0,'A7 33 F0',common),
                                (0x5FB0B,0x9B0B,'3C 33 F0',second),
                                (0x5FBA8,0x9BA8,'9F 32 F0',third)]:
        spans.append((offset,pc,bytes.fromhex(before+tail),after))
    return spans

def patch_image(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Output must differ from the original image')
    if output.suffix.lower() != '.img':
        raise ValueError('Use an .IMG output filename')
    original = source.read_bytes()
    if len(original) != IMAGE_SIZE or hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('Input must be the original unmodified OS2.24 baseline')
    if original[TABLE_OFFSET:TABLE_OFFSET+8] != COMMANDS:
        raise ValueError('Unexpected SDS command table')
    import pypcode
    ctx = pypcode.Context('MCS96:LE:16:default')
    patched = bytearray(original); decoded = []
    for offset, pc, before, after in patches():
        if len(before) != len(after) or original[offset:offset+len(before)] != before:
            raise ValueError(f'Hook byte/length mismatch at {offset:06X}')
        instructions = ctx.disassemble(after, base_address=pc).instructions
        if sum(i.length for i in instructions) != len(after):
            raise ValueError(f'Instruction boundary mismatch at {pc:04X}')
        patched[offset:offset+len(after)] = after
        decoded.append(dict(offset=offset, pc=pc, before=before.hex(), after=after.hex(),
                            instructions=[dict(pc=i.addr.offset, length=i.length, mnemonic=i.mnem, operands=i.body)
                                          for i in instructions]))
    with output.open('xb') as target:
        target.write(patched)
    return dict(source_sha256=SOURCE_SHA256, output_sha256=hashlib.sha256(patched).hexdigest(),
                output=str(output), bytes=len(patched), patches=decoded,
                diff=[dict(offset=i, before=a, after=b) for i,(a,b) in enumerate(zip(original,patched)) if a!=b],
                limitation='Experimental SDS transfer admission in both directions; local UI exit repair; local/remote overlap, disk exclusion, timeouts, stereo and physical behavior remain unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(patch_image(args.input, args.output), indent=2))
