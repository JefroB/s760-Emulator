"""
mame_harness.py — Automated Python + Lua Test Harness for MAME Roland S-760
"""
import os
import subprocess
import time
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

import pytest
from PIL import Image

# --- OS-execution verification constants (Requirement 2) ---------------------
#
# The two execution signals the verification records, each paired with the
# controller that originates it in mame-source/src/mame/roland/s760.cpp:
#   - vdpVramActive: s760_state::m_vdp_vram_active, set true in vdp_w() on a
#     genuine VRAM-port (reg 0x18) write to the Roland RFSC16A VDP.
#   - sedVramActive: s760_state::m_sed_vram_active, set true in lcd_w() on a
#     genuine Epson SED1335 MWRITE (0x42) VRAM-stream write.
#
# These are C++ members, not CPU `state` registers, so the Lua side observes
# them through their genuine side effects on VRAM (non-zero bytes written only
# by the controllers above) read back via the memory-space VDP/SED ports, plus
# the captured CRT snapshot. The source labels below travel with each signal so
# a reader always knows which controller produced it (Requirement 2.2).
VDP_SIGNAL_SOURCE = "RFSC16A VDP (vdp_w)"
SED_SIGNAL_SOURCE = "Epson SED1335 (lcd_w)"

# CRT clear/background color. crt_update() clears the authentic-blank CRT to
# black before any genuine VDP rasterization, so a non-background pixel is any
# pixel that is not pure black. Non-background pixel count > 0 is the evidence a
# genuine frame was produced (Requirement 2.3).
CRT_BACKGROUND_RGB = (0, 0, 0)

DEFAULT_VERIFICATION_DURATION_SEC = 5.0

# The MAME binary + ROM set are local/hardware artifacts (the built `mames760.exe`
# and the S-760 System ROMs) that are NOT committed to the repository. They can be
# overridden via the S760_MAME_EXE / S760_ROMS_DIR environment variables so CI (or
# another workstation) can point at a provisioned build. When the binary is absent
# — e.g. a clean CI runner that only builds the C++ core + runs host-side tests —
# the MAME-launching tests skip gracefully instead of erroring, so `pytest tests`
# stays green. See `.github/workflows/ci.yml` for how CI provisions (or omits) MAME.
MAME_EXE = os.environ.get("S760_MAME_EXE", r"d:\S-760\mame-source\mames760.exe")
ROMS_DIR = os.environ.get(
    "S760_ROMS_DIR",
    r"d:\S-760\roms;d:\S-760\roms\System;d:\S-760\roms\s760;d:\S-760\roms\s760\System",
)
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
        # Skip (don't error) when the MAME binary isn't provisioned on this host
        # — e.g. a CI runner that only builds the C++ core and runs host-side
        # tests. Local/hardware runs that have the built driver run normally.
        if not os.path.exists(MAME_EXE):
            pytest.skip(
                f"MAME binary not found at {MAME_EXE}; set S760_MAME_EXE to run "
                "the MAME-driven UI tests (see .github/workflows/ci.yml)."
            )
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
            timeout=max(35, self.timeout_sec * 5)
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


# =============================================================================
# OS-execution verification (Requirement 2)
# =============================================================================
#
# Design reference — VerificationResult JSON shape (design.md "Data Models"):
#
#   {
#     "status": "pass" | "fail" | "skipped",
#     "skipReason": "<missing artifact>" | null,
#     "durationSec": 5.0,
#     "signals": {
#       "vdpVramActive": { "value": true,  "source": "RFSC16A VDP (vdp_w)" },
#       "sedVramActive": { "value": false, "source": "Epson SED1335 (lcd_w)" }
#     },
#     "crtFrame": { "captured": true, "nonBackgroundPixels": 12345 } | null,
#     "gapFinding": "signals still false after duration: [sedVramActive]" | null
#   }


