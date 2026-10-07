"""
test_dsp_tools.py — Automated Verification for Roland S-760 DSP & Offline Processing Tools
Covers previously untested functions from Roland S-760 Owner's Manual:
- OM Sec. 5.5: Loop Smoothing & Crossfade Looping
- OM Sec. 5.6: Time Stretch, Digital Filter, Sample Rate Convert, Bit Convert
- OM Sec. 5.7: Auto Truncate & Peak Normalization, Wave Editing (Cut, Splice, Erase, Mix)
- OM Sec. 6.6: Disk Optimization / Defragmentation
- OM Sec. 6.8: MS-DOS FAT12 Floppy Format & Sample Exchange
- OM Sec. 7.4: MIDI Sample Dump Standard (SDS) Protocol
"""
import pytest
import math
import struct
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from dsp_tools import (
    S760DSPTools,
    S760DiskOptimizer,
    S760MSDOSExchange,
    S760MIDISampleDump
)
from disk_formats import RolandS760Disk, S760VoiceSynthesizer


def generate_pcm_sine(freq=440.0, rate=44100, num_samples=44100, decay=0.0):
    """Generates 16-bit PCM sine wave."""
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / float(rate)
        env = math.exp(-decay * t) if decay > 0 else 1.0
        val = int(32767.0 * 0.8 * math.sin(2.0 * math.pi * freq * t) * env)
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def test_crossfade_loop_smoothing():
    """OM Sec. 5.5: Test crossfade loop smoothing on discontinuous wave boundaries."""
    # Create PCM tone with discontinuity at loop boundary
    pcm = generate_pcm_sine(freq=440.0, rate=44100, num_samples=44100)
    loop_start = 5000
    loop_end = 35000

    smoothed = S760DSPTools.crossfade_loop(pcm, loop_start, loop_end, xfade_samples=500)
    assert len(smoothed) == len(pcm)

    # Verify that the samples near the loop end transition smoothly
    tail_sample = struct.unpack_from("<h", smoothed, (loop_end - 1) * 2)[0]
    head_sample = struct.unpack_from("<h", smoothed, loop_start * 2)[0]
    # In crossfaded loop, the boundary step difference is bounded
    assert abs(tail_sample - head_sample) < 30000


def test_time_stretch_tempo_expansion_and_compression():
    """OM Sec. 5.6: Test pitch-preserving time compression and expansion (SOLA)."""
    # 440 Hz tone, 1 second (44100 samples)
    pcm = generate_pcm_sine(freq=440.0, rate=44100, num_samples=44100)

    # 1. Expand duration by 1.25x (slower tempo, same pitch)
    expanded = S760DSPTools.time_stretch(pcm, stretch_factor=1.25, sample_rate=44100)
    exp_num_samples = len(expanded) // 2
    assert abs(exp_num_samples - int(44100 * 1.25)) < 100

    # 2. Compress duration by 0.8x (faster tempo, same pitch)
    compressed = S760DSPTools.time_stretch(pcm, stretch_factor=0.8, sample_rate=44100)
    comp_num_samples = len(compressed) // 2
    assert abs(comp_num_samples - int(44100 * 0.8)) < 100

    # Verify audio energy remains strong
    samples_exp = [struct.unpack_from("<h", expanded, i * 2)[0] for i in range(exp_num_samples)]
    rms_exp = math.sqrt(sum(s * s for s in samples_exp) / len(samples_exp)) / 32768.0
    assert rms_exp > 0.10


