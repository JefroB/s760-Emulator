"""
tests/test_calibration_tools.py — Automated verification of Gotek calibration tools,
disk synthesis, sample extraction, and hardware parity analysis scripts.
"""

import os
import sys
import tempfile
import wave
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.generate_calibration_tones import generate_all_tones, OUTPUT_DIR as TONES_DIR
from scripts.build_calibration_disk import build_calibration_disk, OUTPUT_PATH as CALIB_IMG_PATH
from scripts.extract_s760_sample import extract_samples_from_img
from scripts.analyze_hardware_parity import (
    read_wav,
    compute_rms_db,
    compute_thd_n,
    analyze_stage1_analog_in,
    analyze_stage2_pitch_transposition,
    analyze_stage3_tvf_sweeps,
)


def test_generate_calibration_tones_output():
    """Verify calibrated test tones are generated with correct formats and audio invariants."""
    generate_all_tones(sample_rate=44100)

    expected_files = [
        ("01_sine_1khz_0db.wav", 44100 * 3, -4.0, -2.5),        # Sine peak 1.0 -> RMS ~ -3.01 dBFS
        ("02_sine_1khz_minus6db.wav", 44100 * 3, -10.0, -8.0),   # Sine peak ~0.5 -> RMS ~ -9.03 dBFS
        ("03_log_sweep_20hz_22khz.wav", 44100 * 10, -7.0, -5.0), # Sweep @ -3dBFS
        ("04_dirac_impulse.wav", 44100, -50.0, -10.0),          # Impulse spike
        ("05_white_noise.wav", 44100 * 3, -20.0, -12.0),        # Uniform noise
    ]

    for filename, expected_samples, min_rms, max_rms in expected_files:
        filepath = os.path.join(TONES_DIR, filename)
        assert os.path.exists(filepath), f"Missing generated tone: {filepath}"

        with wave.open(filepath, "rb") as wf:
            assert wf.getnchannels() == 1, f"{filename} should be mono"
            assert wf.getsampwidth() == 2, f"{filename} should be 16-bit"
            assert wf.getframerate() == 44100, f"{filename} should be 44.1kHz"
            assert wf.getnframes() == expected_samples, f"{filename} frame count mismatch"

        samples, rate = read_wav(filepath)
        assert len(samples) == expected_samples
        assert rate == 44100
        rms = compute_rms_db(samples)
        assert min_rms <= rms <= max_rms, f"{filename} RMS {rms:.2f} dBFS out of range [{min_rms}, {max_rms}]"


def test_build_calibration_disk_structure():
    """Verify synthesized Gotek floppy disk image conforms to S-760 geometry and directory layout."""
    img_path = build_calibration_disk(CALIB_IMG_PATH)
    assert os.path.exists(img_path)
    assert os.path.getsize(img_path) == 1474560, "Image size must be exactly 1.44MB (1,474,560 bytes)"

    with open(img_path, "rb") as f:
        img_bytes = f.read()

    # Verify Volume Header in Sector 0
    vol_name = img_bytes[0x00:0x10].decode("ascii", errors="ignore").strip()
    assert "S760 CALIBRATION" in vol_name or "S-760" in vol_name or "S760" in vol_name

    # Check Patch Records at offset 0x4800
    assert b"01:RAW_TRANSP" in img_bytes[0x4800:0x6000]
    assert b"02:TVF_CUTOFF" in img_bytes[0x4800:0x6000]
    assert b"03:TVF_RES_SWP" in img_bytes[0x4800:0x6000]
    assert b"04:TVF_MODES" in img_bytes[0x4800:0x6000]

    # Check Sample Descriptor Names at offset 0x10000+
    assert b"Sine 440Hz A4" in img_bytes[0x10000:]
    assert b"Saw 110Hz A2" in img_bytes[0x10000:]
    assert b"White Noise 1s" in img_bytes[0x10000:]


def test_extract_s760_samples_from_calib_img():
    """Verify sample extractor correctly unpacks 16-bit PCM WAV files from .IMG disks."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        extracted = extract_samples_from_img(CALIB_IMG_PATH, tmp_dir)
        assert len(extracted) == 3, f"Expected 3 extracted samples, got {len(extracted)}"

        # Check extracted files exist and contain valid wave data
        for wav_path in extracted:
            assert os.path.exists(wav_path)
            with wave.open(wav_path, "rb") as wf:
                assert wf.getnchannels() == 1
                assert wf.getsampwidth() == 2
                assert wf.getframerate() == 44100
                assert wf.getnframes() > 1000


def test_analyze_hardware_parity_metrics():
    """Verify THD+N, RMS, and multi-stage analysis functions produce mathematically sound metrics."""
    sine_path = os.path.join(TONES_DIR, "01_sine_1khz_0db.wav")
    assert os.path.exists(sine_path)

    # Read and test mathematical metrics on pure 1kHz sine
    samples, rate = read_wav(sine_path)
    rms = compute_rms_db(samples)
    assert -3.10 <= rms <= -2.90, f"Expected 1kHz 0dB sine RMS ~ -3.01 dBFS, got {rms:.2f}"

    thd_n = compute_thd_n(samples, fundamental_freq=1000.0, sample_rate=rate)
    # Pure mathematical sine wave should have extremely low THD+N (quantization noise floor only)
    assert thd_n < -60.0, f"Pure sine THD+N should be < -60 dB, got {thd_n:.2f}"

    # Stage 1: Comparison between source and recorded
    stage1_res = analyze_stage1_analog_in(sine_path, sine_path)
    assert abs(stage1_res["gain_delta_db"]) < 0.01
    assert stage1_res["thd_n_db"] < -60.0

    # Stage 2 & 3: Directory batch analysis
    with tempfile.TemporaryDirectory() as tmp_dir:
        extracted = extract_samples_from_img(CALIB_IMG_PATH, tmp_dir)
        stage2_res = analyze_stage2_pitch_transposition(tmp_dir)
        assert len(stage2_res) == 3

        stage3_res = analyze_stage3_tvf_sweeps(tmp_dir)
        assert len(stage3_res) == 3
