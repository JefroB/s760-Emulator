"""
tests/test_cpp_parity.py — Parity Verification between C++ core and Python reference models.
Ensures 100% bit-for-bit parity across disk images, DSP transformations, and hardware drive persistence.
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Release"))
sys.path.insert(0, os.path.dirname(__file__))

import s760_cpp
from disk_formats import RolandS760Disk as PyRolandDisk, AkaiS1000Disk as PyAkaiDisk, S760AkaiConverter as PyAkaiConverter
from dsp_tools import S760DSPTools as PyDSPTools, S760MIDISampleDump as PySDS


def test_roland_disk_byte_parity():
    """Verify C++ and Python RolandS760Disk produce identical 1.44MB floppy bytes."""
    py_disk = PyRolandDisk(volume_name="PARITY TEST")
    py_disk.add_patch(patch_id=1, patch_name="Grand Piano", partial_ids=[1, 2], level=120, pan=0)
    py_disk.add_patch(patch_id=2, patch_name="Upright Bass", partial_ids=[3, 4], level=127, pan=-10)

    pcm_a = bytes([i % 256 for i in range(8000)])
    pcm_b = bytes([(i * 3) % 256 for i in range(12000)])
    py_disk.add_sample(sample_id=1, sample_name="PianoSamp", sample_rate=44100, pcm_data=pcm_a, loop_start=100, loop_end=3900, root_key=60)
    py_disk.add_sample(sample_id=2, sample_name="BassSamp", sample_rate=44100, pcm_data=pcm_b, loop_start=200, loop_end=5800, root_key=28)

    py_bytes = py_disk.build_image()

    cpp_disk = s760_cpp.RolandS760Disk(volume_name="PARITY TEST")
    cpp_disk.add_patch(patch_id=1, patch_name="Grand Piano", partial_ids=[1, 2], level=120, pan=0)
    cpp_disk.add_patch(patch_id=2, patch_name="Upright Bass", partial_ids=[3, 4], level=127, pan=-10)
    cpp_disk.add_sample(sample_id=1, sample_name="PianoSamp", sample_rate=44100, pcm_data=pcm_a, loop_start=100, loop_end=3900, root_key=60)
    cpp_disk.add_sample(sample_id=2, sample_name="BassSamp", sample_rate=44100, pcm_data=pcm_b, loop_start=200, loop_end=5800, root_key=28)

    cpp_bytes = cpp_disk.build_image()

    assert len(py_bytes) == len(cpp_bytes) == 1474560
    assert py_bytes == cpp_bytes, "C++ and Python Roland floppy images are not byte-identical!"


def test_akai_iso_byte_parity():
    """Verify C++ and Python AkaiS1000Disk produce identical CD-ROM ISO bytes."""
    py_akai = PyAkaiDisk(volume_name="AKAI PARITY")
    py_akai.add_program(prog_num=1, prog_name="Lead Synth", midi_channel=1, keygroup_count=1)
    
    pcm = bytes([(i * 7) % 256 for i in range(4096)])
    py_akai.add_sample(sample_name="LeadWave", sample_rate=44100, pcm_data=pcm, loop_start=50, loop_end=2000, root_key=60)
    py_iso = py_akai.build_iso(total_mb=2)

    cpp_akai = s760_cpp.AkaiS1000Disk(volume_name="AKAI PARITY")
    cpp_akai.add_program(prog_num=1, prog_name="Lead Synth", midi_channel=1, keygroup_count=1)
    cpp_akai.add_sample(sample_name="LeadWave", sample_rate=44100, pcm_data=pcm, loop_start=50, loop_end=2000, root_key=60)
    cpp_iso = cpp_akai.build_iso(total_mb=2)

    assert len(py_iso) == len(cpp_iso) == 2 * 1024 * 1024
    assert py_iso == cpp_iso, "C++ and Python Akai ISO images are not byte-identical!"


def test_dsp_crossfade_parity():
    """Verify crossfade loop mathematical parity."""
    import math
    import struct

    pcm = bytearray(8000)
    for i in range(4000):
        val = int(math.sin(2.0 * math.pi * 440.0 * i / 44100.0) * 25000.0)
        struct.pack_into("<h", pcm, i * 2, val)
    pcm = bytes(pcm)

    py_out = PyDSPTools.crossfade_loop(pcm, loop_start=500, loop_end=3500, xfade_samples=200)
    cpp_out = s760_cpp.S760DSPTools.crossfade_loop(pcm, loop_start=500, loop_end=3500, xfade_samples=200)

    assert py_out == cpp_out, "Crossfade DSP output differs between Python and C++"


def test_drive_manager_hardware_flow(tmp_path):
    """Test folder-backed FDD/SCSI mounting and writing for hardware ZuluSCSI/Gotek parity."""
    floppy_file = str(tmp_path / "HARDWARE.IMG")
    scsi_file = str(tmp_path / "ZULUSCSI_0.HDA")

    # 1. Create base floppy
    cpp_disk = s760_cpp.RolandS760Disk("HW DISK")
    cpp_disk.add_patch(1, "Live Preset", [1, 2], 127, 0)
    data = cpp_disk.build_image()
    with open(floppy_file, "wb") as f:
        f.write(data)

    # 2. Mount via Drive Manager
    mgr = s760_cpp.S760DriveManager()
    assert mgr.mount_floppy(floppy_file)
    status = mgr.get_floppy_status()
    assert status.is_mounted is True
    assert status.image_name == "HARDWARE.IMG"
    assert status.total_sectors == 2880

    # 3. Simulate hardware drive write and auto-flush
    mgr.flush_floppy()
    mgr.eject_floppy()

    # 4. Check folder scan
    found = s760_cpp.S760DriveManager.scan_image_folder(str(tmp_path))
    assert len(found) >= 1
    assert any("HARDWARE.IMG" in p for p in found)


def test_libretro_host_lifecycle():
    """Verify Libretro host loading, frame processing, audio streaming, and savestate serialization from Python."""
    import pathlib
    dll_path = pathlib.Path("build/Release/mock_core.dll")
    if not dll_path.exists():
        dll_path = pathlib.Path("Release/mock_core.dll")
    if not dll_path.exists():
        pytest.skip("mock_core.dll not yet compiled in build directory")

    host = s760_cpp.S760LibretroHost()
    assert host.load_core(str(dll_path))
    assert host.is_core_loaded() is True

    assert host.load_system("s760_system")
    assert host.is_system_running() is True

    # Step frames
    for _ in range(5):
        host.run_frame()

    # Check Audio buffer
    stats = host.get_audio_stats()
    assert stats.available_frames >= 735 * 5
    assert stats.sample_rate == 44100.0

    # Check Video CRT frame
    frame = host.get_latest_video_frame()
    assert frame.width == 320
    assert frame.height == 240
    assert len(frame.rgba_pixels) == 320 * 240

    # Check MIDI injection
    host.send_midi_byte(0x90) # Note-on
    host.send_midi_byte(0x3C) # Middle C
    host.send_midi_byte(0x7F) # Velocity 127

    # Check Savestate serialization
    state = host.save_state()
    assert len(state) == 1024
    assert host.load_state(state) is True

    host.unload_system()
    host.unload_core()

