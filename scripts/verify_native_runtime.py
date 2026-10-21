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
import hashlib

import numpy as np
from PIL import Image
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--loop-modes', action='store_true', help='Verify seven ROBOLOOP modes through firmware playback')
    parser.add_argument('--loop-stress', action='store_true', help='With --loop-modes, overlap/retrigger all modes and verify exact checkpoint replay and release')
    parser.add_argument('--polyphony', action='store_true', help='Verify firmware allocation/stealing/retrigger/sustain with ROBOFULL')
    parser.add_argument('--pitch-loops', action='store_true', help='Build/load a private 21-note ROBOLOOP-derived octave fixture and qualify pitch transitions')
    parser.add_argument('--combined-audio', action='store_true', help='Qualify explicit diagnostic filter/stereo/envelope/interpolation profile on ROBO_TVF')
    parser.add_argument('--combined-normal', action='store_true', help='With --combined-audio, qualify all72 cases through normal defaults')
    parser.add_argument('--combined-baseline', action='store_true', help='With --combined-audio, verify a six-case normal filter/stereo smoke matrix')
    parser.add_argument('--disk-voice-stress', action='store_true', help='Qualify Disk/Load note restrictions and recovery against a Perform completion-status control')
    parser.add_argument('--sample-disk', type=Path, default=ROOT / 'roms/FDD/ROBOFULL.IMG')
    parser.add_argument('--state-dir', type=Path, default=ROOT / 'temp/work/native-runtime-verification')
    parser.add_argument('--wave-dump', type=Path, help='Read-only wave RAM dump for persistence verification')
    parser.add_argument('--system-audio', action='store_true', help='Enable real MAME device output at normal speed')
    parser.add_argument('--empty-drive', action='store_true', help='Qualify empty-drive firmware response, reinsertion and loaded playback after ejection')
    parser.add_argument('--audio-backend', choices=('auto', 'wasapi', 'xaudio2'), default='auto')
    parser.add_argument('--audio-latency-ms', type=float, default=0, help='Requested buffer target, not measured latency')
    parser.add_argument('--runtime-contract', action='store_true', help='Verify pause/step and live PCM against MAME WAV')
    parser.add_argument('--pull-render', action='store_true', help='Verify demand-driven variable PCM block sizes')
    parser.add_argument('--scheduled-midi', action='store_true', help='Verify emulated-time MIDI scheduling with pull rendering')
    parser.add_argument('--executable', type=Path, default=ROOT/'mame-source/mames760.exe', help='Exact native binary to qualify')
    parser.add_argument('--panel-menu', action='store_true', help='Exercise Menu/Exit before absolute pointer checks (BUG-030 regression)')
    parser.add_argument('--rack-dials', action='store_true', help='Exercise real Value edits and output gain/recall against native PCM')
    parser.add_argument('--bus-trace', action='store_true', help='Verify read-only diagnostic taps preserve exact native PCM/display replay')
    args = parser.parse_args()
    if args.disk_voice_stress:
        if any((args.combined_audio, args.polyphony, args.pitch_loops, args.loop_modes, args.bus_trace, args.rack_dials, args.pull_render, args.scheduled_midi, args.runtime_contract)):
            parser.error('--disk-voice-stress is a separate acceptance scenario')
        args.sample_disk = ROOT / 'roms/FDD/ROBOLOOP.IMG'
        if hashlib.sha256(args.sample_disk.read_bytes()).hexdigest() != '65f8a8353d4e5bedfa1cc0f0d600012cf6946cda0129ec96363f49a91cb43060':
            parser.error('Unexpected ROBOLOOP fixture')
    if args.combined_normal and not args.combined_audio:
        parser.error('--combined-normal requires --combined-audio')
    if args.combined_baseline and not args.combined_audio:
        parser.error('--combined-baseline requires --combined-audio')
    if args.combined_audio:
        if any((args.polyphony, args.pitch_loops, args.loop_modes, args.bus_trace, args.rack_dials, args.pull_render, args.scheduled_midi, args.runtime_contract)):
            parser.error('--combined-audio is a separate acceptance scenario')
        args.sample_disk = ROOT / 'roms/FDD/ROBO_TVF.IMG'
        if hashlib.sha256(args.sample_disk.read_bytes()).hexdigest() != '1bcbd06688769883ad0f1477608fd80a134e4b22e7bea76709a98283007f3fad':
            parser.error('Unexpected ROBO_TVF fixture')
    if args.pitch_loops:
        if any((args.polyphony, args.loop_modes, args.bus_trace, args.rack_dials, args.pull_render, args.scheduled_midi, args.runtime_contract)):
            parser.error('--pitch-loops is a separate acceptance scenario')
        from verify_native_loop_pitch import build_fixture
        args.sample_disk = build_fixture(ROOT / 'roms/FDD/ROBOLOOP.IMG', args.state_dir.resolve())
    if args.polyphony:
        if any((args.loop_modes, args.bus_trace, args.rack_dials, args.pull_render, args.scheduled_midi, args.runtime_contract)):
            parser.error('--polyphony is a separate acceptance scenario')
        if hashlib.sha256(args.sample_disk.read_bytes()).hexdigest() != '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae':
            parser.error('--polyphony requires the qualified ROBOFULL.IMG fixture')
    if args.loop_stress and not args.loop_modes:
        parser.error('--loop-stress requires --loop-modes')
    if args.bus_trace and (args.runtime_contract or args.pull_render or args.scheduled_midi or args.rack_dials or args.loop_modes):
        parser.error('--bus-trace uses checkpoint rewind; run other timeline scenarios separately')
    if args.rack_dials and (args.runtime_contract or args.pull_render or args.scheduled_midi):
        parser.error('--rack-dials recalls checkpoints; run WAV timeline qualification separately')
    if args.scheduled_midi and not args.pull_render:
        parser.error('--scheduled-midi requires --pull-render')
    if args.loop_modes:
        if args.rack_dials or args.pull_render or args.scheduled_midi or args.runtime_contract:
            parser.error('--loop-modes is a separate acceptance scenario')
        if hashlib.sha256(args.sample_disk.read_bytes()).hexdigest() != '65f8a8353d4e5bedfa1cc0f0d600012cf6946cda0129ec96363f49a91cb43060':
            parser.error('--loop-modes requires the qualified ROBOLOOP.IMG fixture')
    state = args.state_dir
    cfg = RuntimeConfig(args.executable, ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT / 'roms/System/S760224.IMG', state, args.sample_disk,
        sound=args.system_audio, throttle=args.system_audio, wav_output=state / 'audio.wav', wave_dump=args.wave_dump,
        audio_backend=args.audio_backend, audio_latency_ms=args.audio_latency_ms,
        diagnostic_combined_audio=args.combined_audio and not (args.combined_baseline or args.combined_normal))
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
            deadline = time.monotonic() + 30 + (seconds if args.system_audio else 0)
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
        assert sum(byte.bit_count() for byte in frames[1][6:]) > 100, 'Firmware LCD status is blank'
        Image.frombytes('1', (160, 64), frames[1][6:]).save(state / 'boot-lcd.png')
        if args.panel_menu:
            # Service Notes p18: Value/Menu push closes SC0 to SP4.
            # Exercise the physical input without editing firmware state.
            runtime.request('button', port=':PANEL0', name='Value Menu', down=True)
            wait(.15)
            runtime.request('button', port=':PANEL0', name='Value Menu', down=False)
            wait(.3)
            _, menu_frames = runtime.request('frames')
            assert menu_frames[0] != frames[0], 'Value/Menu push did not change the firmware display'
            Image.frombytes('RGBA', (640, 480), menu_frames[0][6:]).save(state / 'panel-menu.png')
            runtime.request('button', port=':PANEL1', name='Exit', down=True)
            wait(.15)
            runtime.request('button', port=':PANEL1', name='Exit', down=False)
            wait(.3)
        # Long movement must not wrap the signed mouse packet.
        move(150, 60)
        cursor = runtime.request('frames')[0]['cursor']
        assert cursor == [300, 120], f'Incorrect firmware mouse position: {cursor}'
        move(10, 5)
        assert runtime.request('frames')[0]['cursor'] == [20, 10]
        if args.panel_menu:
            for x, y in [(159, 99), (0, 0), (80, 50), (10, 5)]:
                move(x, y)
                actual = runtime.request('frames')[0]['cursor']
                assert all(abs(a-b) <= 1 for a, b in zip(actual, [x*2, y*2])), (x, y, actual)
        if args.empty_drive:
            from s760_readiness import labels
            assert runtime.eject_media()['inserted'] is False
            move(118, 5); click(); wait(2)
            move(80, 22); click(); wait(15)
            empty_frame = runtime.request('frames')[1][0]
            assert 'empty_drive' in labels(empty_frame), 'Firmware did not request a disk'
            Image.frombytes('RGBA', (640, 480), empty_frame[6:]).save(state / 'empty-drive.png')
            assert runtime.media_status()['busy'] is False
            before = runtime.request('status')[0]['seconds']
            wait(10)
            assert runtime.request('status')[0]['seconds'] >= before + 10
            try:
                runtime.export_media(state / 'empty-export.img')
            except RuntimeError as error:
                assert 'No floppy' in str(error), str(error)
            else:
                raise AssertionError('Empty-drive export succeeded')
            assert not (state / 'empty-export.img').exists()
            move(10, 5); click(); move(15, 22); click(); wait(2)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
        runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
        move(118, 5); click(); wait(2)  # Disk menu
        move(80, 22); click(); wait(8)  # Load, including physical directory reads
        move(50, 34); click(); wait(2)  # Mark performance
        move(76, 98); click(); wait(35) # Load samples through firmware/FDC
        _, frames = runtime.request('frames')
        Image.frombytes('RGBA', (640, 480), frames[0][6:]).save(state / 'loaded.png')
        move(10, 5); click(); move(15, 22); click(); wait(3)
        if args.empty_drive:
            assert runtime.eject_media()['inserted'] is False
        if args.polyphony:
            from verify_native_polyphony import qualify
            qualify(runtime, state)
            return
        if args.pitch_loops:
            from verify_native_loop_pitch import qualify
            qualify(runtime, state)
            return
        if args.combined_audio:
            from verify_native_combined_audio import qualify
            qualify(runtime, state, baseline=args.combined_baseline, normal=args.combined_normal or args.combined_baseline)
            return
        if args.disk_voice_stress:
            from verify_native_disk_voice import qualify
            qualify(runtime, state)
            return
        if args.bus_trace:
            runtime.request('pause')
            runtime.request('audio_capture', enabled=True)
            snapshot = state / 'bus-trace.s760state'
            runtime.save_checkpoint(snapshot)
            for invalid in ({'enabled':True, 'first':False},
                            {'enabled':True, 'first':0x100000, 'last':0x104000},
                            {'enabled':False}):
                try:
                    runtime.request('bus_trace', **invalid)
                except RuntimeError:
                    pass
                else:
                    raise AssertionError('Invalid diagnostic request accepted')
            runs = []
            displays = []
            for traced in (False, True):
                runtime.load_checkpoint(snapshot)
                now = runtime.request('status')[0]['seconds']
                timestamp = math.ceil(now * 44100) + 2048
                if traced:
                    runtime.request('bus_trace', enabled=True)
                    try:
                        runtime.save_checkpoint(state / 'active-trace.s760state')
                    except RuntimeError as error:
                        assert 'Stop diagnostic tracing' in str(error)
                    else:
                        raise AssertionError('Checkpoint accepted an active diagnostic observer')
                runtime.schedule_midi([{'sample':timestamp, 'bytes':[144,60,127]},
                                       {'sample':timestamp+32768, 'bytes':[128,60,0]}])
                runs.append(b''.join(runtime.render_audio(8192)[1] for _ in range(16)))
                displays.append(runtime.request('frames')[1])
                if traced:
                    trace = runtime.request('bus_trace', enabled=False)[0]
                    assert trace['accesses'] > 0 and len(trace['rows']) <= 256
            assert runs[0] == runs[1], 'Diagnostic taps changed native PCM'
            assert displays[0] == displays[1], 'Diagnostic taps changed native displays'
            samples = np.frombuffer(runs[0], dtype='<f4')
            assert np.max(np.abs(samples)) > .001, 'Observer replay was silent'
            assert np.max(np.abs(samples[-8192*2:])) == 0, 'Observer replay note-off failed'
            (state / 'bus-trace-result.json').write_text(json.dumps({
                'pcm_frames_exact':131072, 'displays_exact':True,
                'trace_rows':len(trace['rows']), 'trace_dropped':trace['dropped'],
                'pcm_sha256':hashlib.sha256(runs[0]).hexdigest()}), encoding='utf-8')
            # A rewind invalidates the monotonic WAV offsets below. This is a
            # separate replay scenario; normal WAV acceptance runs separately.
            print(json.dumps({'bus_trace_pcm_frames_exact':131072, 'displays_exact':True}))
            return
        if args.loop_modes:
            runtime.request('pause')
            runtime.request('audio_capture', enabled=True)
            from scipy import signal
            raw = np.frombuffer(args.sample_disk.read_bytes()[0x2ac00:0x2cc00], dtype='<i2')
            sequences = {0: raw[1024:2047], 1: raw[1024:2047], 3: raw[1024:2047],
                         4: np.r_[raw[1025:2049], raw[2047:1025:-1]], 6: raw[:1024][::-1]}
            rows = []
            for mode in range(7):
                now = runtime.request('status')[0]['seconds']
                start = math.ceil(now * 44100) + 2048
                runtime.schedule_midi([
                    {'sample': start, 'bytes': [0x90, 60 + mode, 127]},
                    {'sample': start + 3 * 44100, 'bytes': [0x80, 60 + mode, 0]},
                ])
                blocks = []
                remaining = 5 * 44100
                while remaining:
                    n = min(8192, remaining)
                    _, pcm = runtime.render_audio(n)
                    blocks.append(np.frombuffer(pcm, dtype='<f4').reshape(-1, 2))
                    remaining -= n
                audio = np.concatenate(blocks)
                np.save(state / f'loop-{mode}.npy', audio)
                nz = np.flatnonzero(np.max(np.abs(audio), axis=1) > 1e-8)
                assert len(nz), f'Loop mode {mode} is silent'
                assert np.isfinite(audio).all()
                assert np.max(np.abs(audio[-8192:])) == 0, f'Mode {mode} did not release'
                held = float(np.max(np.abs(audio[44100:2*44100])))
                if mode in (2, 5):
                    assert held == 0, f'One-shot {mode} continues looping'
                else:
                    assert held > 0, f'Loop mode {mode} ended before note-off'
                sign_match = None
                if mode in sequences:
                    seq = np.sign(sequences[mode]); n = len(seq)
                    observed = np.sign(audio[44100:44100+n, 0])
                    doubled = np.r_[seq, seq]
                    offset = int(np.argmax(signal.correlate(doubled, observed, mode='valid')))
                    sign_match = float(np.mean(observed == doubled[offset:offset+n]))
                    assert sign_match == 1.0, f'Loop mode {mode} sequence/direction differs'
                rows.append({'mode': mode, 'note': 60 + mode, 'sign_match': sign_match,
                             'peak': float(np.max(np.abs(audio))), 'held_peak': held,
                             'first_nonzero': int(nz[0]), 'last_nonzero': int(nz[-1])})
            report = {'passed': True, 'rate': 44100, 'rows': rows,
                      'scope': 'Current default native profile, ROBOLOOP firmware load; not hardware parity'}
            if args.loop_stress:
                checkpoint = state / 'loop-stress.checkpoint'
                runtime.save_checkpoint(checkpoint)
                runs = []
                stress_rows = []
                for replay in range(2):
                    if replay:
                        runtime.load_checkpoint(checkpoint)
                    blocks = []
                    for cycle in range(8):
                        now = runtime.request('status')[0]['seconds']
                        start = math.ceil(now * 44100) + 2048
                        events = []
                        for mode in range(7):
                            note = 60 + mode
                            events.extend([
                                {'sample': start + mode * 64, 'bytes': [0x90, note, 127]},
                                {'sample': start + 11025 + mode * 64, 'bytes': [0x80, note, 0]},
                                {'sample': start + 12000 + mode * 64, 'bytes': [0x90, note, 127]},
                                {'sample': start + 44100 + mode * 64, 'bytes': [0x80, note, 0]},
                            ])
                        runtime.schedule_midi(sorted(events, key=lambda e: e['sample']))
                        cycle_blocks = []
                        remaining = 3 * 44100
                        while remaining:
                            n = min(8192, remaining)
                            _, pcm = runtime.render_audio(n)
                            cycle_blocks.append(pcm)
                            remaining -= n
                        pcm = b''.join(cycle_blocks)
                        audio = np.frombuffer(pcm, dtype='<f4').reshape(-1, 2)
                        peak = float(np.max(np.abs(audio)))
                        assert np.isfinite(audio).all() and 0 < peak < 1, 'Invalid mixed playback'
                        assert np.max(np.abs(audio[-44100:])) == 0, 'Stuck note after mixed retrigger/release'
                        if not replay:
                            stress_rows.append({'cycle': cycle, 'peak': peak, 'silent_tail_frames': 44100})
                        blocks.append(pcm)
                    runs.append(b''.join(blocks))
                assert runs[0] == runs[1], 'Mixed-mode checkpoint replay differs'
                report['stress'] = {'cycles': stress_rows, 'note_ons_per_run': 112,
                    'exact_replay_frames': len(runs[0]) // 8,
                    'pcm_sha256': hashlib.sha256(runs[0]).hexdigest(),
                    'limits': 'Same-process checkpoint recall; no disk overlap, voice-count/stealing assertion or hardware comparison'}
            (state / 'loop-results.json').write_text(json.dumps(report, indent=2))
            print(json.dumps(report, indent=2))
            return
        if args.rack_dials:
            move(153, 18)  # Perform Play Master Level; firmware labels Dec/Inc.
            def level_pixels(label):
                _, f = runtime.request('frames')
                image = Image.frombytes('RGBA', (640, 480), f[0][6:])
                image.save(state / f'dial-{label}.png')
                return image.crop((594, 64, 640, 80)).tobytes()
            original = level_pixels('127')
            runtime.request('dial', id='ALPHA', delta=-1); wait(.3)
            one = level_pixels('126')
            runtime.request('dial', id='ALPHA', delta=-2); wait(.3)
            three = level_pixels('124')
            assert len({original, one, three}) == 3, 'Value decrement did not edit the selected firmware field'
            runtime.request('pause'); runtime.request('checkpoint_save'); runtime.request('resume')
            runtime.request('dial', id='ALPHA', delta=3); wait(.3)
            assert level_pixels('restored-127') == original, 'Value reversal did not restore the field'
            runtime.request('pause'); runtime.request('checkpoint_load'); runtime.request('resume'); wait(.1)
            assert level_pixels('recalled-124') == three, 'Value edit was not recalled'
            runtime.request('dial', id='ALPHA', delta=2); wait(.3)
            assert level_pixels('recalled-plus2-126') == one, 'Encoder position was not recalled'
            runtime.request('dial', id='ALPHA', delta=1); wait(.3)
            assert level_pixels('recalled-plus3-127') == original
            runtime.request('pause')
            runtime.request('audio_capture', enabled=True)
            runtime.request('midi', bytes=[0x90, 60, 127])
            runtime.render_audio(8192)
            runtime.request('checkpoint_save')
            unity_checkpoint = (state / 'runtime-checkpoint.bin').read_bytes()
            _, unity = runtime.render_audio(8192)
            runtime.request('checkpoint_load')
            runtime.request('dial', id='VOLUME', delta=-25)
            runtime.request('dial', id='VOLUME', delta=-25)
            _, half = runtime.render_audio(8192)
            runtime.request('checkpoint_save')
            _, expected_half_replay = runtime.render_audio(8192)
            runtime.request('dial', id='VOLUME', delta=32)
            runtime.render_audio(8192)
            runtime.request('checkpoint_load')
            assert runtime.request('frames')[0]['output_level'] == 50
            _, actual_half_replay = runtime.render_audio(8192)
            assert actual_half_replay == expected_half_replay, 'Non-unity level recall changed PCM'
            (state / 'runtime-checkpoint.bin').write_bytes(unity_checkpoint)
            runtime.request('checkpoint_load')
            assert runtime.request('frames')[0]['output_level'] == 100, 'Output level was not restored'
            for _ in range(4): runtime.request('dial', id='VOLUME', delta=-32)
            assert runtime.request('frames')[0]['output_level'] == 0
            _, muted = runtime.render_audio(8192)
            # In-flight mixer blocks predate the physical pot change.
            a = np.frombuffer(unity, dtype='<f4')[4096:]
            b = np.frombuffer(half, dtype='<f4')[4096:]
            c = np.frombuffer(muted, dtype='<f4')[4096:]
            assert np.isfinite(a).all() and np.max(np.abs(a)) > .01
            gain_error = float(np.max(np.abs(b-a*.5)))
            np.savez(state / 'dial-audio.npz', unity=a, half=b, muted=c)
            print(json.dumps({'dial_audio_peaks': [float(np.max(np.abs(v))) for v in (a,b,c)], 'gain_error':gain_error}), flush=True)
            assert gain_error < 1e-7, gain_error
            assert np.count_nonzero(c) == 0, 'Minimum output level is not silent'
            runtime.request('checkpoint_load')
            assert runtime.request('dial', id='VOLUME', delta=32)[0]['output_level'] == 100
            runtime.request('midi', bytes=[0x80, 60, 0])
            for _ in range(10): _, released = runtime.render_audio(8192)
            assert np.count_nonzero(np.frombuffer(released, dtype='<f4')) == 0, 'Dial test note-off was not silent'
            runtime.request('audio_capture', enabled=False)
            runtime.request('resume')
            print(json.dumps({'rack_dials': {'value': [127,126,124,127], 'half_gain_max_error': gain_error,
                'muted_nonzero_samples': int(np.count_nonzero(c)), 'restored_output_level': 100,
                'non_unity_replay_exact':True, 'value_recall':True, 'release_silent':True}}), flush=True)
            # MAME's external WAV writer is not rewound by checkpoint_load.
            # Its offsets no longer equal guest time after the recall tests.
            return
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
            if args.panel_menu:
                # The VST host advances this same paused runtime by rendering.
                # Pointer convergence must happen during those render callbacks.
                runtime.request('pointer', x=140, y=70)
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
            if args.panel_menu:
                actual = runtime.request('frames')[0]['cursor']
                assert all(abs(a-b) <= 1 for a, b in zip(actual, [280, 140])), actual
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
    result['system_audio'] = {'enabled': cfg.sound, 'backend_requested': cfg.audio_backend,
                              'buffer_target_ms': cfg.audio_latency_ms, 'throttled': cfg.throttle,
                              'device_latency_measured': False}
    if args.empty_drive:
        result['empty_drive'] = {'firmware_insert_disk_message': True, 'clock_advances': True,
                                 'empty_export_rejected': True, 'reinsert_load': True,
                                 'loaded_playback_after_ejection': True}
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
