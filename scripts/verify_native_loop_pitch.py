"""Private declarative loop/pitch fixture and native acceptance; no guest writes."""
import hashlib
import json
import math

import numpy as np


def build_fixture(source, state):
    original = source.read_bytes()
    assert hashlib.sha256(original).hexdigest() == '65f8a8353d4e5bedfa1cc0f0d600012cf6946cda0129ec96363f49a91cb43060'
    if state.exists() and any(state.iterdir()):
        raise ValueError('Use a fresh private state directory')
    state.mkdir(parents=True, exist_ok=True)
    disk = bytearray(original)
    rows = []
    for mode in range(7):
        for offset, semitones in enumerate((-12, 0, 12)):
            partial = mode * 3 + offset
            note = 48 + partial
            coarse = semitones - (note - (60 + mode))
            assert -24 <= coarse <= 24
            record = bytearray(original[0x10e00 + mode * 128:0x10e80 + mode * 128])
            record[0x15] = coarse & 255
            disk[0x10e00 + partial * 128:0x10e80 + partial * 128] = record
            disk[0x8e20 + note - 21] = partial
            rows.append({'mode': mode, 'note': note, 'partial': partial,
                         'coarse': coarse, 'semitones': semitones,
                         'pitch_word': {-12: 8192, 0: 16384, 12: 32768}[semitones]})
    assert len(disk) == 737280 and disk[0x18e00:] == original[0x18e00:]
    output = state / 'pitch-loops.img'
    output.write_bytes(disk)
    (state / 'pitch-fixture.json').write_text(json.dumps({
        'source_sha256': hashlib.sha256(original).hexdigest(),
        'fixture_sha256': hashlib.sha256(disk).hexdigest(), 'rows': rows,
        'changes': 'Partial copies/coarse tuning and patch key map only; all samples/PCM unchanged'}, indent=2), encoding='utf-8')
    return output


def qualify(runtime, state):
    fixture = json.loads((state / 'pitch-fixture.json').read_text(encoding='utf-8'))
    runtime.request('pause')
    runtime.request('audio_capture', enabled=True)

    def render(frames):
        blocks = []
        while frames:
            n = min(8192, frames)
            _, pcm = runtime.render_audio(n)
            blocks.append(np.frombuffer(pcm, dtype='<f4').reshape(-1, 2))
            frames -= n
        audio = np.concatenate(blocks)
        assert np.isfinite(audio).all() and np.max(np.abs(audio)) < 1
        return audio

    rows = []
    for row in fixture['rows']:
        runtime.request('bus_trace', enabled=True, first=0x100000, last=0x1007ff)
        start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 2048
        runtime.schedule_midi([{'sample': start, 'bytes': [0x90, row['note'], 127]},
                               {'sample': start + 3 * 44100, 'bytes': [0x80, row['note'], 0]}])
        intro = render(8192)
        trace = runtime.request('bus_trace', enabled=False)[0]
        assert trace['dropped'] == 0, 'Pitch observation overflow'
        select = None
        words = []
        for access in trace['rows']:
            if access['kind'] != 'w':
                continue
            address = access['address']
            if 0x100400 <= address < 0x100600:
                select = (address - 0x100400) // 2
            elif address == 0x100014 and select is not None and select % 8 == 2:
                words.append(access['data'] & 0xffff)
        assert row['pitch_word'] in words, (row, words)
        audio = np.concatenate([intro, render(5 * 44100 - len(intro))])
        assert np.max(np.abs(audio[-44100:])) == 0, 'Loop pitch failed to release'
        nz = np.flatnonzero(np.max(np.abs(audio), axis=1) > 1e-8)
        assert len(nz), 'Silent pitched note'
        measured = dict(row, observed_pitch_words=words, peak=float(np.max(np.abs(audio))), trace=trace['rows'])
        if row['mode'] in (2, 5):
            duration = int(nz[-1] - nz[0] + 1)
            expected = 2047 * 16384 / row['pitch_word']
            assert abs(duration - expected) < 8, (row, duration, expected)
            assert np.max(np.abs(audio[44100:2*44100])) == 0
            measured.update(duration_frames=duration, expected_duration_frames=expected)
        else:
            # At +12, use two cycles when the source length is odd so the lag
            # is integral; pitch-register evidence separately verifies speed.
            base = {0: 1023, 1: 1023, 3: 1023, 4: 2046, 6: 1024}[row['mode']]
            lag = base * 2 if row['semitones'] == -12 else base
            a = audio[44100:2*44100, 0]
            correlation = float(np.dot(a[:-lag], a[lag:]) / np.sqrt(np.dot(a[:-lag], a[:-lag]) * np.dot(a[lag:], a[lag:])))
            assert correlation > .99, (row, lag, correlation)
            measured.update(recurrence_lag=lag, recurrence_correlation=correlation)
        rows.append(measured)
    start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 2048
    events = []
    for i, row in enumerate(fixture['rows'] + list(reversed(fixture['rows']))):
        on = start + i * 4410
        events.extend([{'sample': on, 'bytes': [0x90, row['note'], 100]},
                       {'sample': on + 6615, 'bytes': [0x80, row['note'], 0]}])
    runtime.schedule_midi(sorted(events, key=lambda e: e['sample']))
    audio = render(8 * 44100)
    assert np.max(np.abs(audio)) > 0 and np.max(np.abs(audio[-44100:])) == 0
    result = {'passed': True, 'rate': 44100, 'fixture': fixture, 'rows': rows,
              'transition_note_ons': 42, 'transition_peak': float(np.max(np.abs(audio))),
              'transition_silent_tail_frames': 44100,
              'limits': 'Named octave changes through partial/key mapping and overlapping notes; no continuous bend/glide, click-free guarantee, arbitrary pitch ratios or new hardware interpolation parity'}
    (state / 'loop-pitch-results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('fixture', 'rows')}, indent=2))
