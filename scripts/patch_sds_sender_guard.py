"""Build the experimental OS2.24 sender-admission repair for BUG-121.

Includes BUG-118/119/120. New transfers require receive state 2BBA=0 and
sender state B1AE=FF. Original firmware must remain immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path

from patch_sds_request_guard import (COMMANDS, IMAGE_SIZE, SOURCE_SHA256,
                                     TABLE_OFFSET, patches as request_patches)

HEADER_TAIL=bytes.fromhex(
    '28 F3 29 50 DB 1A 2A A7 DB 16 EF E8 E1 A1 FF FF 5C '
    'C3 01 A0 B1 5C C3 01 A2 B1 5C EF 67 07 F8 F0 EF 4E 07 F9 F0')


def short_call(pc,target):
    delta=target-(pc+2)
    if not -1024<=delta<=1023:raise ValueError('Short call out of range')
    return bytes((0x28|((delta&0x7FF)>>8),delta&255))


def long_call(pc,target):
    return bytes([0xEF])+((target-pc-3)&65535).to_bytes(2,'little')


def patches():
    spans=request_patches()
    offset,base,before,old=spans[0]
    # Retain command lookup/table. Repack header setup in the existing extent.
    code=bytearray(old[:0x6D08-base])
    code+=short_call(0x6D08,0x6D20)+bytes.fromhex('D7 24')
    code+=short_call(0x6D0C,0x6E05)+short_call(0x6D0E,0x6E64)+bytes.fromhex('DB 1E')
    code+=short_call(0x6D12,0x6FBF)+bytes.fromhex('DB 1A')
    code+=long_call(0x6D16,0x4F05)+short_call(0x6D19,0x6AA5)
    code+=long_call(0x6D1B,0x7495)+bytes.fromhex('F8 F0')
    assert base+len(code)==0x6D20
    # Z iff receive=0 AND sender=FF. R6A is existing parser scratch.
    # This returns flags only; it never changes owner state or transfer data.
    code+=bytes.fromhex('B3 01 AE B1 6A 17 6A 93 01 BA 2B 6A F0 FD FD FD')
    assert base+len(code)==0x6D30
    code+=HEADER_TAIL[-5:]  # Existing CANCEL/SETC/RET remains at 6D30.
    spans[0]=(offset,base,before+HEADER_TAIL,bytes(code))
    # Both request types share the same temporary 2-byte admission call frame.
    request=(short_call(0x6D81,0x6D20)+bytes.fromhex('D7 AB')
             +long_call(0x6D85,0x7370)+bytes.fromhex('F0 FD FD FD FD FD'))
    offset,base,before,_=spans[-2]
    spans[-2]=(offset,base,before,request)
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
                limitation='Experimental SDS transfer admission in both directions; disk exclusion, timeouts, stereo and physical behavior remain unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(patch_image(args.input, args.output), indent=2))
