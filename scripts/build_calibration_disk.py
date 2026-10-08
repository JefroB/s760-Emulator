"""
scripts/build_calibration_disk.py — Synthesizes a ready-to-mount 1.44MB Roland S-760 Sound Disk (.IMG)
containing precision calibration waveforms and patches for RoboSampler multi-sampling and hardware testing.
"""

import os
import sys
import math
import struct
import random

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from disk_formats import RolandS760Disk

OUTPUT_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "roms", "FDD", "S760_CALIB.IMG")
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)


def generate_single_cycle_sine(freq=440.0, rate=44100, num_cycles=200):
    """Generate loopable single-cycle sine wave at 440 Hz (A4 = Note 69)."""
    cycle_len = int(rate / freq)  # ~100 samples
    total_samples = cycle_len * num_cycles
    pcm = bytearray(total_samples * 2)
    for i in range(total_samples):
        s = math.sin(2.0 * math.pi * freq * i / rate)
        val = int(s * 30000.0)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm), cycle_len, total_samples


def generate_bandlimited_saw(freq=110.0, rate=44100, num_cycles=100):
    """Generate loopable bandlimited sawtooth wave at 110 Hz (A2 = Note 45)."""
    cycle_len = int(rate / freq)  # 400 samples
    total_samples = cycle_len * num_cycles
    pcm = bytearray(total_samples * 2)
    num_harmonics = int(20000.0 / freq)  # Up to 20kHz
    for i in range(total_samples):
        t = float(i) / rate
        s = 0.0
        for h in range(1, min(40, num_harmonics)):
            s += (1.0 / h) * math.sin(2.0 * math.pi * freq * h * t)
        val = int(s * 18000.0)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm), cycle_len, total_samples


def generate_calibration_noise(rate=44100, num_samples=44100):
    """Generate 1 second of white noise for filter testing."""
    rng = random.Random(1234)
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        s = rng.uniform(-0.6, 0.6)
        val = int(s * 32767.0)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm), 0, num_samples


def build_calibration_disk(output_path=OUTPUT_PATH):
    disk = RolandS760Disk(volume_name="S760 CALIBRATION")

    # Sample 1: 440Hz Sine Wave (A4 = Root Key 69)
    sine_pcm, cycle_sine, total_sine = generate_single_cycle_sine(440.0)
    disk.add_sample(1, "Sine 440Hz A4", 44100, sine_pcm, loop_start=0, loop_end=cycle_sine, root_key=69)

    # Sample 2: 110Hz Sawtooth Wave (A2 = Root Key 45)
    saw_pcm, cycle_saw, total_saw = generate_bandlimited_saw(110.0)
    disk.add_sample(2, "Saw 110Hz A2", 44100, saw_pcm, loop_start=0, loop_end=cycle_saw, root_key=45)

    # Sample 3: White Noise for TVF response (Root Key 60)
    noise_pcm, _, total_noise = generate_calibration_noise(44100)
    disk.add_sample(3, "White Noise 1s", 44100, noise_pcm, loop_start=0, loop_end=total_noise, root_key=60)

    # Patch 1: Raw Transposition Test (Bypassed TVF, 100% Sustain)
    disk.add_patch(1, "01:RAW_TRANSP", partial_ids=[1, 2], level=127, pan=0)

    # Patch 2: TVF Cutoff Steps Test
    disk.add_patch(2, "02:TVF_CUTOFF", partial_ids=[3, 3], level=127, pan=0)

    # Patch 3: TVF Resonance Sweep Test
    disk.add_patch(3, "03:TVF_RES_SWP", partial_ids=[2, 2], level=127, pan=0)

    # Patch 4: TVF Mode Comparison (LPF / BPF / HPF)
    disk.add_patch(4, "04:TVF_MODES", partial_ids=[2, 3], level=127, pan=0)

    img_data = disk.build_image()
    with open(output_path, "wb") as f:
        f.write(img_data)

    print(f"Synthesized Gotek Calibration Floppy Disk Image: {output_path} ({len(img_data)} bytes)")
    return output_path


if __name__ == "__main__":
    build_calibration_disk()
