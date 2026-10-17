"""Observe native write/application timing and same-note static controls.

Use a fresh private state folder and a prepared MODDIAG.IMG. No guest writes
except original firmware loading the disk and ordinary MIDI/input controls.
"""
import argparse
import hashlib
import json
import math
import subprocess
from pathlib import Path
from unittest.mock import patch

import numpy as np
import soundfile as sf
from s760_runtime import NativeRuntime, RuntimeConfig
from verify_native_scsi_save import controls
from verify_native_roland_load import render

ROOT = Path(__file__).resolve().parents[1]


def render_with_origin(runtime, frames, block_frames=8192):
    """Capture PCM with its observed speaker-stream origin; never infer from status."""
    if type(frames) is not int or frames <= 0 or type(block_frames) is not int or not 1 <= block_frames <= 8192:
        raise ValueError('Expected positive frame count and bounded render block')
    chunks, blocks = [], []
    remaining = frames
    stream_origin = capture_origin = None
    while remaining:
        count = min(remaining, block_frames)
        meta, pcm = runtime.render_audio(count)
        first, capture_first = meta.get('stream_first_sample'), meta.get('first_sample')
        if (meta.get('stream_contiguous') is not True or type(first) is not int or first < 0
                or type(capture_first) is not int or capture_first < 0):
            raise ValueError('Unqualified PCM origin; observed contiguous stream metadata required')
        if (meta.get('rate') != 44100 or meta.get('channels') != 2
                or meta.get('frames') != count or meta.get('dropped_frames') != 0 or len(pcm) != count * 8):
            raise ValueError('Incomplete or discontinuous PCM capture')
        offset = frames - remaining
        if stream_origin is None:
            stream_origin, capture_origin = first, capture_first
        if first != stream_origin + offset or capture_first != capture_origin + offset:
            raise ValueError('Discontinuous PCM frame mapping')
        blocks.append(dict(wav_frame=offset, frames=count, stream_first_sample=first,
                           capture_first_sample=capture_first))
        chunks.append(pcm)
        remaining -= count
    return b''.join(chunks), dict(stream_first_sample=stream_origin,
        capture_first_sample=capture_origin, frames=frames, rate=44100, blocks=blocks,
        qualification='Observed speaker-buffer sample indices; not absolute MIDI/audio latency.')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--state-dir', type=Path, required=True)
    ap.add_argument('--image', type=Path, required=True)
    ap.add_argument('--executable', type=Path, default=ROOT/'mame-source/mames760.exe')
    ap.add_argument('--trace', action='store_true')
    ap.add_argument('--source-candidate', action='store_true',
                    help='Opt-in forward-loop source reconstruction experiment')
    ap.add_argument('--checkpoint-in', type=Path)
    ap.add_argument('--checkpoint-out', type=Path)
    ap.add_argument('--moving-notes', type=int, nargs='+',
                    help='Render only the moving survey at these numeric MIDI notes')
    args = ap.parse_args()
    if args.moving_notes and any(not 21 <= note <= 108 for note in args.moving_notes):
        ap.error('Moving notes must be MIDI21..108')
    state = args.state_dir.resolve()
    if state.exists() and any(state.iterdir()):
        ap.error('Use a fresh private state folder')
    state.mkdir(parents=True, exist_ok=True)
    trace_path = state/'application.csv'
    launch = subprocess.Popen

    def observe(command, **kwargs):
        if args.source_candidate:
            kwargs['env'] = dict(kwargs['env'], S760_NATIVE_SOURCE_CANDIDATE='1')
        if args.trace:
            kwargs['env'] = dict(kwargs['env'], S760_MODULATION_TRACE=str(trace_path))
        return launch(command, **kwargs)

    cfg = RuntimeConfig(args.executable.resolve(), ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT/'roms/System/S760224.IMG', state, args.image.resolve(),
        sound=False, throttle=False, wave_dump=state/'wave.bin')
    rows = []
    with patch('s760_runtime.subprocess.Popen', observe), NativeRuntime(cfg) as r:
        wait, button, click, shot, _ = controls(r, state)
        if args.checkpoint_in:
            r.request('pause'); r.load_checkpoint(args.checkpoint_in)
        else:
            wait(25); button(':NATIVE_MEDIA', 'Insert Sample Floppy')
            click(118,5); click(80,22); wait(8); click(50,34); click(76,98)
            wait(35); click(10,5); click(15,22); wait(3); shot('loaded.png')
            r.request('pause')
        if args.checkpoint_out:
            r.save_checkpoint(args.checkpoint_out)
        r.request('audio_capture', enabled=True)
        cases = ([(0, f'moving-note{note}', note) for note in args.moving_notes]
            if args.moving_notes else
            [(program, name, 73) for program, name in enumerate(
                ['moving','static64','static80','static96','bypass'])])
        for program, name, note in cases:
            origin = r.request('status')[0]['seconds']
            start = math.ceil(origin*44100)+2048
            on = start+4410
            off = on+3*44100
            events = [dict(sample=start,bytes=[0xc0,program]),
                dict(sample=start+1000,bytes=[0xb0,7,127]),
                dict(sample=start+2000,bytes=[0xb0,10,64]),
                dict(sample=start+3000,bytes=[0xb0,64,0]),
                dict(sample=on,bytes=[0x90,note,127]),
                dict(sample=off,bytes=[0x80,note,0])]
            r.schedule_midi(events)
            pcm, audio_origin = render_with_origin(r, 7*44100)
            audio = np.frombuffer(pcm,dtype='<f4').reshape(-1,2)
            status = r.request('status')[0]
            assert status['midi_pending']==0 and not status['midi_error']
            assert np.isfinite(audio).all() and 0<np.max(np.abs(audio))<1
            assert np.max(np.abs(audio[-44100:]))==0
            sf.write(state/f'{name}.wav',audio,44100,subtype='FLOAT')
            row = dict(name=name,program=program,note=note,origin_seconds=origin,
                origin_seconds_qualification='MIDI scheduling snapshot only; not WAV frame zero.',
                audio_origin=audio_origin,
                scheduled_enqueue_wav_frames=[e['sample']-audio_origin['stream_first_sample'] for e in events],
                events=events,delivered=status['midi_delivered'],
                peak=float(np.max(np.abs(audio))),pcm_sha256=hashlib.sha256(audio.tobytes()).hexdigest())
            rows.append(row)
            print(name,row['peak'],flush=True)
        r.request('audio_capture',enabled=False)
    if args.trace:
        assert trace_path.exists() and trace_path.read_text().startswith('# dropped=0\n')
    image = args.image.read_bytes()
    wave = (state/'wave.bin').read_bytes()
    # Every partial references sample0. Firmware performance Load imports the
    # referenced allocation, not all unused sample slots on the source disk.
    assert wave[16:16+9216] == image[0x2ac00:0x2ac00+9216]
    result = dict(passed=True,cases=rows,trace=args.trace,
        source_candidate=args.source_candidate,
        executable_sha256=hashlib.sha256(args.executable.read_bytes()).hexdigest(),
        image_sha256=hashlib.sha256(image).hexdigest(),exact_loaded_pcm_bytes=9216,
        limits='Native diagnostic controls and instrumentation only. No hardware cutoff trace or production timing correction.')
    (state/'capture.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()
