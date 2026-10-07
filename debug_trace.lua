local emu = manager.machine
local cpu = emu.devices[":maincpu"]

print("=== MAME S760 CPU TRACE START ===")
print("Initial PC: " .. string.format("0x%04X", cpu.state["PC"].value))

local count = 0
local hook = cpu:add_instruction_hook(function()
    count = count + 1
    if count <= 30 then
        print(string.format("Step %d: PC = 0x%04X", count, cpu.state["PC"].value))
    elseif count == 31 then
        print("Tracing paused.")
    end
end)
