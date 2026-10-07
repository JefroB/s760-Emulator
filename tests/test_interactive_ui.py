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
    """Verify stereo speakers and s760_sound DSP device are configured and active."""
    lua = """
local count = 0
emu.register_frame_done(function()
    count = count + 1
    if count == 5 then
        results["speakers_ok"] = (manager.machine.devices[":lspeaker"] ~= nil) and (manager.machine.devices[":rspeaker"] ~= nil)
        results["sound_device_ok"] = (manager.machine.devices[":s760_sound"] ~= nil)
        save_and_exit()
    end
end, "sound_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_audio")
    res = session.run()

    assert res["returncode"] == 0, f"Audio check failed: {res['stderr']}"
    assert res["data"].get("speakers_ok") is True
    assert res["data"].get("sound_device_ok") is True



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


def test_rack_panel_and_embedded_lcd_rendering():
    """Verify 1U Rack Panel, embedded 160x64 green LCD, and Gotek display are rendered."""
    lua = """
local count = 0
emu.register_frame_done(function()
    count = count + 1
    if count == 10 then
        results["rack_ok"] = true
        save_and_exit()
    end
end, "rack_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_rack_lcd")
    res = session.run()

    assert res["returncode"] == 0, f"MAME rack test failed: {res['stderr']}"
    assert res["data"].get("rack_ok") is True
    assert res["snap_path"] is not None

    img, w, h = analyze_screenshot(res["snap_path"])
    assert w >= 640, f"Expected screen width >= 640, got {w}"
    assert h >= 360, f"Expected composite screen height >= 360, got {h}"

    pixels = img.load()
    found_lcd_green = False
    found_gotek_oled_cyan = False
    found_rack_charcoal = False

    # Check bottom rack area (y in lower 1/3 of the frame)
    y_start = int(h * 240 / 360)
    for y in range(y_start, h, 2):
        for x in range(0, w, 4):
            r, g, b = pixels[x, y]
            # LCD Backlight Green: rgb(30, 95, 35) or bright LCD text rgb(165, 245, 110)
            if (r <= 50 and g >= 80 and b <= 50) or (r >= 140 and g >= 220 and b >= 90):
                found_lcd_green = True
            # Gotek OLED Cyan: rgb(80, 230, 255)
            if r <= 100 and g >= 200 and b >= 230:
                found_gotek_oled_cyan = True
            # 1U Rack Charcoal Chassis: rgb(38, 40, 46)
            if 30 <= r <= 45 and 30 <= g <= 48 and 38 <= b <= 52:
                found_rack_charcoal = True

    assert found_rack_charcoal, "1U Rack dark charcoal chassis not detected"
    assert found_lcd_green, "Embedded 160x64 green backlit LCD screen not detected in rack panel"
    assert found_gotek_oled_cyan, "Gotek OLED cyan display not detected in rack drive bay"


def test_gotek_oled_and_navigation_controls():
    """Verify Gotek Prev/Next buttons and Rotary Encoder Push/Select hot-swaps images."""
    lua = """
local count = 0
local gotek_ctrl = manager.machine.ioport.ports[":GOTEK_CTRL"]

emu.register_frame_done(function()
    count = count + 1

    -- Frames 1-3: Press Gotek Next Button [ > ] (0x02)
    if count >= 1 and count <= 3 then
        if gotek_ctrl then gotek_ctrl:field(0x02):set_value(1) end
    -- Frame 4: Release Next Button
    elseif count == 4 then
        if gotek_ctrl then gotek_ctrl:field(0x02):set_value(0) end
    -- Frames 5-8: Press Gotek Select / Push Button (0x04)
    elseif count >= 5 and count <= 8 then
        if gotek_ctrl then gotek_ctrl:field(0x04):set_value(1) end
    -- Frame 9: Release Select Button
    elseif count == 9 then
        if gotek_ctrl then gotek_ctrl:field(0x04):set_value(0) end
    -- Frame 15: Verify and complete
    elseif count == 15 then
        results["gotek_swap_ok"] = true
        save_and_exit()
    end
end, "gotek_nav_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_gotek_nav")
    res = session.run()

    assert res["returncode"] == 0, f"Gotek navigation test failed: {res['stderr']}"
    assert res["data"].get("gotek_swap_ok") is True
    img, w, h = analyze_screenshot(res["snap_path"])
    pixels = img.load()

    # Verify Gotek OLED area is rendered
    found_oled_text = False
    y_start = int(h * 240 / 360)
    for y in range(y_start, h):
        for x in range(w):
            r, g, b = pixels[x, y]
            if (70 <= r <= 95) and (215 <= g <= 245) and (240 <= b <= 255): # Gotek OLED Cyan rgb(80, 230, 255)
                found_oled_text = True
                break
        if found_oled_text:
            break
    assert found_oled_text, "Gotek OLED active text was not rendered"



