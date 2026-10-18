"""End-to-end verification of the modified IC15 Boot ROM v1.11 + OS 2.24 System Disk
4th controller option ('GB-6 +CRT', mode 3) and native MAME GB-6 trackball config."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from build_gb6_combo import (
    BOOT_SIZE,
    BOOT_SOURCE_SHA256,
    DEFAULT_BOOT_SOURCE,
    DEFAULT_OS_SOURCE,
    OS_SIZE,
    OS_SOURCE_SHA256,
    build_combo,
    build_os_gb6_poll_stub,
    patch_boot_rom_bytes,
    patch_os_disk_bytes,
    verify_disassembly,
)
from s760_runtime import NativeRuntime, RuntimeConfig

MAME_EXE = ROOT / "mame-source" / "mames760.exe"


@pytest.fixture
def combo_firmware():
    """Only full firmware integrations need local proprietary inputs/tooling."""
    if not all(path.is_file() for path in (DEFAULT_BOOT_SOURCE, DEFAULT_OS_SOURCE)):
        pytest.skip("Private IC15 Boot ROM and OS 2.24 image required")
    pytest.importorskip("pypcode", reason="Optional firmware disassembler required")


@pytest.mark.parametrize("patch,size", [(patch_boot_rom_bytes, BOOT_SIZE), (patch_os_disk_bytes, OS_SIZE)])
def test_combo_patch_rejects_unrecognized_baselines(patch, size):
    for data in (b"not firmware", bytes(size)):
        with pytest.raises(ValueError, match="unmodified"):
            patch(data)


@pytest.mark.parametrize("profile", ("v8", "v9"))
def test_combo_dispatch_preserves_mouse_target_and_isolates_scaling(profile):
    """Public generated-code checks require neither ROMs nor a disassembler."""
    code = build_os_gb6_poll_stub(profile)
    assert code[:6] == bytes.fromhex("99 01 DA D7 03 E7")
    assert 0x7A20 + 8 + int.from_bytes(code[6:8], "little", signed=True) == 0x57B4
    assert code[8:14] == bytes.fromhex("99 03 DA DF 01 F0")
    other = build_os_gb6_poll_stub("v9" if profile == "v8" else "v8")
    assert len(code) == len(other)
    differences = [i for i, pair in enumerate(zip(code, other)) if pair[0] != pair[1]]
    assert len(differences) == 1
    index = differences[0]
    assert code[index-1] == 0x19 and code[index+1] == 0xAD  # X-axis SHLB operand only
    assert code[index] == (3 if profile == "v8" else 2)


def test_gb6_combo_builder_and_pypcode_disassembly(tmp_path: Path, combo_firmware) -> None:
    """Verify deterministic combo build, byte-diff boundaries, pypcode disassembly, and source immutability."""
    report_v9 = build_combo(
        boot_source=DEFAULT_BOOT_SOURCE,
        os_source=DEFAULT_OS_SOURCE,
        out_dir=tmp_path / "v9",
        profile="v9",
    )
    assert report_v9["boot_size"] == BOOT_SIZE
    assert report_v9["boot_diff_bytes"] == 13
    assert report_v9["boot_output_sha256"] == "a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb"

    assert report_v9["os_size"] == OS_SIZE
    assert report_v9["os_diff_bytes"] == 220
    assert report_v9["os_output_sha256"] == "0a15c81ad6747803160815393f2c2c207f15861bd5671d349ebde4aa3929af15"

    assert len(report_v9["disasm_instruction_counts"]) == 10
    for count in report_v9["disasm_instruction_counts"].values():
        assert count > 0

    # Verify v8 profile also builds and disassembles cleanly
    rom_bytes = patch_boot_rom_bytes(DEFAULT_BOOT_SOURCE.read_bytes())
    os_v8_bytes = patch_os_disk_bytes(DEFAULT_OS_SOURCE.read_bytes(), profile="v8")
    checks_v8 = verify_disassembly(rom_bytes, os_v8_bytes)
    assert len(checks_v8) == 10

    # Ensure canonical baseline files were not modified
    assert hashlib.sha256(DEFAULT_BOOT_SOURCE.read_bytes()).hexdigest() == BOOT_SOURCE_SHA256
    assert hashlib.sha256(DEFAULT_OS_SOURCE.read_bytes()).hexdigest() == OS_SOURCE_SHA256


def test_runtime_config_validates_pointing_device_and_config_file(tmp_path: Path) -> None:
    """Verify RuntimeConfig validates pointing_device and config_file options."""
    exe = tmp_path / "mame.exe"
    boot = tmp_path / "boot.bin"
    disk = tmp_path / "system.img"
    cfg_file = tmp_path / "s760_config.json"
    exe.write_bytes(b"exe")
    boot.write_bytes(b"boot")
    disk.write_bytes(bytes(OS_SIZE))
    cfg_file.write_text('{"pointing_device": "gb6"}', encoding="utf-8")

    for mode in ("mouse", "gb6", "auto"):
        rc = RuntimeConfig(exe, boot, disk, tmp_path / "state", pointing_device=mode, config_file=cfg_file)
        rc.validate()

    bad_mode = RuntimeConfig(exe, boot, disk, tmp_path / "state", pointing_device="invalid")
    with pytest.raises(ValueError, match="Pointing device must be mouse, gb6 or auto"):
        bad_mode.validate()

    missing_cfg = RuntimeConfig(exe, boot, disk, tmp_path / "state", config_file=tmp_path / "missing.json")
    with pytest.raises(FileNotFoundError):
        missing_cfg.validate()


@pytest.mark.skipif(not MAME_EXE.is_file(), reason="mames760.exe not built")
def test_gb6_combo_mame_setup_persistence_and_native_gb6_config(tmp_path: Path, combo_firmware) -> None:
    """Test IC15 Setup Menu, EEPROM cold-reboot persistence, native s760.cpp GB-6 config file,
    CRT cursor movement, System Parameter 2 Controller selection, and F00A=80 fallback."""
    out_dir = tmp_path / "images"
    report = build_combo(
        boot_source=DEFAULT_BOOT_SOURCE,
        os_source=DEFAULT_OS_SOURCE,
        out_dir=out_dir,
        profile="v9",
    )
    boot_rom = Path(report["boot_output"])
    os_disk = Path(report["os_output"])
    nvram_dir = tmp_path / "nvram"
    snap_dir = tmp_path / "snaps"
    nvram_dir.mkdir(parents=True, exist_ok=True)
    snap_dir.mkdir(parents=True, exist_ok=True)

    # Write s760_config.json enabling native Sony GB-6 emulation in s760.cpp (no Lua 0xF008 bus taps!)
    config_file = tmp_path / "s760_config.json"
    config_file.write_text(json.dumps({"pointing_device": "gb6"}, indent=2), encoding="utf-8")

    def run_mame(lua_body: str, seconds: int = 35, f00a: str = "00", clear_nvram: bool = False) -> str:
        if clear_nvram and nvram_dir.exists():
            shutil.rmtree(nvram_dir)
            nvram_dir.mkdir(parents=True, exist_ok=True)
        res_file = tmp_path / "result.txt"
        res_file.unlink(missing_ok=True)
        lua_file = tmp_path / "test.lua"
        lua_file.write_text(
            f"local RESULT_PATH = {json.dumps(str(res_file.resolve()))}\n" + lua_body,
            encoding="utf-8",
        )
        env = {k: v for k, v in os.environ.items() if not k.startswith("S760_")}
        env.update(
            S760_ROM_BOOT=str(boot_rom.resolve()),
            S760_FLOPPY=str(os_disk.resolve()),
            S760_CONFIG=str(config_file.resolve()),
            S760_F00A=f00a,
        )
        cmd = [
            str(MAME_EXE),
            "s760",
            "-rompath",
            str(ROOT / "roms"),
            "-window",
            "-nomaximize",
            "-video",
            "none",
            "-sound",
            "none",
            "-nothrottle",
            "-nvram_directory",
            str(nvram_dir.resolve()),
            "-snapshot_directory",
            str(snap_dir.resolve()),
            "-autoboot_script",
            str(lua_file.resolve()),
            "-seconds_to_run",
            str(seconds),
        ]
        subprocess.run(cmd, cwd=str(ROOT / "mame-source"), env=env, capture_output=True, text=True, timeout=seconds + 30, check=True)
        return res_file.read_text(encoding="utf-8") if res_file.exists() else ""

    # 1. Boot with Mode held -> IC15 Setup Menu -> step Controller 0..3 -> Save & Boot OS -> Move GB-6 & open System Parameter 2
    lua_setup_and_os = r"""
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local reg = cpu.spaces["register"]
local iop = manager.machine.ioport

