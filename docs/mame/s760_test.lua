-- MAME Lua automated verification script for Roland S-760 driver
-- Usage: mame s760 -autoboot_script docs/mame/s760_test.lua -headless

print("==================================================")
print("Roland S-760 MAME Driver Verification Script")
print("==================================================")

local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]

local RESET_VECTOR = 0x2080
local STACK_INIT = 0x1120
local ENTRY_OPCODE = 0xFA -- DI (Disable Interrupts)

-- Check opcode at reset vector
local first_byte = mem:read_u8(RESET_VECTOR)
print(string.format("Checking Reset Vector at 0x%04X...", RESET_VECTOR))
print(string.format("First byte opcode: 0x%02X (Expected 0x%02X DI)", first_byte, ENTRY_OPCODE))

if first_byte == ENTRY_OPCODE then
    print("[PASS] Reset vector contains valid 80C196 DI opcode (0xFA).")
else
    print(string.format("[FAIL] Unexpected opcode 0x%02X at reset vector 0x%04X", first_byte, RESET_VECTOR))
end

-- Monitor execution steps
emu.register_frame(function()
    local pc = cpu.state["PC"].value
    local sp = cpu.state["SP"].value
    
    print(string.format("[TRACE] Frame tick | PC: 0x%04X | SP: 0x%04X", pc, sp))

    if pc >= 0x2831 then
        print("[PASS] Reached main initialization routine at 0x2831!")
        manager.machine:exit()
    end
end)
