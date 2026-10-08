"""
scripts/generate_calibration_tones.py — Generates calibrated 16-bit 44.1kHz reference WAV files
for physical Roland S-760 input stage, ADC, and filter testing.
"""

import os
import math
import random
import struct
import wave

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tests", "hardware_recordings", "input_tones")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def write_wav(filepath, samples, sample_rate=44100):
    """Write 16-bit mono PCM WAV file."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        pcm_bytes = bytearray()
        for s in samples:
            val = max(-32767, min(32767, int(s * 32767.0)))
            pcm_bytes.extend(struct.pack("<h", val))
        wf.writeframes(pcm_bytes)
    print(f"Generated: {filepath} ({len(samples)} samples)")


def generate_all_tones(sample_rate=44100):
    # 1. 1 kHz Sine @ 0 dBFS (3 seconds)
    n_samples = sample_rate * 3
    sine_0db = [math.sin(2.0 * math.pi * 1000.0 * i / sample_rate) for i in range(n_samples)]
    write_wav(os.path.join(OUTPUT_DIR, "01_sine_1khz_0db.wav"), sine_0db, sample_rate)

    # 2. 1 kHz Sine @ -6 dBFS (3 seconds)
    sine_minus6db = [0.501187 * math.sin(2.0 * math.pi * 1000.0 * i / sample_rate) for i in range(n_samples)]
    write_wav(os.path.join(OUTPUT_DIR, "02_sine_1khz_minus6db.wav"), sine_minus6db, sample_rate)

    # 3. Logarithmic Sine Sweep (20 Hz -> 22.05 kHz over 10 seconds @ -3 dBFS)
    sweep_duration = 10.0
    n_sweep = int(sample_rate * sweep_duration)
    f_start = 20.0
    f_end = 22050.0
    amp = 0.707946  # -3 dBFS
    sweep = []
    for i in range(n_sweep):
        t = float(i) / sample_rate
        # Instantaneous frequency: f(t) = f_start * (f_end / f_start) ^ (t / T)
        # Phase integral: phi(t) = 2 * pi * f_start * ( (f_end / f_start)^(t/T) - 1 ) / (ln(f_end/f_start) / T)
        rate_log = math.log(f_end / f_start) / sweep_duration
        phi = 2.0 * math.pi * f_start * (math.exp(rate_log * t) - 1.0) / rate_log
        sweep.append(amp * math.sin(phi))
    write_wav(os.path.join(OUTPUT_DIR, "03_log_sweep_20hz_22khz.wav"), sweep, sample_rate)

    # 4. Bandlimited Dirac Impulse with 1-second silence
    impulse = [0.0] * sample_rate
    impulse[1000] = 0.95  # Sharp excitation
    write_wav(os.path.join(OUTPUT_DIR, "04_dirac_impulse.wav"), impulse, sample_rate)

    # 5. Full Spectrum White Noise (3 seconds @ -12 dBFS)
    rng = random.Random(42)
    noise = [rng.uniform(-0.25, 0.25) for _ in range(n_samples)]
    write_wav(os.path.join(OUTPUT_DIR, "05_white_noise.wav"), noise, sample_rate)


if __name__ == "__main__":
    generate_all_tones()
