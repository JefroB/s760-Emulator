"""
Script to trace and reverse-engineer the exact Roland Gate Array register protocol (0xF000-0xF020).
Disassembles all 80C196 instructions interacting with the MMIO Gate Array window in S760224.IMG.
"""

import struct

with open('roms/s760/S760224.IMG', 'rb') as f:
    rom = f.read()

# 80C196 Disassembly table for common MMIO operations
# STB: C4 (dir), C5 (immed), C6 (ind), C7 (ext 16-bit)
# LDB: B0 (dir), B1 (immed), B2 (ind), B3 (ext 16-bit)
# ORB: 94 / 97, ANDB: 84 / 87, XORB: A4 / A7
# JBC: 30-37, JBS: 38-3F

print("=== ROLAND S-760 GATE ARRAY (0xF000 - 0xF020) REVERSE-ENGINEERING TRACE ===")

gate_array_regs = {}

for i in range(0x4800, 0xC8000 - 4):
    # Check for direct 16-bit address matching 0xF000 - 0xF020
    val16 = struct.unpack('<H', rom[i:i+2])[0]
    if 0xF000 <= val16 <= 0xF020:
        reg_addr = val16
        # Find the opcode preceding it
        if i >= 2:
            op = rom[i-2]
            op_prev = rom[i-1]
            op_name = "UNKNOWN"
            direction = "ACCESS"
            
            # Identify 80C196 extended addressing opcodes
            if op == 0xC7:
                op_name = f"STB reg_0x{op_prev:02X}, [0x{reg_addr:04X}]"
                direction = "WRITE"
            elif op == 0xB3:
                op_name = f"LDB reg_0x{op_prev:02X}, [0x{reg_addr:04X}]"
                direction = "READ"
            elif op == 0x97:
                op_name = f"ORB reg_0x{op_prev:02X}, [0x{reg_addr:04X}]"
                direction = "R/W (OR)"
            elif op == 0x87:
                op_name = f"ANDB reg_0x{op_prev:02X}, [0x{reg_addr:04X}]"
                direction = "R/W (AND)"
            elif op == 0xC3:
                op_name = f"LD reg_0x{op_prev:02X}, [0x{reg_addr:04X}]"
                direction = "READ_WORD"
            elif op == 0xC9:
                op_name = f"ST reg_0x{op_prev:02X}, [0x{reg_addr:04X}]"
                direction = "WRITE_WORD"

            if reg_addr not in gate_array_regs:
                gate_array_regs[reg_addr] = {"reads": 0, "writes": 0, "sites": []}
            
            if "WRITE" in direction:
                gate_array_regs[reg_addr]["writes"] += 1
            else:
                gate_array_regs[reg_addr]["reads"] += 1
                
            gate_array_regs[reg_addr]["sites"].append((i-2, op_name))

for reg in sorted(gate_array_regs.keys()):
    info = gate_array_regs[reg]
    print(f"\nRegister [0x{reg:04X}]: Total Reads = {info['reads']}, Total Writes = {info['writes']}")
    print("Sample Usage Instructions:")
    for site, name in info["sites"][:6]:
        # Context bytes
        context = ' '.join(f"{b:02X}" for b in rom[site:site+6])
        print(f"  ROM @ 0x{site:06X} ({context}): {name}")