local function write_log(lines)
    local f = io.open(RESULT_PATH, "w")
    if f then
        for _, l in ipairs(lines) do f:write(l .. "\n") end
        f:close()
    end
end

local function set_switch(port_tag, mask, pressed)
    local port = iop.ports[port_tag]
    if not port then return end
    for _, field in pairs(port.fields) do
        if field.mask == mask then
            field:set_value(pressed and 1 or 0)
            return
        end
    end
end

local mouse_x, mouse_y = 0, 0
local function set_mouse_xy(x, y)
    mouse_x = x & 0xffff
    mouse_y = y & 0xffff
    for _, f in pairs(iop.ports[":NATIVE_MOUSE_X"].fields) do f:set_value(mouse_x) end
    for _, f in pairs(iop.ports[":NATIVE_MOUSE_Y"].fields) do f:set_value(mouse_y) end
end

local function set_mouse_btn(left_down, right_down)
    for _, f in pairs(iop.ports[":NATIVE_MOUSE_BUTTONS"].fields) do
        if f.mask == 0x10 then f:set_value(left_down and 1 or 0) end
        if f.mask == 0x20 then f:set_value(right_down and 1 or 0) end
    end
end

local function read_cursor()
    return reg:read_u16(0xd0), reg:read_u8(0xd2)
