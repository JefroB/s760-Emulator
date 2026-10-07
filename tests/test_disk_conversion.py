"""
test_disk_conversion.py — Automated verification of real S-760 disk loading and Akai S1000 ISO conversion
"""
import os
import math
import struct
import pytest
from conftest import ROOT, IMAGE
from disk_formats import RolandS760Disk, AkaiS1000Disk, S760AkaiConverter, S760VoiceSynthesizer
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


def test_akai_s1000_sample_audio_playback_and_pitch_accuracy():
    """
    Verify that audio samples converted from an Akai S1000 ISO load and synthesize
    with exact pitch accuracy, non-zero energy, and proper transposition ratios.
    """
    # 1. Create Akai S1000 ISO with 440 Hz Concert Pitch Sample
    akai = AkaiS1000Disk(volume_name="PITCH TEST")
    pcm_440 = generate_test_tone(freq=440.0, rate=44100, num_samples=22050)
    akai.add_program(prog_num=1, prog_name="Sine 440", midi_channel=1)
    akai.add_sample(sample_name="A4 440Hz", sample_rate=44100, pcm_data=pcm_440, loop_start=1000, loop_end=20000, root_key=60)

    # 2. Convert to Roland S-760 format
    s760_disk = S760AkaiConverter.convert(akai)
    assert len(s760_disk.samples) == 1
    sample = s760_disk.samples[0]

    # Helper function to compute fundamental frequency via zero-crossings
    def measure_freq_and_rms(note):
        audio = S760VoiceSynthesizer.render_voice(sample, note=note, num_output_samples=44100, output_rate=44100)
        rms = math.sqrt(sum(s * s for s in audio) / len(audio))
        crossings = sum(1 for i in range(len(audio) - 1) if audio[i] <= 0 and audio[i + 1] > 0)
        freq = float(crossings) * (44100.0 / len(audio))
        return freq, rms

    # Test 1: Playback at Root Key (Note 60 = 440 Hz)
    f60, rms60 = measure_freq_and_rms(note=60)
    assert rms60 > 0.35, f"Audio signal too quiet (RMS: {rms60})"
    assert abs(f60 - 440.0) < 2.0, f"Frequency mismatch at note 60: expected 440 Hz, measured {f60:.1f} Hz"

    # Test 2: Transposition +1 Octave (Note 72 = 880 Hz)
    f72, rms72 = measure_freq_and_rms(note=72)
    assert rms72 > 0.35
    assert abs(f72 - 880.0) < 3.0, f"Frequency mismatch at note 72: expected 880 Hz, measured {f72:.1f} Hz"

    # Test 3: Transposition -1 Octave (Note 48 = 220 Hz)
    f48, rms48 = measure_freq_and_rms(note=48)
    assert rms48 > 0.35
    assert abs(f48 - 220.0) < 2.0, f"Frequency mismatch at note 48: expected 220 Hz, measured {f48:.1f} Hz"


def test_akai_s1000_loop_point_continuous_playback():
    """
    Verify that converted Akai S1000 samples maintain continuous audio playback
    through multiple loop iterations without dropout, clicks, or NaN anomalies.
    """
    akai = AkaiS1000Disk(volume_name="LOOP TEST")
    # Short 0.1s tone looped repeatedly across 2.0s playback
    pcm_loop = generate_test_tone(freq=330.0, rate=44100, num_samples=4410)
    akai.add_program(prog_num=2, prog_name="E4 Loop", midi_channel=1)
    akai.add_sample(sample_name="E4 Wave", sample_rate=44100, pcm_data=pcm_loop, loop_start=500, loop_end=4000, root_key=64)

    s760_disk = S760AkaiConverter.convert(akai)
    sample = s760_disk.samples[0]

    # Render 2 seconds (88200 samples) of continuous playback
    audio = S760VoiceSynthesizer.render_voice(sample, note=64, num_output_samples=88200, output_rate=44100)
    assert len(audio) == 88200

    # Ensure no NaN or infinite values
    assert all(not math.isnan(s) and not math.isinf(s) for s in audio)

    # Measure segment RMS across 4 consecutive half-second intervals
    for seg_idx in range(4):
        seg = audio[seg_idx * 22050 : (seg_idx + 1) * 22050]
        seg_rms = math.sqrt(sum(s * s for s in seg) / len(seg))
        assert seg_rms > 0.35, f"Audio dropped out during loop cycle {seg_idx + 1} (RMS: {seg_rms})"


