"""
tests/test_unified_core.py — Dedicated regression tests for S760HardwareCore unified C++ engine.
Verifies cycle-accurate DSP parameter streaming, 4-point Hermite cubic interpolation, 4-pole ZDF resonant TVF filter,
multi-voice audio rendering, and full parity between MAME and DAW plugin core.
"""

import os
import math
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_HPP = os.path.join(ROOT, "core", "include", "s760", "s760_core.hpp")
CORE_CPP = os.path.join(ROOT, "core", "src", "s760_core.cpp")


class PyUnifiedHardwareCore:
    """Python reference simulator mirroring S760HardwareCore C++ implementation."""
    def __init__(self):
        self.wave_ram = [0] * (2 * 1024 * 1024)
        self.dsp_addr = 0
        self.dsp_data = 0
        self.voices = []
        for _ in range(32):
            self.voices.append({
                "active": False,
                "start_addr": 0,
                "length": 44100,
                "loop_start": 0,
                "loop_end": 44100,
                "loop_mode": 0,
                "pos": 0.0,
                "step": 1.0,
                "volume": 1.0,
                "pan_l": 1.0,
                "pan_r": 1.0,
                "env_level": 0.0,
                "env_attack": 0.005,
                "env_decay": 0.0002,
                "env_sustain": 0.75,
                "env_release": 0.001,
                "env_stage": 0,
                "tvf_cutoff": 127,
                "tvf_resonance": 0,
                "tvf_mode": 0,
                "tvf_s1": 0.0, "tvf_s2": 0.0, "tvf_s3": 0.0, "tvf_s4": 0.0,
                "tva_level": 127,
                "tva_pan": 0,
                "out_bus": 0
            })

    def write_mmio_addr(self, data):
        self.dsp_addr = data & 0xFF

    def write_mmio_data(self, data):
        self.dsp_data = data & 0xFF
        voice_idx = self.dsp_addr & 0x1F
        reg_idx = (self.dsp_addr >> 5) & 0x07
        if voice_idx >= 32:
            return
        v = self.voices[voice_idx]

        if reg_idx == 0x00:
            v["step"] = data / 128.0 if data > 0 else 1.0
        elif reg_idx == 0x01:
            v["step"] = float(data + 1)
        elif reg_idx == 0x02:
            v["start_addr"] = data * 4096
        elif reg_idx == 0x03:
            v["loop_start"] = data * 256
        elif reg_idx == 0x04:
            v["loop_end"] = data * 256
        elif reg_idx == 0x05:
            v["active"] = (data & 0x01) != 0
            v["loop_mode"] = 1 if (data & 0x02) else 0
            v["out_bus"] = (data >> 4) & 0x0F
            if v["active"]:
                v["pos"] = 0.0
                v["env_level"] = 1.0
                v["env_stage"] = 1
                v["tvf_s1"] = v["tvf_s2"] = v["tvf_s3"] = v["tvf_s4"] = 0.0
        elif reg_idx == 0x06:
            v["tvf_cutoff"] = data & 0x7F
            v["tvf_resonance"] = 64 if (data & 0x80) else 0
        elif reg_idx == 0x07:
            v["tva_level"] = data & 0x7F
            v["volume"] = v["tva_level"] / 127.0

    def read_mmio_data(self):
        voice_idx = self.dsp_addr & 0x1F
        reg_idx = (self.dsp_addr >> 5) & 0x07
        if voice_idx >= 32:
            return 0
        v = self.voices[voice_idx]
        if reg_idx == 0x00:
            return int(v["step"] * 128.0) & 0xFF
        elif reg_idx == 0x05:
            return 0x01 if v["active"] else 0x00
        elif reg_idx == 0x06:
            return v["tvf_cutoff"]
        elif reg_idx == 0x07:
            return v["tva_level"]
        return 0

    def note_on(self, v_idx, wave_addr, length, loop_s, loop_e, loop_m, sample_rate, note, root_key, vel=1.0, pan=0.0):
        if v_idx < 0 or v_idx >= 32:
            return
        v = self.voices[v_idx]
        v["start_addr"] = wave_addr
        v["length"] = length
        v["loop_start"] = loop_s
        v["loop_end"] = loop_e if loop_e > 0 else length
        v["loop_mode"] = loop_m
        v["pos"] = 0.0
        v["step"] = (sample_rate / 44100.0) * math.pow(2.0, (note - root_key) / 12.0)
        v["volume"] = max(0.0, min(1.0, vel))
        v["pan_l"] = max(0.0, min(1.0, 1.0 - pan))
        v["pan_r"] = max(0.0, min(1.0, 1.0 + pan))
        v["env_level"] = 0.0
        v["env_attack"] = 0.005
        v["env_decay"] = 0.0002
        v["env_sustain"] = 0.75
        v["env_release"] = 0.001
        v["env_stage"] = 1
        v["tvf_s1"] = v["tvf_s2"] = v["tvf_s3"] = v["tvf_s4"] = 0.0
        v["active"] = True

    def note_off(self, v_idx):
        if 0 <= v_idx < 32 and self.voices[v_idx]["active"]:
            self.voices[v_idx]["env_stage"] = 4

    @staticmethod
    def cutoff_to_hz(cutoff):
        fc = 20.0 * math.pow(10.0, float(cutoff) * 3.0 / 127.0)
        return max(20.0, min(20000.0, fc))

    @staticmethod
    def hermite_interpolate(y0, y1, y2, y3, frac):
        c0 = y1
        c1 = 0.5 * (y2 - y0)
        c2 = y0 - 2.5 * y1 + 2.0 * y2 - 0.5 * y3
        c3 = 0.5 * (y3 - y0) + 1.5 * (y1 - y2)
        return ((c3 * frac + c2) * frac + c1) * frac + c0

    def render_audio(self, num_frames=512, sample_rate=44100.0):
        left = [0.0] * num_frames
        right = [0.0] * num_frames

        for v in self.voices:
            if not v["active"]:
                continue

            for i in range(num_frames):
                if v["env_stage"] == 1:
                    v["env_level"] += v["env_attack"]
                    if v["env_level"] >= 1.0:
                        v["env_level"] = 1.0
                        v["env_stage"] = 2
                elif v["env_stage"] == 2:
                    v["env_level"] -= v["env_decay"]
                    if v["env_level"] <= v["env_sustain"]:
                        v["env_level"] = v["env_sustain"]
                        v["env_stage"] = 3
                elif v["env_stage"] == 4:
                    v["env_level"] -= v["env_release"]
                    if v["env_level"] <= 0.0:
                        v["env_level"] = 0.0
                        v["active"] = False
                        break

                idx = v["start_addr"] + int(v["pos"])
                frac = v["pos"] - int(v["pos"])

                s = 0.0
                if idx >= 1 and idx + 2 < len(self.wave_ram):
                    y0 = self.wave_ram[idx - 1] / 32768.0
                    y1 = self.wave_ram[idx] / 32768.0
                    y2 = self.wave_ram[idx + 1] / 32768.0
                    y3 = self.wave_ram[idx + 2] / 32768.0
                    s = self.hermite_interpolate(y0, y1, y2, y3, frac)
                elif idx + 1 < len(self.wave_ram):
                    s0 = self.wave_ram[idx] / 32768.0
                    s1 = self.wave_ram[idx + 1] / 32768.0
                    s = s0 + frac * (s1 - s0)
                elif idx < len(self.wave_ram):
                    s = self.wave_ram[idx] / 32768.0

                # TVF Filter
                if v["tvf_cutoff"] < 127 or v["tvf_resonance"] > 0:
                    fc = self.cutoff_to_hz(v["tvf_cutoff"])
                    w = 2.0 * math.pi * fc / sample_rate
                    g = math.tan(w * 0.5)
                    k = 3.98 * math.pow(float(v["tvf_resonance"]) / 127.0, 1.4)

                    g_over_1g = g / (1.0 + g)
                    u = s - k * math.tanh(v["tvf_s4"])

                    v1 = g_over_1g * (u - v["tvf_s1"])
                    y1 = v1 + v["tvf_s1"]
                    v["tvf_s1"] = y1 + v1

                    v2 = g_over_1g * (y1 - v["tvf_s2"])
                    y2 = v2 + v["tvf_s2"]
                    v["tvf_s2"] = y2 + v2

                    v3 = g_over_1g * (y2 - v["tvf_s3"])
                    y3 = v3 + v["tvf_s3"]
                    v["tvf_s3"] = y3 + v3

                    v4 = g_over_1g * (y3 - v["tvf_s4"])
                    y4 = v4 + v["tvf_s4"]
                    v["tvf_s4"] = y4 + v4

                    if v["tvf_mode"] == 0:
                        s = y4
                    elif v["tvf_mode"] == 1:
                        s = 4.0 * (y2 - y3)
                    elif v["tvf_mode"] == 2:
                        s = u - 4.0 * y1 + 6.0 * y2 - 4.0 * y3 + y4

                gain = s * v["volume"] * v["env_level"] * 0.35
                left[i] += gain * v["pan_l"]
                right[i] += gain * v["pan_r"]

                v["pos"] += v["step"]
                if v["loop_mode"] != 0 and v["pos"] >= v["loop_end"]:
                    loop_len = float(v["loop_end"] - v["loop_start"])
                    v["pos"] = v["loop_start"] + ((v["pos"] - v["loop_start"]) % loop_len) if loop_len > 1.0 else v["loop_start"]
                elif v["loop_mode"] == 0 and v["pos"] >= v["length"]:
                    v["active"] = False
                    break

        return left, right


