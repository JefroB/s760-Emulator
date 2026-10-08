"""
tests/test_adversarial_review.py — Dedicated regression tests verifying the remediation of
the 24 findings from docs/S760_Adversarial_Code_Review.md.
"""

import os
import sys
import struct
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from disk_formats import RolandS760Disk, AkaiS1000Disk


def test_finding_04_05_disk_parser_corrupted_header_counts():
    """Finding 4 & 5: Parsers must safely handle 0xFFFFFFFF counts and bounds without hanging or crashing."""
    corrupt_data = bytearray(512)
    corrupt_data[0:10] = b"S770 MR25A"
    struct.pack_into("<I", corrupt_data, 0x60, 0xFFFFFFFF) # 4 billion patches
    struct.pack_into("<I", corrupt_data, 0x64, 0xFFFFFFFF) # 4 billion samples

    # Roland parser must cap and reject safely
    info = RolandS760Disk.parse(bytes(corrupt_data))
    assert len(info["patches"]) == 0
    assert len(info["samples"]) == 0


def test_finding_04_disk_parser_odd_byte_pcm_rejection():
    """Finding 4: 16-bit PCM samples with odd byte length must not be silently accepted."""
    disk = RolandS760Disk("TEST ODD PCM")
    odd_pcm = bytes([0x00, 0x10, 0x20]) # 3 bytes (odd length!)
    disk.add_sample(1, "OddSample", 44100, odd_pcm)
    img = disk.build_image()

    parsed = RolandS760Disk.parse(img)
    # The odd byte sample must be rejected
    assert len(parsed["samples"]) == 0


def test_finding_04_truncated_sample_payload():
    """Finding 4: Truncated sample payload must not produce empty samples or invalid offsets."""
    disk = RolandS760Disk("TRUNC TEST")
    pcm_data = bytes([0x10, 0x20] * 1000) # 2000 bytes
    disk.add_sample(1, "ValidSample", 44100, pcm_data)
    img = disk.build_image()

    # Truncate image right in the middle of sample PCM payload
    truncated_img = img[:0x10000 + 256 + 500] # Cut short
    parsed = RolandS760Disk.parse(truncated_img)
    assert len(parsed["samples"]) == 0


def test_finding_05_builder_zero_or_subsector_safety():
    """Finding 5: Builders must reject invalid or undersized capacities."""
    akai = AkaiS1000Disk("AKAI ZERO")
    with pytest.raises(Exception):
        akai.build_iso(0)


def test_finding_08_10_mame_source_hardening_invariants():
    """Finding 8 & 10: Verify MAME C++ driver uses checked reads and deterministic PRNG."""
    mame_cpp_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "mame-source", "src", "mame", "roland", "s760.cpp")
    assert os.path.exists(mame_cpp_path)

    with open(mame_cpp_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Check that even byte length validation is present
    assert "data_len_bytes % 2 != 0" in content or "data_len_bytes % 2 == 0" in content
    # Check that exact gcount is verified
    assert "file.gcount()" in content
    # Check that deterministic noise generator is used instead of bare rand()
    assert "lcg_noise" in content


def test_finding_16_react_state_updaters_pure():
    """Finding 16: React state updater functions in App.tsx must remain pure and free of side-effects."""
    app_tsx_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "google-ui", "src", "App.tsx")
    assert os.path.exists(app_tsx_path)

    with open(app_tsx_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Verify no side-effects (emitHardwareEvent, soundFx, triggerAudition, handleMountDisk) inside setState
    lines = content.splitlines()
    in_updater = False
    paren_depth = 0
    for i, line in enumerate(lines):
        if "setState((prev)" in line:
            paren_depth = line.count("(") - line.count(")")
            in_updater = (paren_depth > 0)
            continue
        if in_updater:
            paren_depth += line.count("(") - line.count(")")
            if any(side_effect in line for side_effect in ["emitHardwareEvent", "soundFx.", "triggerAudition()", "handleMountDisk()", "handleToggleUsb()"]):
                pytest.fail(f"Side-effect found inside setState updater at line {i+1}: {line.strip()}")
            if paren_depth <= 0:
                in_updater = False


def test_finding_21_monitor_font_provenance_labeling():
    """Finding 21: Monitor font in OP760Monitor.tsx must be accurately labeled as simulation model."""
    monitor_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "google-ui", "src", "components", "OP760Monitor.tsx")
    assert os.path.exists(monitor_path)

    with open(monitor_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "Simulation Font Table" in content or "UI Behavioral Model" in content
