# S-760 Ghidra Project Initialization & Symbol Setup Script
#
# Run this script inside Ghidra:
#   Window -> Script Manager -> Run or Ghidra Python Interpreter
#
# Prerequisites:
#   1. New Project in Ghidra.
#   2. File -> Import File: select 's760_resident_os.bin' (extracted using extract_resident_and_banks.py).
#   3. Language: MCS-96 / 16-bit little-endian (MCS96:LE:16:default).
#   4. In Options: set Block Name = "OS_RESIDENT", Base Address = 0x2080.
#   5. Open in CodeBrowser and run this script!
#
# @category Roland S-760
# @author S-760 Reverse Engineering Team

import os
import csv

try:
    from ghidra.program.model.symbol import SourceType
    from ghidra.program.model.address import AddressSet
    from ghidra.program.model.listing import CodeUnit
except ImportError:
    SourceType = None
    AddressSet = None
    CodeUnit = None

def get_addr(offset):
    return currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(offset)

def create_block(name, start, size, read, write, execute):
    mem = currentProgram.getMemory()
    addr = get_addr(start)
    block = mem.getBlock(addr)
    if block is not None and block.getName() == name:
        print("[*] Memory block '%s' already exists at 0x%04X." % (name, start))
        return block
    try:
        new_block = mem.createUninitializedBlock(name, addr, size, False)
        new_block.setRead(read)
        new_block.setWrite(write)
        new_block.setExecute(execute)
        print("[+] Created memory block: %s (0x%04X..0x%04X)" % (name, start, start + size - 1))
        return new_block
    except Exception as e:
        print("[-] Notice creating block '%s': %s" % (name, str(e)))
        return None

def set_symbol(name, offset, is_func=False, comment=None):
    addr = get_addr(offset)
    st = currentProgram.getSymbolTable()
    try:
        st.createLabel(addr, name, SourceType.USER_DEFINED)
        if is_func:
            createFunction(addr, name)
        if comment and CodeUnit:
            try:
                currentProgram.getListing().setComment(addr, CodeUnit.EOL_COMMENT, comment)
            except Exception:
                pass
    except Exception as e:
        pass

print("=== Setting up Roland S-760 Memory Map ===")

# 1. On-Chip Register File & SFRs (0x0000..0x00FF)
create_block("SFR_REGS", 0x0000, 0x0100, True, True, False)

# 2. CPU Work RAM (0x0100..0x1FFF, Stack at 0x1120)
create_block("WORK_RAM", 0x0100, 0x1F00, True, True, False)

# 3. Dynamic Vector RAM (0x2000..0x207F)
create_block("VEC_RAM", 0x2000, 0x0080, True, True, True)

# 4. Hardware MMIO / Peripheral Windows (if not covered by OS_RESIDENT)
create_block("MMIO_SAMPLE", 0xC000, 0x0020, True, True, False)
create_block("MMIO_VDP",    0xD000, 0x0100, True, True, False)
create_block("MMIO_LCD",    0xE000, 0x0010, True, True, False)
create_block("MMIO_SCSI",   0xE400, 0x0020, True, True, False)
create_block("MMIO_GATE",   0xF000, 0x0020, True, True, False)

print("\n=== Installing S-760 Named Symbols ===")

# Standard MCS-96 Special Function Registers
set_symbol("R0", 0x0000)
set_symbol("INT_MASK", 0x0008)
set_symbol("INT_PEND", 0x0009)
set_symbol("TIMER1", 0x000A)
set_symbol("TIMER2", 0x000C)
set_symbol("PORT0_AD", 0x000E)
set_symbol("PORT1", 0x000F)
set_symbol("PORT2", 0x0010)
set_symbol("SP_STAT", 0x0011)
set_symbol("INT_PEND1", 0x0012)
set_symbol("INT_MASK1", 0x0013)
set_symbol("WDT", 0x0014)
set_symbol("IOS0", 0x0015)
set_symbol("IOS1", 0x0016)
set_symbol("SP", 0x0018)

# Memory Bank Selectors (Gate Array)
set_symbol("FETCH_SEL_WIN0", 0x0100)
set_symbol("FETCH_SEL_WIN1", 0x0102)
set_symbol("FETCH_SEL_WIN2", 0x0104)
set_symbol("FETCH_SEL_WIN3", 0x0106)
set_symbol("DATA_SEL_WIN0",  0x0108)
set_symbol("DATA_SEL_WIN1",  0x010A)
set_symbol("DATA_SEL_WIN2",  0x010C)
set_symbol("DATA_SEL_WIN3",  0x010E)

