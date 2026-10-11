"""Native firmware Save/export/reload acceptance using a private ROBOFULL copy.

Requires local MAME/firmware/ROBOFULL. Leaves originals untouched. This validates
the supported save path, not formatting, write protection or SCSI persistence.
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', action='store_true', help='Verify dirty-controller state in a fresh process')
    args = parser.parse_args()
    work = ROOT / 'docs/ic20-hle-findings/chatGPT-work' / ('media-verification-' + time.strftime('%Y%m%d-%H%M%S'))
    work.mkdir(parents=True)
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
        click(118, 5); wait(2); click(80, 30); wait(8)
        click(50, 34); wait(1); click(76, 98); wait(3)
        click(62, 70); wait(3); click(66, 70); wait(35)
        dirty = runtime.media_status()
        assert dirty['dirty'] and not dirty['busy'], dirty
        if args.checkpoint:
            runtime.request('pause')
            runtime.save_checkpoint(work/'dirty.s760state')
            with NativeRuntime(replace(cfg, state_dir=work/'checkpoint-restart', sample_disk=None, wave_dump=None)) as restored:
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
              'original_preserved': True, 'dirty_media_protection': True,
              'before_export': dirty, 'after_export': clean,
              'fresh_machine_audio': json.loads((work / 'reload/result.json').read_text())}
    result['dirty_checkpoint_cold_restore'] = args.checkpoint
    (work / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    print(f'Evidence: {work}')


if __name__ == '__main__':
    main()
