"""Decoded dispatch equivalence, busy rejection and immutable-image safeguards."""
import hashlib
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from patch_sds_cancel_guard import (COMMANDS, END, IMAGE_SIZE, ORIGINAL, PC,
                                    SOURCE_SHA256, START, dispatcher, patch_image)


def decode(code):
    pypcode = pytest.importorskip('pypcode')
    rows = pypcode.Context('MCS96:LE:16:default').disassemble(code, base_address=PC).instructions
    assert sum(i.length for i in rows) == len(code)
    return {i.addr.offset: i for i in rows}


def execute(code, rows, command, state):
    """Step decoded instructions until a stock handler/return is reached."""
    pc, r, equal = PC, {0: 0}, False
    memory = {0xB048: command, 0x2BBA: state,
              **{0xB158 + i: value for i, value in enumerate(COMMANDS)}}
    for _ in range(100):
        if not PC <= pc < PC + len(code):
            return pc
        instruction = rows[pc]
        b = code[pc - PC:pc - PC + instruction.length]
        pc += instruction.length
        if b[0] == 0xB3:
            r[b[4]] = memory[int.from_bytes(b[2:4], 'little')]
        elif b[0] == 0xA1:
            r[b[3]] = int.from_bytes(b[1:3], 'little')
        elif b[0] == 0xB2:
            pointer = b[1] & 0xFE
            r[b[2]] = memory[r[pointer]]
            r[pointer] += b[1] & 1
        elif b[0] == 0x3F:
            if r[b[1]] & 128:
                pc += int.from_bytes(b[2:3], 'little', signed=True)
        elif b[0] == 0x98:
            equal = r[b[2]] == r[b[1]]
        elif b[0] == 0x99:
            equal = r[b[2]] == b[1]
        elif b[0] == 0x9B:
            equal = r[b[4]] == memory[int.from_bytes(b[2:4], 'little')]
        elif b[0] == 0xD7:
            if not equal:
                pc += int.from_bytes(b[1:2], 'little', signed=True)
        elif b[0] == 0x64:
            r[b[2]] = (r[b[2]] + r[b[1]]) & 65535
        elif b[0] in (0x65, 0x69):
            immediate = int.from_bytes(b[1:3], 'little')
            r[b[3]] = (r[b[3]] + (immediate if b[0] == 0x65 else -immediate)) & 65535
        elif b[0] == 0xE3:
            pc = r[b[1]]
        elif 0x20 <= b[0] <= 0x27:
            relative = ((b[0] & 7) << 8) | b[1]
            pc = (pc + (relative - 2048 if relative & 1024 else relative)) & 65535
        elif b[0] == 0xF9:
            return 0x6D33  # Original unknown-command SETC/RET equivalent.
        else:
            assert instruction.mnem == 'NOP'
    raise AssertionError('Dispatcher did not terminate')


def test_dispatch_and_busy_state_matrix():
    replacement = dispatcher()
    old_rows, new_rows = decode(ORIGINAL), decode(replacement)
    handlers = dict(zip(COMMANDS[:-1], (0x6D10, 0x6D35, 0x6D81, 0x6D8E,
                                          0x6D8F, 0x6DA3, 0x6DD5)))
    for command in range(256):
        expected = handlers.get(command, 0x6D33)
        assert execute(ORIGINAL, old_rows, command, 0) == expected
        for state in range(256):
            destination = 0x6D30 if command == 1 and state else expected
            assert execute(replacement, new_rows, command, state) == destination


def test_source_safety(tmp_path):
    source, output = tmp_path / 'source.IMG', tmp_path / 'output.IMG'
    source.write_bytes(bytes(IMAGE_SIZE))
    with pytest.raises(ValueError, match='unmodified'):
        patch_image(source, output)
    with pytest.raises(ValueError, match='differ'):
        patch_image(source, source)
    with pytest.raises(ValueError, match='.IMG'):
        patch_image(source, output.with_suffix('.bin'))
    assert not output.exists()
    assert source.read_bytes() == bytes(IMAGE_SIZE)


def test_baseline_patch_exact_extent_and_no_overwrite(tmp_path):
    source = ROOT / 'roms/System/S760224.IMG'
    if not source.exists():
        pytest.skip('Requires the user-owned original OS2.24 image')
    pytest.importorskip('pypcode')
    original = source.read_bytes()
    output = tmp_path / 'guarded.IMG'
    report = patch_image(source, output)
    patched = output.read_bytes()
    assert len(patched) == IMAGE_SIZE
    assert patched[:START] == original[:START]
    assert patched[END:] == original[END:]
    assert patched[START:END] == dispatcher()
    assert report['source_sha256'] == hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    with pytest.raises(FileExistsError):
        patch_image(source, output)
    assert output.read_bytes() == patched
