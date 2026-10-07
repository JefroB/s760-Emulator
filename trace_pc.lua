local emu = manager.machine
local cpu = emu.devices[":maincpu"]

print("=== STARTING PC TRACE ===")

emu:add_machine_reset_notifier(function()
    print("Reset PC: " .. string.format("0x%04X", cpu.state["PC"].value))
end)
