"""Disk/Load note restriction, Perform completion control and recovery acceptance."""
import json
import hashlib
import math
import time

import numpy as np
from PIL import Image


def qualify(runtime, state):
    def wait(seconds):
        until = runtime.request('status')[0]['seconds'] + seconds
        deadline = time.monotonic() + 60
        while runtime.request('status')[0]['seconds'] < until:
            assert time.monotonic() < deadline, 'Firmware stopped advancing'
            time.sleep(.005)

    def click(x, y):
        runtime.request('pointer', x=x, y=y); wait(.2)
        runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
        runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.2)

    trials = []
    # Establish completion-status reads in Perform before interpreting the
    # restricted note-allocation behavior in Disk/Load.
    runtime.request('pause'); runtime.request('audio_capture', enabled=True)
    runtime.request('bus_trace', enabled=True, first=0x100000, last=0x100003)
    control_start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 512
    control_events = []
    for i in range(12):
        on = control_start + i * 22050
        control_events.extend([{'sample': on, 'bytes': [0x90, 63, 100]},
                               {'sample': on + 17640, 'bytes': [0x80, 63, 0]}])
    runtime.schedule_midi(control_events)
    remaining = 7 * 44100
    while remaining:
        n = min(8192, remaining); runtime.render_audio(n); remaining -= n
    control_trace = runtime.request('bus_trace', enabled=False)[0]
    control_status = runtime.request('status')[0]
    assert control_trace['dropped'] == 0
    # Each pulse's first enabled slot is4 in this isolated fixture.
    control_requests = [r for r in control_trace['rows'] if r['kind'] == 'r'
                        and r['address'] == 0x100002 and r['data'] & 0x20]
    delivered = control_status['midi_delivered']
    (state / 'perform-control.json').write_text(json.dumps({'trace': control_trace, 'status': control_status,
                                                           'completion_requests': control_requests}, indent=2), encoding='utf-8')
    assert control_requests, 'Perform control did not expose source2 completion status'
    runtime.request('audio_capture', enabled=False); runtime.request('resume')
    for trial in range(3):
        click(118, 5); wait(.3)
        # Put the pointer on Load first, so subsequent disk and MIDI activity
        # starts close together. Each bounded pulse has a note-off so the key
        # can retrigger normally; status reads identify completion requests.
        runtime.request('pointer', x=80, y=22); wait(.3)
        runtime.request('pause')
        if trial == 0:
            try:
                runtime.request('bus_trace', enabled=True, include_fdc='yes')
            except RuntimeError:
                pass
            else:
                raise AssertionError('Invalid diagnostic selector accepted')
        runtime.request('bus_trace', enabled=True, first=0x100000, last=0x100003, include_fdc=True)
        start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 512
        events = []
        for i in range(12):
            sample = start + i * 22050
            events.append({'sample': sample, 'bytes': [0x90, 63, 100]})
            events.append({'sample': sample + 17640, 'bytes': [0x80, 63, 0]})
        runtime.schedule_midi(events)
        runtime.request('audio_capture', enabled=True)
        runtime.render_audio(1536)
        runtime.request('resume')
        runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
        runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(7)
        runtime.request('pause')
        trace = runtime.request('bus_trace', enabled=False)[0]
        assert trace['dropped'] == 0, 'Incomplete trace cannot establish firmware suppression'
        status = runtime.request('status')[0]
        assert status['midi_pending'] == 0 and not status['midi_error']
        assert len(status['midi_delivered']) == 24
        bitmap = 0
        completions = []
        for row in trace['rows']:
            if row['kind'] == 'w' and row['address'] in (0x100000, 0x100002):
                shift = (row['address'] - 0x100000) * 8
                mask = row['mask'] << shift
                previous = bitmap
                bitmap = (bitmap & ~mask) | ((row['data'] << shift) & mask)
                if previous & ~bitmap & 0xfff0fff0:
                    completions.append(row['seconds'])
        fdc = [r['seconds'] for r in trace['rows'] if r['kind'] == 'w' and r['address'] == 0x102002]
        (state / f'trial-{trial}.json').write_text(json.dumps({'trace': trace, 'status': status, 'completions': completions, 'fdc': fdc}, indent=2), encoding='utf-8')
        assert fdc and completions, 'No disk commands or playable-pool clear observed'
        delivered = status['midi_delivered']
        requests = [r for r in trace['rows'] if r['kind'] == 'r'
                    and r['address'] == 0x100002 and r['data'] & 0x20]
        observed = [r['seconds'] for r in requests]
        overlapping = [t for t in observed if min(fdc) <= t <= max(fdc)]
        assert not overlapping, 'Disk/Load restriction changed; requalify simultaneous-source behavior'
        assert completions and max(completions) < min(fdc), 'Playable pool was not cleared before disk commands'
        active_after_disk = [r for r in trace['rows'] if r['kind'] == 'w'
                             and r['address'] in (0x100000, 0x100002)
                             and r['seconds'] >= min(fdc) and r['data'] & 0xfff0]
        assert not active_after_disk, 'Notes were allocated during the restricted disk mode'
        trials.append({'trial': trial, 'trace': trace, 'serial_delivered': status['midi_delivered'],
                       'enable_clear_times': completions, 'fdc_interval': [min(fdc), max(fdc)],
                       'overlapping_completions': overlapping,
                       'note_offs_during_trace': 12, 'completion_requests': requests})
        runtime.request('resume')
        for _ in range(12): runtime.request('midi', bytes=[0x80, 63, 0])
        wait(2)
        click(10, 5); click(15, 22); wait(1)
    Image.frombytes('RGBA', (640, 480), runtime.request('frames')[1][0][6:]).save(state / 'post-stress.png')
    runtime.request('pause'); runtime.request('audio_capture', enabled=True)
    blocks = []
    for _ in range(8):
        _, pcm = runtime.render_audio(8192); blocks.append(pcm)
    assert np.max(np.abs(np.frombuffer(b''.join(blocks), dtype='<f4'))) == 0, 'Stuck voice after stress'
    start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 512
    runtime.schedule_midi([{'sample': start, 'bytes': [0x90, 60, 100]},
                           {'sample': start + 44100, 'bytes': [0x80, 60, 0]}])
    blocks = []
    for _ in range(20):
        _, pcm = runtime.render_audio(8192); blocks.append(pcm)
    audio = np.frombuffer(b''.join(blocks), dtype='<f4')
    assert np.isfinite(audio).all() and 0 < np.max(np.abs(audio)) < 1
    assert np.max(np.abs(audio[-88200:])) == 0
    runtime.request('audio_capture', enabled=False); runtime.request('resume')
    media = runtime.media_status()
    assert not media['dirty'] and not media['busy']
    exported = state / 'post-stress.img'
    runtime.export_media(exported)
    assert exported.read_bytes() == runtime.config.sample_disk.read_bytes(), 'Directory stress changed media'
    report = {'passed': True, 'perform_control': {'trace': control_trace, 'completion_requests': control_requests,
                                                'serial_delivered': control_status['midi_delivered']},
              'trials': trials, 'post_stress_peak': float(np.max(np.abs(audio))),
              'media': media, 'unchanged_media_sha256': hashlib.sha256(exported.read_bytes()).hexdigest(),
              'firmware_restriction': 'Disk/Load clears playable voices before FDC commands and suppresses new note allocations. Return to Perform before auditioning; no event-preservation or musical-continuity guarantee during Load.',
              'limits': 'Named workload robustness/restriction qualification; no observed three-source simultaneous IRQ arbitration. Sample Load-under-MIDI qualified separately; bitmap clears in Disk are not labelled natural completions.'}
    (state / 'disk-voice-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({'passed': True, 'trials': len(trials), 'overlapping_completions': [len(t['overlapping_completions']) for t in trials]}))
