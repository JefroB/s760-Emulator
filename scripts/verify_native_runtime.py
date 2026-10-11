"""Explicit live-machine regression (requires local firmware and ROBOFULL.IMG).

Run from the repository root. Artifacts stay in the assigned local work folder.
This exercises physical input ports and MIDI serialization; never patches RAM.
"""
import json
import argparse
from pathlib import Path
import time
import wave
import math

import numpy as np
from PIL import Image
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sample-disk', type=Path, default=ROOT / 'roms/FDD/ROBOFULL.IMG')
    parser.add_argument('--state-dir', type=Path, default=ROOT / 'docs/ic20-hle-findings/chatGPT-work/native-runtime-verification')
    parser.add_argument('--wave-dump', type=Path, help='Read-only wave RAM dump for persistence verification')
    parser.add_argument('--runtime-contract', action='store_true', help='Verify pause/step and live PCM against MAME WAV')
    parser.add_argument('--pull-render', action='store_true', help='Verify demand-driven variable PCM block sizes')
    parser.add_argument('--scheduled-midi', action='store_true', help='Verify emulated-time MIDI scheduling with pull rendering')
    parser.add_argument('--executable', type=Path, default=ROOT/'mame-source/mames760.exe', help='Exact native binary to qualify')
    args = parser.parse_args()
    if args.scheduled_midi and not args.pull_render:
        parser.error('--scheduled-midi requires --pull-render')
    state = args.state_dir
    cfg = RuntimeConfig(args.executable, ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT / 'roms/System/S760224.IMG', state, args.sample_disk,
        sound=False, throttle=False, wav_output=state / 'audio.wav', wave_dump=args.wave_dump)
    with NativeRuntime(cfg) as runtime:
        captured = []
        capture_active = False
        captured_frames = 0
        def drain():
            nonlocal captured_frames
            meta, data = runtime.read_audio()
            assert meta['dropped_frames'] == 0, meta
            assert meta['first_sample'] == captured_frames, meta
            captured_frames += meta['frames']
            captured.append(data)

        def wait(seconds):
            target = runtime.request('frames')[0]['seconds'] + seconds
            deadline = time.monotonic() + 30
            while runtime.request('frames')[0]['seconds'] < target:
                if time.monotonic() > deadline:
                    raise TimeoutError('Machine stopped advancing')
                if capture_active: drain()
                time.sleep(.01)

        def move(x, y):
            runtime.request('pointer', x=x, y=y)
            wait(.2)

        def click():
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True)
            wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False)
            wait(.2)

        wait(20)
        if args.runtime_contract:
            paused = runtime.request('pause')[0]['seconds']
            time.sleep(.15)
            assert runtime.request('status')[0]['seconds'] == paused
            stepped = runtime.request('step')[0]['seconds']
            assert 0 < stepped - paused < .025, (paused, stepped)
            assert runtime.request('status')[0]['state'] == 'paused'
            runtime.request('resume')
        _, frames = runtime.request('frames')
        assert any(frames[0][6:][0::4]), 'Boot produced no coloured pixels'
        # Long movement must not wrap the signed mouse packet.
        move(150, 60)
        cursor = runtime.request('frames')[0]['cursor']
        assert cursor == [300, 120], f'Incorrect firmware mouse position: {cursor}'
        move(10, 5)
        assert runtime.request('frames')[0]['cursor'] == [20, 10]
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
        move(118, 5); click(); wait(2)  # Disk menu
        move(80, 22); click(); wait(8)  # Load, including physical directory reads
        move(50, 34); click(); wait(2)  # Mark performance
        move(76, 98); click(); wait(35) # Load samples through firmware/FDC
        _, frames = runtime.request('frames')
        Image.frombytes('RGBA', (640, 480), frames[0][6:]).save(state / 'loaded.png')
        move(10, 5); click(); move(15, 22); click(); wait(3)
        start = runtime.request('frames')[0]['seconds']
        if args.runtime_contract:
            runtime.request('audio_capture', enabled=True)
            capture_active = True
        runtime.request('midi', bytes=[0x90, 60, 127]); wait(2)
        release = runtime.request('frames')[0]['seconds']
        runtime.request('midi', bytes=[0x80, 60, 0]); wait(2)
        end = runtime.request('frames')[0]['seconds']
        if capture_active:
            drain()
            capture_active = False
            runtime.request('audio_capture', enabled=False)
            runtime.request('audio_capture', enabled=True)
            wait(2)
            overflow, _ = runtime.read_audio()
            assert overflow['dropped_frames'] > 0 and 0 < overflow['frames'] <= 44100
            runtime.request('audio_capture', enabled=False)
        if args.pull_render:
            pull_start = runtime.request('pause')[0]['seconds']
            runtime.request('audio_capture', enabled=True)
            if args.scheduled_midi:
                first = math.ceil(pull_start*44100)+1000
                events = [{'sample': first, 'bytes': [0x90,60,127]},
                          {'sample': first+44100, 'bytes': [0x80,60,0]}]
                for bad in ([{'sample': first-44100, 'bytes': [0x90,60,127]}],
                            list(reversed(events)), [{'sample': first, 'bytes': [256]}]):
                    try:
                        runtime.schedule_midi(bad)
                    except RuntimeError:
                        pass
                    else:
                        raise AssertionError('Invalid MIDI schedule accepted')
                    assert runtime.request('status')[0]['midi_pending'] == 0
                assert runtime.schedule_midi(events) == 2
                assert runtime.request('status')[0]['midi_pending'] == 2
            else:
                runtime.request('midi', bytes=[0x90, 60, 127])
            pulled, position = [], 0
            sizes = [1, 63, 127, 256, 511, 1024, 4096, 8192] * 4
            for count in sizes:
                meta, data = runtime.render_audio(count)
                assert meta['frames'] == count and len(data) == count*8
                assert meta['first_sample'] == position and meta['dropped_frames'] == 0
                position += count
                pulled.append(data)
                status = runtime.request('status')[0]
                assert status['state'] == 'paused'
            frozen = runtime.request('status')[0]['seconds']
            time.sleep(.1)
            assert runtime.request('status')[0]['seconds'] == frozen
            if not args.scheduled_midi:
                runtime.request('midi', bytes=[0x80, 60, 0])
            for _ in range(8):
                meta, data = runtime.render_audio(8192)
                assert meta['first_sample'] == position and meta['dropped_frames'] == 0
                position += 8192
                pulled.append(data)
            runtime.request('audio_capture', enabled=False)
            if args.scheduled_midi:
                midi_status = runtime.request('status')[0]
                assert midi_status['midi_pending'] == 0 and midi_status['midi_error'] == ''
                assert len(midi_status['midi_delivered']) == 2
                for actual, expected in zip(midi_status['midi_delivered'], events):
                    assert actual['sample'] == expected['sample']
                    assert abs(actual['seconds']*44100-expected['sample']) < .001
            runtime.request('resume')
            wait(.25)  # Flush the independent WAV writer beyond the capture tail.
    with wave.open(str(state / 'audio.wav')) as recording:
        rate, channels = recording.getframerate(), recording.getnchannels()
        pcm = np.frombuffer(recording.readframes(recording.getnframes()), dtype='<i2').reshape(-1, channels)
    held = pcm[int((start + .3) * rate):int((release - .1) * rate)].astype(float)
    tail = pcm[int((end - .5) * rate):int((end - .1) * rate)].astype(float)
    assert np.max(np.abs(held)) > 100, 'Live MIDI did not produce native audio'
    assert np.max(np.abs(tail)) == 0, 'Note-off left a sounding voice'
    result = {'native_boot_frames': True, 'long_mouse_jump': cursor, 'midi_note': 60,
              'held_peak_pcm16': float(np.max(np.abs(held))), 'release_tail_peak_pcm16': 0,
              'sample_rate': rate, 'note_start': start, 'note_release': release,
              'process_shutdown': 'clean'}
    if args.pull_render:
        from scipy.signal import correlate
        pull = np.frombuffer(b''.join(pulled), dtype='<f4').reshape(-1, 2)
        (state / 'pull.f32').write_bytes(pull.tobytes())
        assert np.isfinite(pull).all() and np.max(np.abs(pull[-10000:])) == 0
        segment = pull[10000:20000].astype(float)*32768
        base = int((pull_start-.1)*rate)
        reference = pcm[base:].astype(float)
        offset = int(np.argmax(correlate(reference[:,0], pull[:,0], mode='valid', method='fft')))
        origin = base+offset
        aligned = pcm[origin:origin+len(pull)].astype(float)
        assert aligned.shape == pull.shape
        error = float(np.max(np.abs(aligned-pull.astype(float)*32768)))
        assert np.max(np.abs(segment)) > 100 and error <= 2, error
        result['pull_render'] = {'sizes': sorted(set(sizes)), 'frames': len(pull),
            'wav_max_error_pcm16': error, 'dropped_frames': 0,
            'paused_between_requests': True, 'release_tail_silent': True}
        if args.scheduled_midi:
            result['scheduled_midi'] = midi_status['midi_delivered']
    if args.runtime_contract:
        from scipy.signal import correlate
        live = np.frombuffer(b''.join(captured), dtype='<f4').reshape(-1, 2)
        assert np.isfinite(live).all() and len(live) > rate * 3
        # Align a held segment against MAME's independently recorded WAV.
        # The capture subscription can begin between sound update boundaries.
        segment = live[rate//2:rate, 0].astype(float) * 32768
        reference = pcm[int(start*rate):int((release+.1)*rate), 0].astype(float)
        offset = int(np.argmax(correlate(reference, segment, mode='valid', method='fft')))
        aligned = pcm[int(start*rate)+offset:int(start*rate)+offset+len(segment)].astype(float)
        error = aligned - live[rate//2:rate].astype(float) * 32768
        assert np.max(np.abs(error)) <= 2, float(np.max(np.abs(error)))
        assert np.max(np.abs(live[-rate//2:])) == 0
        result['runtime_contract'] = {'pause_freezes_time': True,
            'step_seconds': stepped-paused, 'pcm_frames': len(live),
            'pcm_dropped_frames': 0, 'overflow_reported_frames': overflow['dropped_frames'],
            'pcm_wav_max_error_pcm16': float(np.max(np.abs(error)))}
    (state / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
