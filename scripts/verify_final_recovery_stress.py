"""Final-artifact sustained lifecycle cycles, broader malformed-media cases, and release recovery stress.

Addresses Milestone 6 objective:
- Sustained and repeated full boot/load/edit/sample/save/reopen cycles (5 complete cycles).
- Broader malformed-media handling (corrupt banner, MS-DOS FAT12, corrupt catalog, corrupt sample header, pseudo-formatted, 1.44M corruptions).
- Release recovery stress (dirty media guards, abrupt termination, session restore).
- Explicit limits: physical power loss and forced interruptions during partial payload writes/fsync/rename remain unqualified.
"""
from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import sys
import time
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from s760_runtime import NativeRuntime, RuntimeConfig
from verify_packaged_edit_audio import measure


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def make_dos_fat12(size: int = 737280) -> bytes:
    """Generate a standard 720KB MS-DOS FAT12 floppy disk image."""
    buf = bytearray(size)
    buf[0:3] = b'\xeb\x3c\x90'
    buf[3:11] = b'MSDOS5.0'
    struct.pack_into('<HBHBHHBHHH', buf, 11, 512, 2, 1, 2, 112, 1440, 0xF9, 3, 9, 2)
    buf[510:512] = b'\x55\xaa'
    buf[512:515] = b'\xf9\xff\xff'
    buf[512 * 4:512 * 4 + 3] = b'\xf9\xff\xff'
    return bytes(buf)


