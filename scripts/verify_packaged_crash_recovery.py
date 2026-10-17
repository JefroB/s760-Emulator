"""Cold native readback of the packaged abrupt-termination browser acceptance.

Uses the tested package's MAME with identical source/package protocol. No device
audio, guest writes or physical power-loss claims. Private firmware is required.
"""
import argparse
import hashlib
import json
from pathlib import Path

from s760_runtime import NativeRuntime, RuntimeConfig
from verify_packaged_edit_audio import measure

ROOT = Path(__file__).resolve().parents[1]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--browser-work', type=Path, required=True, help='The browser crash/ case folder')
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    package, browser, work = (p.resolve() for p in (args.package, args.browser_work, args.state_dir))
    assert not work.exists(), 'Use fresh private state'
    assert (package/'scripts/s760_runtime.lua').read_bytes() == (ROOT/'scripts/s760_runtime.lua').read_bytes()
    source = ROOT/'roms/FDD/ROBOFULL.IMG'
    original = source.read_bytes()
    assert digest(original) == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    report = json.loads((browser/'result.json').read_text())
    assert report['passed'] and len(report['cycles']) == 3
    assert len({row['pid'] for row in report['cycles']}) == 3
    checkpoint = (browser/'automatic.s760state').read_bytes()
    assert digest(checkpoint) == report['checkpoint_sha256']
    edited = (browser/'edited.img').read_bytes()
    assert digest(edited) == report['edited_sha256'] and edited[0x4e40] == 192
    samples = original[0x2ac00:0x2ac00+13*9216]
    assert edited[0x2ac00:0x2ac00+len(samples)] == samples
    work.mkdir(parents=True)
    baseline = measure(package, source, work/'baseline', 60)
    disk = measure(package, browser/'edited.img', work/'cold-disk', 60)
    rows = []
    for index, cycle in enumerate(report['cycles']):
        assert cycle['export_sha256'] == report['edited_sha256']
        assert cycle['recovery_sha256'] == report['checkpoint_sha256']
        archive = browser/f'recovered-{index}.s760state'
        dump = work/f'recovered-{index}.wave.bin'
        export = work/f'recovered-{index}.img'
        cfg = RuntimeConfig(package/'mame-source/mames760.exe',
                            ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN', ROOT/'roms/System/S760224.IMG',
                            work/f'wave-{index}', sound=False, throttle=False, wave_dump=dump)
        with NativeRuntime(cfg) as runtime:
            runtime.request('pause')
            runtime.load_checkpoint(archive)
            # Peripheral media acknowledgements require normal input polling.
            runtime.request('resume')
            status = runtime.media_status()
            assert status['dirty'] and not status['busy'], status
            runtime.export_media(export)
        wave = dump.read_bytes()
        assert len(wave) == 32*1024*1024
        assert wave[16:16+len(samples)] == samples
        assert export.read_bytes() == edited
        audio = measure(package, browser/'edited.img', work/f'audio-{index}', 60, archive)
        for before, saved, restored in zip(baseline, disk, audio):
            assert before['peak'] > 0 and before['frequency_hz'] is not None
            assert before['frequency_hz'] == saved['frequency_hz'] == restored['frequency_hz']
            assert .49 < restored['peak']/before['peak'] < .52
            assert abs(restored['peak']-saved['peak']) < 1e-6
            assert restored['silent_release'] and saved['silent_release']
        rows.append(dict(cycle=index, archive_sha256=digest(archive.read_bytes()),
                         wave_sha256=digest(wave), exact_sample_bytes=len(samples),
                         export_sha256=digest(export.read_bytes()), dirty_restored=True, audio=audio))
        print(f'Crash cycle {index+1}: dirty media, all sample bytes, pitch/level and release pass', flush=True)
    retry_result = None
    if report.get('retry_sha256'):
        archive = browser/'retry.s760state'
        assert digest(archive.read_bytes()) == report['retry_sha256'] != report['checkpoint_sha256']
        assert report['replace_denied_preserves_previous']
        assert report['failed_save_preserves_live_field'] == report['retry_restored_field']
        dump, export = work/'retry.wave.bin', work/'retry.img'
        cfg = RuntimeConfig(package/'mame-source/mames760.exe',
                            ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN', ROOT/'roms/System/S760224.IMG',
                            work/'retry-wave', sound=False, throttle=False, wave_dump=dump)
        with NativeRuntime(cfg) as runtime:
            runtime.request('pause'); runtime.load_checkpoint(archive); runtime.request('resume')
            status = runtime.media_status()
            assert status['dirty'] and not status['busy'], status
            runtime.export_media(export)
        wave = dump.read_bytes()
        assert len(wave) == 32*1024*1024 and wave[16:16+len(samples)] == samples
        assert export.read_bytes() == edited
        audio = measure(package, browser/'edited.img', work/'retry-audio', 60, archive)
        for saved, restored in zip(disk, audio):
            assert restored['frequency_hz'] == saved['frequency_hz']
            # The successful replacement contains the new Level63 edit, rather
            # than silently retaining the prior Level64 checkpoint.
            assert .97 < restored['peak']/saved['peak'] < .999
            assert restored['silent_release']
        retry_result = dict(passed=True, archive_sha256=digest(archive.read_bytes()),
                            wave_sha256=digest(wave), exact_sample_bytes=len(samples),
                            export_sha256=digest(export.read_bytes()), dirty_restored=True, audio=audio)
        print('Replacement retry: new Level63 state, exact disk/samples and release pass', flush=True)
    assert source.read_bytes() == original
    result = dict(passed=True, cycles=rows, baseline_audio=baseline, cold_disk_audio=disk,
                  native_processes=10 if retry_result else 8, browser_result=report, retry=retry_result,
                  scope='Cold native validation of frozen browser crash recovery; physical power loss and device audio excluded')
    (work/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


if __name__ == '__main__':
    main()
