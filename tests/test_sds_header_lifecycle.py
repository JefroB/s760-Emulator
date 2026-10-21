"""Decoded completion boundaries, cleanup control flow and image safety."""
from pathlib import Path
from functools import lru_cache
import hashlib
import struct
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from patch_sds_header_lifecycle import COMPLETE, IMAGE_SIZE, SOURCE_SHA256, patch_image, patches


@lru_cache(maxsize=None)
def decode(code, base):
    pypcode = pytest.importorskip('pypcode')
    rows = pypcode.Context('MCS96:LE:16:default').disassemble(code, base_address=base).instructions
    assert sum(i.length for i in rows) == len(code)
    return {i.addr.offset: i for i in rows}


def run(code, base, memory=None, registers=None, equal=False):
    decoded = decode(code, base)
    memory = dict(memory or {})
    registers = bytearray(registers or bytes(256))
    pc, greater, signed_greater, writes, calls = base, False, False, [], []
    def word(a): return int.from_bytes(registers[a:a+2], 'little')
    def put_word(a, value): registers[a:a+2] = value.to_bytes(2, 'little')
    for _ in range(100):
        if pc not in decoded:
            return pc, registers, memory, writes, calls
        i = decoded[pc]; b = code[pc-base:pc-base+i.length]; pc += i.length
        if b[0] == 0xA1:
            put_word(b[3], int.from_bytes(b[1:3], 'little'))
        elif b[0] == 0xA2:
            pointer = b[1] & 0xFE; address = word(pointer)
            put_word(b[2], memory[address] | memory[address+1] << 8)
            if b[1] & 1: put_word(pointer, (address+2) & 65535)
        elif b[0] == 0xC5:
            left = int.from_bytes(registers[b[2]:b[2]+4], 'little')
            right = int.from_bytes(registers[b[1]:b[1]+4], 'little')
            greater, equal = left > right, left == right
        elif b[0] == 0x99:
            left, right = registers[b[2]], b[1]
            greater, equal = left > right, left == right
            # MCS96 JGT uses N/Z from the byte subtraction; it does not XOR V.
            signed_greater = not equal and not ((left-right) & 128)
        elif b[0] in (0xD9, 0xD1, 0xD2, 0xDF, 0xD7):
            take = {0xD9:greater, 0xD1:not greater, 0xD2:signed_greater, 0xDF:equal, 0xD7:not equal}[b[0]]
            if take: pc += int.from_bytes(b[1:2], 'little', signed=True)
        elif b[0] == 0xB1:
            registers[b[2]] = b[1]
        elif b[0] == 0xC7:
            address = int.from_bytes(b[2:4], 'little')
            memory[address] = registers[b[4]]; writes.append((address, memory[address]))
        elif 0x20 <= b[0] <= 0x27:
            relative = ((b[0] & 7) << 8) | b[1]
            pc = (pc + (relative-2048 if relative & 1024 else relative)) & 65535
        elif b[0] == 0xEF:
            calls.append(((pc+int.from_bytes(b[1:3], 'little', signed=True)) & 65535, word(0x1E)))
        elif b[0] == 0xF0:
            return pc, registers, memory, writes, calls
        else:
            assert i.mnem == 'NOP', i
    raise AssertionError('Control flow did not terminate')


def test_completion_unsigned_boundaries_and_write_extent():
    _, pc, _, code = patches()[1]
    values = sorted({0, 0xFFFFFFFF} | {v for bit in (0,1,7,8,15,16,23,24,30,31)
                                     for v in (2**bit-1, 2**bit, 2**bit+1)})
    initial = bytes((i*17+3) & 255 for i in range(256))
    scratch = set(range(0x5C,0x64)) | {0x6A,0x6B}
    for end in values:
        for current in values:
            source = dict(enumerate(struct.pack('<II', end, current), 0xB198))
            _, regs, memory, writes, calls = run(code, pc, {**source,0x2BBA:1}, initial)
            assert memory[0x2BBA] == (COMPLETE if current >= end else 1)
            assert writes == ([(0x2BBA,COMPLETE)] if current >= end else [])
            assert all(memory[a] == value for a,value in source.items())
            assert all(regs[i] == initial[i] for i in range(256) if i not in scratch)
            assert not calls


def test_completion_and_error_dispatch():
    spans = {pc: after for _,pc,_,after in patches()}
    for state in (1,2,3,4,5,10,COMPLETE):
        registers = bytearray(256);registers[0x30] = state
        dest, *_ = run(spans[0x87E4], 0x87E4, registers=registers)
        assert dest == (0x87E9 if state in (1,COMPLETE) else 0x87ED)
    for state in range(256):
        registers = bytearray(256);registers[0x30] = state
        dest,_,_,writes,_ = run(spans[0x8998], 0x8998, registers=registers)
        assert dest == (0x89A6 if state <= 5 else 0x8905)
        assert not writes  # The error owner keeps its state until final cleanup.
        registers[0xDA] = state
        dest,*_ = run(spans[0x8848]+bytes.fromhex('D7 03'),0x8848,registers=registers)
        assert dest == (0x884D if state == COMPLETE else 0x8850)


def test_error_crt_lcd_join_final_cleanup():
    code = patches()[-1][3]
    for lcd in (False, True):
        dest,_,_,writes,calls = run(code, 0x8A5A, equal=lcd)
        assert calls == [(0xCE62, 0xDACC if lcd else 0xF732)]
        assert dest == 0x8905 and not writes


def test_patch_safety_and_extent(tmp_path):
    source = ROOT/'roms/System/S760224.IMG'; output = tmp_path/'lifecycle.IMG'
    with pytest.raises(ValueError, match='differ'): patch_image(source,source)
    with pytest.raises(ValueError, match='.IMG'): patch_image(source,output.with_suffix('.bin'))
    invalid = tmp_path/'invalid.IMG';invalid.write_bytes(bytes(IMAGE_SIZE))
    with pytest.raises(ValueError, match='unmodified'):patch_image(invalid,output)
    assert not output.exists()
    if not source.exists():pytest.skip('Requires the user-owned OS2.24 baseline')
    pytest.importorskip('pypcode')
    before = source.read_bytes(); report = patch_image(source,output);after = output.read_bytes()
    allowed = {i for offset,_,old,_ in patches() for i in range(offset,offset+len(old))}
    assert len(after) == IMAGE_SIZE and report['source_sha256'] == SOURCE_SHA256
    assert {i for i,(a,b) in enumerate(zip(before,after)) if a!=b} <= allowed
    assert hashlib.sha256(source.read_bytes()).hexdigest() == SOURCE_SHA256
    with pytest.raises(FileExistsError):patch_image(source,output)
    assert output.read_bytes() == after