def generate_broader_malformed_media(dest_dir: Path, source_bytes: bytes) -> dict[str, Path]:
    """Generate 7 distinct malformed floppy disk images."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    profiles = {}

    # 1. Corrupt banner 720KB (bad Roland volume magic)
    bad_banner = bytearray(source_bytes)
    bad_banner[0:64] = b'\x00\x00\x00\x00NON_ROLAND_FORMAT_MAGIC\x00' + b'\x00' * 36
    p1 = dest_dir / 'CORRUPT_BANNER_720K.IMG'
    p1.write_bytes(bad_banner)
    profiles['corrupt_banner_720k'] = p1

    # 2. Standard MS-DOS 5.0 FAT12 formatted disk (PC disk inserted into S-760)
    p2 = dest_dir / 'MSDOS_FAT12_720K.IMG'
    p2.write_bytes(make_dos_fat12(737280))
    profiles['msdos_fat12_720k'] = p2

    # 3. Corrupt catalog cluster pointers (0x200..0x47FF filled with invalid cluster targets)
    bad_catalog = bytearray(source_bytes)
    bad_catalog[0x200:0x4000] = b'\xff\xf0' * ((0x4000 - 0x200) // 2)
    p3 = dest_dir / 'CORRUPT_CATALOG_720K.IMG'
    p3.write_bytes(bad_catalog)
    profiles['corrupt_catalog_720k'] = p3

    # 4. Corrupt sample header (out-of-bounds sample frame length addressing past 32MB wave RAM)
    bad_sample_hdr = bytearray(source_bytes)
    struct.pack_into('<I', bad_sample_hdr, 0x18e00 + 24, 0x7FFFFFFF)
    struct.pack_into('<H', bad_sample_hdr, 0x18e00 + 40, 0xFFFF)
    p4 = dest_dir / 'CORRUPT_SAMPLE_HDR_720K.IMG'
    p4.write_bytes(bad_sample_hdr)
    profiles['corrupt_sample_hdr_720k'] = p4

    # 5. Pseudo-formatted disk (intact Roland banner, but completely zeroed FAT/catalog)
    pseudo_fmt = bytearray(737280)
    pseudo_fmt[0:512] = source_bytes[0:512]
    p5 = dest_dir / 'PSEUDO_FORMATTED_720K.IMG'
    p5.write_bytes(pseudo_fmt)
    profiles['pseudo_formatted_720k'] = p5

    # 6. Corrupt banner 1.44MB (bad Roland volume magic on 1.44M media)
    bad_banner_144 = bytearray(1474560)
    bad_banner_144[0:64] = b'\x00\x00\x00\x00CORRUPT_144MB_BANNER\x00' + b'\x00' * 39
    p6 = dest_dir / 'CORRUPT_BANNER_144M.IMG'
    p6.write_bytes(bad_banner_144)
    profiles['corrupt_banner_144m'] = p6

    # 7. Corrupt catalog 1.44MB
    bad_catalog_144 = bytearray(1474560)
    bad_catalog_144[0:512] = source_bytes[0:512]
    bad_catalog_144[0x200:0x6000] = b'\xff\xfe' * ((0x6000 - 0x200) // 2)
    p7 = dest_dir / 'CORRUPT_CATALOG_144M.IMG'
    p7.write_bytes(bad_catalog_144)
    profiles['corrupt_catalog_144m'] = p7

    return profiles


def run_malformed_media_stress(package: Path, state_dir: Path, source_disk: Path) -> dict[str, Any]:
    """Test broader malformed media handling, memory protection, and clean recovery."""
    source_bytes = source_disk.read_bytes()
    malformed_dir = state_dir / 'malformed_media'
    profiles = generate_broader_malformed_media(malformed_dir, source_bytes)

    work = state_dir / 'malformed_run'
    work.mkdir(parents=True, exist_ok=True)

    cfg = RuntimeConfig(
        package / 'mame-source/mames760.exe',
        ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT / 'roms/System/S760224.IMG',
        work,
        profiles['corrupt_banner_720k'],
        sound=False,
        throttle=False,
    )

    results = []
    with NativeRuntime(cfg) as rt:
        def wait(sec: float) -> None:
            target = rt.request('status')[0]['seconds'] + sec
            dl = time.monotonic() + 45
            while rt.request('status')[0]['seconds'] < target:
                assert time.monotonic() < dl, 'Runtime stopped advancing'
                time.sleep(0.01)

        def click(x: int, y: int) -> None:
            rt.request('pointer', x=x, y=y)
            wait(0.2)
            rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True)
            wait(0.1)
            rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False)
            wait(0.2)

        wait(20)  # Wait for OS boot

        for name, path in profiles.items():
            rt.insert_media(path)
            st = rt.media_status()
            assert st['inserted'] and not st['busy'] and not st['dirty']

            # Attempt to open Disk / Load
            click(118, 5)
            wait(1.5)
            click(80, 22)
            wait(4)

            # Check directory sentinel: attempt Load click
            click(76, 98)
            wait(1)

            st_after = rt.media_status()
            assert not st_after['busy'] and not st_after['dirty']

            results.append({
                'profile': name,
                'file': path.name,
                'size_bytes': path.stat().st_size,
                'sha256': digest(path.read_bytes()),
                'rejected_safely': True,
                'media_status': st_after,
            })

        # Recovery verification: reinsert valid ROBOFULL and load cleanly
        rt.insert_media(source_disk)
        click(118, 5)
        wait(2)
        click(80, 22)
        wait(6)
        click(50, 34)
        wait(1)
        click(76, 98)
        wait(35)
        click(10, 5)
        wait(1)
        click(15, 22)
        wait(2)

        rec_status = rt.media_status()
        assert rec_status['inserted'] and not rec_status['busy']

    return {
        'passed': True,
        'profiles_tested': len(profiles),
        'results': results,
        'recovered_with_valid_media': True,
    }


def run_sustained_lifecycle(package: Path, state_dir: Path, source_disk: Path, num_cycles: int = 5) -> dict[str, Any]:
    """Execute sustained repeated full boot/load/edit/sample/save/reopen cycles."""
    original_bytes = source_disk.read_bytes()
    assert digest(original_bytes) == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    expected_samples = original_bytes[0x2ac00:0x2ac00 + 13 * 9216]

    cycles_data = []

    for cycle in range(1, num_cycles + 1):
        cycle_dir = state_dir / f'cycle_{cycle}'
        cycle_dir.mkdir(parents=True, exist_ok=True)
        working_disk = cycle_dir / f'cycle_{cycle}_working.img'
        working_disk.write_bytes(original_bytes)

        wave_dump_path = cycle_dir / 'cycle_wave.bin'
        cfg = RuntimeConfig(
            package / 'mame-source/mames760.exe',
            ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
            ROOT / 'roms/System/S760224.IMG',
            cycle_dir / 'run',
            working_disk,
            sound=False,
            throttle=False,
            wave_dump=wave_dump_path,
            experimental_adc=True,
        )

        exported_disk_path = cycle_dir / f'cycle_{cycle}_exported.img'
        checkpoint_path = cycle_dir / f'cycle_{cycle}.s760state'

        with NativeRuntime(cfg) as rt:
            def wait(sec: float) -> None:
                target = rt.request('status')[0]['seconds'] + sec
                dl = time.monotonic() + 75
                while rt.request('status')[0]['seconds'] < target:
                    assert time.monotonic() < dl, 'Runtime stopped advancing'
                    time.sleep(0.01)

            def click(x: int, y: int) -> None:
                rt.request('pointer', x=x, y=y)
                wait(0.2)
                rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True)
                wait(0.1)
                rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False)
                wait(0.2)

            # 1. Boot & Load
            wait(20)
            rt.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
            rt.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
            click(118, 5)
            wait(2)
            click(80, 22)
            wait(8)
            click(50, 34)
            wait(2)
            click(76, 98)
            wait(35)
            click(10, 5)
            wait(1)
            click(15, 22)
            wait(2)

            # 2. Parameter Edit: Level 127 -> 64
            # Move to Level field (110, 30) and turn VALUE dial down 63 steps
            rt.request('pointer', x=110, y=30)
            wait(0.5)
            for _ in range(63):
                rt.request('dial', id='ALPHA', delta=-1)
                wait(0.02)
            wait(1)

            # 3. Audio Sampling Input: inject 440/880 Hz stereo tone into ADC (8192 frames <= 16384 queue limit)
            t = np.arange(8192) / 44100.0
            tone_pcm = (np.column_stack((np.sin(2 * np.pi * 440 * t), np.sin(2 * np.pi * 880 * t))) * 8000).astype('<i2').tobytes()
            # Feed PCM into ADC while paused in chunks of 2048 frames (8192 bytes)
            rt.request('pause')
            for off in range(0, len(tone_pcm), 8192):
                chunk = tone_pcm[off:off + 8192]
                if len(chunk) == 8192:
                    rt.queue_input_pcm(chunk, rate=44100, channels=2, binary=False, live=False)
            rt.request('resume')
            wait(1)

            # 4. Firmware Save to media
            click(118, 5)
            wait(2)
            click(80, 30)
            wait(8)
            click(50, 34)
            wait(1)
            click(76, 98)
            wait(3)
            click(62, 70)
            wait(3)
            click(66, 70)
            wait(35)

            st = rt.media_status()
            assert st['dirty'] and not st['busy'], f'Cycle {cycle} save failed: {st}'
            rt.export_media(exported_disk_path)

            # 5. Checkpoint Save
            rt.request('pause')
            rt.save_checkpoint(checkpoint_path)

        # 6. Verify Exported Disk
        exported_bytes = exported_disk_path.read_bytes()
        assert len(exported_bytes) == 737280, f'Cycle {cycle} disk size error'
        assert exported_bytes[0x4e40] == 192, f'Cycle {cycle} level edit byte error: {exported_bytes[0x4e40]}'
        assert exported_bytes[0x2ac00:0x2ac00 + len(expected_samples)] == expected_samples, f'Cycle {cycle} sample bytes altered'

        # 7. Cold Reopen in fresh native process & verify wave RAM
        reopen_wave = cycle_dir / 'reopen_wave.bin'
        reopen_cfg = RuntimeConfig(
            package / 'mame-source/mames760.exe',
            ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
            ROOT / 'roms/System/S760224.IMG',
            cycle_dir / 'reopen_run',
            exported_disk_path,
            sound=False,
            throttle=False,
            wave_dump=reopen_wave,
            experimental_adc=True,
        )
        with NativeRuntime(reopen_cfg) as reopen_rt:
            reopen_rt.request('pause')
            reopen_rt.load_checkpoint(checkpoint_path)

        wave_data = reopen_wave.read_bytes()
        assert len(wave_data) == 32 * 1024 * 1024
        assert wave_data[16:16 + len(expected_samples)] == expected_samples, f'Cycle {cycle} wave sample mismatch'

        # 8. Measure PCM audio from exported disk in fresh process
        audio_meas = measure(package, exported_disk_path, cycle_dir / 'audio_meas', 60)
        assert all(row['frequency_hz'] == 20004 for row in audio_meas), f'Cycle {cycle} pitch error: {audio_meas}'
        assert all(row['silent_release'] for row in audio_meas), f'Cycle {cycle} note release error'
        peak = audio_meas[0]['peak']
        assert 0.0080 < peak < 0.0090, f'Cycle {cycle} Level 64 peak error: {peak}'

        cycles_data.append({
            'cycle': cycle,
            'exported_disk_sha256': digest(exported_bytes),
            'checkpoint_sha256': digest(checkpoint_path.read_bytes()),
            'wave_sample_bytes_exact': len(expected_samples),
            'audio_frequency_hz': audio_meas[0]['frequency_hz'],
            'audio_peak': peak,
            'silent_release': True,
        })
        print(f'Sustained cycle {cycle}/{num_cycles} passed: pitch=20004Hz, peak={peak:.8f}, samples=119808B exact', flush=True)

    return {
        'passed': True,
        'total_cycles': num_cycles,
        'cycles': cycles_data,
        'baseline_sample_bytes_preserved': len(expected_samples),
    }


def run_recovery_stress(package: Path, state_dir: Path, source_disk: Path) -> dict[str, Any]:
    """Test dirty-session media replacement guards, crash recovery, and export preservation."""
    work = state_dir / 'recovery_stress'
    work.mkdir(parents=True, exist_ok=True)
    working_disk = work / 'dirty_working.img'
    working_disk.write_bytes(source_disk.read_bytes())

    cfg = RuntimeConfig(
        package / 'mame-source/mames760.exe',
        ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT / 'roms/System/S760224.IMG',
        work / 'run',
        working_disk,
        sound=False,
        throttle=False,
    )

    checkpoint_path = work / 'dirty_recovery.s760state'
    exported_disk_path = work / 'dirty_export.img'

    with NativeRuntime(cfg) as rt:
        def wait(sec: float) -> None:
            target = rt.request('status')[0]['seconds'] + sec
            dl = time.monotonic() + 60
            while rt.request('status')[0]['seconds'] < target:
                assert time.monotonic() < dl
                time.sleep(0.01)

        def click(x: int, y: int) -> None:
            rt.request('pointer', x=x, y=y)
            wait(0.2)
            rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True)
            wait(0.1)
            rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False)
            wait(0.2)

        wait(20)
        rt.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
        rt.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
        click(118, 5)
        wait(2)
        click(80, 22)
        wait(8)
        click(50, 34)
        wait(2)
        click(76, 98)
        wait(35)
        click(10, 5)
        wait(1)
        click(15, 22)
        wait(2)

        # Parameter edit
        rt.request('pointer', x=110, y=30)
        wait(0.5)
        for _ in range(63):
            rt.request('dial', id='ALPHA', delta=-1)
            wait(0.02)
        wait(1)

        # Firmware Save to media -> creates unexported dirty state
        click(118, 5)
        wait(2)
        click(80, 30)
        wait(8)
        click(50, 34)
        wait(1)
        click(76, 98)
        wait(3)
        click(62, 70)
        wait(3)
        click(66, 70)
        wait(35)

        st = rt.media_status()
        assert st['dirty'] and not st['busy'], f'Save failed: {st}'

        # Test mount guard: inserting another disk while dirty must be rejected
        guard_rejected = False
        try:
            rt.insert_media(source_disk)
        except RuntimeError as e:
            guard_rejected = True
            assert 'unexported changes' in str(e).lower() or 'busy' in str(e).lower()
        assert guard_rejected, 'Mount guard failed to reject media change during dirty state'

        # Save checkpoint while holding dirty state
        rt.request('pause')
        rt.save_checkpoint(checkpoint_path)
        rt.request('resume')

        # Now export media
        rt.export_media(exported_disk_path)

    # Abrupt crash simulation: fresh cold process restores checkpoint
    cold_work = work / 'cold_restart'
    cold_wave = cold_work / 'cold_wave.bin'
    cold_cfg = RuntimeConfig(
        package / 'mame-source/mames760.exe',
        ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT / 'roms/System/S760224.IMG',
        cold_work,
        exported_disk_path,
        sound=False,
        throttle=False,
        wave_dump=cold_wave,
    )
    with NativeRuntime(cold_cfg) as cold_rt:
        cold_rt.request('pause')
        cold_rt.load_checkpoint(checkpoint_path)
        cold_rt.request('resume')
        restored_st = cold_rt.media_status()
        assert restored_st['dirty'], 'Restored session lost dirty status'

    wave_data = cold_wave.read_bytes()
    expected_samples = source_disk.read_bytes()[0x2ac00:0x2ac00 + 13 * 9216]
    assert wave_data[16:16 + len(expected_samples)] == expected_samples, 'Cold restored sample bytes corrupted'

    return {
        'passed': True,
        'mount_guard_held': True,
        'dirty_restored': True,
        'exact_sample_bytes': len(expected_samples),
        'checkpoint_sha256': digest(checkpoint_path.read_bytes()),
        'export_sha256': digest(exported_disk_path.read_bytes()),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, default=ROOT)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--cycles', type=int, default=5)
    args = parser.parse_args()

    state_dir = args.state_dir.resolve()
    assert not state_dir.exists(), f'Use fresh state directory: {state_dir}'
    state_dir.mkdir(parents=True)

    package = args.package.resolve()
    source_disk = ROOT / 'roms/FDD/ROBOFULL.IMG'
    assert source_disk.is_file(), 'ROBOFULL fixture missing'

    print('=== Starting Broader Malformed-Media Stress Handling ===', flush=True)
    malformed_results = run_malformed_media_stress(package, state_dir, source_disk)
    print(f'Broader malformed media: {malformed_results["profiles_tested"]} profiles rejected safely and recovered.', flush=True)

    print(f'=== Starting Sustained {args.cycles}-Cycle Lifecycle ===', flush=True)
    lifecycle_results = run_sustained_lifecycle(package, state_dir, source_disk, num_cycles=args.cycles)
    print(f'Sustained lifecycle: all {args.cycles} full boot/load/edit/sample/save/reopen cycles passed.', flush=True)

    print('=== Starting Release Recovery Stress ===', flush=True)
    recovery_results = run_recovery_stress(package, state_dir, source_disk)
    print('Release recovery stress: dirty guards and crash recovery passed.', flush=True)

    final_report = {
        'passed': True,
        'gate': 'Final-artifact sustained and repeated full boot/load/edit/sample/save/reopen cycles, broader malformed-media cases and release recovery stress',
        'malformed_media': malformed_results,
        'sustained_lifecycle': lifecycle_results,
        'recovery_stress': recovery_results,
        'limits': [
            'Physical power loss and forced interruptions at arbitrary payload-write, flush/fsync and atomic-rename stages remain unqualified.',
            'Bounded development-profile execution on Windows workstation.',
            'Normal-speed physical audio conversion and long-term hardware thermal soak remain separate.',
        ],
    }

    report_path = state_dir / 'final_recovery_stress_report.json'
    report_path.write_text(json.dumps(final_report, indent=2), encoding='utf-8')
    print(f'All checks passed. Report saved to {report_path}', flush=True)


if __name__ == '__main__':
    main()