end

local function step_cursor_toward(tx, ty)
    local cx, cy = read_cursor()
    local ex, ey = tx - cx, ty - cy
    local dx, dy = 0, 0
    if math.abs(ex) >= 8 then
        dx = math.max(-7, math.min(7, math.floor(ex / 8)))
        if dx == 0 then dx = (ex > 0) and 1 or -1 end
    end
    if math.abs(ey) >= 8 then
        dy = math.max(-7, math.min(7, math.floor(ey / 8)))
        if dy == 0 then dy = (ey > 0) and 1 or -1 end
    end
    if dx ~= 0 or dy ~= 0 then
        set_mouse_xy(mouse_x + dx, mouse_y + dy)
    end
end

local frame = 0
local log = {}
local vals = {}

-- Hold Mode BEFORE frame 1 executes so IC15 power-on scan enters Setup Menu
set_switch(":PANEL1", 0x01, true)

emu.register_frame_done(function()
    frame = frame + 1
    if frame < 120 then
        set_switch(":PANEL1", 0x01, true)
    elseif frame == 120 then
        set_switch(":PANEL1", 0x01, false)
    elseif frame == 128 then
        set_switch(":PANEL1", 0x04, true) -- Panel Up: field 3 (Contrast) -> field 2 (Controller)
    elseif frame == 131 then
        set_switch(":PANEL1", 0x04, false)
    elseif frame == 135 then
        table.insert(log, string.format("setup_field=%d", mem:read_u8(0x4D30)))
        set_switch(":PANEL0", 0x02, true) -- S1 (Dec) -> 0
    elseif frame == 138 then set_switch(":PANEL0", 0x02, false)
    elseif frame == 145 then
        table.insert(vals, tostring(mem:read_u8(0x4CB2)))
        set_switch(":PANEL0", 0x02, true) -- S1 (Dec) -> clamp at 0
    elseif frame == 148 then set_switch(":PANEL0", 0x02, false)
    elseif frame == 155 then
        table.insert(vals, tostring(mem:read_u8(0x4CB2)))
        set_switch(":PANEL0", 0x04, true) -- S2 (Inc) -> 1
    elseif frame == 158 then set_switch(":PANEL0", 0x04, false)
    elseif frame == 165 then
        table.insert(vals, tostring(mem:read_u8(0x4CB2)))
        set_switch(":PANEL0", 0x04, true) -- S2 (Inc) -> 2
    elseif frame == 168 then set_switch(":PANEL0", 0x04, false)
    elseif frame == 175 then
        table.insert(vals, tostring(mem:read_u8(0x4CB2)))
        set_switch(":PANEL0", 0x04, true) -- S2 (Inc) -> 3 (GB-6 +CRT)
    elseif frame == 178 then set_switch(":PANEL0", 0x04, false)
    elseif frame == 185 then
        table.insert(vals, tostring(mem:read_u8(0x4CB2)))
        set_switch(":PANEL0", 0x04, true) -- S2 (Inc) -> clamp at 3
    elseif frame == 188 then set_switch(":PANEL0", 0x04, false)
    elseif frame == 195 then
        table.insert(vals, tostring(mem:read_u8(0x4CB2)))
        table.insert(log, "setup_vals=" .. table.concat(vals, ","))
        set_switch(":PANEL1", 0x02, true) -- Exit: saves EEPROM and boots OS
    elseif frame == 200 then
        set_switch(":PANEL1", 0x02, false)
    elseif frame == 980 then
        local cx, cy = read_cursor()
        table.insert(log, string.format("os_2476=%d start_cursor=(%d,%d)", mem:read_u8(0x2476), cx, cy))
    elseif frame >= 985 and frame < 1045 and (frame % 2 == 0) then
        step_cursor_toward(288, 8) -- Move to System menu button using native C++ GB-6 emulation
    elseif frame == 1048 then
        local cx, cy = read_cursor()
        table.insert(log, string.format("at_system=(%d,%d)", cx, cy))
        set_mouse_btn(true, false)
    elseif frame == 1053 then
        set_mouse_btn(false, false)
    elseif frame >= 1060 and frame < 1100 and (frame % 2 == 0) then
        step_cursor_toward(256, 40) -- Move to System PRM
    elseif frame == 1102 then
        set_mouse_btn(true, false)
    elseif frame == 1107 then
        set_mouse_btn(false, false)
    elseif frame >= 1125 and frame < 1185 and (frame % 2 == 0) then
        step_cursor_toward(40, 176) -- Move to Page( 1)
    elseif frame == 1188 then
        set_mouse_btn(false, true) -- Right click (Inc) -> Page( 2)
    elseif frame == 1193 then
        set_mouse_btn(false, false)
    elseif frame >= 1205 and frame < 1255 and (frame % 2 == 0) then
        step_cursor_toward(240, 112) -- Move to Controller on System Parameter 2
    elseif frame == 1260 then
        local cx, cy = read_cursor()
        table.insert(log, string.format("at_controller=(%d,%d)", cx, cy))
        write_log(log)
        manager.machine:exit()
    end
end)
"""
    res1 = run_mame(lua_setup_and_os, seconds=35, f00a="00", clear_nvram=True)
    assert "setup_field=2" in res1
    assert "setup_vals=0,0,1,2,3,3" in res1
    assert "os_2476=3 start_cursor=(0,0)" in res1
    assert "at_system=(288,8)" in res1
    assert "at_controller=(240,112)" in res1

    # 2. Cold reboot from saved NVRAM: verify 0x4CB2 == 3 and 0x2476 == 3 persist
    lua_reboot = r"""
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local frame = 0
local boot_4cb2 = -1
emu.register_frame_done(function()
    frame = frame + 1
    if frame == 60 then boot_4cb2 = mem:read_u8(0x4CB2) end
    if frame == 850 then
        local f = io.open(RESULT_PATH, "w")
        if f then
            f:write(string.format("reboot_4cb2=%d reboot_2476=%d\n", boot_4cb2, mem:read_u8(0x2476)))
            f:close()
        end
        manager.machine:exit()
    end
end)
"""
    res2 = run_mame(lua_reboot, seconds=25, f00a="00", clear_nvram=False)
    assert "reboot_4cb2=3 reboot_2476=3" in res2

    # 3. Boot with S760_F00A=80 (no OP-760 CRT board): verify clean fallback to 0 (Panel+LCD)
    lua_no_crt = r"""
