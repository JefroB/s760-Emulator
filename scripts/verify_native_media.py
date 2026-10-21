"""Native firmware Save/export/reload acceptance using a private ROBOFULL copy.

Requires local MAME/firmware/ROBOFULL. Leaves originals untouched. This validates
the supported save path, optional 720KB formatting and write protection, not SCSI persistence.
"""
import hashlib
import argparse
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from PIL import Image
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_wave_records(before, after):
    """Report every changed byte; do not treat a disk Load as a full session restore."""
    import numpy as np
    if len(before) != len(after):
        raise AssertionError('Wave RAM size changed across media reload')
    changed = np.flatnonzero(np.frombuffer(before, dtype='u1') != np.frombuffer(after, dtype='u1'))
    groups = np.split(changed, np.flatnonzero(np.diff(changed) > 1) + 1) if len(changed) else []
    return {'bytes': len(before), 'equal': not len(changed), 'changed_bytes': len(changed),
            'before_sha256': hashlib.sha256(before).hexdigest(), 'after_sha256': hashlib.sha256(after).hexdigest(),
            'ranges': [{'first': int(g[0]), 'last_exclusive': int(g[-1]) + 1,
                        'before_hex': before[int(g[0]):int(g[-1]) + 1].hex(),
                        'after_hex': after[int(g[0]):int(g[-1]) + 1].hex()} for g in groups]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, help='Fresh private absolute output directory')
    parser.add_argument('--checkpoint', action='store_true', help='Verify dirty-controller state in a fresh process')
    parser.add_argument('--write-protect', action='store_true', help='Verify firmware protected Save, exact unchanged media and cold protection recall')
    parser.add_argument('--format', action='store_true', help='Format private loaded media through firmware before Save/export/reload')
    args = parser.parse_args()
    if args.format and args.write_protect:
        parser.error('Run formatting and write-protection workflows separately')
    work = args.state_dir.resolve() if args.state_dir else ROOT / 'temp/work' / ('media-verification-' + time.strftime('%Y%m%d-%H%M%S'))
    if work.exists() and any(work.iterdir()):parser.error('Use a fresh private state directory')
    work.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'roms/FDD/ROBOFULL.IMG'
    original = digest(source)
    assert original == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae', 'Unexpected ROBOFULL fixture'
    disk = work / 'working.img'
    shutil.copyfile(source, disk)
    cfg = RuntimeConfig(ROOT / 'mame-source/mames760.exe', ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
                        ROOT / 'roms/System/S760224.IMG', work, disk, sound=False, throttle=False,
                        wave_dump=work / 'before-wave.bin')
    saved = work / 'saved.img'
    with NativeRuntime(cfg) as runtime:
        def wait(seconds):
            until = runtime.request('frames')[0]['seconds'] + seconds
            deadline = time.monotonic() + 60
            while runtime.request('frames')[0]['seconds'] < until:
                if time.monotonic() > deadline: raise TimeoutError('Native machine stopped advancing')
                time.sleep(.01)

        def click(x, y):
            runtime.request('pointer', x=x, y=y); wait(.2)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.2)

        wait(20)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
        click(118, 5); wait(2); click(80, 22); wait(8)
        click(50, 34); wait(2); click(76, 98); wait(35)
        if args.format:
            runtime.set_media_write_protect(True)
            click(118,5);wait(2);click(80,54);wait(3)
            click(76,98);wait(2);click(66,70);wait(10)
            protected_format_status = runtime.media_status()
            assert protected_format_status['writeProtected'] and not protected_format_status['dirty'] and not protected_format_status['busy']
            runtime.export_media(work/'protected-format.img')
            assert digest(work/'protected-format.img') == original, 'Protected Format changed media'
            Image.frombytes('RGBA',(640,480),runtime.request('frames')[1][0][6:]).save(work/'protected-format.png')
            runtime.set_media_write_protect(False)
            click(80,70);wait(1)
            click(76,98);wait(2);click(66,70);wait(100)
            formatted_status = runtime.media_status()
            assert formatted_status['dirty'] and not formatted_status['busy'], formatted_status
            assert formatted_status['revision'] == 161, formatted_status
            if args.checkpoint:
                runtime.request('pause');runtime.save_checkpoint(work/'formatted.s760state')
                with NativeRuntime(replace(cfg,state_dir=work/'format-restart',sample_disk=None,wave_dump=None)) as restored_format:
                    restored_format.request('pause');restored_format.load_checkpoint(work/'formatted.s760state');restored_format.request('resume')
                    recalled_format = restored_format.media_status()
                    assert recalled_format['dirty'] and recalled_format['revision'] == formatted_status['revision']
                    restored_format.export_media(work/'format-checkpoint-export.img')
                runtime.request('resume')
            runtime.export_media(work/'formatted.img')
            if args.checkpoint:
                assert digest(work/'formatted.img') == digest(work/'format-checkpoint-export.img')
            formatted = (work/'formatted.img').read_bytes()
            assert formatted[4096:] == b'\x0f' * (len(formatted)-4096), 'Format did not fill every sample/data sector'
            Image.frombytes('RGBA',(640,480),runtime.request('frames')[1][0][6:]).save(work/'formatted.png')
            click(10,5);click(15,22);wait(2)
        if args.write_protect:
            assert runtime.set_media_write_protect(True)['writeProtected'] is True
            runtime.request('pause')
            runtime.save_checkpoint(work/'protected.s760state')
            with NativeRuntime(replace(cfg, state_dir=work/'protected-restart', sample_disk=None, wave_dump=None)) as protected:
                protected.request('pause'); protected.load_checkpoint(work/'protected.s760state'); protected.request('resume')
                assert protected.media_status()['writeProtected'] is True
            runtime.request('resume')
            click(118, 5); wait(2); click(80, 30); wait(8)
            click(50, 34); wait(1); click(76, 98); wait(3)
            click(62, 70); wait(3); click(66, 70); wait(15)
            protected_status = runtime.media_status()
            assert protected_status['writeProtected'] and not protected_status['dirty'] and not protected_status['busy'], protected_status
            runtime.export_media(work/'protected-export.img')
            assert digest(work/'protected-export.img') == original, 'Protected firmware Save changed controller bytes'
            protected_frame = Image.frombytes('RGBA', (640,480), runtime.request('frames')[1][0][6:])
            protected_frame.save(work/'protected-save.png')
            error_pixels = hashlib.sha256(protected_frame.convert('RGB').crop((180,156,440,180)).tobytes()).hexdigest()
            assert error_pixels == '57900bf239f4830117f71695bb0888a46a9cbc5d9d1e45fdc523cbe29c6f960a', 'Firmware Write Protected error missing'
            assert runtime.set_media_write_protect(False)['writeProtected'] is False
            click(80,70); wait(1) # Dismiss the firmware Write Protected error.
            click(10,5); click(15,22); wait(2)
        click(118, 5); wait(2); click(80, 30); wait(8)
        click(50, 34); wait(1); click(76, 98); wait(3)
        click(62, 70); wait(3); click(66, 70); wait(35)
        dirty = runtime.media_status()
        assert dirty['dirty'] and not dirty['busy'], dirty
        if args.checkpoint:
            runtime.request('pause')
            runtime.save_checkpoint(work/'dirty.s760state')
            with NativeRuntime(replace(cfg, state_dir=work/'checkpoint-restart', sample_disk=None, wave_dump=work/'checkpoint-wave.bin')) as restored:
                restored.request('pause')
                restored.load_checkpoint(work/'dirty.s760state')
                restored.request('resume')
                restored_dirty = restored.media_status()
                assert restored_dirty['dirty'] and restored_dirty['revision'] == dirty['revision']
                try:
                    restored.eject_media()
                except RuntimeError:
                    pass
                else:
                    raise AssertionError('Restored dirty disk could be ejected')
                restored.export_media(work/'checkpoint-export.img')
                assert not restored.media_status()['dirty']
            runtime.request('resume')
        for change in (lambda: runtime.insert_media(source), runtime.eject_media):
            try:
                change()
            except RuntimeError:
                pass
            else:
                raise AssertionError('Dirty media change was accepted')
        runtime.export_media(saved)
        clean = runtime.media_status()
        assert not clean['dirty'], clean
        assert runtime.eject_media()['inserted'] is False
        assert runtime.insert_media(saved)['inserted'] is True
        Image.frombytes('RGBA', (640, 480), runtime.request('frames')[1][0][6:]).save(work / 'saved-screen.png')
    assert digest(source) == original, 'Original library image changed'
    assert digest(disk) == original, 'Working input file was overwritten implicitly'
    assert digest(saved) != original, 'No firmware disk changes were exported'
    if args.checkpoint:
        assert digest(saved) == digest(work/'checkpoint-export.img'), 'Restored controller media differs'
    subprocess.run([sys.executable, str(ROOT / 'scripts/verify_native_runtime.py'),
                    '--sample-disk', str(saved), '--state-dir', str(work / 'reload'),
                    '--wave-dump', str(work / 'after-wave.bin')], check=True)
    before = (work / 'before-wave.bin').read_bytes()
    after = (work / 'after-wave.bin').read_bytes()
    full_wave = compare_wave_records(before, after)
    if args.checkpoint:
        checkpoint_wave = (work / 'checkpoint-wave.bin').read_bytes()
        assert before == checkpoint_wave, 'Full-session checkpoint changed wave RAM metadata or samples'
    source_bytes = source.read_bytes()
    samples = []
    # Fixture123 has13 generated9216-byte payloads used by all88 MIDI keys.
    # High wave memory also contains OS records that change on Save/reload;
    # compare independently known sample bytes, not those unrelated records.
    for sample in range(13):
        start = 0x2ac00 + sample * 0x2400
        expected = source_bytes[start:start + 0x2400]
        offset = 16 + sample * 0x2400
        assert before[offset:offset + len(expected)] == expected, f'Original sample {sample} differs from fixture'
        assert after[offset:offset + len(expected)] == expected, f'Reloaded sample {sample} changed'
        samples.append({'sample': sample, 'wave_offset': offset, 'bytes': len(expected), 'sha256': hashlib.sha256(expected).hexdigest()})
    result = {'source_sha256': original, 'saved_sha256': digest(saved),
              'sample_payloads': samples, 'sample_bytes_compared': sum(s['bytes'] for s in samples),
              'whole_wave_ram_equal': before == after,
              'whole_wave_comparison': full_wave,
              'checkpoint_whole_wave_exact': args.checkpoint,
              'comparison_contract': 'Media reload preserves the saved samples/program, not unrelated RAM/catalog state; checkpoint restore preserves full wave RAM.',
              'original_preserved': True, 'dirty_media_protection': True,
              'before_export': dirty, 'after_export': clean,
              'fresh_machine_audio': json.loads((work / 'reload/result.json').read_text())}
    result['dirty_checkpoint_cold_restore'] = args.checkpoint
    result['protected_save_unchanged_and_cold_recall'] = args.write_protect
    result['firmware_format_save_fresh_reload'] = args.format
    if args.format:
        result['formatted_status'] = formatted_status
        result['formatted_sha256'] = digest(work/'formatted.img')
        result['format_fill_bytes_compared'] = len(formatted)-4096
        result['protected_format_unchanged'] = True
        result['formatted_dirty_cold_recall'] = args.checkpoint
    if args.write_protect:
        result['protected_save_status'] = protected_status
        result['protected_export_sha256'] = digest(work/'protected-export.img')
        result['write_protected_error_rgb_region'] = [180,156,440,180]
        result['write_protected_error_rgb_sha256'] = error_pixels
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, indent=2))
    print(f'Evidence: {work}')


if __name__ == '__main__':
    main()