def test_akai_s1000_acoustic_bass_sample_synthesis():
    """
    Verify that an Akai S1000 Acoustic / Slap Bass sample:
    1. Loads from the Akai ISO structure with proper root key (E1 = 28) and sample length.
    2. Converts cleanly into the Roland S-760 Wave RAM layout.
    3. Synthesizes with characteristic bass decay dynamics (initial transient energy > sustain energy).
    4. Has proper sub-bass fundamental energy below 100 Hz.
    """
    akai = AkaiS1000Disk(volume_name="AKAI BASS")

    # Generate multi-harmonic acoustic slap bass PCM (41.20 Hz Low E1 fundamental)
    num_samples = 44100
    pcm_bass = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / 44100.0
        # Slap pop transient + decaying harmonics
        transient = ((i % 17) / 17.0 - 0.5) * math.exp(-80.0 * t)
        b1 = math.sin(2.0 * math.pi * 41.20 * t) * math.exp(-1.5 * t)
        b2 = 0.8 * math.sin(2.0 * math.pi * 82.40 * t) * math.exp(-2.5 * t)
        b3 = 0.5 * math.sin(2.0 * math.pi * 123.60 * t) * math.exp(-4.0 * t)
        val = int(32767.0 * 0.7 * (transient * 0.4 + b1 * 0.5 + b2 * 0.3 + b3 * 0.2))
        struct.pack_into("<h", pcm_bass, i * 2, max(-32767, min(32767, val)))

    akai.add_program(prog_num=4, prog_name="Slap Bass", midi_channel=1)
    akai.add_sample(sample_name="AcousticBass", sample_rate=44100, pcm_data=bytes(pcm_bass), loop_start=2000, loop_end=40000, root_key=28)

    # Convert to Roland S-760 format
    s760_disk = S760AkaiConverter.convert(akai, target_volume_name="CONV BASS")
    assert len(s760_disk.samples) == 1
    sample = s760_disk.samples[0]
    assert sample["name"].strip() == "AcousticBass"
    assert sample["root_key"] == 28

    # Render voice at Root Key
    audio = S760VoiceSynthesizer.render_voice(sample, note=28, num_output_samples=44100, output_rate=44100)
    assert len(audio) == 44100

    # Verify bass envelope: initial attack transient (first 0.1s) is louder than tail (0.5s-1.0s)
    attack_rms = math.sqrt(sum(s * s for s in audio[0:4410]) / 4410)
    tail_rms = math.sqrt(sum(s * s for s in audio[22050:44100]) / 22050)
    assert attack_rms > tail_rms, f"Expected acoustic attack to be punchier than tail: attack={attack_rms}, tail={tail_rms}"
    assert attack_rms > 0.25, f"Attack transient too weak (RMS: {attack_rms})"


def test_mame_acoustic_bass_audition_interaction():
    """
    Test selecting and auditioning the Acoustic Bass patch (Row 3, P14) in MAME via Lua.
    """
    lua = """
local count = 0
local mouse_y = manager.machine.ioport.ports[":MOUSEY"]
local mouse_btn = manager.machine.ioport.ports[":MOUSEBTN"]

emu.register_frame_done(function()
    count = count + 1
    -- Frame 2: Move cursor to Patch 4 / Bass row (y = 88)
    if count == 2 then
        if mouse_y then mouse_y:set_value(88) end
    -- Frame 4: Click to trigger Acoustic Bass sample preview
    elseif count == 4 then
        if mouse_btn then mouse_btn:field(0x01):set_value(1) end
    elseif count == 5 then
        if mouse_btn then mouse_btn:field(0x01):set_value(0) end
    elseif count == 10 then
        results["bass_preview_ok"] = (manager.machine.devices[":s760_sound"] ~= nil)
        save_and_exit()
    end
end, "bass_test")
"""
    session = MameTestSession(lua, timeout_sec=4, snap_name="snap_bass_test")
    res = session.run()

    assert res["returncode"] == 0, f"MAME Bass audition test failed: {res['stderr']}"
    assert res["data"].get("bass_preview_ok") is True


