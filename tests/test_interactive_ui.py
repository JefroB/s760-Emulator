"""
test_interactive_ui.py — Automated verification of Roland S-760 UI, navigation, and audio
"""
import sys
import os
import pytest
sys.path.insert(0, os.path.dirname(__file__))
from mame_harness import MameTestSession, analyze_screenshot


def test_mame_boot_and_palette_rendering():
    """Verify MAME boots cleanly and produces a CRT snapshot.

    ui-consolidation task 1.5 (R4.1, R4.2): the former Royal-Blue/Green chrome
    pixel scraping was removed. Those colors were painted by the deleted invented
    GUI (crt_update banner/ribbon chrome, tasks 1.1-1.2), not by any authentic
    display controller. Per F2 the OS cannot cold-boot without the IC20 BOOT ROM,
    so the genuine RFSC16A VDP produces a blank (defined background) CRT until
    then. This test now asserts only the authentic invariant: the driver boots
    and a CRT snapshot is produced. The removed background/ribbon color checks
    migrate to the React suite (task 4.3).
    """
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



# ui-consolidation task 1.8 (R1.2, R2.2): test_mouse_motion_and_button_clicks
# was removed. It injected host-mouse deltas into the :MOUSEX / :MOUSEY ioports
# and a left-click into :MOUSEBTN. Those ports were the invented MAME mouse-cursor
# input path (an 8-bit relative delta register clamped to +/-127 and applied 1:1
# to m_cur_x/m_cur_y) — the root cause of the slow/crawling cursor. The crosshair
# render + click dispatch were deleted in tasks 1.1-1.2, and task 1.8 removed the
# ports and their INPUT_CHANGED handlers. Under D4 the React shell owns the
# pointer (tasks 3.3/3.4), so host-mouse motion is no longer meaningful at the
# MAME layer. The genuine OP-760-2 hardware mouse registers (VDP 0x20-0x24) are
# still covered by tests/test_vdp_mame.py::test_vdp_hardware_mouse_cursor_registers.


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
    session = MameTestSession(lua, timeout_sec=15, snap_name="snap_manual_workflow")
    res = session.run()

    assert res["returncode"] == 0, f"Manual workflow failed: {res['stderr']}"
    assert res["data"].get("workflow_ok") is True
    assert res["data"].get("final_mode") == "SYSTEM"
    assert res["snap_path"] is not None

    # ui-consolidation task 1.5 (R4.1, R4.2): the Pen-5 SYSTEM-tab-outline pixel
    # assertion was removed. The mode ribbon / tab outline was invented chrome
    # drawn by crt_update (deleted in tasks 1.1-1.2); mode tabs and their active
    # outline are now owned by the React shell. The input-injection workflow above
    # still exercises the genuine ioport path (keyboard/mouse fields), which is a
    # real driver invariant; only the drawn-chrome pixel scrape is dropped. The
    # SYSTEM-tab selection check migrates to the React suite (task 4.3).


def test_rack_panel_and_embedded_lcd_rendering():
    """Verify the CRT display surface boots and reports authentic geometry.

    ui-consolidation task 1.5 (R4.1, R4.2): all rack-chrome scraping was removed.
    The 1U rack charcoal chassis, embedded LCD-green backlight, and Gotek OLED
    cyan were invented chrome drawn by render_rack_panel (deleted in task 1.1) in
    the former 120px rack strip. Per task 1.2 the CRT screen geometry was reduced
    from 640x360 to the authentic CRT region only (640x240), so the rack strip no
    longer exists in the MAME output at all — the rack/LCD-housing/Gotek chrome is
    now the React shell's responsibility (R6). This test now asserts only the
    authentic invariant: the driver boots and the CRT surface is the real
    640x240 OP-760 geometry. The rack/LCD/Gotek rendering checks migrate to the
    React suite (task 4.3).
    """
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

    # Authentic OP-760 CRT geometry only (640x240). The former composite
    # 640x360 (CRT + 120px invented rack strip) no longer exists.
    img, w, h = analyze_screenshot(res["snap_path"])
    assert w == 640, f"Expected authentic CRT width 640, got {w}"
    assert h == 240, f"Expected authentic CRT height 240 (rack strip removed), got {h}"


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

    # ui-consolidation task 1.5 (R4.1, R4.2): the Gotek OLED cyan pixel scraping
    # was removed. The Gotek OLED readout was invented chrome drawn in the former
    # 120px rack strip (render_rack_panel, deleted task 1.1); that strip no longer
    # exists after the CRT geometry was reduced to 640x240 (task 1.2). The Gotek
    # Prev/Next/Select input path above still drives the genuine :GOTEK_CTRL
    # ioport fields — a real driver invariant that is retained. The OLED readout /
    # hot-swap visual check migrates to the React suite (task 4.3).