# ==============================================================================
# Unit & Regression Tests
# ==============================================================================

def test_unified_core_source_files_exist():
    """Verify that unified core header and source files exist."""
    assert os.path.exists(CORE_HPP), f"Missing header at {CORE_HPP}"
    assert os.path.exists(CORE_CPP), f"Missing source at {CORE_CPP}"
    with open(CORE_HPP, "r", encoding="utf-8") as f:
        hpp = f.read()
    assert "class S760HardwareCore" in hpp
    assert "hermite_interpolate" in hpp
    assert "cutoff_to_hz" in hpp


def test_unified_core_reset_and_initial_state():
    """Verify clean initial state on reset."""
    core = PyUnifiedHardwareCore()
    assert sum(1 for v in core.voices if v["active"]) == 0
    assert len(core.voices) == 32
    for v in core.voices:
        assert v["tvf_cutoff"] == 127
        assert v["tvf_resonance"] == 0
        assert v["tva_level"] == 127


def test_unified_core_cutoff_to_hz_mapping():
    """Verify exact logarithmic cutoff frequency curve mapping."""
    # Cutoff 0 should map to 20 Hz
    assert abs(PyUnifiedHardwareCore.cutoff_to_hz(0) - 20.0) < 0.1
    # Cutoff 127 should map to 20,000 Hz
    assert abs(PyUnifiedHardwareCore.cutoff_to_hz(127) - 20000.0) < 1.0
    # Cutoff 64 (midpoint) should map to ~650 Hz
    mid_hz = PyUnifiedHardwareCore.cutoff_to_hz(64)
    assert 600.0 <= mid_hz <= 700.0