@dataclass
class VerificationResult:
    """Structured result of a bounded OS-execution verification run.

    Mirrors the design "Data Models / VerificationResult" JSON shape. Build this
    with the pure `classify_verification` predicate so the pass/skip/gap decision
    is testable without launching MAME.
    """

    status: str                                  # "pass" | "fail" | "skipped"
    duration_sec: float
    signals: Dict[str, Dict[str, Any]]           # vdpVramActive / sedVramActive
    skip_reason: Optional[str] = None
    crt_frame: Optional[Dict[str, Any]] = None   # {captured, nonBackgroundPixels}
    gap_finding: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to the exact design JSON shape (camelCase keys)."""
        return {
            "status": self.status,
            "skipReason": self.skip_reason,
            "durationSec": self.duration_sec,
            "signals": self.signals,
            "crtFrame": self.crt_frame,
            "gapFinding": self.gap_finding,
        }


def make_signals(vdp_active: bool, sed_active: bool) -> Dict[str, Dict[str, Any]]:
    """Build the `signals` block, pairing each flag with its originating controller.

    Each signal records its value AND the controller that produces it, satisfying
    Requirement 2.2 (record each execution signal with its originating controller).
    """
    return {
        "vdpVramActive": {"value": bool(vdp_active), "source": VDP_SIGNAL_SOURCE},
        "sedVramActive": {"value": bool(sed_active), "source": SED_SIGNAL_SOURCE},
    }


def classify_verification(
    signals: Dict[str, Dict[str, Any]],
    crt_frame: Optional[Dict[str, Any]],
    artifacts_present: bool,
    duration_elapsed: bool,
    duration_sec: float = DEFAULT_VERIFICATION_DURATION_SEC,
    skip_reason: Optional[str] = None,
) -> VerificationResult:
    """Pure predicate: classify a verification run as pass / fail / skipped.

    This function performs NO I/O and launches no emulator — it is the reusable
    piece unit-tested by task 10.3. It encodes Requirement 2.3 / 2.4 / 2.5:

    - skipped  : artifacts absent. Never pass/fail. (2.4)
    - pass     : at least one signal true AND a captured CRT frame whose
                 nonBackgroundPixels > 0. (2.3)
    - gap/fail : if the bounded run elapsed and NEITHER signal became true, set an
                 explicit gap finding naming the signals that stayed false, and do
                 NOT report a captured frame as a pass — status is "fail". (2.5)
    - fail     : otherwise (e.g. a signal is true but no genuine frame captured).

    Args:
        signals: the `signals` block from `make_signals`.
        crt_frame: {"captured": bool, "nonBackgroundPixels": int} or None.
        artifacts_present: whether the MAME binary / ROM / image were available.
        duration_elapsed: whether the bounded run ran to its full duration.
        duration_sec: configured bound (default 5s, overridable).
        skip_reason: human-readable missing-artifact reason (only when skipped).
    """
    # --- skipped: artifacts absent, never a pass/fail (R2.4) ---
    if not artifacts_present:
        return VerificationResult(
            status="skipped",
            duration_sec=duration_sec,
            signals=signals,
            skip_reason=skip_reason or "MAME binary / ROM set / s760224.img absent",
            crt_frame=None,
            gap_finding=None,
        )

    vdp_true = bool(signals.get("vdpVramActive", {}).get("value"))
    sed_true = bool(signals.get("sedVramActive", {}).get("value"))
    any_signal = vdp_true or sed_true

    frame_captured = bool(crt_frame and crt_frame.get("captured"))
    non_bg = int(crt_frame.get("nonBackgroundPixels", 0)) if crt_frame else 0
    frame_has_pixels = frame_captured and non_bg > 0

    # --- gap finding: neither signal true after the bounded duration (R2.5) ---
    gap_finding = None
    if duration_elapsed and not any_signal:
        false_signals = [
            name for name, flag in (("vdpVramActive", vdp_true),
                                    ("sedVramActive", sed_true)) if not flag
        ]
        gap_finding = (
            "signals still false after duration: [" + ", ".join(false_signals) + "]"
        )

    # --- pass requires a true signal AND a genuine captured frame (R2.3) ---
    if any_signal and frame_has_pixels:
        status = "pass"
    else:
        status = "fail"

    # R2.5: when a gap is found, a captured frame is NEVER reported as a pass.
    # status is already "fail" here because any_signal is False.
    return VerificationResult(
        status=status,
        duration_sec=duration_sec,
        signals=signals,
        skip_reason=None,
        crt_frame=crt_frame,
        gap_finding=gap_finding,
    )


def count_non_background_pixels(png_path: str, background=CRT_BACKGROUND_RGB):
    """Count pixels in a captured CRT snapshot that are not the clear color.

    Returns None when the snapshot is absent (so the caller treats the frame as
    not captured). Otherwise returns an int >= 0. Uses analyze_screenshot() for
    the load so it shares the existing PIL path.
    """
    loaded = analyze_screenshot(png_path)
    if loaded is None:
        return None
    img, w, h = loaded
    bg = tuple(background)
    non_bg = 0
    # getcolors with a generous maxcolors avoids a full per-pixel Python loop for
    # the common low-color CRT; fall back to the pixel iterator if it overflows.
    colors = img.getcolors(maxcolors=w * h)
    if colors is not None:
        for count, color in colors:
            if color != bg:
                non_bg += count
        return non_bg
    for px in img.getdata():
        if px != bg:
            non_bg += 1
    return non_bg


def run_verification(duration_sec: float = DEFAULT_VERIFICATION_DURATION_SEC,
                     snap_name: str = "verify_os_exec") -> VerificationResult:
    """Run a bounded OS-execution verification session and classify the result.

    Builds a Lua autoboot script that, over the bounded run, observes the two
    genuine execution signals through their VRAM side effects (the VDP VRAM port
    and the SED1335 VRAM, both written only by the real vdp_w / lcd_w paths),
    captures a CRT snapshot, and writes the signal values into the JSON results.
    The harness then counts non-background pixels in the snapshot and assembles a
    VerificationResult via the pure `classify_verification` predicate.

    Skips gracefully (via MameTestSession.run()'s existing skip path) when the
    MAME binary / ROM set / image are absent (Requirements 2.4 / 8.3).

    Requirement coverage:
      2.1 — the Lua session boots the s760 driver, loading s760224.img into
            maincpu and beginning execution at the mapped reset/base address.
      2.2 — each signal (m_vdp_vram_active via a genuine vdp_w VRAM-port write;
            m_sed_vram_active via a genuine SED1335 write) is recorded true/false
            WITH its originating controller (see make_signals / *_SIGNAL_SOURCE).
      2.3 — pass requires >=1 signal true AND a captured CRT frame with
            nonBackgroundPixels > 0 (enforced in classify_verification).
      2.5 — bounded run for `duration_sec` (default 5s, overridable); if neither
            signal becomes true an explicit gap finding is reported and the frame
            is NOT reported as a pass.
    """
    # MAME runs the emulation an integer number of seconds; bound at >= 1s.
    timeout_sec = max(1, int(round(duration_sec)))

    # Lua observes genuine controller activity through VRAM side effects. The VDP
    # VRAM port (reg 0x18 at 0xD018) and the SED1335 data port (0xE000) are driven
    # only by the real vdp_w / lcd_w code; a non-zero byte read back from VDP VRAM
    # or any SED VRAM data flags that the originating controller ran. We scan each
    # frame so a signal latches true the moment the OS first drives that path.
    lua = """
local vdp = manager.machine.devices[":maincpu"].spaces["program"]
local vdp_active = false
local sed_active = false

results["vdpVramActive"] = false
results["sedVramActive"] = false

local function scan_signals()
    -- Reading the VDP VRAM data port (0xD018) returns the byte at the current
    -- 17-bit VRAM pointer and auto-increments it; genuine vdp_w writes are the
    -- only producer of non-zero VRAM, so a non-zero read evidences m_vdp_vram_active.
    if not vdp_active then
        for i = 0, 2399 do
            local b = vdp:read_u8(0xD018)
            if b ~= 0 then vdp_active = true; break end
        end
        if vdp_active then results["vdpVramActive"] = true end
    end
    -- The SED1335 data port (0xE000) returns m_sed_vram at the cursor address and
    -- auto-increments; genuine lcd_w MWRITE is the only producer, so a non-zero
    -- read evidences m_sed_vram_active.
    if not sed_active then
        for i = 0, 4095 do
            local b = vdp:read_u8(0xE000)
            if b ~= 0 then sed_active = true; break end
        end
        if sed_active then results["sedVramActive"] = true end
    end
end

local frame = 0
emu.register_frame_done(function()
    frame = frame + 1
    scan_signals()
    -- Capture a CRT snapshot a couple of frames before exit so a produced frame
    -- is on disk, then persist signals + exit on the final bounded frame.
    if frame >= {FRAMES} then
        save_and_exit()
    end
end, "verify_os_exec")
""".replace("{FRAMES}", str(max(2, timeout_sec * 60)))

    session = MameTestSession(lua, timeout_sec=timeout_sec, snap_name=snap_name)
    res = session.run()  # pytest.skip() here when artifacts are absent (R2.4/8.3)

    # If we reach here, artifacts were present (otherwise run() skipped).
    data = res.get("data", {}) or {}
    vdp_active = bool(data.get("vdpVramActive", False))
    sed_active = bool(data.get("sedVramActive", False))
    signals = make_signals(vdp_active, sed_active)

    # Count non-background pixels in the captured CRT snapshot.
    snap_path = res.get("snap_path")
    non_bg = count_non_background_pixels(snap_path) if snap_path else None
    if non_bg is None:
        crt_frame = None
    else:
        crt_frame = {"captured": True, "nonBackgroundPixels": non_bg}

    return classify_verification(
        signals=signals,
        crt_frame=crt_frame,
        artifacts_present=True,
        duration_elapsed=True,
        duration_sec=float(duration_sec),
    )
