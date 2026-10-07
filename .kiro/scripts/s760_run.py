"""
s760_run.py — Roland S-760 System Disk Execution Harness & Verification Engine

Executes the Intel 80C196KB reset sequence and OS boot routines loaded from S760224.IMG.
Tracks CPU registers, Work RAM mutations, SFR initializations, and Gate Array MMIO pulses.
"""
import sys
import os

BASE = 0x2080
FILE_OFF = 0x4800
IMAGE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "S760224.IMG")

class MCS96Emulator:
    def __init__(self, img_path):
        with open(img_path, "rb") as f:
            self.image = f.read()

        # 64 KB Address Space
        self.mem = bytearray(65536)
        
        # Load OS Payload (file offset 0x4800) into RAM base 0x2080
        payload_len = len(self.image) - FILE_OFF
        self.mem[BASE:BASE + payload_len] = self.image[FILE_OFF:]

        # Special Function Register (SFR) offsets
        self.SP = 0x18          # Stack Pointer
        self.INT_MASK = 0x08    # Interrupt Mask
        self.INT_PEND = 0x09    # Interrupt Pending
        self.INT_MASK1 = 0x13   # Interrupt Mask 1
        self.INT_PEND1 = 0x12   # Interrupt Pending 1
        self.IOS0 = 0x15        # I/O Status 0
        self.IOS1 = 0x16        # I/O Status 1
        self.PORT1 = 0x0F       # Port 1
        self.PORT2 = 0x10       # Port 2

        self.pc = BASE
        self.interrupts_enabled = False
        self.mmio_log = []
        self.ram_writes = []
        self.zero_flag = False

    def read_u8(self, addr):
        return self.mem[addr & 0xFFFF]

    def read_u16(self, addr):
        addr &= 0xFFFF
        return self.mem[addr] | (self.mem[addr + 1] << 8)

    def write_u8(self, addr, val):
        addr &= 0xFFFF
        val &= 0xFF
        if 0xF000 <= addr <= 0xF00A:
            self.mmio_log.append((self.pc, f"MMIO WRITE 0x{addr:04X} = 0x{val:02X}"))
        elif 0x0120 <= addr <= 0x1120:
            self.ram_writes.append((addr, val))
        self.mem[addr] = val

    def write_u16(self, addr, val):
        addr &= 0xFFFF
        val &= 0xFFFF
        self.write_u8(addr, val & 0xFF)
        self.write_u8(addr + 1, (val >> 8) & 0xFF)

    def step(self):
        old_pc = self.pc
        b0 = self.read_u8(self.pc)

        # 0xFA = DI (Disable Interrupts)
        if b0 == 0xFA:
            self.interrupts_enabled = False
            self.pc += 1
            return True, "DI (Disable Interrupts)"

        # 0xFB = EI (Enable Interrupts)
        elif b0 == 0xFB:
            self.interrupts_enabled = True
            self.pc += 1
            return True, "EI (Enable Interrupts)"

        # 0xA1 = LD RW, #imm16
        elif b0 == 0xA1:
            imm16 = self.read_u16(self.pc + 1)
            reg = self.read_u8(self.pc + 3)
            self.write_u16(reg, imm16)
            self.pc += 4
            return True, f"LD 0x{reg:02X}, #0x{imm16:04X}"

        # 0xB1 = LDB RB, #imm8
        elif b0 == 0xB1:
            imm8 = self.read_u8(self.pc + 1)
            reg = self.read_u8(self.pc + 2)
            self.write_u8(reg, imm8)
            self.pc += 3
            return True, f"LDB 0x{reg:02X}, #0x{imm8:02X}"

        # 0xB0 = LDB RB, reg
        elif b0 == 0xB0:
            src = self.read_u8(self.pc + 1)
            dst = self.read_u8(self.pc + 2)
            self.write_u8(dst, self.read_u8(src))
            self.pc += 3
            return True, f"LDB 0x{dst:02X}, 0x{src:02X}"

        # 0xB3 = LDB RB, [base + index] (Indexed / Long 16-bit offset)
        elif b0 == 0xB3:
            raw_reg = self.read_u8(self.pc + 1)
            off = self.read_u16(self.pc + 2)
            dst = self.read_u8(self.pc + 4)
            val = self.read_u8(off)
            self.write_u8(dst, val)
            self.pc += 5
            return True, f"LDB 0x{dst:02X}, [0x{off:04X}]"

        # 0xC2 = ST ZR, [RW]+ (Store zero, auto-increment word pointer)
        elif b0 == 0xC2:
            raw_reg = self.read_u8(self.pc + 1)
            reg = raw_reg & 0xFE
            ptr_val = self.read_u16(reg)
            self.write_u16(ptr_val, 0x0000)
            self.write_u16(reg, ptr_val + 2)
            self.pc += 3
            return True, f"ST ZR, [0x{reg:02X} = 0x{ptr_val:04X}]+"

        # 0xC3 = ST RW, table[index] (Indexed 16-bit store)
        elif b0 == 0xC3:
            raw_reg = self.read_u8(self.pc + 1)
            off = self.read_u8(self.pc + 2)
            dest_addr = self.read_u16(self.pc + 3)
            src_val = self.read_u16(raw_reg & 0xFE)
            self.write_u16(dest_addr, src_val)
            self.pc += 5
            return True, f"ST 0x{raw_reg & 0xFE:02X} (0x{src_val:04X}), 0x{dest_addr:04X}"

        # 0xC4 = STB RB, reg
        elif b0 == 0xC4:
            src = self.read_u8(self.pc + 1)
            dst = self.read_u8(self.pc + 2)
            self.write_u8(dst, self.read_u8(src))
            self.pc += 3
            return True, f"STB 0x{dst:02X}, 0x{src:02X}"

        # 0xC7 = STB RB, [addr]
        elif b0 == 0xC7:
            src = self.read_u8(self.pc + 1)
            off = self.read_u8(self.pc + 2)
            dest_addr = self.read_u16(self.pc + 3)
            val = self.read_u8(src)
            self.write_u8(dest_addr, val)
            self.pc += 5
            return True, f"STB 0x{src:02X} (0x{val:02X}), 0x{dest_addr:04X}"

        # 0x89 = CMP RW, #imm16
        elif b0 == 0x89:
            imm16 = self.read_u16(self.pc + 1)
            reg = self.read_u8(self.pc + 3)
            val = self.read_u16(reg)
            self.zero_flag = (val == imm16)
            self.pc += 4
            return True, f"CMP 0x{reg:02X} (0x{val:04X}), #0x{imm16:04X}"

        # 0xD7 = JNE rel8
        elif b0 == 0xD7:
            rel = self.read_u8(self.pc + 1)
            if rel > 127: rel -= 256
            target = (self.pc + 2 + rel) & 0xFFFF
            if not self.zero_flag:
                self.pc = target
            else:
                self.pc += 2
            return True, f"JNE 0x{target:04X} (ZeroFlag={self.zero_flag})"

        # 0x71 = ANDB RB, #imm8
        elif b0 == 0x71:
            imm8 = self.read_u8(self.pc + 1)
            reg = self.read_u8(self.pc + 2)
            val = self.read_u8(reg) & imm8
            self.write_u8(reg, val)
            self.pc += 3
            return True, f"ANDB 0x{reg:02X}, #0x{imm8:02X}"

        # 0x91 = ORB RB, #imm8
        elif b0 == 0x91:
            imm8 = self.read_u8(self.pc + 1)
            reg = self.read_u8(self.pc + 2)
            val = self.read_u8(reg) | imm8
            self.write_u8(reg, val)
            self.pc += 3
            return True, f"ORB 0x{reg:02X}, #0x{imm8:02X}"

        # 0xEF = LCALL rel16
        elif b0 == 0xEF:
            rel = self.read_u16(self.pc + 1)
            if rel > 32767: rel -= 65536
            target = (self.pc + 3 + rel) & 0xFFFF
            sp_val = self.read_u16(self.SP) - 2
            self.write_u16(self.SP, sp_val)
            self.write_u16(sp_val, self.pc + 3)
            self.pc = target
            return True, f"LCALL 0x{target:04X}"

        # 0xE0 = DJNZ RB, rel8
        elif b0 == 0xE0:
            reg = self.read_u8(self.pc + 1)
            rel = self.read_u8(self.pc + 2)
            if rel > 127: rel -= 256
            target = (self.pc + 3 + rel) & 0xFFFF
            val = (self.read_u8(reg) - 1) & 0xFF
            self.write_u8(reg, val)
            if val != 0:
                self.pc = target
            else:
                self.pc += 3
            return True, f"DJNZ 0x{reg:02X}, 0x{target:04X}"

        # 0xF0 = RET
        elif b0 == 0xF0:
            sp_val = self.read_u16(self.SP)
            ret_addr = self.read_u16(sp_val)
            self.write_u16(self.SP, sp_val + 2)
            self.pc = ret_addr
            return True, f"RET to 0x{ret_addr:04X}"

        return False, f"Unhandled Opcode: 0x{b0:02X} at 0x{old_pc:04X}"

