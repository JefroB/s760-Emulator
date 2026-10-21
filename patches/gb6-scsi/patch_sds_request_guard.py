"""Build the experimental OS2.24 outgoing-request guard for BUG-120.

Includes the BUG-118/119 header lifecycle repairs. Reject command 03 while a
receive owns state 2BBA, before slot decoding, voice stop or sender setup.
"""
import argparse
import hashlib
import json
from pathlib import Path

from patch_sds_header_lifecycle import (COMMANDS, IMAGE_SIZE, SOURCE_SHA256,
                                        TABLE_OFFSET, patches as header_patches)

REQUEST = bytes.fromhex('EF EC 05 DB 06 EF D1 FB DB 01 F0 F9 F0')
DECODE = bytes.fromhex('A1 4F B0 5C B2 5D 5E B2 5D 5F 19 01 5E 08 01 5E '
                       'C3 01 80 B1 5E 89 FF 01 5E D9 02 F8 F0 F9 F0')


def patches():
    # The existing 13-byte request handler becomes a guard and decoder call.
    # Busy requests use the existing CANCEL/SETC return without decoding B180.
    request = bytes.fromhex('9B 01 BA 2B 00 D7 A8 EF E5 05 F0 FD FD')
    # CMP slot,#512 supplies the correct carry for both valid and invalid
    # slots. Removing redundant CLRC/SETC makes room for a tail jump to the
    # original sender. Its return consumes the decoder call's existing frame.
    decoder = DECODE[:21]+bytes.fromhex('89 00 02 5E DB 03 E7 CC F5 F0')
    return header_patches()+[
        (0xF181,0x6D81,REQUEST,request),
        (0xF770,0x7370,DECODE,decoder),
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
                limitation='Experimental receive-owner protection against outgoing requests; outgoing-session ownership, disk/stereo and physical behavior remain unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(patch_image(args.input, args.output), indent=2))
