"""Observed speaker frame metadata survives varied pulls, capture resets and recall."""
import os
import csv
import json
from pathlib import Path
import subprocess
import sys

import numpy as np
import pytest
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from s760_runtime import NativeRuntime, RuntimeConfig


def test_native_pcm_origin_and_buffered_checkpoint(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    rom = ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'
    disk = ROOT / 'roms/System/S760224.IMG'
    if not all(p.is_file() for p in (exe, rom, disk)):
        pytest.skip('Native MAME and local firmware required')
    config = RuntimeConfig(exe, rom, disk, tmp_path / 'state', sound=False, throttle=False)
    with NativeRuntime(config) as runtime:
        runtime.request('pause')
        runtime.request('audio_capture', enabled=True)
        first = None
        position = 0
        observations = []
        for frames in [1, 127, 8192, 63, 2048]:
            meta, pcm = runtime.render_audio(frames)
            assert meta.get('stream_contiguous') is True, meta
            assert type(meta.get('stream_first_sample')) is int, meta
            assert meta['first_sample'] == position and len(pcm) == frames * 8
            if first is None:
                first = meta['stream_first_sample']
            assert meta['stream_first_sample'] == first + position
            observations.append(meta)
            position += frames
        checkpoint = tmp_path / 'buffered.s760state'
        runtime.save_checkpoint(checkpoint)
        meta, pcm = runtime.render_audio(4096)
        runtime.load_checkpoint(checkpoint)
        restored, replay = runtime.render_audio(4096)
        assert pcm == replay
        assert meta == restored
        assert meta['stream_contiguous'] is True
        runtime.request('audio_capture', enabled=True)
        reset, _ = runtime.render_audio(1024)
        assert reset['first_sample'] == 0 and reset['stream_contiguous'] is True
        assert reset['stream_first_sample'] >= meta['stream_first_sample'] + 4096
        (tmp_path / 'origins.json').write_text(json.dumps(dict(blocks=observations,
            checkpoint=meta, restored=restored, reset=reset), indent=2), encoding='utf-8')


def test_modulation_wav_origin_matches_native_source_trace(tmp_path):
    image = ROOT / 'temp/fixtures/modulation/MODDIAG.IMG'
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    if not all(p.is_file() for p in (image, exe, ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
                                    ROOT / 'roms/System/S760224.IMG')):
        pytest.skip('Native MAME, local firmware and private MODDIAG fixture required')
    state = tmp_path / 'modulation'
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/verify_modulation_application.py'),
        '--state-dir', str(state), '--image', str(image), '--executable', str(exe),
        '--trace', '--moving-notes', '73'], cwd=ROOT, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    case = json.loads((state / 'capture.json').read_text())['cases'][0]
    on, off = case['events'][4]['sample'], case['events'][5]['sample']
    with (state / 'application.csv').open() as trace:
        assert trace.readline().strip() == '# dropped=0'
        rows = [r for r in csv.DictReader(trace)
                if r['kind'] == 'a' and on <= int(r['audio_frame']) < off]
    first = rows[0]
    assert float(first['low_before']) == float(first['band_before']) == 0
    assert float(first['input']) != 0
    samples, rate = sf.read(state / 'moving-note73.wav', dtype='float32', always_2d=True)
    assert rate == 44100
    source_frame = int(first['audio_frame']) - case['audio_origin']['stream_first_sample']
    first_nonzero = int(np.flatnonzero(np.abs(samples[:, 0]) > 1e-12)[0])
    # LP starts with zero state: the first source sample updates band, and the
    # next output sample updates low. No cross-correlation or fitted shift.
    assert first_nonzero == source_frame + 1
