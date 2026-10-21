"""Correct four OS2.24 disk-warning label sequences without relocating resources."""
from pathlib import Path
import argparse
import hashlib
import json

CRT_BEFORE = b'You will lose all the existing\0\x01\x06\xf0in this \x01\x85.\0'
CRT_AFTER = b'All existing data on this\0\x01\x06\xf0\x01\x85 will be lost.\0'
LCD_BEFORE = b'You will lose\0\x05\x04\x01all the existing\0\x0a\x05\x01in this \x01\x85.\0'
LCD_AFTER = b'All existing data\0\x02\x04\x01on this \x01\x85\0\x02\x05\x01will be lost.\0'
PATCHES = ((0xC162C, CRT_BEFORE, CRT_AFTER), (0xC168F, LCD_BEFORE, LCD_AFTER),
           (0xC196C, CRT_BEFORE, CRT_AFTER), (0xC19CA, LCD_BEFORE, LCD_AFTER))


def patch_bytes(source: bytes) -> bytes:
    if len(source) != 1474560:
        raise ValueError('Expected a 1,474,560-byte OS2.24 disk image')
    result = bytearray(source)
    for offset, before, after in PATCHES:
        assert len(before) == len(after)
        if source[offset:offset+len(before)] != before:
            raise ValueError(f'Unexpected warning resource at {offset:06X}')
        result[offset:offset+len(after)] = after
    return bytes(result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    before = args.source.read_bytes()
    after = patch_bytes(before)
    with args.destination.open('xb') as output:
        output.write(after)
    print(json.dumps({'source_sha256': hashlib.sha256(before).hexdigest(),
                      'patched_sha256': hashlib.sha256(after).hexdigest(),
                      'changed_bytes': sum(a != b for a, b in zip(before, after)),
                      'resource_growth': 0}, indent=2))


if __name__ == '__main__':
    main()
