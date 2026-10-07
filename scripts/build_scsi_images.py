"""
scripts/build_scsi_images.py — Generates BlueSCSI & ZuluSCSI compliant disk images in roms/SCSI/
1. HD00_512.img  : Roland S-760 SCSI Hard Disk Image (Target ID 0, 512 bytes/sector)
2. CD10_2048.iso : Akai S1000 SCSI CD-ROM ISO Image  (Target ID 1, 2048 bytes/block)
"""
import os
import sys
import math
import struct

# Add tests/ to sys.path for disk builders
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "tests"))
from disk_formats import RolandS760Disk, AkaiS1000Disk


def generate_pcm_sine(freq=440.0, rate=44100, num_samples=44100, decay=2.0):
    """Generate 16-bit signed PCM with exponential acoustic decay."""
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / rate
        val = int(32767.0 * 0.75 * math.sin(2.0 * math.pi * freq * t) * math.exp(-decay * t))
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def generate_acoustic_bass_pcm():
    """Multi-harmonic slap/upright bass PCM (Low E1 = 41.20 Hz)."""
    num_samples = 44100
    pcm = bytearray(num_samples * 2)
    for i in range(num_samples):
        t = float(i) / 44100.0
        transient = ((i % 19) / 19.0 - 0.5) * math.exp(-90.0 * t)
        b1 = math.sin(2.0 * math.pi * 41.20 * t) * math.exp(-1.4 * t)
        b2 = 0.7 * math.sin(2.0 * math.pi * 82.40 * t) * math.exp(-2.2 * t)
        b3 = 0.4 * math.sin(2.0 * math.pi * 123.60 * t) * math.exp(-3.5 * t)
        val = int(32767.0 * 0.75 * (transient * 0.4 + b1 * 0.5 + b2 * 0.3 + b3 * 0.2))
        struct.pack_into("<h", pcm, i * 2, max(-32767, min(32767, val)))
    return bytes(pcm)


def build_scsi_hard_disk_image(target_path="roms/SCSI/HD00_512.img", size_mb=10):
    """Creates a Roland S-760 SCSI Hard Disk Image (SCSI ID 0, 512B sectors)."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    disk = RolandS760Disk(volume_name="S760 SCSI HD0")

    # Add Patches
    disk.add_patch(patch_id=1, patch_name="Ac. UprightBass", partial_ids=[1], level=127, pan=0)
    disk.add_patch(patch_id=2, patch_name="Jazz Guitar E2",  partial_ids=[2], level=115, pan=-10)
    disk.add_patch(patch_id=3, patch_name="Concert Grand C4",partial_ids=[3], level=120, pan=0)

    # Add Samples
    disk.add_sample(sample_id=1, sample_name="UprightBass E1", sample_rate=44100, pcm_data=generate_acoustic_bass_pcm(), loop_start=2000, loop_end=40000, root_key=28)
    disk.add_sample(sample_id=2, sample_name="JazzGuitar E2",  sample_rate=44100, pcm_data=generate_pcm_sine(freq=82.41, num_samples=44100, decay=2.5), loop_start=1500, loop_end=42000, root_key=40)
    disk.add_sample(sample_id=3, sample_name="GrandPiano C4",  sample_rate=44100, pcm_data=generate_pcm_sine(freq=261.63, num_samples=44100, decay=1.8), loop_start=3000, loop_end=42000, root_key=60)

    img_data = disk.build_image(size_mb=size_mb)
    with open(target_path, "wb") as f:
        f.write(img_data)
    print(f"[SCSI BUILD] Built Roland SCSI Hard Disk Image '{target_path}' ({len(img_data):,} bytes, SCSI ID 0).")
    return target_path


def build_scsi_cdrom_iso_image(target_path="roms/SCSI/CD10_2048.iso", size_mb=4):
    """Creates an Akai S1000 SCSI CD-ROM ISO Image (SCSI ID 1, 2048B blocks)."""
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    akai = AkaiS1000Disk(volume_name="AKAI_S1000_1")

    # Add Programs
    akai.add_program(prog_num=1, prog_name="Slap Bass 01",  midi_channel=1)
    akai.add_program(prog_num=2, prog_name="AcousticPiano", midi_channel=2)
    akai.add_program(prog_num=3, prog_name="Sect.Strings",  midi_channel=3)

    # Add Samples
    akai.add_sample(sample_name="SlapBass E1",  sample_rate=44100, pcm_data=generate_acoustic_bass_pcm(), loop_start=2000, loop_end=40000, root_key=28)
    akai.add_sample(sample_name="Piano High C", sample_rate=44100, pcm_data=generate_pcm_sine(freq=523.25, num_samples=44100, decay=2.0), loop_start=2500, loop_end=40000, root_key=72)
    akai.add_sample(sample_name="Violin Sust",  sample_rate=44100, pcm_data=generate_pcm_sine(freq=440.00, num_samples=44100, decay=0.8), loop_start=1000, loop_end=42000, root_key=69)

    iso_data = akai.build_iso(total_mb=size_mb)
    with open(target_path, "wb") as f:
        f.write(iso_data)
    print(f"[SCSI BUILD] Built Akai S1000 SCSI CD-ROM ISO '{target_path}' ({len(iso_data):,} bytes, SCSI ID 1).")
    return target_path


def format_and_save_to_hd(source_floppy_path: str, target_hd_path: str, volume_name="S760 INTERNAL HD", size_mb=10):
    """
    Emulates the Roland S-760 DISK subsystem operations:
    1. Reads & loads sound library (Patches, Partials, Wave PCM samples) from a source Floppy Disk image.
    2. Initializes / Formats a blank SCSI Hard Disk image with the Roland disk architecture.
    3. Saves all loaded RAM sound structures into the SCSI Hard Disk image file.
    """
    if not os.path.exists(source_floppy_path):
        raise FileNotFoundError(f"Source floppy not found: {source_floppy_path}")

    with open(source_floppy_path, "rb") as f:
        floppy_data = f.read()

    # Load from floppy into S-760 memory representation
    ram_disk = RolandS760Disk.from_image(floppy_data)
    ram_disk.volume_name = volume_name[:16].ljust(16)

    # Build formatted hard disk image
    hd_data = ram_disk.build_image(size_mb=size_mb)
    os.makedirs(os.path.dirname(target_hd_path), exist_ok=True)
    with open(target_hd_path, "wb") as f:
        f.write(hd_data)

    print(f"[SCSI HD] Saved {len(ram_disk.patches)} patches and {len(ram_disk.samples)} samples from '{source_floppy_path}' to '{target_hd_path}' ({len(hd_data):,} bytes).")
    return target_hd_path


if __name__ == "__main__":
    build_scsi_hard_disk_image("roms/SCSI/HD00_512.img", size_mb=10)
    build_scsi_cdrom_iso_image("roms/SCSI/CD10_2048.iso", size_mb=4)