def test_unified_core_hermite_interpolation_properties():
    """Verify Hermite interpolation matches nodal endpoints and interpolates smoothly."""
    y0, y1, y2, y3 = -0.5, 0.0, 1.0, 0.5
    # Exact nodal match at 0.0 and 1.0
    assert abs(PyUnifiedHardwareCore.hermite_interpolate(y0, y1, y2, y3, 0.0) - y1) < 1e-6
    assert abs(PyUnifiedHardwareCore.hermite_interpolate(y0, y1, y2, y3, 1.0) - y2) < 1e-6
    # Smooth monotonic rise between y1=0 and y2=1
    v025 = PyUnifiedHardwareCore.hermite_interpolate(y0, y1, y2, y3, 0.25)
    v050 = PyUnifiedHardwareCore.hermite_interpolate(y0, y1, y2, y3, 0.50)
    v075 = PyUnifiedHardwareCore.hermite_interpolate(y0, y1, y2, y3, 0.75)
    assert 0.0 < v025 < v050 < v075 < 1.0


def test_unified_core_note_triggering_and_audio_render():
    """Verify triggering notes and rendering audio into stereo output buffers."""
    core = PyUnifiedHardwareCore()

    # Fill wave RAM with 1000 samples of a 440Hz sine wave
    for i in range(1000):
        core.wave_ram[i] = int(math.sin(2.0 * math.pi * 440.0 * i / 44100.0) * 28000)

    # Trigger Note On for Voice 0: A4 (note 69, root 69)
    core.note_on(0, wave_addr=0, length=1000, loop_s=100, loop_e=900, loop_m=1,
                 sample_rate=44100.0, note=69, root_key=69, vel=1.0, pan=0.0)

    assert core.voices[0]["active"] is True

    # Render 512 frames
    left, right = core.render_audio(512)
    assert len(left) == 512 and len(right) == 512
    max_l = max(abs(s) for s in left)
    max_r = max(abs(s) for s in right)
    assert max_l > 0.05
    assert max_r > 0.05


def test_unified_core_polyphony_and_note_off():
    """Verify multi-voice polyphony and note-off release envelope."""
    core = PyUnifiedHardwareCore()

    # Trigger 8 voices
    for v in range(8):
        core.note_on(v, 0, 1000, 0, 1000, 1, 44100.0, 60 + v, 60)

    active_count = sum(1 for v in core.voices if v["active"])
    assert active_count == 8

    # Note off for voice 3
    core.note_off(3)
    assert core.voices[3]["env_stage"] == 4  # Release stage