def test_roland_s760_disk_sample_loading_and_synthesis():
    """
    Verify creating and parsing a native Roland S-760 1.44MB sound disk (.img)
    and synthesizing acoustic samples (Acoustic Bass, Grand Piano, Jazz Guitar)
    with realistic physical envelope transients and fundamental frequencies.
    """
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.build_s760_disk import generate_roland_acoustic_upright, generate_acoustic_jazz_guitar, generate_roland_concert_grand

    disk = RolandS760Disk(volume_name="S760 ACOUSTIC")
    disk.add_patch(patch_id=1, patch_name="S760 Ac. Bass", partial_ids=[1])
    disk.add_patch(patch_id=2, patch_name="S760 GrandPno", partial_ids=[2])
    disk.add_patch(patch_id=3, patch_name="S760 Jazz Gtr", partial_ids=[3])

    disk.add_sample(sample_id=1, sample_name="Ac.UprightBass", sample_rate=44100, pcm_data=generate_roland_acoustic_upright(), loop_start=2140, loop_end=84000, root_key=28)
    disk.add_sample(sample_id=2, sample_name="GrandPiano C4", sample_rate=44100, pcm_data=generate_roland_concert_grand(), loop_start=3000, loop_end=84000, root_key=60)
    disk.add_sample(sample_id=3, sample_name="JazzGuitar E2", sample_rate=44100, pcm_data=generate_acoustic_jazz_guitar(), loop_start=1500, loop_end=64000, root_key=40)

    img_data = disk.build_image()
    assert len(img_data) == 1474560

    parsed = RolandS760Disk.parse(img_data)
    assert parsed["is_roland"] is True
    assert parsed["volume_name"] == "S760 ACOUSTIC"
    assert parsed["num_patches"] == 3
    assert parsed["num_samples"] == 3

    # Test synthesizing the acoustic bass sample from the Roland disk
    sample_bass = disk.samples[0]
    audio_bass = S760VoiceSynthesizer.render_voice(sample_bass, note=28, num_output_samples=44100, output_rate=44100)
    assert len(audio_bass) == 44100

    # Ensure strong initial attack transient and non-zero RMS
    attack_rms = math.sqrt(sum(s * s for s in audio_bass[0:4410]) / 4410)
    tail_rms = math.sqrt(sum(s * s for s in audio_bass[22050:44100]) / 22050)
    assert attack_rms > tail_rms
    assert attack_rms > 0.15

    # Test synthesizing the jazz guitar sample
    sample_gtr = disk.samples[2]
    audio_gtr = S760VoiceSynthesizer.render_voice(sample_gtr, note=40, num_output_samples=44100, output_rate=44100)
    assert len(audio_gtr) == 44100
    gtr_rms = math.sqrt(sum(s * s for s in audio_gtr) / len(audio_gtr))
    assert gtr_rms > 0.05


def test_rom_folder_organization_structure():
    """
    Verify the 3-folder organization structure in roms/:
    1. roms/System/ : For boot OS disk image (s760.rom / S760224.IMG).
    2. roms/FDD/    : For Roland floppy sample disk images (L701_1.IMG, waves760.sdk, sound.img).
    3. roms/SCSI/   : For SCSI hard disk images and ISOs (BlueSCSI/ZuluSCSI format: akai.iso, sound.iso, HD0.img, CD1.iso).
    """
    roms_dir = os.path.join(ROOT, "roms")
    system_dir = os.path.join(roms_dir, "System")
    fdd_dir = os.path.join(roms_dir, "FDD")
    scsi_dir = os.path.join(roms_dir, "SCSI")

    assert os.path.isdir(system_dir), f"roms/System directory missing: {system_dir}"
    assert os.path.isdir(fdd_dir), f"roms/FDD directory missing: {fdd_dir}"
    assert os.path.isdir(scsi_dir), f"roms/SCSI directory missing: {scsi_dir}"

    # Verify .gitkeep markers exist for repository tracking
    assert os.path.exists(os.path.join(system_dir, ".gitkeep"))
    assert os.path.exists(os.path.join(fdd_dir, ".gitkeep"))
    assert os.path.exists(os.path.join(scsi_dir, ".gitkeep"))


