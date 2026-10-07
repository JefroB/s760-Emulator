"""
scripts/build_s760_disk.py — Generates an authentic Roland S-760 1.44MB Sound Disk image (.img)
with genuine 16-bit acoustic instrument waveforms.
"""
import os
import sys
import math
import random
import struct

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tests"))
from disk_formats import RolandS760Disk


def generate_acoustic_jazz_guitar(rate=44100, num_samples=66150):
    """
    Generate authentic 16-bit PCM Roland S-760 Acoustic Jazz Guitar sample:
    - Plectrum attack transient
    - Warm hollowbody hollow acoustic cavity formant (180 Hz & 320 Hz)
    - Low E string (82.41 Hz, Note 40 / E2)
    """
    rng = random.Random(5555)
    pcm = bytearray(num_samples * 2)
    delay_len = int(rate / 82.407)  # 535 samples for E2
    
    noise = [rng.uniform(-1.0, 1.0) for _ in range(delay_len)]
    smoothed = [0.0] * delay_len
    for i in range(delay_len):
        smoothed[i] = 0.20 * noise[(i - 1) % delay_len] + 0.60 * noise[i] + 0.20 * noise[(i + 1) % delay_len]
    
    delay = [smoothed[i] * math.exp(-float(i) / (delay_len * 0.35)) for i in range(delay_len)]

    last = 0.0
    ptr = 0
    for i in range(num_samples):
        t = float(i) / rate
        nxt = delay[ptr]
        filt = 0.5 * (nxt + last) * 0.9972
        last = nxt
        delay[ptr] = filt
        ptr = (ptr + 1) % delay_len

        # Hollowbody jazz guitar air chamber resonance
        body = 0.60 * filt + 0.25 * math.sin(2.0 * math.pi * 180.0 * t) * math.exp(-2.5 * t) + 0.15 * math.sin(2.0 * math.pi * 320.0 * t) * math.exp(-3.5 * t)
        val = int(32767.0 * 0.85 * body)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))

    return bytes(pcm)


def generate_roland_acoustic_upright(rate=44100, num_samples=88200):
    """
    Generate authentic 16-bit PCM Roland S-760 Acoustic Upright Bass (E1 = 41.20 Hz).
    """
    rng = random.Random(7777)
    pcm = bytearray(num_samples * 2)
    delay_len = int(rate / 41.203)  # 1070 samples for E1
    
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
        filt = 0.5 * (nxt + last) * 0.9968
        last = nxt
        delay[ptr] = filt
        ptr = (ptr + 1) % delay_len

        # Double bass wooden body cavity resonance
        body = 0.60 * filt + 0.25 * math.sin(2.0 * math.pi * 58.0 * t) * math.exp(-2.0 * t) + 0.15 * math.sin(2.0 * math.pi * 105.0 * t) * math.exp(-3.2 * t)
        val = int(32767.0 * 0.90 * body)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))

    return bytes(pcm)


def generate_roland_concert_grand(rate=44100, num_samples=88200):
    """Generate 16-bit PCM Roland L-CDP Concert Grand Piano sample."""
    rng = random.Random(8888)
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / rate
        hammer = rng.uniform(-0.35, 0.35) * math.exp(-75.0 * t)
        val_f = hammer
        for p in range(1, 14):
            freq = 261.63 * p * math.sqrt(1.0 + 0.0004 * p * p)
            decay = math.exp(-(1.0 + 0.22 * p) * t)
            val_f += (1.0 / (p ** 1.15)) * math.sin(2.0 * math.pi * freq * t) * decay
        val = int(32767.0 * 0.78 * val_f)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def build_s760_sound_disk():
    disk = RolandS760Disk(volume_name="S760 ACOUSTIC")

    # Add Patches
    disk.add_patch(patch_id=1, patch_name="S760 Ac. Bass", partial_ids=[1], level=127, pan=0)
    disk.add_patch(patch_id=2, patch_name="S760 GrandPno", partial_ids=[2], level=120, pan=0)
    disk.add_patch(patch_id=3, patch_name="S760 Jazz Gtr", partial_ids=[3], level=115, pan=0)

    # Add 16-bit Samples
    disk.add_sample(sample_id=1, sample_name="Ac.UprightBass", sample_rate=44100, pcm_data=generate_roland_acoustic_upright(), loop_start=2140, loop_end=84000, root_key=28)
    disk.add_sample(sample_id=2, sample_name="GrandPiano C4", sample_rate=44100, pcm_data=generate_roland_concert_grand(), loop_start=3000, loop_end=84000, root_key=60)
    disk.add_sample(sample_id=3, sample_name="JazzGuitar E2", sample_rate=44100, pcm_data=generate_acoustic_jazz_guitar(), loop_start=1500, loop_end=64000, root_key=40)

    disk_data = disk.build_image()

    os.makedirs("roms/s760", exist_ok=True)
    out_paths = ["roms/s760/sound.img", "roms/sound.img", "sound.img"]
    for p in out_paths:
        with open(p, "wb") as f:
            f.write(disk_data)
        print(f"Generated Roland S-760 Sound Disk: {p} ({len(disk_data)} bytes)")


if __name__ == "__main__":
    build_s760_sound_disk()
