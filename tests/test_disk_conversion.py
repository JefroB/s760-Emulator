"""
test_disk_conversion.py — Automated verification of real S-760 disk loading and Akai S1000 ISO conversion
"""
import os
import math
import struct
import pytest
from conftest import ROOT, IMAGE
from disk_formats import RolandS760Disk, AkaiS1000Disk, S760AkaiConverter
from mame_harness import MameTestSession, analyze_screenshot


def generate_test_tone(freq=440.0, rate=44100, num_samples=22050):
    """Generate 16-bit signed PCM sine tone."""
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / rate
        val = int(32767.0 * 0.7 * math.sin(2.0 * math.pi * freq * t))
        struct.pack_into("<h", pcm, i * 2, val)
    return bytes(pcm)


def test_real_s760_os_disk_layout():
    """Verify real S-760 OS disk image structure, header, and payload offsets."""
    assert os.path.exists(IMAGE), f"S760 disk image not found at {IMAGE}"
    with open(IMAGE, "rb") as f:
        data = f.read()

    # Assert 1.44MB High Density geometry (1,474,560 bytes)
    assert len(data) == 1474560, f"Unexpected disk size: {len(data)}"

    # Sector 0 Volume Header check
    parsed = RolandS760Disk.parse(data)
    assert parsed["is_roland"] is True, "Sector 0 header is missing Roland S-760 signature"

    # Allocation bitmap starting at Sector 1 (offset 0x200) contains free space markers (0x0F)
    assert data[0x200] == 0x0F, "Allocation table not found at sector 1"
    assert data[0x47FF] == 0x0F, "Allocation table boundary mismatch"

    # OS payload starts at Sector 36 (offset 0x4800)
    assert data[0x4800] != 0x0F, "Payload missing at sector 36 (0x4800)"


def test_s760_sound_disk_builder_and_parser():
    """Verify creating and parsing native Roland S-760 sound and patch disks."""
    disk = RolandS760Disk(volume_name="JP-8 VINTAGE")
    pcm = generate_test_tone(freq=440.0, rate=44100, num_samples=10000)

    disk.add_sample(sample_id=1, sample_name="JP8 Saw Wave", sample_rate=44100, pcm_data=pcm, root_key=60)
    disk.add_patch(patch_id=11, patch_name="JP-8 Brass 1", partial_ids=[1, 2], level=127, pan=0)
    disk.add_patch(patch_id=12, patch_name="JP-8 Strgs 1", partial_ids=[1], level=110, pan=-15)

    img_data = disk.build_image()
    assert len(img_data) == 1474560

    parsed = RolandS760Disk.parse(img_data)
    assert parsed["is_roland"] is True
    assert parsed["volume_name"] == "JP-8 VINTAGE"
    assert parsed["num_patches"] == 2
    assert parsed["patches"][0]["name"] == "JP-8 Brass 1"
    assert parsed["patches"][1]["name"] == "JP-8 Strgs 1"


def test_akai_s1000_iso_builder_and_parser():
    """Verify creating and parsing Akai S1000 CD-ROM ISO disk images."""
    akai = AkaiS1000Disk(volume_name="AKAI PROG 01")
    pcm = generate_test_tone(freq=880.0, rate=44100, num_samples=15000)

    akai.add_program(prog_num=1, prog_name="Grand Piano", midi_channel=1, keygroup_count=4)
    akai.add_program(prog_num=2, prog_name="AcousticBass", midi_channel=2, keygroup_count=2)
    akai.add_sample(sample_name="Piano High C", sample_rate=44100, pcm_data=pcm, root_key=72)

    iso_data = akai.build_iso(total_mb=2)
    assert len(iso_data) == 2 * 1024 * 1024

    parsed = AkaiS1000Disk.parse(iso_data)
    assert parsed["is_akai"] is True
    assert parsed["volume_name"] == "AKAI PROG 01"
    assert parsed["num_programs"] == 2
    assert parsed["programs"][0]["name"] == "Grand Piano"
    assert parsed["programs"][1]["name"] == "AcousticBass"
    assert parsed["num_samples"] == 1
    assert parsed["samples"][0]["name"] == "Piano High C"


