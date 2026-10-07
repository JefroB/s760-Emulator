"""
mame_harness.py — Automated Python + Lua Test Harness for MAME Roland S-760
"""
import os
import subprocess
import time
import json
from PIL import Image

MAME_EXE = r"d:\S-760\mame-source\mames760.exe"
ROMS_DIR = r"d:\S-760\roms;d:\S-760\roms\System;d:\S-760\roms\s760;d:\S-760\roms\s760\System"
SNAP_DIR = r"d:\S-760\mame-source\snap\s760"
SCRATCH_DIR = r"d:\S-760\temp\test_harness"

os.makedirs(SCRATCH_DIR, exist_ok=True)


class MameTestSession:
    def __init__(self, script_body: str, timeout_sec: int = 5, snap_name: str = "test_snap"):
        self.script_body = script_body
        self.timeout_sec = timeout_sec
        self.snap_name = snap_name
        self.script_path = os.path.join(SCRATCH_DIR, f"{snap_name}.lua")
        self.out_json = os.path.join(SCRATCH_DIR, f"{snap_name}_out.json").replace("\\", "/")
        self.snap_path = os.path.join(SNAP_DIR, f"{snap_name}.png")

    def run(self):
        # Wrap script body with bootstrap & exit logic
        full_lua = f"""
local json = require("json")
local frame_count = 0
local results = {{}}

local function log_state(msg)
    print("[HARNESS] " .. tostring(msg))
end

local function save_and_exit()
    local f = io.open("{self.out_json}", "w")
    if f then
        f:write(json.stringify(results))
        f:close()
    end
    manager.machine.video:snapshot()
    manager.machine:exit()
end

{self.script_body}
"""
        with open(self.script_path, "w", encoding="utf-8") as f:
            f.write(full_lua)

        cmd = [
            MAME_EXE,
            "s760",
            "-window",
            "-video", "gdi",
            "-numscreens", "1",
            "-nothrottle",
            "-rompath", ROMS_DIR,
            "-snapname", f"s760/{self.snap_name}",
            "-autoboot_script", self.script_path,
            "-str", str(self.timeout_sec)
        ]

        proc = subprocess.run(
            cmd,
            cwd=r"d:\S-760\mame-source",
            capture_output=True,
            text=True,
            timeout=max(20, self.timeout_sec * 3)
        )

        data = {}
        if os.path.exists(self.out_json):
            with open(self.out_json, "r", encoding="utf-8") as f:
                try:
                    data = json.load(f)
                except Exception:
                    pass

        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "data": data,
            "snap_path": self.snap_path if os.path.exists(self.snap_path) else None
        }


def analyze_screenshot(png_path: str):
    """Analyze pixel colors from captured screenshot."""
    if not os.path.exists(png_path):
        return None
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    return img, w, h
