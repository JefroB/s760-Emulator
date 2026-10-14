"""Reproduce the GB-6 v8/v9 mouse-decoder experiments on a user-owned OS2.24.

Contains only independently authored replacement instructions, not an OS image.
The original image must match the known baseline and is never overwritten.
"""
import argparse
import hashlib
import json
from pathlib import Path

SOURCE_SHA256 = '3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'
IMAGE_SIZE = 0x168000
PATCH_START, PATCH_END = 0x18BB5, 0x18C11
DISCONNECT_OFFSET = 0x18C2D
OUTPUT_SHA256 = {
    'v8': 'cf29f7fdf75a3a672eefdd34d52f66aa25a6624632a85d52c0500d84223afead',
    'v9': 'c611e7156c9069dc632bcfd8e4d20a52da70ed2528112f29fe87258803f42deb',
}


def decoder(profile):
    if profile not in OUTPUT_SHA256:
        raise ValueError('Profile must be v8 or v9')
    code = bytearray()

    def emit(text):
        code.extend(bytes.fromhex(text))

    def call(target):
        displacement = (target - (0x43B5 + len(code) + 2)) & 0x7ff
        code.extend((0x28 | displacement >> 8, displacement & 255))

    def select(level):
        emit(f'B1 {level} DA C7 01 08 F0 DA')

    def motion(register, destination, shift):
        emit(f'B3 01 08 F0 {register} 71 0F {register} 79 08 {register} '
             f'B0 {register} {destination} 19 {shift:02X} {destination}')

    # Pin8 low=X/high=Y. Read before the edge that resets that counter.
    select('BF')
    call(0x4476)  # Existing firmware button helper remains intact.
    call(0x446F)  # Existing short settling delay.
    motion('28', 'AD', 3 if profile == 'v8' else 2)
    select('40')
    call(0x446F)
    motion('2A', 'D3', 2)
    select('BF')
    # Preserve the experiment's negative-endpoint clamp; necessity is unproved.
    for destination in ('AD', 'D3'):
        emit(f'99 C0 {destination} D7 03 B1 C1 {destination}')
    if len(code) > PATCH_END - PATCH_START:
        raise ValueError('Replacement decoder exceeds reserved patch span')
    code.extend([0xFD] * (PATCH_END - PATCH_START - len(code)))
    return bytes(code)


def patch_image(source, output, profile='v9'):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Output must differ from the original image')
    if output.suffix.lower() != '.img':
        raise ValueError('Use an .IMG output filename so firmware exclusion rules apply')
    original = source.read_bytes()
    if len(original) != IMAGE_SIZE or hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('Input must be the original, unmodified S-760 OS2.24 baseline')
    patched = bytearray(original)
    patched[PATCH_START:PATCH_END] = decoder(profile)
    patched[DISCONNECT_OFFSET] = 0xF0
    result_hash = hashlib.sha256(patched).hexdigest()
    if len(patched) != IMAGE_SIZE or result_hash != OUTPUT_SHA256[profile]:
        raise ValueError('Generated image does not match the recorded experiment')
    # Exclusive creation also refuses an existing symlink/hardlink to the source.
    with output.open('xb') as target:
        target.write(patched)
    return dict(profile=profile, source_sha256=SOURCE_SHA256,
                output=str(output), output_sha256=result_hash, bytes=len(patched),
                gain_x=8 if profile == 'v8' else 4, gain_y=4,
                status='Experimental mouse-decoder replacement; combined controller modes are not implemented')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True, help='Original user-supplied OS2.24 image')
    parser.add_argument('--output', type=Path, required=True, help='New .IMG file; parent directory must exist')
    parser.add_argument('--profile', choices=tuple(OUTPUT_SHA256), default='v9')
    options = parser.parse_args()
    try:
        print(json.dumps(patch_image(options.input, options.output, options.profile), indent=2))
    except (OSError, ValueError) as error:
        parser.exit(1, f'{error}\n')


if __name__ == '__main__':
    main()
