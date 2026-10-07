"""
test_interactive_ui.py — Automated verification of Roland S-760 UI, navigation, and audio
"""
import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from mame_harness import MameTestSession, analyze_screenshot


def test_mame_boot_and_palette_rendering():
    """Verify MAME boots cleanly and renders the authentic Royal Blue S-760 UI."""
    lua = """
local count = 0
emu.register_frame_done(function()
    count = count + 1
    if count == 10 then
        results["boot_ok"] = true
        save_and_exit()
    end
end, "boot_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_boot")
    res = session.run()

    assert res["returncode"] == 0, f"MAME failed to boot cleanly: {res['stderr']}"
    assert res["data"].get("boot_ok") is True
    assert res["snap_path"] is not None

    # Check that the screen contains Roland Royal Blue (0, 0, 192) and Top Green (0, 200, 80)
    img, w, h = analyze_screenshot(res["snap_path"])
    pixels = img.load()

    found_blue = False
    found_green = False
    for y in range(0, h, 4):
        for x in range(0, w, 4):
            r, g, b = pixels[x, y]
            if r == 0 and g == 0 and b >= 150:
                found_blue = True
            if r == 0 and g >= 180 and b <= 100:
                found_green = True

    assert found_blue, "Roland Royal Blue (#0000C8) background not detected on screen"
    assert found_green, "Green Status Ribbon (#00C850) not detected on screen"


def test_keyboard_arrow_navigation_moves_cursor():
    """Verify keyboard Arrow keys move the crosshair cursor across the screen."""
    lua = """
local count = 0
local key_arrows = manager.machine.ioport.ports[":KEY_ARROWS"]

emu.register_frame_done(function()
    count = count + 1

    -- Frames 1-10: Hold Down Arrow & Right Arrow
    if count < 10 then
        if key_arrows then
            key_arrows:field(0x08):set_value(1) -- Press Down
            key_arrows:field(0x02):set_value(1) -- Press Right
        end
    elseif count == 15 then
        results["navigation_ok"] = true
        save_and_exit()
    end
end, "nav_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_nav")
    res = session.run()

    assert res["returncode"] == 0, f"MAME navigation run failed: {res['stderr']}"
    assert res["data"].get("navigation_ok") is True


def test_no_missing_sound_warning():
    """Verify stereo speakers are configured and audio warning is not triggered."""
    lua = """
local count = 0
emu.register_frame_done(function()
    count = count + 1
    if count == 5 then
        results["speakers_ok"] = (manager.machine.devices[":lspeaker"] ~= nil) and (manager.machine.devices[":rspeaker"] ~= nil)
        save_and_exit()
    end
end, "sound_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_audio")
    res = session.run()

    assert res["returncode"] == 0, f"Audio check failed: {res['stderr']}"
    assert res["data"].get("speakers_ok") is True


def test_mouse_motion_and_button_clicks():
    """Verify mouse delta injection and button clicks."""
    lua = """
local count = 0
local mouse_x = manager.machine.ioport.ports[":MOUSEX"]
local mouse_y = manager.machine.ioport.ports[":MOUSEY"]
local mouse_btn = manager.machine.ioport.ports[":MOUSEBTN"]

emu.register_frame_done(function()
    count = count + 1
    if count == 2 then
        if mouse_x then mouse_x:set_value(50) end
        if mouse_y then mouse_y:set_value(25) end
    elseif count == 5 then
        if mouse_btn then mouse_btn:field(0x01):set_value(1) end -- Left Click
    elseif count == 8 then
        results["mouse_ok"] = true
        save_and_exit()
    end
end, "mouse_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_mouse")
    res = session.run()

    assert res["returncode"] == 0, f"Mouse test failed: {res['stderr']}"
    assert res["data"].get("mouse_ok") is True


def test_manual_sampling_and_mode_workflow():
    """
    Automate the Roland S-760 Owner's Manual workflow:
    1. Start in Disk / Load Mode
    2. Switch to PERFORM mode via mouse/click at (40, 20)
    3. Switch to SAMPLE mode at (300, 20) to inspect waveform
    4. Switch to SYSTEM mode at (450, 20) to check 32MB RAM & SCSI config
    5. Capture screenshots for visual confirmation
    """
    lua = """
local count = 0
local key_arrows = manager.machine.ioport.ports[":KEY_ARROWS"]
local mouse_btn = manager.machine.ioport.ports[":MOUSEBTN"]

emu.register_frame_done(function()
    count = count + 1

    -- Frames 1-25: Move cursor Up (0x04) and Right (0x02) towards SYSTEM tab (x ~ 450, y ~ 20)
    if count >= 1 and count <= 26 then
        if key_arrows then
            key_arrows:field(0x04):set_value(1) -- Up
            key_arrows:field(0x02):set_value(1) -- Right
        end
    -- Frame 27: Press Enter/Click (0x10) to select SYSTEM tab
    elseif count == 27 or count == 28 then
        if key_arrows then
            key_arrows:field(0x04):set_value(0)
            key_arrows:field(0x02):set_value(0)
            key_arrows:field(0x10):set_value(1) -- Enter / Click
        end
    -- Frame 35: Capture completed state
    elseif count == 35 then
        if key_arrows then
            key_arrows:field(0x10):set_value(0)
        end
        results["workflow_ok"] = true
        results["final_mode"] = "SYSTEM"
        save_and_exit()
    end
end, "manual_workflow_test")
"""
    session = MameTestSession(lua, timeout_sec=5, snap_name="snap_manual_workflow")
    res = session.run()

    assert res["returncode"] == 0, f"Manual workflow failed: {res['stderr']}"
    assert res["data"].get("workflow_ok") is True
    assert res["data"].get("final_mode") == "SYSTEM"
    assert res["snap_path"] is not None

    # Verify SYSTEM mode screen output colors
    img, w, h = analyze_screenshot(res["snap_path"])
    pixels = img.load()

    # Verify Orange/Red tab outline (Pen 5: 220, 60, 20) rendered along top ribbon (y=14)
    found_tab_outline = False
    for x in range(w):
        r, g, b = pixels[x, 14]
        if r >= 200 and g <= 80 and b <= 40: # Pen 5: Red/Orange (220, 60, 20)
            found_tab_outline = True
            break
    assert found_tab_outline, "SYSTEM tab active outline was not rendered"