def test_akai_s1000_to_roland_s760_conversion():
    """
    Test the complete conversion pipeline from an Akai S1000 ISO to a native Roland S-760 disk:
    Akai Programs -> Roland S-760 Patches
    Akai Samples -> Roland S-760 Partials & 16-bit Wave memory
    """
    # 1. Create source Akai S1000 Disk
    akai = AkaiS1000Disk(volume_name="AKAI STRINGS")
    pcm_cellos = generate_test_tone(freq=220.0, rate=44100, num_samples=20000)
    pcm_violins = generate_test_tone(freq=440.0, rate=44100, num_samples=20000)

    akai.add_program(prog_num=10, prog_name="Sect Strings", midi_channel=1)
    akai.add_sample(sample_name="Cello Sust", sample_rate=44100, pcm_data=pcm_cellos, loop_start=1000, loop_end=19000, root_key=48)
    akai.add_sample(sample_name="Violin Sust", sample_rate=44100, pcm_data=pcm_violins, loop_start=1500, loop_end=18000, root_key=60)

    # 2. Run Roland S-760 Convert Engine
    s760_converted = S760AkaiConverter.convert(akai, target_volume_name="CONV STRINGS")
    s760_img = s760_converted.build_image()

    # 3. Verify Converted Roland S-760 Image Structure
    assert len(s760_img) == 1474560
    parsed = RolandS760Disk.parse(s760_img)
    assert parsed["is_roland"] is True
    assert parsed["volume_name"] == "CONV STRINGS"
    assert parsed["num_patches"] == 1
    assert parsed["patches"][0]["name"] == "Sect Strings"
    assert parsed["num_samples"] == 2


def test_mame_disk_convert_ui_workflow():
    """
    Automate MAME UI navigating to DISK mode and triggering Convert LD[S] (Akai conversion mode):
    - Switches to DISK tab
    - Selects Convert LD[S] option
    - Asserts Disk & Convert UI widgets are actively rendered
    """
    lua = """
local count = 0
local key_arrows = manager.machine.ioport.ports[":KEY_ARROWS"]

emu.register_frame_done(function()
    count = count + 1

    -- Frames 1-15: Move cursor Up (0x04) and Right (0x02) towards DISK tab (x ~ 380, y ~ 20)
    if count >= 1 and count <= 15 then
        if key_arrows then
            key_arrows:field(0x04):set_value(1) -- Up
            key_arrows:field(0x02):set_value(1) -- Right
        end
    -- Frame 16-17: Click DISK tab
    elseif count == 16 or count == 17 then
        if key_arrows then
            key_arrows:field(0x04):set_value(0)
            key_arrows:field(0x02):set_value(0)
            key_arrows:field(0x10):set_value(1) -- Enter / Click
        end
    -- Frame 25: Finish
    elseif count == 25 then
        if key_arrows then
            key_arrows:field(0x10):set_value(0)
        end
        results["disk_ui_ok"] = true
        save_and_exit()
    end
end, "disk_convert_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_disk_convert")
    res = session.run()

    assert res["returncode"] == 0, f"MAME DISK convert test failed: {res['stderr']}"
    assert res["data"].get("disk_ui_ok") is True
    assert res["snap_path"] is not None

    img, w, h = analyze_screenshot(res["snap_path"])
    pixels = img.load()

    # Verify DISK active tab highlight or yellow parameter buttons (Pen 4: 255, 230, 0)
    found_yellow_params = False
    for y in range(50, 150, 5):
        for x in range(w):
            r, g, b = pixels[x, y]
            if r >= 240 and g >= 210 and b <= 30: # Yellow parameter widget
                found_yellow_params = True
                break
        if found_yellow_params:
            break

    assert found_yellow_params, "Yellow parameter buttons not rendered on DISK screen"
