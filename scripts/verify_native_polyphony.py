"""Native firmware allocation acceptance, called after ROBOFULL firmware Load.

Read-only enable-register bus taps; no RAM/PC writes or synthetic guest flags.
Not a hardware arbitration/voice-stealing-priority qualification.
"""
import json
import math

import numpy as np


def qualify(runtime, state):
    runtime.request('pause')
    runtime.request('audio_capture', enabled=True)
    bitmap = 0
    rows = []

    def step(label, packets, seconds=.15):
        nonlocal bitmap
        runtime.request('bus_trace', enabled=True, first=0x100000, last=0x100003)
        start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 512
        runtime.schedule_midi([{'sample': start + i * 64, 'bytes': p}
                               for i, p in enumerate(packets)])
        chunks = []
        remaining = math.ceil(seconds * 44100)
        while remaining:
            n = min(8192, remaining)
            _, pcm = runtime.render_audio(n)
            chunks.append(pcm)
            remaining -= n
        trace = runtime.request('bus_trace', enabled=False)[0]
        assert trace['dropped'] == 0, 'Enable-register trace overflow'
        transitions = []
        for row in trace['rows']:
            if row['kind'] != 'w' or not 0x100000 <= row['address'] <= 0x100003:
                continue
            shift = (row['address'] - 0x100000) * 8
            mask = row['mask'] << shift
            bitmap = (bitmap & ~mask) | ((row['data'] << shift) & mask)
            transitions.append((bitmap & 0xfff0fff0).bit_count())
        audio = np.frombuffer(b''.join(chunks), dtype='<f4').reshape(-1, 2)
        assert np.isfinite(audio).all() and np.max(np.abs(audio)) < 1
        count = (bitmap & 0xfff0fff0).bit_count()
        rows.append({'label': label, 'bitmap': f'{bitmap:08x}', 'voices': count,
                     'transitions': transitions,
                     'peak': float(np.max(np.abs(audio))), 'trace': trace['rows']})
        return count, audio

    for i, note in enumerate(range(48, 72)):
        count, _ = step(f'allocate-{note}', [[0x90, note, 100]])
        assert count == i + 1, f'Allocation {note}: {count}, expected {i+1}'
    for note in range(72, 80):
        count, _ = step(f'steal-{note}', [[0x90, note, 100]])
        assert count == 24, f'Voice pool changed during stealing: {count}'
        assert 23 in rows[-1]['transitions'], 'Excess note did not recycle a voice'
    count, audio = step('release-original-notes', [[0x80, n, 0] for n in range(48, 72)], 2)
    assert count == 8 and np.max(np.abs(audio[-8192:])) > 0, 'Stolen-note release affected replacement voices'
    count, audio = step('release-replacement-notes', [[0x80, n, 0] for n in range(72, 80)], 2)
    assert count == 0 and np.max(np.abs(audio[-44100:])) == 0, 'Voice leak after stealing'
    for cycle in range(8):
        count, _ = step(f'retrigger-on-{cycle}', [[0x90, 60, 100]])
        assert count == 1, 'Retrigger allocation leak'
        count, audio = step(f'retrigger-off-{cycle}', [[0x80, 60, 0]], 1)
        assert count == 0 and np.max(np.abs(audio[-8192:])) == 0, 'Retrigger release leak'
    step('pedal-down', [[0xb0, 64, 127]])
    step('sustain-on', [[0x90, 60, 100]])
    count, audio = step('sustain-held', [[0x80, 60, 0]], 1)
    assert count == 1 and np.max(np.abs(audio[-8192:])) > 0, 'Pedal did not sustain'
    count, audio = step('pedal-up', [[0xb0, 64, 0]], 2)
    assert count == 0 and np.max(np.abs(audio[-44100:])) == 0, 'Pedal release leak'
    report = {'passed': True, 'rate': 44100, 'rows': rows,
              'scope': 'ROBOFULL native firmware allocation bitmap and PCM; 24 voices, eight excess notes, retrigger and sustain',
              'limits': 'No steal-order claim, disk overlap, panic sequence or hardware parity; enabled slots are not a per-voice spectral mix proof'}
    (state / 'polyphony-results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