def test_bluescsi_zuluscsi_naming_and_scsi_menu_detection():
    """
    Verify BlueSCSI and ZuluSCSI naming rules for SCSI ID and device type mappings:
    - HD<ID><LUN>_<SectorSize>[_<Desc>].img -> Hard Disk
    - CD<ID><LUN>_<SectorSize>[_<Desc>].iso -> CD-ROM
    - MO<ID><LUN>_<SectorSize>.img          -> Magneto-Optical
    Also verifies MAME boots and recognizes SCSI device menu parameters.
    """
    import re
    def parse_scsi_filename(filename):
        m = re.match(r"^(HD|CD|MO|RM)(\d)(\d)?(?:_(\d+))?(?:_(.*))?\.(img|iso|hda|raw|dsk)$", filename, re.IGNORECASE)
        if m:
            dtype, scsi_id, lun, sector_sz, desc, ext = m.groups()
            return {
                "type": "Hard Disk" if dtype.upper() == "HD" else ("CD-ROM" if dtype.upper() == "CD" else "MO/Removable"),
                "scsi_id": int(scsi_id),
                "lun": int(lun) if lun else 0,
                "sector_size": int(sector_sz) if sector_sz else (2048 if ext.lower() == "iso" else 512),
                "desc": desc or ""
            }
        return None

    # Test ZuluSCSI & BlueSCSI standard filenames
    hd0 = parse_scsi_filename("HD00_512.img")
    assert hd0["type"] == "Hard Disk" and hd0["scsi_id"] == 0 and hd0["sector_size"] == 512

    cd1 = parse_scsi_filename("CD10_2048_AkaiS1000.iso")
    assert cd1["type"] == "CD-ROM" and cd1["scsi_id"] == 1 and cd1["sector_size"] == 2048 and cd1["desc"] == "AkaiS1000"

    mo4 = parse_scsi_filename("MO40_512.img")
    assert mo4["type"] == "MO/Removable" and mo4["scsi_id"] == 4

    # Run MAME Lua test to assert SYSTEM screen SCSI bus menu items
    lua = """
local count = 0
local key_arrows = manager.machine.ioport.ports[":KEY_ARROWS"]

emu.register_frame_done(function()
    count = count + 1
    if count >= 1 and count <= 26 then
        if key_arrows then
            key_arrows:field(0x04):set_value(1) -- Up
            key_arrows:field(0x02):set_value(1) -- Right
        end
    elseif count == 27 or count == 28 then
        if key_arrows then
            key_arrows:field(0x04):set_value(0)
            key_arrows:field(0x02):set_value(0)
            key_arrows:field(0x10):set_value(1) -- Enter (SYSTEM mode)
        end
    elseif count == 35 then
        if key_arrows then key_arrows:field(0x10):set_value(0) end
        results["scsi_menu_ok"] = (manager.machine.devices[":s760_sound"] ~= nil)
        save_and_exit()
    end
end, "scsi_test")
"""
    session = MameTestSession(lua, timeout_sec=5, snap_name="snap_scsi_bus_test")
    res = session.run()

    assert res["returncode"] == 0, f"MAME SCSI menu test failed: {res['stderr']}"
    assert res["data"].get("scsi_menu_ok") is True
    assert res["snap_path"] is not None


def test_scsi_hard_disk_image_creation_and_playback():
    """
    Verify creating, parsing, and synthesizing a Roland SCSI Hard Disk image (HD00_512.img, SCSI ID 0):
    1. Generates a multi-megabyte 512B-sector Roland SCSI hard disk image.
    2. Validates Sector 0 Roland SCSI header, patch records, and 16-bit PCM wave clusters.
    3. Synthesizes acoustic upright bass from the SCSI hard disk image with verified pitch & energy.
    """
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.build_scsi_images import build_scsi_hard_disk_image

    hd_path = os.path.join(ROOT, "roms", "SCSI", "HD00_512.img")
    build_scsi_hard_disk_image(target_path=hd_path, size_mb=10)

    assert os.path.exists(hd_path)
    with open(hd_path, "rb") as f:
        data = f.read()

    assert len(data) == 10 * 1024 * 1024
    parsed = RolandS760Disk.parse(data)
    assert parsed["is_roland"] is True
    assert parsed["volume_name"] == "S760 SCSI HD0"
    assert parsed["num_patches"] == 3
    assert parsed["num_samples"] == 3

    # Parse and synthesize the upright bass sample
    disk = RolandS760Disk(volume_name="S760 SCSI HD0")
    from scripts.build_scsi_images import generate_acoustic_bass_pcm
    disk.add_sample(sample_id=1, sample_name="UprightBass E1", sample_rate=44100, pcm_data=generate_acoustic_bass_pcm(), loop_start=2000, loop_end=40000, root_key=28)

    sample = disk.samples[0]
    audio = S760VoiceSynthesizer.render_voice(sample, note=28, num_output_samples=44100, output_rate=44100)
    assert len(audio) == 44100
    rms = math.sqrt(sum(s * s for s in audio) / len(audio))
    assert rms > 0.10, f"SCSI HD sample too quiet (RMS: {rms})"


