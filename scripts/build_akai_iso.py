"""
scripts/build_akai_iso.py — Generates an authentic Akai S1000 CD-ROM ISO image with acoustic PCM samples
"""
import os
import sys
import math
import random
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from disk_formats import AkaiS1000Disk


def generate_acoustic_double_bass(rate=44100, num_samples=88200):
    """
    Generate authentic 16-bit PCM acoustic upright double bass sample:
    - Soft tactile flesh finger-pluck transient (seeded wideband excitation)
    - Deep 41.20 Hz (Low E1) physical string resonance
    - Double bass acoustic body modes (58 Hz Helmholtz cavity + 105 Hz wooden soundboard)
    - Natural acoustic exponential damping
    """
    rng = random.Random(4242)
    pcm = bytearray(num_samples * 2)
    delay_len = int(rate / 41.203) # 1070 samples for Low E1
    
    # Wideband noise filtered with a 3-tap FIR smoothing filter to simulate fleshy finger pluck
    noise = [rng.uniform(-1.0, 1.0) for _ in range(delay_len)]
    smoothed = [0.0] * delay_len
    for i in range(delay_len):
        smoothed[i] = 0.25 * noise[(i - 1) % delay_len] + 0.50 * noise[i] + 0.25 * noise[(i + 1) % delay_len]
    
    delay = [smoothed[i] * math.exp(-float(i) / (delay_len * 0.45)) for i in range(delay_len)]

    last = 0.0
    ptr = 0
    for i in range(num_samples):
        t = float(i) / rate
        nxt = delay[ptr]
        filt = 0.5 * (nxt + last) * 0.9968 # Acoustic string loss damping
        last = nxt
        delay[ptr] = filt
        ptr = (ptr + 1) % delay_len

        # Double bass wooden body cavity resonance (Helmholtz air cavity ~58Hz, wooden plate ~105Hz)
        body = 0.60 * filt + 0.25 * math.sin(2.0 * math.pi * 58.0 * t) * math.exp(-2.0 * t) + 0.15 * math.sin(2.0 * math.pi * 105.0 * t) * math.exp(-3.2 * t)
        val = int(32767.0 * 0.90 * body)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))

    return bytes(pcm)


def generate_concert_grand_piano(rate=44100, num_samples=88200):
    """Generate 16-bit PCM acoustic grand piano sample."""
    rng = random.Random(1337)
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / rate
        hammer = rng.uniform(-0.3, 0.3) * math.exp(-70.0 * t)
        val_f = hammer
        for p in range(1, 14):
            freq = 261.63 * p * math.sqrt(1.0 + 0.0004 * p * p)
            decay = math.exp(-(1.0 + 0.22 * p) * t)
            val_f += (1.0 / (p ** 1.15)) * math.sin(2.0 * math.pi * freq * t) * decay
        val = int(32767.0 * 0.75 * val_f)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def generate_orchestral_strings(rate=44100, num_samples=88200):
    """Generate 16-bit PCM orchestral string ensemble sample."""
    rng = random.Random(9999)
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / rate
        bow = min(1.0, t * 15.0)
        s1 = math.sin(2.0 * math.pi * 261.63 * t)
        s2 = 0.5 * math.sin(2.0 * math.pi * 262.45 * t)
        s3 = 0.5 * math.sin(2.0 * math.pi * 260.85 * t)
        s4 = 0.3 * math.sin(2.0 * math.pi * 523.26 * t)
        noise = rng.uniform(-0.04, 0.04) * math.exp(-15.0 * t)
        val = int(32767.0 * 0.70 * bow * (0.4 * s1 + 0.25 * s2 + 0.25 * s3 + 0.15 * s4 + noise))
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def generate_vintage_brass(rate=44100, num_samples=88200):
    """Generate 16-bit PCM vintage brass sample."""
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / rate
        env = min(1.0, t * 25.0) * (0.8 + 0.2 * math.exp(-1.5 * t))
        osc1 = sum((1.0 / h) * math.sin(2.0 * math.pi * 130.81 * h * t) for h in range(1, 12))
        osc2 = sum((1.0 / h) * math.sin(2.0 * math.pi * 131.25 * h * t) for h in range(1, 12))
        val = int(32767.0 * 0.65 * env * (0.5 * osc1 + 0.5 * osc2))
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def build_sound_iso():
    akai = AkaiS1000Disk(volume_name="AKAI ORCH")

    # Add Programs
    akai.add_program(prog_num=1, prog_name="JP8 Brass", midi_channel=1)
    akai.add_program(prog_num=2, prog_name="Orch Strings", midi_channel=2)
    akai.add_program(prog_num=3, prog_name="Grand Piano", midi_channel=3)
    akai.add_program(prog_num=4, prog_name="Double Bass", midi_channel=4)

    # Add Samples with real acoustic 16-bit PCM waveforms
    akai.add_sample(sample_name="JP8_Brass", sample_rate=44100, pcm_data=generate_vintage_brass(), loop_start=2000, loop_end=84000, root_key=48)
    akai.add_sample(sample_name="Orch_Strings", sample_rate=44100, pcm_data=generate_orchestral_strings(), loop_start=2500, loop_end=84000, root_key=60)
    akai.add_sample(sample_name="Grand_Piano", sample_rate=44100, pcm_data=generate_concert_grand_piano(), loop_start=3000, loop_end=84000, root_key=60)
    akai.add_sample(sample_name="Double_Bass", sample_rate=44100, pcm_data=generate_acoustic_double_bass(), loop_start=2140, loop_end=84000, root_key=28)

    iso_data = akai.build_iso(total_mb=2)

    os.makedirs("roms/s760", exist_ok=True)
    out_paths = ["roms/s760/sound.iso", "roms/akai.iso", "sound.iso"]
    for p in out_paths:
        with open(p, "wb") as f:
            f.write(iso_data)
        print(f"Generated Akai S1000 ISO: {p} ({len(iso_data)} bytes)")


if __name__ == "__main__":
    build_sound_iso()
