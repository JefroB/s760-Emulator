"""Build an experimental OS2.24 SDS header guard for BUG-118.

Reject headers while transfer state 2BBA is nonzero, before header decoding or
allocation. Repack the existing dispatcher; no new RAM or free-space claim.
This is a cancellation fix, not a complete transfer-ownership protocol.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'
IMAGE_SIZE = 0x168000
START, END, PC = 0xF0DD, 0xF110, 0x6CDD
ORIGINAL = bytes.fromhex(
    'B3 01 48 B0 6A A1 58 B1 5C B2 5D 6B 99 FF 6B D7 02 F9 F0 '
    '98 6B 6A D7 F1 69 59 B1 5C 64 5C 5C 65 02 6D 5C E3 5C '
    '20 0C 20 2F 20 79 20 84 20 83 20 95 20 C5')
TABLE_OFFSET = 0x4800 + (0x2BE << 10) + 0x3158
COMMANDS = bytes.fromhex('01 02 03 7C 7D 7E 7F FF')


def dispatcher():
    code = bytearray(bytes.fromhex('B3 01 48 B0 6A A1 58 B1 5C B2 5D 6B'))
    # All valid table entries have bit 7 clear; FF branches to existing SETC/RET.
    code.extend((0x3F, 0x6B, 0x6D33 - (PC + len(code) + 3)))
    code.extend(bytes.fromhex('98 6B 6A D7 F5 64 5C 5C 65 48 0A 5C E3 5C'))
    assert PC + len(code) == 0x6CFA
    # 2*(B159 + index) + 0A48 = 6CFA + 2*index (16-bit arithmetic).
    for target in (0x6D08, 0x6D35, 0x6D81, 0x6D8E, 0x6D8F, 0x6DA3, 0x6DD5):
        displacement = target - (PC + len(code) + 2)
        assert -1024 <= displacement <= 1023
        code.extend((0x20 | ((displacement & 0x7FF) >> 8), displacement & 255))
    assert PC + len(code) == 0x6D08
    # Busy -> existing CANCEL response and SETC/RET, without touching the owner.
    code.extend(bytes.fromhex('9B 01 BA 2B 00 D7 21 FD'))
    assert len(code) == END - START
    return bytes(code)


def patch_image(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Output must differ from the original image')
    if output.suffix.lower() != '.img':
        raise ValueError('Use an .IMG output filename')
    original = source.read_bytes()
    if len(original) != IMAGE_SIZE or hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('Input must be the original unmodified OS2.24 baseline')
    assert original[START:END] == ORIGINAL
    assert original[TABLE_OFFSET:TABLE_OFFSET + 8] == COMMANDS
    patched = bytearray(original)
    patched[START:END] = dispatcher()
    import pypcode
    decoded = pypcode.Context('MCS96:LE:16:default').disassemble(dispatcher(), base_address=PC).instructions
    assert sum(i.length for i in decoded) == END - START
    with output.open('xb') as target:
        target.write(patched)
    return dict(source_sha256=SOURCE_SHA256, output_sha256=hashlib.sha256(patched).hexdigest(),
                bytes=len(patched), output=str(output),
                diff=[dict(offset=f'{i:06X}', before=a, after=b)
                      for i, (a, b) in enumerate(zip(original, patched)) if a != b],
                decoded=[dict(pc=f'{i.addr.offset:04X}', length=i.length, mnemonic=i.mnem, operands=i.body)
                         for i in decoded],
                limitation='Native cancellation guard; full completion/error ownership and hardware acceptance remain open')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(patch_image(args.input, args.output), indent=2))