def test_digital_filter_lpf_and_hpf():
    """OM Sec. 5.6: Test 2-pole digital Low-Pass and High-Pass offline filters."""
    # Composite signal: Low 100 Hz tone + High 8000 Hz tone
    num_samples = 44100
    pcm_composite = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / 44100.0
        v_low = 0.5 * math.sin(2.0 * math.pi * 100.0 * t)
        v_high = 0.5 * math.sin(2.0 * math.pi * 8000.0 * t)
        val = int(32767.0 * (v_low + v_high))
        struct.pack_into("<h", pcm_composite, i * 2, max(-32767, min(32767, val)))
    pcm_composite = bytes(pcm_composite)

    # 1. Apply Low-Pass Filter @ 500 Hz (attenuates 8000 Hz)
    lpf_pcm = S760DSPTools.digital_filter(pcm_composite, cutoff_hz=500.0, sample_rate=44100, filter_type="lpf")
    assert len(lpf_pcm) == len(pcm_composite)
    lpf_samples = [struct.unpack_from("<h", lpf_pcm, i * 2)[0] for i in range(num_samples)]
    lpf_rms = math.sqrt(sum(s * s for s in lpf_samples) / num_samples) / 32768.0
    assert lpf_rms > 0.10

    # 2. Apply High-Pass Filter @ 3000 Hz (attenuates 100 Hz)
    hpf_pcm = S760DSPTools.digital_filter(pcm_composite, cutoff_hz=3000.0, sample_rate=44100, filter_type="hpf")
    assert len(hpf_pcm) == len(pcm_composite)
    hpf_samples = [struct.unpack_from("<h", hpf_pcm, i * 2)[0] for i in range(num_samples)]
    hpf_rms = math.sqrt(sum(s * s for s in hpf_samples) / num_samples) / 32768.0
    assert hpf_rms > 0.10


def test_sample_rate_conversion_44k_to_22k_and_32k():
    """OM Sec. 5.6: Test sample rate conversion between standard rates (44.1k -> 22.05k / 32k)."""
    pcm_44k = generate_pcm_sine(freq=440.0, rate=44100, num_samples=44100) # 1 sec = 44100 samples

    # 1. Downsample to 22050 Hz
    pcm_22k = S760DSPTools.sample_rate_convert(pcm_44k, in_rate=44100, out_rate=22050)
    assert len(pcm_22k) // 2 == 22050

    # 2. Resample to 32000 Hz
    pcm_32k = S760DSPTools.sample_rate_convert(pcm_44k, in_rate=44100, out_rate=32000)
    assert len(pcm_32k) // 2 == 32000