# MIDI & DMA Control
set_symbol("MIDI_STATUS_PORT", 0x0114)
set_symbol("MIDI_DATA_PORT",   0x0116)
set_symbol("DMA_COUNT_REG",    0x0118)
set_symbol("DMA_PHYS_LO",      0x011A)
set_symbol("DMA_PHYS_HI",      0x011C)
set_symbol("DMA_MODE_CTRL",    0x011D)

# External Interrupt Stubs (0x0120 + 4*i)
set_symbol("IRQ_STUB_FDC",   0x0120, is_func=True)
set_symbol("IRQ_STUB_WAVE",  0x0128, is_func=True)
set_symbol("IRQ_STUB_COMPL", 0x0130, is_func=True)
set_symbol("IRQ_STUB_MIDI",  0x0138, is_func=True)

# Stack Pointer Target
set_symbol("STACK_INITIAL_TOP", 0x1120)

# Vector Table
set_symbol("VEC_TIMER_ISR", 0x200A)
set_symbol("VEC_EXT_IRQ",   0x200E)

# Entry Points and Core Functions
set_symbol("entry_reset",          0x2080, is_func=True)
set_symbol("midi_ring_dispatcher", 0x213A, is_func=True)
set_symbol("reset_tail_jump_main", 0x218B, is_func=True)
set_symbol("resident_helper_218e", 0x218E, is_func=True)
set_symbol("reset_phase2_init",    0x23E9, is_func=True)
set_symbol("main_os_init",         0x2831, is_func=True)
set_symbol("ret_stub_2b22",        0x2B22, is_func=True)
set_symbol("isr_timer1",           0x2B51, is_func=True)
set_symbol("isr_external_irq",     0x2C4F, is_func=True)
set_symbol("sys_helper_b93a",      0xB93A, is_func=True)

# Hardware MMIO Ports
set_symbol("SAMPLE_PORT_STATUS",   0xC000)
set_symbol("SAMPLE_PORT_DATA",     0xC00A)
set_symbol("SAMPLE_PORT_ADDR_LO",  0xC00C)
set_symbol("SAMPLE_PORT_ADDR_HI",  0xC00E)

set_symbol("VDP_REG_DISPLAY_CTRL", 0xD010)
set_symbol("VDP_PORT_VRAM_DATA",   0xD018)
set_symbol("VDP_REG_VRAM_ADDR_LO", 0xD034)
set_symbol("VDP_REG_VRAM_ADDR_HI", 0xD036)

set_symbol("LCD_REG_STATUS_CMD",   0xE000)
set_symbol("LCD_PORT_DATA",        0xE002)

set_symbol("SCSI_REG_BASE",        0xE400)

set_symbol("GATE_STROBE_PULSE",    0xF000)
set_symbol("GATE_PORT_B_FDD",      0xF002)
set_symbol("GATE_CONFIG_REG",      0xF004)
set_symbol("GATE_MOUSE_NIBBLE",    0xF008)
set_symbol("GATE_CRT_STATUS_CONFIG", 0xF00A)

# Load full symbol database from s760_symbols.csv
csv_candidates = [
    os.path.join(os.path.dirname(getSourceFile().getAbsolutePath()), "s760_symbols.csv") if 'getSourceFile' in globals() else None,
    "scripts/ghidra/s760_symbols.csv",
    "d:/S-760/scripts/ghidra/s760_symbols.csv",
    "s760_symbols.csv"
]
csv_path = None
for candidate in csv_candidates:
    if candidate and os.path.exists(candidate):
        csv_path = candidate
        break

if csv_path:
    print("\n=== Loading Symbols from %s ===" % csv_path)
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        loaded = 0
        for row in reader:
            s_name = row.get("Name")
            s_addr_str = row.get("Address")
            s_type = row.get("Type", "Address")
            s_comment = row.get("Comments", "")
            if not s_name or not s_addr_str:
                continue
            try:
                s_addr = int(s_addr_str, 16)
                is_function = (s_type == "Function")
                set_symbol(s_name, s_addr, is_func=is_function, comment=s_comment)
                loaded += 1
                if loaded % 1000 == 0:
                    print("  [+] Loaded %d symbols..." % loaded)
            except Exception:
                pass
        print("[+] Installed %d symbols from CSV." % loaded)
else:
    print("\n[-] Note: s760_symbols.csv not found; standard symbols installed.")

print("\n=== Initializing Disassembly at Known Entries ===")
for ep in [0x2080, 0x2B51, 0x2C4F]:
    try:
        disassemble(get_addr(ep))
        print("  [DISASM] Disassembled at 0x%04X" % ep)
    except Exception as e:
        print("  [-] Disasm note at 0x%04X: %s" % (ep, str(e)))

print("\n[SUCCESS] S-760 Ghidra setup complete!")