def main():
    print("=========================================================")
    print(" Roland S-760 System Disk Execution Harness (S760224.IMG)")
    print("=========================================================")
    
    emu = MCS96Emulator(IMAGE_PATH)
    print(f"[BOOT] Loaded S760224.IMG (file 0x{FILE_OFF:X}) -> Base Execution Address 0x{emu.pc:04X}\n")

    step_count = 0
    max_steps = 10000

    while step_count < max_steps:
        pc_before = emu.pc
        ok, desc = emu.step()
        step_count += 1

        if step_count <= 25 or "MMIO" in desc or "SP" in desc or not ok or step_count % 500 == 0:
            print(f"Step {step_count:4d} | PC: 0x{pc_before:04X} | {desc}")

        if not ok:
            print(f"\n[STOP] Execution stopped at step {step_count}: {desc}")
            break

    print("\n=========================================================")
    print(" Execution Verification Summary")
    print("=========================================================")
    print(f"Total instructions executed: {step_count}")
    print(f"Final Program Counter (PC): 0x{emu.pc:04X}")
    print(f"Final Stack Pointer (SP @ 0x18): 0x{emu.read_u16(emu.SP):04X}")
    print(f"Total Work RAM zero writes (0x0120 - 0x1120): {len(emu.ram_writes)}")
    print(f"Total Gate Array MMIO accesses (0xF000 - 0xF00A): {len(emu.mmio_log)}")
    if emu.mmio_log:
        print("\nGate Array MMIO Pulse Log:")
        for pc, log in emu.mmio_log:
            print(f"  [PC: 0x{pc:04X}] {log}")

if __name__ == "__main__":
    main()