def test_bit_depth_reduction_16bit_to_8bit():
    """OM Sec. 5.6: Test 16-bit to 8-bit resolution reduction."""
    pcm_16 = generate_pcm_sine(freq=440.0, rate=44100, num_samples=1000)
    pcm_8 = S760DSPTools.bit_convert(pcm_16, target_bits=8)

    assert len(pcm_8) == len(pcm_16)
    # Check that lower 8 bits are zeroed out (quantized to 8-bit grid)
    for i in range(len(pcm_8) // 2):
        val = struct.unpack_from("<h", pcm_8, i * 2)[0]
        assert (val & 0xFF) == 0


def test_auto_truncate_and_peak_normalization():
    """OM Sec. 5.7: Test silence stripping at start/end and 0 dBFS peak normalization."""
    # Create signal with 1000 samples silence, 5000 samples low-volume tone, 1000 samples silence
    silence = bytes(2000) # 1000 samples of 0
    tone = generate_pcm_sine(freq=440.0, rate=44100, num_samples=5000)
    # Attenuate tone to 25% peak
    attenuated = bytearray(len(tone))
    for i in range(len(tone) // 2):
        v = int(struct.unpack_from("<h", tone, i * 2)[0] * 0.25)
        struct.pack_into("<h", attenuated, i * 2, v)

    raw_audio = silence + bytes(attenuated) + silence

    processed, start_idx, end_idx = S760DSPTools.auto_truncate_and_normalize(raw_audio, threshold_db=-40.0, peak_target=0.98)

    assert start_idx >= 990
    assert end_idx <= 6010
    proc_samples = [struct.unpack_from("<h", processed, i * 2)[0] for i in range(len(processed) // 2)]
    peak = max(abs(s) for s in proc_samples)
    # Peak should be normalized close to 98% of 32767 (~32111)
    assert peak >= 31500


def test_destructive_wave_editing_cut_splice_erase_mix():
    """OM Sec. 5.7: Test destructive wave operations: cut, splice, erase, mix."""
    pcm_a = generate_pcm_sine(freq=440.0, rate=44100, num_samples=10000)
    pcm_b = generate_pcm_sine(freq=880.0, rate=44100, num_samples=2000)

    # 1. Cut 2000 samples from index 3000
    cut_res = S760DSPTools.wave_edit(pcm_a, operation="cut", start=3000, length=2000)
    assert len(cut_res) // 2 == 8000

    # 2. Erase (silence) 1000 samples at index 1000
    erase_res = S760DSPTools.wave_edit(pcm_a, operation="erase", start=1000, length=1000)
    assert len(erase_res) == len(pcm_a)
    for i in range(1000, 2000):
        val = struct.unpack_from("<h", erase_res, i * 2)[0]
        assert val == 0

    # 3. Splice pcm_b into pcm_a at index 4000
    splice_res = S760DSPTools.wave_edit(pcm_a, pcm_b=pcm_b, operation="splice", start=4000)
    assert len(splice_res) // 2 == 12000

    # 4. Mix pcm_b into pcm_a
    mix_res = S760DSPTools.wave_edit(pcm_a, pcm_b=pcm_b, operation="mix")
    assert len(mix_res) == len(pcm_a)


def test_disk_optimization_and_defragmentation():
    """OM Sec. 6.6: Test disk optimization and allocation map defragmentation."""
    disk = RolandS760Disk(volume_name="OPT TEST")
    disk.add_patch(1, "Test Patch 1")
    disk.add_sample(1, "Sine 440", 44100, generate_pcm_sine(freq=440.0, num_samples=10000))
    raw_img = disk.build_image()

    opt_img = S760DiskOptimizer.optimize_disk(raw_img)
    assert len(opt_img) == len(raw_img)

    parsed = RolandS760Disk.parse(opt_img)
    assert parsed["is_roland"] is True
    assert parsed["volume_name"] == "OPT TEST"
    assert parsed["num_patches"] == 1


def test_msdos_fat12_floppy_formatting_and_wav_exchange():
    """OM Sec. 6.8: Test MS-DOS FAT12 floppy creation, WAV file embedding, and extraction."""
    orig_pcm = generate_pcm_sine(freq=440.0, rate=44100, num_samples=22050)
    dos_floppy = S760MSDOSExchange.build_msdos_sample_floppy("PIANO_C4.WAV", orig_pcm, sample_rate=44100)

    assert len(dos_floppy) == 1474560
    assert dos_floppy[510:512] == b"\x55\xAA"

    extracted = S760MSDOSExchange.extract_wav_from_msdos(dos_floppy)
    assert extracted["is_dos"] is True
    assert extracted["is_wav"] is True
    assert extracted["filename"] == "PIANO_C4.WAV"
    assert extracted["sample_rate"] == 44100
    assert extracted["pcm_data"] == orig_pcm


def test_midi_sample_dump_standard_sds_header_and_sysex():
    """OM Sec. 7.4: Test MIDI Sample Dump Standard (SDS) header generation and parsing."""
    header_sysex = S760MIDISampleDump.build_sds_dump_header(
        sample_num=1,
        sample_rate=44100,
        length=22050,
        loop_start=1000,
        loop_end=20000,
        channel=0
    )

    assert header_sysex[0] == 0xF0
    assert header_sysex[-1] == 0xF7
    assert header_sysex[1] == 0x7E # Universal Non-Realtime
    assert header_sysex[3] == 0x01 # Dump Header opcode

    parsed = S760MIDISampleDump.parse_sds_dump_header(header_sysex)
    assert parsed["valid_sds"] is True
    assert parsed["sample_num"] == 1
    assert parsed["bits"] == 16
    assert abs(parsed["sample_rate"] - 44100) < 50
    assert parsed["length"] == 22050
    assert parsed["loop_start"] == 1000
    assert parsed["loop_end"] == 20000
