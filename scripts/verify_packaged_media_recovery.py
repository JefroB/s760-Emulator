"""Verify sample RAM/audio retained by packaged-media.spec.ts browser checkpoints.

Requires the same package, actual local firmware and both completed browser cases.
This is cold native inspection, separate from browser and physical-device evidence.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path

from s760_runtime import NativeRuntime, RuntimeConfig
from verify_packaged_edit_audio import measure
from verify_native_media import compare_wave_records

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--browser-work', type=Path, required=True)
    parser.add_argument('--unformatted-work', type=Path, help='Optional unformatted case directory from a targeted rerun')
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    assert not args.state_dir.exists(), 'Use fresh private native state'
    args.state_dir.mkdir(parents=True)
    args.package = args.package.resolve()
    assert (args.package/'scripts/s760_runtime.lua').read_bytes() == (ROOT/'scripts/s760_runtime.lua').read_bytes()
    unformatted = args.unformatted_work or args.browser_work/'unformatted'
    dirty = args.browser_work/'dirty'
    bad_result = json.loads((unformatted/'result.json').read_text())
    dirty_result = json.loads((dirty/'result.json').read_text())
    assert bad_result['passed'] and len(bad_result['cycles']) == 8 and dirty_result['passed']
    source = ROOT/'roms/FDD/ROBOFULL.IMG'
    original = source.read_bytes()
    assert digest(original) == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    expected_samples = original[0x2ac00:0x2ac00+13*9216]
    cfg = RuntimeConfig(args.package/'mame-source/mames760.exe',
                        ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN', ROOT/'roms/System/S760224.IMG',
                        args.state_dir/'unused', source, sound=False, throttle=False)

    def inspect(archive, name):
        dump = (args.state_dir/(name+'.wave.bin')).resolve()
        with NativeRuntime(replace(cfg, state_dir=args.state_dir/name, wave_dump=dump)) as runtime:
            runtime.request('pause'); runtime.load_checkpoint(archive)
        wave = dump.read_bytes()
        assert len(wave) == 32*1024*1024
        assert wave[16:16+len(expected_samples)] == expected_samples, 'A loaded sample allocation changed'
        return wave

    baseline_archive = unformatted/'baseline.s760state'
    baseline_wave = inspect(baseline_archive, 'baseline-wave')
    baseline_audio = measure(args.package, source, args.state_dir/'baseline-audio', 60, baseline_archive)
    assert all(row['frequency_hz'] == 20004 and row['peak'] > 0 for row in baseline_audio)
    rows = []
    for index, row in enumerate(bad_result['cycles']):
        archive = unformatted/row['archive']
        wave = inspect(archive, f'retained-{index}-wave')
        # Disk scans may update firmware catalog records in high wave RAM.
        # The independently identified 13 allocations above must remain exact.
        comparison = compare_wave_records(baseline_wave, wave)
        audio = measure(args.package, source, args.state_dir/f'retained-{index}-audio', 60, archive)
        for before, after in zip(baseline_audio, audio):
            assert after['frequency_hz'] == before['frequency_hz']
            assert abs(after['peak'] - before['peak']) < 1e-6
        rows.append({'round': row['round'], 'file': row['file'], 'archive_sha256': digest(archive.read_bytes()),
                     'exact_sample_bytes': len(expected_samples), 'wave_sha256': digest(wave),
                     'full_wave_comparison': comparison, 'audio': audio})
        print(f'Retained case {index+1}/8: all sample allocations and playback/release pass', flush=True)
    dirty_wave = inspect(dirty/'dirty.s760state', 'dirty-wave')
    edited = dirty/'edited.img'
    assert digest(edited.read_bytes()) == dirty_result['saved_sha256'] == dirty_result['recalled_sha256']
    disk_audio = measure(args.package, edited, args.state_dir/'edited-disk', 60)
    session_audio = measure(args.package, edited, args.state_dir/'edited-session', 60, dirty/'dirty.s760state')
    for disk, session, baseline in zip(disk_audio, session_audio, baseline_audio):
        assert disk['frequency_hz'] == session['frequency_hz'] == baseline['frequency_hz']
        assert abs(disk['peak'] - session['peak']) < 1e-6
        assert .49 < disk['peak']/baseline['peak'] < .52
    assert source.read_bytes() == original
    result = {'passed': True, 'baseline': {'wave_sha256': digest(baseline_wave), 'wave_bytes': len(baseline_wave), 'audio': baseline_audio},
              'retained': rows, 'dirty': {'exact_sample_bytes': len(expected_samples),
                                        'full_wave_comparison': compare_wave_records(baseline_wave, dirty_wave),
                                        'disk_audio': disk_audio, 'session_audio': session_audio},
              'scope': 'Cold native readback of browser checkpoints and exported disk; no physical audio or realtime qualification'}
    (args.state_dir/'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('All media-recovery native checks passed', flush=True)


if __name__ == '__main__':
    main()