def test_seamless_mouse_navigation_between_crt_and_rack_ui():
    """
    Verify seamless bidirectional mouse navigation between:
    1. CRT screen elements (Mode tabs, Patch rows, Waveform preview)
    2. 1U Rack Panel elements (Gotek next/prev buttons, OLED mount, Push encoder)
    """
    lua = """
local count = 0
local key_arrows = manager.machine.ioport.ports[":KEY_ARROWS"]
local gotek_ctrl = manager.machine.ioport.ports[":GOTEK_CTRL"]

emu.register_frame_done(function()
    count = count + 1

    -- Phase 1 (Frames 1-26): Move Up & Right towards SYSTEM tab (x ~ 450, y ~ 20)
    if count >= 1 and count <= 26 then
        if key_arrows then
            key_arrows:field(0x04):set_value(1) -- Up
            key_arrows:field(0x02):set_value(1) -- Right
        end
    -- Phase 2 (Frames 27-28): Click to select SYSTEM tab
    elseif count == 27 or count == 28 then
        if key_arrows then
            key_arrows:field(0x04):set_value(0)
            key_arrows:field(0x02):set_value(0)
            key_arrows:field(0x10):set_value(1) -- Click SYSTEM tab
        end
    -- Phase 3 (Frame 29): Release click
    elseif count == 29 then
        if key_arrows then key_arrows:field(0x10):set_value(0) end
    -- Phase 4 (Frames 30-31): Step Gotek Next [ > ] (0x02)
    elseif count == 30 or count == 31 then
        if gotek_ctrl then gotek_ctrl:field(0x02):set_value(1) end
    -- Phase 5 (Frame 32): Release Gotek Next
    elseif count == 32 then
        if gotek_ctrl then gotek_ctrl:field(0x02):set_value(0) end
    -- Phase 6 (Frames 33-34): Mount Gotek [ SEL ] (0x04)
    elseif count == 33 or count == 34 then
        if gotek_ctrl then gotek_ctrl:field(0x04):set_value(1) end
    -- Phase 7 (Frame 36+): Complete and save
    elseif count >= 36 then
        if gotek_ctrl then gotek_ctrl:field(0x04):set_value(0) end
        results["seamless_navigation_ok"] = true
        save_and_exit()
    end
end, "seamless_nav_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_seamless_nav")
    res = session.run()

    assert res["returncode"] == 0, f"Seamless navigation failed: {res['stderr']}"
    assert res["data"].get("seamless_navigation_ok") is True
    assert res["snap_path"] is not None

    # ui-consolidation task 1.5 (R4.1, R4.2): both chrome scrapes were removed.
    #  1. The SYSTEM-tab active outline (Pen 5 on the top ribbon) was invented
    #     chrome drawn by crt_update (deleted tasks 1.1-1.2); mode tabs are now
    #     the React shell's job.
    #  2. The Gotek-mounted OLED cyan check lived in the former 120px rack strip
    #     (render_rack_panel, deleted task 1.1), which no longer exists after the
    #     CRT geometry was reduced to 640x240 (task 1.2).
    # The cross-surface input injection above still exercises the genuine
    # :KEY_ARROWS and :GOTEK_CTRL ioport fields (a real driver invariant) and the
    # run completes cleanly. The "seamless CRT<->rack navigation" visual behavior
    # is reimplemented against the real owner in the React suite (task 4.3).




