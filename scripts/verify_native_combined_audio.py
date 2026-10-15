"""Named normal/diagnostic combined-path native acceptance; physical fidelity separate."""
import json
import math

import numpy as np


def qualify(runtime, state, baseline=False, normal=False):
    runtime.request('pause')
    runtime.request('audio_capture', enabled=True)
    patches = [(0, 'bypass'), (13, 'LP-C32-R0'), (14, 'LP-C64-R0'),
               (15, 'LP-C96-R0'), (17, 'LP-C64-R64'),
               (1, 'LP-sweep-R0'), (5, 'BP-sweep-R0'), (9, 'HP-sweep-R0')]
    rows = []
    if baseline:
        patches = patches[:2]
    for program, label in patches:
        for pan in (0, 64, 127):
            for note in ((60,) if baseline else (57, 60, 63)):
                start = math.ceil(runtime.request('status')[0]['seconds'] * 44100) + 2048
                runtime.schedule_midi([
                    {'sample': start, 'bytes': [0xc0, program]},
                    {'sample': start + 256, 'bytes': [0xb0, 10, pan]},
                    {'sample': start + 2048, 'bytes': [0x90, note, 100]},
                    {'sample': start + 4 * 44100, 'bytes': [0x80, note, 0]},
                ])
                blocks = []
                remaining = 6 * 44100
                while remaining:
                    n = min(8192, remaining)
                    _, pcm = runtime.render_audio(n)
                    blocks.append(np.frombuffer(pcm, dtype='<f4').reshape(-1, 2))
                    remaining -= n
                audio = np.concatenate(blocks)
                assert np.isfinite(audio).all() and 0 < np.max(np.abs(audio)) < 1
                assert np.max(np.abs(audio[-44100:])) == 0, 'Combined path did not release'
                held = audio[44100:3*44100]
                peaks = np.max(np.abs(held), axis=0)
                if pan == 0:
                    assert peaks[0] > 0 and peaks[1] == 0, 'Left pan routing differs'
                elif pan == 127:
                    assert peaks[1] > 0 and peaks[0] == 0, 'Right pan routing differs'
                else:
                    assert np.array_equal(held[:, 0], held[:, 1]), 'Centre pan is asymmetric'
                mono = held[:, int(pan == 127)]
                spectrum = np.abs(np.fft.rfft(mono * np.hanning(len(mono)))) ** 2
                frequencies = np.fft.rfftfreq(len(mono), 1/44100)
                low = float(np.sum(spectrum[frequencies < 2000]))
                high = float(np.sum(spectrum[frequencies > 8000]))
                rows.append({'program': program, 'patch': label, 'pan': pan, 'note': note,
                             'left_peak': float(peaks[0]), 'right_peak': float(peaks[1]),
                             'rms': float(np.sqrt(np.mean(mono ** 2))),
                             'low_high_power_ratio': low / max(high, 1e-30),
                             'early_rms': float(np.sqrt(np.mean(audio[11025:22050] ** 2))),
                             'late_rms': float(np.sqrt(np.mean(audio[3*44100:4*44100] ** 2))),
                             'silent_release_frames': 44100})
                np.save(state / f'combined-p{program}-pan{pan}-note{note}.npy', audio)
    def row(program):
        return next(r for r in rows if r['program'] == program and r['pan'] == 64 and r['note'] == 60)
    if not baseline:
        assert row(13)['rms'] < row(0)['rms'] * .8, 'LP cutoff did not attenuate noise'
        assert row(13)['low_high_power_ratio'] > row(15)['low_high_power_ratio'] * 2, 'Cutoff change did not alter spectrum'
        assert abs(row(1)['late_rms'] - row(1)['early_rms']) > row(1)['early_rms'] * .05, 'Moving filter did not change output'
    else:
        assert row(13)['rms'] < row(0)['rms'] * .8, 'Normal LP cutoff did not attenuate noise'
    report = {'passed': True, 'profile': 'normal stereo/filter/interpolation' if normal else 'explicit diagnostic combined',
              'rate': 44100, 'cases': len(rows), 'rows': rows,
              'limits': 'Named patches/pan/pitch at native44.1kHz, forward loops and finite/release checks; no exact moving/resonant filter parity, other modes/clocks, packaged qualification'}
    (state / 'combined-audio-results.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k != 'rows'}, indent=2))
