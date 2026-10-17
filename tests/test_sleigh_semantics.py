"""Regression tests for MCS-96 SLEIGH instruction lengths and semantics (BUG-084 and BUG-086)."""
import pytest

pypcode = pytest.importorskip('pypcode')


def test_bug086_instruction_lengths():
    """Intel 80C196KB Table 3-2B: SKIP is 2 bytes (0x00 <byte>), IDLPD is 1 byte (0xF6)."""
    ctx = pypcode.Context('MCS96:LE:16:default')

    # Test SKIP (0x00 0x12) -> length 2
    d_skip = ctx.disassemble(bytes.fromhex('0012'), base_address=0x4000, max_instructions=1)
    assert len(d_skip.instructions) == 1
    assert d_skip.instructions[0].mnem.upper() == 'SKIP'
    assert d_skip.instructions[0].length == 2

    # Test IDLPD (0xF6 0x00) -> first instruction is 1 byte
    d_idlpd = ctx.disassemble(bytes.fromhex('f600'), base_address=0x4000, max_instructions=1)
    assert len(d_idlpd.instructions) == 1
    assert d_idlpd.instructions[0].mnem.upper() == 'IDLPD'
    assert d_idlpd.instructions[0].length == 1


def test_bug084_pusha_popa_lifting_semantics():
    """Intel 80C196KB User's Guide (270651-003):

    PUSHA:
      (SP) <- (SP) - 2; ((SP)) <- INT_MASK, PSW
      (SP) <- (SP) - 2; ((SP)) <- INT_MASK1, WSR
      PSW <- 0; INT_MASK1 <- 0

    POPA:
      WSR <- ((SP)); INT_MASK1 <- ((SP) + 1); (SP) <- (SP) + 2
      PSW <- ((SP)); INT_MASK <- ((SP) + 1); (SP) <- (SP) + 2
    """
    ctx = pypcode.Context('MCS96:LE:16:default')

    # PUSHA (0xF4)
    tr_pusha = ctx.translate(bytes.fromhex('f4'), base_address=0x4000)
    pusha_ops = [str(op) for op in tr_pusha.ops]

    # Verify flags word pushed first, then extension word pushed second
    # Flags word: RAM[8] (INT_MASK) in high byte, PSW in low byte
    # Extension word: RAM[13] (INT_MASK1) in high byte, RAM[14] (WSR) in low byte
    has_flags_push = any('RAM[8:1]' in op for op in pusha_ops)
    has_ext_push = any('RAM[13:1]' in op and 'RAM[14:1]' not in op for op in pusha_ops)
    assert has_flags_push, "PUSHA must read INT_MASK (RAM[8:1])"
    assert has_ext_push, "PUSHA must read INT_MASK1 (RAM[13:1]) for extension word"

    # Verify push order: RAM[8:1] operation appears before RAM[13:1] operation
    idx_mask0 = next(i for i, op in enumerate(pusha_ops) if 'RAM[8:1]' in op)
    idx_mask1 = next(i for i, op in enumerate(pusha_ops) if 'RAM[13:1]' in op)
    assert idx_mask0 < idx_mask1, "PUSHA must push flags word before extension word"

    # Verify clearing of PSW and INT_MASK1
    assert any('PSW = 0x0' in op for op in pusha_ops), "PUSHA must clear PSW"
    assert any('RAM[13:1] = 0x0' in op for op in pusha_ops), "PUSHA must clear INT_MASK1"

    # POPA (0xF5)
    tr_popa = ctx.translate(bytes.fromhex('f5'), base_address=0x4000)
    popa_ops = [str(op) for op in tr_popa.ops]

    # First popped word restores WSR (RAM[14:1]) and INT_MASK1 (RAM[13:1])
    # Second popped word restores PSW and INT_MASK (RAM[8:1])
    idx_pop_wsr = next(i for i, op in enumerate(popa_ops) if 'RAM[14:1]' in op)
    idx_pop_mask1 = next(i for i, op in enumerate(popa_ops) if 'RAM[13:1]' in op)
    idx_pop_psw = next(i for i, op in enumerate(popa_ops) if 'PSW =' in op)
    idx_pop_mask0 = next(i for i, op in enumerate(popa_ops) if 'RAM[8:1]' in op)

    # Extension word popped first, flags word popped second
    assert idx_pop_wsr < idx_pop_psw, "POPA must pop extension word before flags word"
    assert idx_pop_mask1 < idx_pop_mask0, "POPA must restore INT_MASK1 before INT_MASK"
