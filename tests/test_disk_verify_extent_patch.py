"""Execute decoded verification-loop instructions against boundary capacities."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import patch_disk_verify_extent as patch

pypcode = pytest.importorskip('pypcode')


def execute(code, last_lba, failed_lba=None, abort=False):
    ctx = pypcode.Context('MCS96:LE:16:default')
    instructions = ctx.disassemble(code, base_address=patch.PC).instructions
    assert sum(i.length for i in instructions) == len(code)
    ins = {i.addr.offset: i for i in instructions}
    words = {'RW30': last_lba & 65535, 'RW32': last_lba >> 16, 'ZR': 0}
    pc, carry, zero = patch.PC, False, False
    reads, errors = [], []
    for _ in range((last_lba + 1) * 24 + 100):
        i = ins[pc]
        pc += i.length
        op, body = i.mnem, i.body
        parts = body.split(', ')
        if op == 'DEC':
            carry = words[parts[0]] != 0
            words[parts[0]] = (words[parts[0]] - 1) & 65535
        elif op == 'SUBC':
            value = words[parts[0]] - words[parts[1]] - (not carry)
            carry = value >= 0
            words[parts[0]] = value & 65535
        elif op == 'CMPB':
            zero = (words['RW30'] & 255) == 0
        elif op == 'CMP':
            zero = words[parts[0]] == words[parts[1]]
        elif op == 'LD':
            words[parts[0]] = int(parts[1][1:], 16) if parts[1].startswith('#') else words[parts[1]]
        elif op == 'OR':
            words[parts[0]] |= words[parts[1]]
        elif op == 'ST':
            assert body == 'RW1C, 0x102, TABLE[ZR]' and words['RW1C'] == 0x68
        elif op in ('SCALL', 'LCALL'):
            target = int(body, 16)
            lba = (words['RW32'] << 16) | words['RW30']
            if target == 0xB747:
                words['read_lba'] = lba
            elif target == 0x5D3B:
                reads.append(words['read_lba'])
                assert reads[-1] <= last_lba, 'verification wrapped outside the medium'
                carry = reads[-1] == failed_lba
            elif target == 0xB75B:
                errors.append(lba)
                carry = abort
            else:
                assert target == 0xB77A  # Native progress rendering; no loop-state mutation.
        elif op in ('JE', 'JNE', 'JNC', 'SJMP'):
            if op == 'SJMP' or {'JE': zero, 'JNE': not zero, 'JNC': not carry}.get(op, False):
                pc = int(body, 16)
        elif op == 'CLRC':
            carry = False
        elif op == 'RET':
            return reads, errors, carry
        else:
            raise AssertionError((op, body))
    raise AssertionError('verification did not terminate')


def image():
    data = bytearray(1474560)
    data[patch.OFFSET:patch.OFFSET + len(patch.BEFORE)] = patch.BEFORE
    return bytes(data)


@pytest.mark.parametrize('sectors', [1, 2, 255, 256, 257, 65535, 65536, 65537])
def test_verify_reads_every_sector_once_without_wrap(sectors):
    result = patch.patch_bytes(image())
    reads, errors, carry = execute(result[patch.OFFSET:patch.OFFSET + len(patch.BEFORE)], sectors - 1)
    assert reads == list(range(sectors - 1, -1, -1))
    assert not errors and not carry


@pytest.mark.parametrize('abort', [False, True])
def test_verify_preserves_error_handler_and_abort(abort):
    result = patch.patch_bytes(image())
    reads, errors, carry = execute(result[patch.OFFSET:patch.OFFSET + len(patch.BEFORE)], 256, failed_lba=256, abort=abort)
    assert reads == ([256] if abort else list(range(256, -1, -1)))
    assert errors == [256] and carry == abort


def test_original_loop_reproduces_last_sector_omission():
    reads, _, carry = execute(patch.BEFORE, 256)
    assert reads == list(range(255, -1, -1)) and not carry


def test_verify_patch_is_size_preserving_and_guarded():
    original = image()
    result = patch.patch_bytes(original)
    assert len(result) == len(original)
    assert result[:patch.OFFSET] == original[:patch.OFFSET]
    assert result[patch.OFFSET + len(patch.BEFORE):] == original[patch.OFFSET + len(patch.BEFORE):]
    with pytest.raises(ValueError):
        patch.patch_bytes(bytes(1474560))
    with pytest.raises(ValueError):
        patch.patch_bytes(original[:-1])