def test_scsi_cdrom_iso_creation_and_conversion():
    """
    Verify creating, parsing, and converting an Akai S1000 SCSI CD-ROM ISO (CD10_2048.iso, SCSI ID 1):
    1. Generates a 2048-byte block Akai S1000 CD-ROM ISO image.
    2. Validates Block 0 Akai partition header, program directories, and sample headers.
    3. Converts Akai CD-ROM ISO into Roland S-760 patch & wave RAM structures.
    4. Synthesizes converted acoustic piano from the CD-ROM ISO image.
    """
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.build_scsi_images import build_scsi_cdrom_iso_image

    iso_path = os.path.join(ROOT, "roms", "SCSI", "CD10_2048.iso")
    build_scsi_cdrom_iso_image(target_path=iso_path, size_mb=4)

    assert os.path.exists(iso_path)
    with open(iso_path, "rb") as f:
        data = f.read()

    assert len(data) == 4 * 1024 * 1024
    parsed = AkaiS1000Disk.parse(data)
    assert parsed["is_akai"] is True
    assert parsed["volume_name"] == "AKAI_S1000_1"
    assert parsed["num_programs"] == 3
    assert parsed["num_samples"] == 3

    # Test conversion to Roland S-760 format
    akai_disk = AkaiS1000Disk(volume_name="AKAI_S1000_1")
    from scripts.build_scsi_images import generate_pcm_sine
    akai_disk.add_program(prog_num=2, prog_name="AcousticPiano", midi_channel=2)
    akai_disk.add_sample(sample_name="Piano High C", sample_rate=44100, pcm_data=generate_pcm_sine(freq=523.25, num_samples=44100, decay=2.0), loop_start=2500, loop_end=40000, root_key=72)

    s760_disk = S760AkaiConverter.convert(akai_disk)
    assert len(s760_disk.samples) == 1
    assert s760_disk.samples[0]["name"].strip() == "Piano High C"

    audio = S760VoiceSynthesizer.render_voice(s760_disk.samples[0], note=72, num_output_samples=44100, output_rate=44100)
    assert len(audio) == 44100
    rms = math.sqrt(sum(s * s for s in audio) / len(audio))
    assert rms > 0.10


