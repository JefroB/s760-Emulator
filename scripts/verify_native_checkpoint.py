"""Cold native checkpoint acceptance using real firmware controls and PCM."""
import argparse
import hashlib
import json
import math
import time
import shutil
from dataclasses import replace
from pathlib import Path
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    import numpy as np
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--realtime', action='store_true', help='Use normal MAME throttling')
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--scheduled', action='store_true', help='Checkpoint pending future note-on/off')
    mode.add_argument('--serial', action='store_true', help='Checkpoint just after MIDI serial enqueue')
    mode.add_argument('--pre-capture', action='store_true', help='Repeated in-process rewind to before audio capture')
    mode.add_argument('--standalone-session', action='store_true', help='Standalone session save/restore and crash recovery')
    parser.add_argument('--filter-state', action='store_true', help='Cold replay of an active normal-profile LP C32 filter on ROBO_TVF')
    parser.add_argument('--scsi', action='store_true', help='Stage generated SCSI media and verify identity rejection before cold replay')
    args = parser.parse_args()
    if args.filter_state and any((args.scheduled,args.serial,args.pre_capture,args.standalone_session)):
        parser.error('--filter-state uses the active-note scenario')
    if args.filter_state:
        assert hashlib.sha256((ROOT/'roms/FDD/ROBO_TVF.IMG').read_bytes()).hexdigest() == '1bcbd06688769883ad0f1477608fd80a134e4b22e7bea76709a98283007f3fad', 'Unexpected filter fixture'
    blocks = 16 if args.scheduled else 8
    work = args.state_dir.resolve()
    work.mkdir(parents=True, exist_ok=True)
    def config(name):
        if args.scsi:
            media=work/name/'roms/SCSI';media.mkdir(parents=True,exist_ok=True)
            (media/'HD00_512.img').write_bytes(bytes(range(256))*4)
        return RuntimeConfig(ROOT/'mame-source/mames760.exe', ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
                             ROOT/'roms/System/S760224.IMG', work/name, None if args.standalone_session else ROOT/('roms/FDD/ROBO_TVF.IMG' if args.filter_state else 'roms/FDD/ROBOFULL.IMG'),
                             sound=False, throttle=args.realtime)
    with NativeRuntime(config('first')) as runtime:
        def wait(seconds):
            target = runtime.request('status')[0]['seconds']+seconds
            deadline = time.monotonic()+max(30, seconds+15)
            while runtime.request('status')[0]['seconds'] < target:
                assert time.monotonic() < deadline, 'Native clock stalled'
                time.sleep(.005)
        def click(x, y):
            runtime.request('pointer', x=x, y=y); wait(.2)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.2)
        wait(20)
        if args.standalone_session:
            library = work/'source-library'
            library.mkdir(exist_ok=True)
            source_sample = library/'ROBOFULL.IMG'
            shutil.copyfile(ROOT/'roms/FDD/ROBOFULL.IMG', source_sample)
            runtime.insert_media(source_sample)
        else:
            runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
            runtime.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
        click(118, 5); wait(2); click(80, 22); wait(8); click(50, 34); wait(2); click(76, 98); wait(35)
        click(10, 5); click(15, 22); wait(3)
        try:
            runtime.save_checkpoint(work/'running.s760state')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Running checkpoint accepted')
        now = runtime.request('pause')[0]['seconds']
        if args.standalone_session:
            from s760_standalone import StandaloneSession
            session = StandaloneSession(runtime, ROOT/'roms/FDD')
            assert session.input({'type':'SAVE_SESSION','payload':{}})['type'] == 'SESSION_SAVED'
            saved = session.session_path.read_bytes()
            runtime.request('audio_capture', enabled=True)
            timestamp = math.ceil(now*44100)+4096
            runtime.schedule_midi([{'sample':timestamp,'bytes':[144,60,127]},
                                   {'sample':timestamp+44100,'bytes':[128,60,0]}])
            reference = b''.join(runtime.render_audio(8192)[1] for _ in range(16))
            expected = runtime.request('frames')[1]
            assert session.input({'type':'RESTORE_SESSION','payload':{'discard':True}})['type'] == 'SESSION_RESTORED'
            runtime.request('audio_capture', enabled=True)
            runtime.schedule_midi([{'sample':timestamp,'bytes':[144,60,127]},
                                   {'sample':timestamp+44100,'bytes':[128,60,0]}])
            replay = b''.join(runtime.render_audio(8192)[1] for _ in range(16))
            assert replay == reference, 'Standalone restore PCM differs'
            assert runtime.request('frames')[1] == expected, 'Standalone restore displays differ'
            assert np.max(np.abs(np.frombuffer(reference, dtype='<f4'))) > .001
            assert np.max(np.abs(np.frombuffer(reference[-8192*8:], dtype='<f4'))) == 0
            old_pid = runtime.process.pid
            runtime.process.kill(); runtime.process.wait(timeout=10)
            assert session.poll() == []
            assert session.input({'type':'RESTORE_SESSION','payload':{'discard':True}})['type'] == 'SESSION_RESTORED'
            assert runtime.process.pid != old_pid
            wait(4)
            session.poll()
            assert session.firmware_status['state'] == 'ready', session.firmware_status
            runtime.request('pause'); runtime.request('audio_capture', enabled=True)
            runtime.request('midi', bytes=[144,60,127])
            active=b''.join(runtime.render_audio(8192)[1] for _ in range(4))
            assert np.max(np.abs(np.frombuffer(active, dtype='<f4'))) > .001
            runtime.request('midi', bytes=[128,60,0])
            release=b''.join(runtime.render_audio(8192)[1] for _ in range(8))
            assert np.max(np.abs(np.frombuffer(release[-8192*8:], dtype='<f4'))) == 0
            assert session.session_path.read_bytes() == saved
            result={'standalone_pcm_frames_exact':len(reference)//8,'displays_exact':True,
                    'crash_recovery_new_process':True,'recovered_patch_play_release':True,
                    'saved_archive_preserved':True,'firmware_ready_after_recovery':True}
            # All floppy bytes must come from the archive, with no original
            # source library or private insertion slot in the new instance.
            source_sample.unlink()
            library.rmdir()
            relocated = work/'relocated'
            relocated.mkdir(exist_ok=True)
            boot, system = relocated/'moved-boot.bin', relocated/'moved-system.img'
            shutil.copyfile(runtime.config.boot_rom, boot)
            shutil.copyfile(runtime.config.system_disk, system)
            recovered = NativeRuntime(replace(runtime.config, state_dir=relocated,
                boot_rom=boot, system_disk=system, sample_disk=source_sample))
            try:
                try:
                    recovered.start()
                except FileNotFoundError as error:
                    startup_error = str(error)
                else:
                    raise AssertionError('Missing source sample unexpectedly started')
                moved_session = StandaloneSession(recovered, library, startup_error)
                moved_session.session_path.parent.mkdir(parents=True, exist_ok=True)
                moved_session.session_path.write_bytes(saved)
                moved_session.input({'type':'RESTORE_SESSION','payload':{'discard':True}})
                assert moved_session.startup_error is None
                recovered.request('pause')
                # Rewind directly for byte-exact replay independent of the
                # standalone policy that resumes a recovered stopped child.
                recovered.load_checkpoint(moved_session.session_path)
                recovered.request('audio_capture', enabled=True)
                recovered.schedule_midi([{'sample':timestamp,'bytes':[144,60,127]},
                                         {'sample':timestamp+44100,'bytes':[128,60,0]}])
                moved_pcm = b''.join(recovered.render_audio(8192)[1] for _ in range(16))
                assert moved_pcm == reference, 'Relocated session PCM differs'
                assert recovered.request('frames')[1] == expected, 'Relocated displays differ'
                assert moved_session.session_path.read_bytes() == saved
                assert not (relocated/'inserted-floppy.img').exists()
                result.update(relocated_firmware_paths=True, missing_source_library=True,
                              missing_initial_sample_recovered=True, relocated_pcm_frames_exact=len(reference)//8,
                              relocated_displays_exact=True)
            finally:
                recovered.close()
            (work/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
            print(json.dumps(result,indent=2))
            return
        if args.pre_capture:
            baseline = work/'pre-capture.s760state'
            runtime.save_checkpoint(baseline)
            reference = None
            for attempt in range(3):
                if attempt:
                    runtime.load_checkpoint(baseline)
                runtime.request('audio_capture', enabled=True)
                timestamp = math.ceil(now*44100)+4096
                runtime.schedule_midi([
                    {'sample': timestamp, 'bytes': [144, 60, 127]},
                    {'sample': timestamp+44100, 'bytes': [128, 60, 0]}])
                replay = b''.join(runtime.render_audio(2048)[1] for _ in range(64))
                if reference is None:
                    reference = replay
                else:
                    assert replay == reference, 'Pre-capture rewind PCM differs'
                assert runtime.request('status')[0]['audio_dropped'] == 0
            assert np.max(np.abs(np.frombuffer(reference, dtype='<f4'))) > .001
            assert np.max(np.abs(np.frombuffer(reference[-8192*8:], dtype='<f4'))) == 0
            result = {'pre_capture_rewinds': 2, 'pcm_frames_exact': len(reference)//8,
                      'note_off_silent': True, 'capture_drops': 0}
            (work/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
            print(json.dumps(result, indent=2))
            return
        runtime.request('audio_capture', enabled=True)
        if args.filter_state:
            runtime.request('midi', bytes=[0xc0,13])
            runtime.render_audio(8192)
            now=runtime.request('status')[0]['seconds']
        timestamp = math.ceil(now*44100)+1000
        if args.serial:
            # Rendering stops at a native frame boundary whose phase need not
            # equal pause time + 735 samples. Measure it on a saved timeline,
            # then replay from that same state with the first byte in flight.
            baseline = work/'serial-baseline.s760state'
            runtime.save_checkpoint(baseline)
            runtime.render_audio(1)
            boundary = runtime.request('status')[0]['seconds']
            runtime.load_checkpoint(baseline)
            timestamp = math.floor(boundary*44100)-1
            assert timestamp >= math.ceil(now*44100)
        events = [{'sample': timestamp, 'bytes': [144, 60, 127]}]
        if args.scheduled:
            events.append({'sample': timestamp+44100, 'bytes': [128, 60, 0]})
        runtime.schedule_midi(events)
        if args.serial:
            runtime.render_audio(1)
        elif not args.scheduled:
            for _ in range(4): runtime.render_audio(8192)
        checkpoint_time = runtime.request('status')[0]['seconds']
        enqueue_age = checkpoint_time-timestamp/44100
        if args.serial:
            assert 0 <= enqueue_age < 10/31250, f'Checkpoint outside first serial byte: {enqueue_age}'
        frames = runtime.request('frames')[1]
        runtime.save_checkpoint(work/'active.s760state')
        reference = b''.join(runtime.render_audio(8192)[1] for _ in range(blocks))
        expected_frames = runtime.request('frames')[1]
    # A fresh process has not booted/loaded the sample patch before restoration.
    with NativeRuntime(replace(config('second'), sample_disk=None)) as runtime:
        runtime.request('pause')
        damaged = bytearray((work/'active.s760state').read_bytes()); damaged[-1] ^= 1
        (work/'damaged.s760state').write_bytes(damaged)
        before = runtime.request('status')[0]['seconds']
        try:
            runtime.load_checkpoint(work/'damaged.s760state')
        except ValueError:
            pass
        else:
            raise AssertionError('Damaged checkpoint accepted')
        assert runtime.request('status')[0]['seconds'] == before
        if args.scheduled:
            # Loading must cancel this unrelated old coroutine before rearming
            # the saved events, even when its old timer would fire sooner.
            runtime.schedule_midi([{'sample': math.ceil(before*44100)+500,
                                    'bytes': [144, 61, 127]}])
        if args.scsi:
            image=runtime.config.state_dir/'roms/SCSI/HD00_512.img'
            original=image.read_bytes();image.write_bytes(bytes(len(original)))
            try:
                runtime.load_checkpoint(work/'active.s760state')
            except ValueError:
                pass
            else:
                raise AssertionError('Changed SCSI backing accepted')
            assert runtime.request('status')[0]['seconds']==before
            image.write_bytes(original)
        runtime.load_checkpoint(work/'active.s760state')
        assert runtime.request('status')[0]['midi_pending'] == (2 if args.scheduled else 0)
        replay_frames = runtime.request('frames')[1]
        replay = b''.join(runtime.render_audio(8192)[1] for _ in range(blocks))
        assert replay == reference, 'Cold restore PCM differs'
        # Framebuffers refresh from restored controller state at the next frame.
        final_frames = runtime.request('frames')[1]
        assert any(final_frames[0][6:][0::4]), 'Cold restore CRT is black'
        assert final_frames == expected_frames, 'Cold restore CRT/LCD differ'
        if args.scheduled:
            status = runtime.request('status')[0]
            assert status['midi_pending'] == 0 and status['midi_error'] == ''
            assert [event['sample'] for event in status['midi_delivered']] == [timestamp,timestamp+44100]
            assert np.max(np.abs(np.frombuffer(replay[-8192*8:], dtype='<f4'))) == 0, 'Restored scheduled note-off did not release'
            runtime.load_checkpoint(work/'active.s760state')
            assert b''.join(runtime.render_audio(8192)[1] for _ in range(blocks)) == reference
        now = runtime.request('status')[0]['seconds']
        runtime.schedule_midi([{'sample': math.ceil(now*44100)+1000, 'bytes': [128, 60, 0]}])
        release = b''.join(runtime.render_audio(8192)[1] for _ in range(blocks))
        import numpy as np
        assert np.max(np.abs(np.frombuffer(reference, dtype='<f4'))) > (1e-5 if args.filter_state else .001)
        assert np.max(np.abs(np.frombuffer(release, dtype='<f4')[-8192:])) == 0
    result = {'active_normal_filter': args.filter_state, 'scsi_identity_verified': args.scsi, 'cold_pcm_frames_exact': len(reference)//8, 'note_off_silent': True,
              'immediate_frames_equal': replay_frames == frames, 'refreshed_frames_exact': True,
              'corrupt_rejected_before_mutation': True, 'running_checkpoint_rejected': True, 'scheduled_midi_restored': args.scheduled,
              'serial_boundary': args.serial, 'enqueue_age_seconds': enqueue_age,
              'fresh_process_sample_disk_supplied': False}
    (work/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
