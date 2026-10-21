"""Repair OS2.24 Verify Medium's last-sector omission without growing code."""
from pathlib import Path
import argparse
import hashlib
import json

OFFSET = 0x52317
PC = 0xB717
BEFORE = bytes.fromhex('0530a80032980030d70228572822a168001cc30102011cef0aa6d3052826d301f0a030da8032da8800dadf0227d2f8f0')
# READ CAPACITY returns the inclusive last LBA. Read that LBA first, test for
# zero after the native read/error handlers, and only then decrement. The
# native progress, request setup, read and error helpers retain their targets.
AFTER = bytes.fromhex('980030d702285c2827a168001cc30102011cef0fa6d305282bd301f0a030da8032da8800dadf070530a8003227d2f8f0')


def patch_bytes(source: bytes) -> bytes:
    if len(source) != 1474560:
        raise ValueError('Expected a 1,474,560-byte OS2.24 disk image')
    if source[OFFSET:OFFSET + len(BEFORE)] != BEFORE:
        raise ValueError('Unexpected Verify Medium loop at 052317')
    assert len(AFTER) == len(BEFORE)
    result = bytearray(source)
    result[OFFSET:OFFSET + len(BEFORE)] = AFTER
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
                      'code_growth': 0}, indent=2))


if __name__ == '__main__':
    main()
