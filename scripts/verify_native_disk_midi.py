"""Original-firmware floppy Load under scheduled MIDI, plus post-load release.

No guest memory/PC writes. Read-only wave dump is compared with known fixture
payloads after clean shutdown. This does not infer firmware MIDI acceptance from
serial delivery or claim exact IC4 arbitration.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np
from PIL import Image

from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    state = args.state_dir.resolve()
    if state.exists() and any(state.iterdir()):
        parser.error('Use a fresh private state directory')
    disk = ROOT / 'roms/FDD/ROBOFULL.IMG'
    original = hashlib.sha256(disk.read_bytes()).hexdigest()
    assert original == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    cfg = RuntimeConfig(ROOT / 'mame-source/mames760.exe', ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
                        ROOT / 'roms/System/S760224.IMG', state, disk,
                        sound=False, throttle=False, wave_dump=state / 'wave.bin')
    report = {'passed': False, 'scope': 'Native firmware Load under MIDI and post-load recovery; no hardware parity'}
    with NativeRuntime(cfg) as runtime:
        def wait(seconds):
            until = runtime.request('status')[0]['seconds'] + seconds
            deadline = time.monotonic() + 60
            while runtime.request('status')[0]['seconds'] < until:
                assert time.monotonic() < deadline, 'Native firmware stopped advancing'
                time.sleep(.01)

        def click(x, y):
            runtime.request('pointer', x=x, y=y); wait(.2)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.2)

        def burst():
            runtime.request('pause')
            runtime.request('bus_trace', enabled=True, first=0x102000, last=0x102003)
            start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 2048
            events = []
            for i in range(120):
                note = 48 + i % 32
                sample = start + (i // 12) * 88200 + (i % 12) * 64
                events.extend([{'sample': sample, 'bytes': [0x90, note, 100]},
                               {'sample': sample + 44100, 'bytes': [0x80, note, 0]}])
            events.sort(key=lambda e: e['sample'])
            runtime.schedule_midi(events)
            runtime.request('resume')
            return events

        wait(20)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
        click(118, 5); wait(2); click(80, 22); wait(8)
        click(50, 34); wait(2)
        events = burst()
        load_start = runtime.request('status')[0]['seconds']
        click(76, 98); wait(35)
        status = runtime.request('status')[0]
        assert status['midi_pending'] == 0 and status['midi_error'] == '', status
        assert len(status['midi_delivered']) == len(events), 'Serial schedule incomplete'
        assert [x['sample'] for x in status['midi_delivered']] == [x['sample'] for x in events]
        runtime.request('pause')
        trace = runtime.request('bus_trace', enabled=False)[0]
        first, last = (status['midi_delivered'][i]['seconds'] for i in (0, -1))
        overlap = [row for row in trace['rows'] if row['address'] == 0x102002
                   and row['kind'] == 'w' and first <= row['seconds'] <= last]
        assert overlap, 'No observed FDC commands during the MIDI schedule'
        report['fdc_trace'] = trace
        report['observed_overlapping_fdc_writes'] = len(overlap)
        report['serial_delivered'] = status['midi_delivered']
        runtime.request('resume')
        report['load_serial_events'] = len(events)
        report['load_emulated_interval'] = [load_start, status['seconds']]
        Image.frombytes('RGBA', (640, 480), runtime.request('frames')[1][0][6:]).save(state / 'loaded.png')
        click(10, 5); click(15, 22); wait(3)
        # Notes during Load may be suppressed by the firmware. Explicitly release
        # them before checking that ordinary post-load playback remains usable.
        for note in range(48, 80):
            runtime.request('midi', bytes=[0x80, note, 0])
        wait(2)
        runtime.request('pause')
        runtime.request('audio_capture', enabled=True)
        now = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 2048
        runtime.schedule_midi([{'sample': now, 'bytes': [0x90, 60, 100]},
                               {'sample': now + 44100, 'bytes': [0x80, 60, 0]}])
        blocks = []
        remaining = 3 * 44100
        while remaining:
            n = min(8192, remaining)
            _, pcm = runtime.render_audio(n); blocks.append(pcm); remaining -= n
        audio = np.frombuffer(b''.join(blocks), dtype='<f4').reshape(-1, 2)
        assert np.isfinite(audio).all() and 0 < np.max(np.abs(audio)) < 1
        assert np.max(np.abs(audio[-44100:])) == 0, 'Post-load note did not release'
        report['post_load_peak'] = float(np.max(np.abs(audio)))
        report['post_load_silent_tail_frames'] = 44100
        runtime.request('resume')
        report['media'] = runtime.media_status()
        assert not report['media']['busy'] and not report['media']['dirty']
    wave = (state / 'wave.bin').read_bytes()
    source = disk.read_bytes()
    rows = []
    for sample in range(13):
        expected = source[0x2ac00 + sample * 0x2400:0x2ac00 + (sample + 1) * 0x2400]
        offset = 16 + sample * 0x2400
        assert wave[offset:offset + len(expected)] == expected, f'Loaded payload {sample} differs'
        rows.append({'sample': sample, 'wave_offset': offset, 'bytes': len(expected),
                     'sha256': hashlib.sha256(expected).hexdigest()})
    assert hashlib.sha256(disk.read_bytes()).hexdigest() == original
    report.update(passed=True, sample_payloads=rows, exact_sample_bytes=119808,
                  limits='Serial delivery is not guest MIDI handling; no proven simultaneous voice completions during Load, disk Save overlap or exact IC4 priority')
    (state / 'disk-midi-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
