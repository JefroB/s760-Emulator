"""Build an experimental OS2.24 header-admission repair for BUG-118/119.

Keep receive completion and allocation errors busy until supervisor cleanup.
This qualifies SDS header admission, not exclusion of every MIDI/disk command.
"""
import argparse
import hashlib
import json
from pathlib import Path

from patch_sds_cancel_guard import (COMMANDS, END, IMAGE_SIZE, ORIGINAL, PC,
                                    SOURCE_SHA256, START, TABLE_OFFSET, dispatcher)

COMPLETE = 0xFF


def sjmp(pc, target):
    displacement = target - (pc + 2)
    if not -1024 <= displacement <= 1023:
        raise ValueError('Short jump out of range')
    return bytes((0x20 | ((displacement & 0x7FF) >> 8), displacement & 255))


def patches():
    # Indirect word reads save four bytes in the original completion routine.
    # RW6A is scratch in the enclosing MIDI parser; no caller-live register added.
    completion = bytes.fromhex(
        'A1 98 B1 6A A2 6B 5C A2 6B 5E A2 6B 60 A2 6A 62 '
        'C5 60 5C D9 09 B1 FF 6A C7 01 BA 2B 6A FD F0')
    error_entry = bytes.fromhex('99 05 30 D1 09') + sjmp(0x899D, 0x8905) + bytes([0xFD]*7)
    # Share the CRT/LCD CE62 call, then join the existing final state/parser clear.
    error_exit = (bytes.fromhex('DF 06 A1 32 F7 1E 20 04 A1 CC DA 1E EF F9 43')
                  + sjmp(0x8A69, 0x8905) + bytes([0xFD]*2))
    return [
        (START, PC, ORIGINAL, dispatcher()),
        (0xF78F, 0x738F, bytes.fromhex(
            'A3 01 98 B1 5C A3 01 9A B1 5E A3 01 9C B1 60 A3 01 9E B1 62 '
            'C5 60 5C D9 05 C7 01 BA 2B 00 F0'), completion),
        # Legal positive errors go to 8998; 1 and FF use 8810. FF-1 has N set
        # without overflow; 80-1 would have N clear and misroute MCS96 JGT.
        (0x5E7E4, 0x87E4, bytes.fromhex('99 01 30 D7 04'), bytes.fromhex('99 01 30 D2 04')),
        (0x5E848, 0x8848, bytes.fromhex('98 00 DA'), bytes.fromhex('99 FF DA')),
        (0x5E998, 0x8998, bytes.fromhex('C7 01 BA 2B 00 B1 08 72 99 05 30 D1 01 F0'), error_entry),
        (0x5EA5A, 0x8A5A, bytes.fromhex('DF 09 A1 32 F7 1E EF FF 43 20 07 A1 CC DA 1E EF F6 43 F0'), error_exit),
    ]


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
                limitation='Experimental SDS header admission only; other command families, stereo and physical behavior remain unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(patch_image(args.input, args.output), indent=2))