local cpu = manager.machine.devices[":maincpu"]
local mem = cpu.spaces["program"]
local frame = 0
local boot_4cb2 = -1
emu.register_frame_done(function()
    frame = frame + 1
    if frame == 60 then boot_4cb2 = mem:read_u8(0x4CB2) end
    if frame == 850 then
        local f = io.open(RESULT_PATH, "w")
        if f then
            f:write(string.format("nocrt_4cb2=%d nocrt_2476=%d\n", boot_4cb2, mem:read_u8(0x2476)))
            f:close()
        end
        manager.machine:exit()
    end
end)
"""
    res3 = run_mame(lua_no_crt, seconds=25, f00a="80", clear_nvram=False)
    assert "nocrt_4cb2=0 nocrt_2476=0" in res3


@pytest.mark.skipif(not MAME_EXE.is_file(), reason="mames760.exe not built")
def test_gb6_combo_native_runtime_integration(tmp_path: Path, combo_firmware) -> None:
    """Verify NativeRuntime works with modified Boot ROM, modified OS disk, and GB-6 config file."""
    out_dir = tmp_path / "images"
    report = build_combo(
        boot_source=DEFAULT_BOOT_SOURCE,
        os_source=DEFAULT_OS_SOURCE,
        out_dir=out_dir,
        profile="v9",
    )
    boot_rom = Path(report["boot_output"])
    os_disk = Path(report["os_output"])
    state_dir = tmp_path / "runtime_state"
    config_file = tmp_path / "s760_config.json"
    config_file.write_text(json.dumps({"pointing_device": "auto"}, indent=2), encoding="utf-8")

    # Pre-populate NVRAM with Controller = 3 (GB-6 +CRT) at byte offset 8 (word 4 low byte)
    # matching the 64-word AK93C45 default image in s760.cpp with word[4] = 0x0803 instead of 0x0801
    nvram_dir = state_dir / "nvram" / "s760"
    nvram_dir.mkdir(parents=True, exist_ok=True)
    initial_eeprom = [
        0x0702, 0x0000, 0x0001, 0x0000, 0x0803, 0x0000, 0x2e31, 0x3030,
        0x6f52, 0x616c, 0x646e, 0x6556, 0x2e72, 0x3120, 0x312e, 0x3631,
        0x0100, 0x00ff, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000,
        0x0000, 0x0000, 0x0000, 0x0000, 0x0001, 0x0000, 0x0000, 0x0000,
        0x7f08, 0x0000, 0x0001, 0x00ff, 0x0001, 0x3c3c, 0x3c3c, 0x7f7f,
        0x7f7f, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000, 0x0000,
        0x1918, 0x1b1a, 0x1d1c, 0x1f1e, 0x4f4e, 0x5150, 0x5352, 0x5554,
        0x1110, 0x1312, 0x1514, 0x1716, 0x4746, 0x4948, 0x4b4a, 0x4d4c,
    ]
    import struct
    (nvram_dir / "serial_eeprom").write_bytes(struct.pack("<64H", *initial_eeprom))

    cfg = RuntimeConfig(
        executable=MAME_EXE,
        boot_rom=boot_rom,
        system_disk=os_disk,
        state_dir=state_dir,
        sound=False,
        throttle=False,
        pointing_device="auto",
        config_file=config_file,
    )
    with NativeRuntime(cfg) as runtime:
        target = runtime.request("frames")[0]["seconds"] + 18.0
        deadline = time.monotonic() + 30.0
        while runtime.request("frames")[0]["seconds"] < target:
            if time.monotonic() > deadline:
                raise TimeoutError("NativeRuntime stopped advancing")
            time.sleep(0.01)

        meta, frames = runtime.request("frames")
        assert any(frames[0][6:][0::4]), "CRT frame is blank in GB-6 +CRT mode"
        assert sum(b.bit_count() for b in frames[1][6:]) > 100, "LCD frame is blank in GB-6 +CRT mode"

        # Move pointer via NativeRuntime's pointer command in GB-6 +CRT mode
        runtime.request("pointer", x=120, y=56)
        target_move = runtime.request("frames")[0]["seconds"] + 0.5
        while runtime.request("frames")[0]["seconds"] < target_move:
            time.sleep(0.01)

        cursor = runtime.request("frames")[0]["cursor"]
        assert abs(cursor[0] - 240) <= 8 and abs(cursor[1] - 112) <= 8, f"Unexpected GB-6 cursor: {cursor}"
