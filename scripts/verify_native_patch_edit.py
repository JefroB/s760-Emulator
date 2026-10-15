"""Firmware patch bend or performance part-level edit, Save/fresh Load acceptance.

User-supplied firmware and library media are immutable. Controls only; no guest
RAM/PC edits. Native headless functional evidence, not packaged/hardware parity.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import time

import numpy as np
from PIL import Image

from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--perform-level', action='store_true', help='Qualify performance part1 level127 to64 instead of patch bend')
    parser.add_argument('--partial-tune', action='store_true', help='Qualify Partial Common coarse tune0 to12 instead of patch bend')
    parser.add_argument('--sample-erase', action='store_true', help='Qualify whole-range Area Erase on sample1 and cold media persistence')
    options = parser.parse_args()
    if sum((options.perform_level, options.partial_tune, options.sample_erase)) > 1:
        parser.error('Choose one editing scenario')
    state = options.state_dir.resolve()
    if state.exists() and any(state.iterdir()):
        parser.error('Use a fresh private state directory')
    state.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'roms/FDD/ROBOFULL.IMG'
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert digest == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    working = state / 'working.img'; shutil.copyfile(source, working)
    saved = state / 'edited.img'
    cfg = RuntimeConfig(ROOT / 'mame-source/mames760.exe', ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
                        ROOT / 'roms/System/S760224.IMG', state / 'edit', working, sound=False, throttle=False)
    if options.sample_erase:
        cfg = replace(cfg, wave_dump=state / 'edited-wave.bin')
    report = {}

    def workflow(runtime, folder):
        def wait(seconds):
            until = runtime.request('status')[0]['seconds'] + seconds
            deadline = time.monotonic() + 60
            while runtime.request('status')[0]['seconds'] < until:
                assert time.monotonic() < deadline, 'Firmware stopped advancing'
                time.sleep(.01)

        def move(x, y):
            runtime.request('pointer', x=x, y=y); wait(.3)

        def click(x, y):
            move(x, y)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.3)

        def screenshot(name):
            Image.frombytes('RGBA', (640, 480), runtime.request('frames')[1][0][6:]).save(folder / name)

        def load():
            wait(20)
            runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
            runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
            click(118, 5); wait(2); click(80, 22); wait(8)
            click(50, 34); wait(2); click(76, 98); wait(35)
            click(10, 5); click(15, 22); wait(3)
            screenshot('loaded.png')

        def render(frames):
            blocks = []
            while frames:
                n = min(frames, 8192)
                _, pcm = runtime.render_audio(n)
                blocks.append(np.frombuffer(pcm, dtype='<f4').reshape(-1, 2)); frames -= n
            return np.concatenate(blocks)

        def audition(label):
            runtime.request('pause'); runtime.request('audio_capture', enabled=True)
            rows = []
            for name, bend in [('centre', 8192), ('up', 16383), ('down', 0)]:
                runtime.request('midi', bytes=[0xe0, bend & 127, bend >> 7])
                note = 21 if options.partial_tune or options.sample_erase else 60
                runtime.request('midi', bytes=[0x90, note, 100])
                render(16384)
                audio = render(44100)
                assert np.isfinite(audio).all() and np.max(np.abs(audio)) < 1
                if options.sample_erase and label != 'before':
                    assert np.max(np.abs(audio)) == 0, 'Erased sample still plays'
                else:
                    assert np.max(np.abs(audio)) > 0, 'Unexpected silent sample'
                spectrum = np.abs(np.fft.rfft(audio[:, 0] * np.hanning(len(audio))))
                frequency = int(np.argmax(spectrum)) if np.any(audio) else None
                runtime.request('midi', bytes=[0x80, note, 0])
                tail = render(88200)
                assert np.max(np.abs(tail[-44100:])) == 0, 'Edited patch failed to release'
                rows.append({'bend': name, 'frequency_hz': frequency, 'peak': float(np.max(np.abs(audio)))})
                np.save(folder / f'{label}-{name}.npy', audio)
            runtime.request('midi', bytes=[0xe0, 0, 64]); render(8192)
            runtime.request('audio_capture', enabled=False); runtime.request('resume')
            return rows
        return wait, move, click, screenshot, load, audition

    with NativeRuntime(cfg) as runtime:
        wait, move, click, screenshot, load, audition = workflow(runtime, cfg.state_dir)
        load()
        report['before'] = audition('before')
        assert len({row['frequency_hz'] for row in report['before']}) == 1, 'Fixture unexpectedly has bend enabled'
        if options.sample_erase:
            click(100, 5); wait(1); click(60, 62); wait(2)
            screenshot('before-edit.png')
            click(140, 98); wait(3)
        elif options.partial_tune:
            click(70, 5); wait(1); click(75, 22); wait(2)
            move(77, 46); screenshot('before-edit.png')
            for _ in range(12):
                runtime.request('dial', id='ALPHA', delta=1); wait(.1)
        elif options.perform_level:
            move(110, 30)
            screenshot('before-edit.png')
            for _ in range(63):
                runtime.request('dial', id='ALPHA', delta=-1); wait(.1)
        else:
            click(40, 5); wait(1); click(60, 39); wait(2)
            screenshot('before-edit.png')
            for y in (49, 44):
                move(77, y)
                for _ in range(12):
                    runtime.request('dial', id='ALPHA', delta=1); wait(.1)
        screenshot('after-edit.png')
        click(10, 5); click(15, 22); wait(2)
        report['edited'] = audition('edited')
        frequencies = [row['frequency_hz'] for row in report['edited']]
        if options.sample_erase:
            assert frequencies == [None] * 3, 'Area Erase failed to silence sample'
        elif options.partial_tune:
            assert len(set(frequencies)) == 1, 'Fixture unexpectedly responds to bend'
            ratio = frequencies[0] / report['before'][0]['frequency_hz']
            assert abs(ratio - 2) < .02, ('Coarse tune did not raise an octave', ratio)
            report['edited_frequency_ratio'] = ratio
        elif options.perform_level:
            assert abs(frequencies[0] - report['before'][0]['frequency_hz']) <= 1
            assert len(set(frequencies)) == 1, 'Part level edit changed pitch'
            ratio = report['edited'][0]['peak'] / report['before'][0]['peak']
            assert .05 < ratio < .8, ('Part level did not attenuate playback', ratio)
            report['edited_gain_ratio'] = ratio
        else:
            assert abs(frequencies[0] - report['before'][0]['frequency_hz']) <= 1
            assert 4000 < frequencies[1] < 4200 and 9900 < frequencies[2] < 10100, frequencies
        click(118, 5); wait(2); click(80, 30); wait(8)
        click(50, 34); wait(1); click(76, 98); wait(3)
        click(62, 70); wait(3); click(66, 70); wait(35)
        report['dirty'] = runtime.media_status()
        assert report['dirty']['dirty'] and not report['dirty']['busy']
        runtime.export_media(saved)
        assert not runtime.media_status()['dirty']
        screenshot('saved.png')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == digest
    assert hashlib.sha256(working.read_bytes()).hexdigest() == digest
    assert saved.read_bytes() != source.read_bytes()
    # A different native process has no shared runtime/NVRAM/checkpoint state.
    cold = replace(cfg, state_dir=state / 'reload', sample_disk=saved)
    if options.sample_erase:
        cold = replace(cold, wave_dump=state / 'reloaded-wave.bin')
    with NativeRuntime(cold) as runtime:
        wait, move, click, screenshot, load, audition = workflow(runtime, cold.state_dir)
        load()
        report['reloaded'] = audition('reloaded')
    for edited, reloaded in zip(report['edited'], report['reloaded']):
        assert edited['frequency_hz'] == reloaded['frequency_hz'], 'Patch edit did not survive fresh firmware Load'
        assert abs(edited['peak'] - reloaded['peak']) < 1e-6
    if options.sample_erase:
        source_bytes = source.read_bytes()
        edited_wave = (state / 'edited-wave.bin').read_bytes()
        reloaded_wave = (state / 'reloaded-wave.bin').read_bytes()
        assert source_bytes[0x2ac00:0x2cc00] != bytes(8192)
        # Area Erase compacts other samples down and appends the replacement
        # allocation. Fresh firmware Load puts sample1 first again.
        edited_offset = 16 + 12 * 9216
        assert edited_wave[edited_offset:edited_offset + 8192] == bytes(8192), 'Erase did not zero the4096-frame source body'
        assert edited_wave[edited_offset:edited_offset + 9216] == reloaded_wave[16:16 + 9216], 'Erased sample allocation changed on cold Load'
        for sample in range(1, 13):
            expected = source_bytes[0x2ac00 + sample * 9216:0x2ac00 + (sample + 1) * 9216]
            offset = 16 + sample * 9216
            compacted = 16 + (sample - 1) * 9216
            assert edited_wave[compacted:compacted + 9216] == expected, 'Erase changed a neighboring sample'
            assert reloaded_wave[offset:offset + 9216] == expected, 'Cold Load changed a neighboring sample'
        report['sample_data'] = {'zero_source_body_bytes': 8192, 'exact_cold_allocation_bytes': 9216,
                                 'unchanged_neighbor_sample_bytes': 12 * 9216,
                                 'edited_wave_offset': edited_offset, 'cold_wave_offset': 16,
                                 'edited_allocation_sha256': hashlib.sha256(edited_wave[edited_offset:edited_offset + 9216]).hexdigest()}
    elif options.perform_level:
        before = Image.open(cfg.state_dir / 'before-edit.png').crop((416, 112, 472, 128)).tobytes()
        edited = Image.open(cfg.state_dir / 'after-edit.png').crop((416, 112, 472, 128)).tobytes()
        # The pointer highlight differs on fresh Load; audio above is the
        # persistence assertion. Screen before/after still proves a field edit.
        assert before != edited, 'Performance field pixels did not change'
    report.update(passed=True, source_sha256=digest, saved_sha256=hashlib.sha256(saved.read_bytes()).hexdigest(),
                  scope=('Sample1 whole-range Area Erase' if options.sample_erase else
                         'Partial Common coarse tune0 to12' if options.partial_tune else
                         'Performance part1 level127 to64' if options.perform_level else 'Patch Bend Up/Down0 to12')
                        + ' via firmware controls; original-firmware Save/export/fresh Load and measured audio',
                  limits='One named operation; not arbitrary edits, hardware or packaged-interface acceptance')
    filename = ('sample-erase-results.json' if options.sample_erase else
                'partial-edit-results.json' if options.partial_tune else
                'perform-edit-results.json' if options.perform_level else 'patch-edit-results.json')
    (state / filename).write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
