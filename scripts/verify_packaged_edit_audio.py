"""Cold native PCM checks of media exported by packaged-editing.spec.ts.

This is native verification of packaged UI output, not physical/device audio.
Supply the same package used by the browser test and its private result folder.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def measure(package, disk, state, note, checkpoint=None, experimental_adc=False):
    cfg = RuntimeConfig(package / 'mame-source/mames760.exe',
                        ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
                        ROOT / 'roms/System/S760224.IMG', state, disk,
                        sound=False, throttle=False, experimental_adc=experimental_adc)
    with NativeRuntime(cfg) as runtime:
        def wait(seconds):
            target = runtime.request('status')[0]['seconds'] + seconds
            deadline = time.monotonic() + 60
            while runtime.request('status')[0]['seconds'] < target:
                assert time.monotonic() < deadline, 'Firmware stopped advancing'
                time.sleep(.01)

        def click(x, y):
            runtime.request('pointer', x=x, y=y); wait(.3)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.3)

        if checkpoint is None:
            wait(20)
            runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
            runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
            click(118, 5); wait(2); click(80, 22); wait(8)
            click(50, 34); wait(2); click(76, 98); wait(35)
        else:
            runtime.request('pause'); runtime.load_checkpoint(checkpoint); runtime.request('resume')
        click(10, 5); click(15, 22); wait(3)
        runtime.request('pause'); runtime.request('audio_capture', enabled=True)

        def render(frames):
            blocks = []
            while frames:
                count = min(frames, 8192)
                _, pcm = runtime.render_audio(count)
                blocks.append(np.frombuffer(pcm, dtype='<f4').reshape(-1, 2))
                frames -= count
            return np.concatenate(blocks)

        rows = []
        for name, bend in [('centre', 8192), ('up', 16383), ('down', 0)]:
            runtime.request('midi', bytes=[0xe0, bend & 127, bend >> 7])
            runtime.request('midi', bytes=[0x90, note, 100]); render(16384)
            audio = render(44100)
            assert np.isfinite(audio).all() and np.max(np.abs(audio)) < 1
            peak = float(np.max(np.abs(audio)))
            frequency = int(np.argmax(np.abs(np.fft.rfft(audio[:, 0] * np.hanning(len(audio)))))) if peak else None
            runtime.request('midi', bytes=[0x80, note, 0])
            tail = render(88200)
            assert np.max(np.abs(tail[-44100:])) == 0, 'Note failed to release'
            rows.append({'bend': name, 'frequency_hz': frequency, 'peak': peak, 'silent_release': True})
        return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--browser-work', type=Path, required=True)
    parser.add_argument('--erase-work', type=Path, help='Optional erase case directory from a targeted rerun')
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--require-webview', action='store_true', help='Reject fixtures produced in an external browser')
    args = parser.parse_args()
    assert (args.package / 'scripts/s760_runtime.lua').read_bytes() == (ROOT / 'scripts/s760_runtime.lua').read_bytes(), 'Package/source Lua differ'
    assert not args.state_dir.exists(), 'Use a fresh private state directory'
    args.state_dir.mkdir(parents=True)
    source = ROOT / 'roms/FDD/ROBOFULL.IMG'
    original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    assert original_hash == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    report = {'baseline60': measure(args.package, source, args.state_dir / 'baseline60', 60),
              'baseline21': measure(args.package, source, args.state_dir / 'baseline21', 21)}
    for scenario in ('perform', 'patch', 'partial', 'erase'):
        folder = args.erase_work if scenario == 'erase' and args.erase_work else args.browser_work / scenario
        evidence = json.loads((folder / 'result.json').read_text())
        assert evidence['passed'] and evidence['scenario'] == scenario
        if args.require_webview:
            assert evidence.get('interface') == 'Packaged WebView2', 'Actual desktop WebView2 evidence required'
            assert len(evidence.get('renderers', [])) == 2, 'Both edit and cold-launch renderer identities required'
        disk = folder / 'library/EDITED.IMG'
        assert hashlib.sha256(disk.read_bytes()).hexdigest() == evidence['saved_sha256']
        rows = measure(args.package, disk, args.state_dir / scenario, 21 if scenario in ('partial', 'erase') else 60)
        frequencies = [row['frequency_hz'] for row in rows]
        if scenario == 'erase':
            assert frequencies == [None] * 3 and all(row['peak'] == 0 for row in rows)
        elif scenario == 'partial':
            assert len(set(frequencies)) == 1
            assert abs(frequencies[0] / report['baseline21'][0]['frequency_hz'] - 2) < .02
        elif scenario == 'patch':
            assert abs(frequencies[0] - report['baseline60'][0]['frequency_hz']) <= 1
            assert 4000 < frequencies[1] < 4200 and 9900 < frequencies[2] < 10100
        else:
            assert len(set(frequencies)) == 1 and frequencies[0] == report['baseline60'][0]['frequency_hz']
            assert .05 < rows[0]['peak'] / report['baseline60'][0]['peak'] < .8
        report[scenario] = rows
        recalled = measure(args.package, disk, args.state_dir / (scenario + '-session'),
                           21 if scenario in ('partial', 'erase') else 60,
                           folder / 'edit/sessions/latest.s760state')
        for cold, saved in zip(rows, recalled):
            assert cold['frequency_hz'] == saved['frequency_hz']
            assert abs(cold['peak'] - saved['peak']) < 1e-6
        report[scenario + '_session'] = recalled
    assert hashlib.sha256(source.read_bytes()).hexdigest() == original_hash
    report.update(passed=True, required_interface='Packaged WebView2' if args.require_webview else 'Packaged browser',
                  scope='Cold native PCM from packaged-interface exported media and sessions; no physical audio or clean-machine claim')
    (args.state_dir / 'results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