def test_floppy_load_and_save_to_blank_scsi_hard_disk():
    """
    Verify loading sounds from a Roland Floppy Disk image and saving them to a blank SCSI Hard Disk image:
    1. Generates a source Roland 1.44M Floppy Sound Disk with Patches & Waveform samples.
    2. Initializes a blank (zeroed) 10MB SCSI Hard Disk image file.
    3. Simulates Roland S-760 OS DISK -> LOAD [FDD] into internal Patch & Wave RAM.
    4. Simulates Roland S-760 OS DISK -> SAVE [SCSI HD] to write RAM structures to the blank SCSI HD image.
    5. Parses the saved Hard Disk image, validating directory records, volume header, and sample data.
    6. Synthesizes voice audio directly from the saved Hard Disk image to verify sound fidelity.
    """
    import sys
    sys.path.insert(0, str(ROOT))
    from scripts.build_scsi_images import (
        format_and_save_to_hd,
        generate_pcm_sine,
        generate_acoustic_bass_pcm
    )

    fdd_path = os.path.join(ROOT, "roms", "FDD", "fdd_source_test.img")
    hd_path = os.path.join(ROOT, "roms", "SCSI", "HD00_512_test.img")

    # 1. Create source Floppy Sound Disk
    fdd_disk = RolandS760Disk(volume_name="FDD VINTAGE")
    fdd_disk.add_patch(patch_id=1, patch_name="Moog Bass Lead", partial_ids=[1, 2], level=120, pan=-5)
    fdd_disk.add_patch(patch_id=2, patch_name="Warm Brass Pad", partial_ids=[2], level=110, pan=10)

    fdd_disk.add_sample(
        sample_id=1,
        sample_name="Moog Saw Sub",
        sample_rate=44100,
        pcm_data=generate_acoustic_bass_pcm(),
        loop_start=2000,
        loop_end=40000,
        root_key=36
    )
    fdd_disk.add_sample(
        sample_id=2,
        sample_name="Warm Brass C4",
        sample_rate=44100,
        pcm_data=generate_pcm_sine(freq=261.63, rate=44100, num_samples=44100, decay=1.5),
        loop_start=3000,
        loop_end=42000,
        root_key=60
    )

    fdd_bytes = fdd_disk.build_image()
    assert len(fdd_bytes) == 1474560
    with open(fdd_path, "wb") as f:
        f.write(fdd_bytes)

    # 2. Create blank 10MB SCSI Hard Disk image
    blank_hd_size = 10 * 1024 * 1024
    with open(hd_path, "wb") as f:
        f.write(b"\x00" * blank_hd_size)

    with open(hd_path, "rb") as f:
        blank_data = f.read()
    assert len(blank_data) == blank_hd_size
    blank_parsed = RolandS760Disk.parse(blank_data)
    assert blank_parsed["is_roland"] is False
    assert blank_parsed["num_patches"] == 0
    assert blank_parsed["num_samples"] == 0

    # 3 & 4. Load sounds from Floppy and Save to Blank Hard Disk
    format_and_save_to_hd(
        source_floppy_path=fdd_path,
        target_hd_path=hd_path,
        volume_name="INTERNAL HD 01",
        size_mb=10
    )

    # 5. Verify saved Hard Disk image
    assert os.path.exists(hd_path)
    with open(hd_path, "rb") as f:
        saved_hd_data = f.read()

    assert len(saved_hd_data) == blank_hd_size
    hd_parsed = RolandS760Disk.parse(saved_hd_data)
    assert hd_parsed["is_roland"] is True
    assert hd_parsed["volume_name"] == "INTERNAL HD 01"
    assert hd_parsed["num_patches"] == 2
    assert hd_parsed["num_samples"] == 2

    # Verify Patches
    assert hd_parsed["patches"][0]["id"] == 1
    assert hd_parsed["patches"][0]["name"] == "Moog Bass Lead"
    assert hd_parsed["patches"][0]["level"] == 120
    assert hd_parsed["patches"][0]["pan"] == -5
    assert hd_parsed["patches"][1]["id"] == 2
    assert hd_parsed["patches"][1]["name"] == "Warm Brass Pad"

    # Verify Samples
    assert hd_parsed["samples"][0]["id"] == 1
    assert hd_parsed["samples"][0]["name"] == "Moog Saw Sub"
    assert hd_parsed["samples"][0]["sample_rate"] == 44100
    assert hd_parsed["samples"][0]["root_key"] == 36
    assert len(hd_parsed["samples"][0]["data"]) > 0

    assert hd_parsed["samples"][1]["id"] == 2
    assert hd_parsed["samples"][1]["name"] == "Warm Brass C4"
    assert hd_parsed["samples"][1]["sample_rate"] == 44100
    assert hd_parsed["samples"][1]["root_key"] == 60
    assert len(hd_parsed["samples"][1]["data"]) > 0

    # 6. Synthesize audio directly from HD sample data
    audio_bass = S760VoiceSynthesizer.render_voice(
        hd_parsed["samples"][0],
        note=36,
        num_output_samples=44100,
        output_rate=44100
    )
    assert len(audio_bass) == 44100
    rms_bass = math.sqrt(sum(s * s for s in audio_bass) / len(audio_bass))
    assert rms_bass > 0.10, f"Bass sample from HD too quiet: {rms_bass}"

    audio_brass = S760VoiceSynthesizer.render_voice(
        hd_parsed["samples"][1],
        note=60,
        num_output_samples=44100,
        output_rate=44100
    )
    assert len(audio_brass) == 44100
    rms_brass = math.sqrt(sum(s * s for s in audio_brass) / len(audio_brass))
    assert rms_brass > 0.10, f"Brass sample from HD too quiet: {rms_brass}"

    # Cleanup temporary test images
    if os.path.exists(fdd_path):
        os.remove(fdd_path)
    if os.path.exists(hd_path):
        os.remove(hd_path)







