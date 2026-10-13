"""Qualify OS 2.24 sampling postprocessing DMA, not live ADC recording.

Uses only firmware controls and read-only diagnostic taps. A silent, unconnected
ADC and unsupported recording-position reads remain explicit limitations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from PIL import Image
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--executable', type=Path, default=ROOT / 'mame-source/mames760.exe')
    args = parser.parse_args()
    state = args.state_dir.resolve()
    cfg = RuntimeConfig(args.executable.resolve(),
                        ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN',
                        ROOT / 'roms/System/S760224.IMG', state,
                        sound=False, throttle=False)
    with NativeRuntime(cfg) as runtime:
        def wait(seconds):
            target = runtime.request('status')[0]['seconds'] + seconds
            deadline = time.monotonic() + 60
            while runtime.request('status')[0]['seconds'] < target:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Native sampling DMA workflow stopped advancing')
                time.sleep(.01)

        def click(x, y):
            runtime.request('pointer', x=x, y=y)
            wait(.2)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True)
            wait(.1)
            runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False)
            wait(.2)

        def picture(name):
            frame = runtime.request('frames')[1][0]
            image = Image.frombytes('RGBA', (640, 480), frame[6:])
            image.save(state / name)
            return image

        wait(20)
        click(100, 5)
        click(80, 22)
        wait(3)
        picture('sampling.png')
        runtime.request('pause')
        runtime.request('bus_trace', enabled=True)
        runtime.request('resume')
        wait(.2)
        runtime.request('pause')
        meter = runtime.request('bus_trace', enabled=False)[0]
        assert any(r['address'] == 0x10001c and r['data'] == 0xffff for r in meter['rows']), meter
        runtime.request('resume')
        click(76, 98)  # Ready; firmware asks for a new sample name.
        click(62, 66)  # Accept NEW:Unnamed.
        picture('armed.png')
        runtime.request('pause')
        runtime.request('bus_trace', enabled=True, first=0x10000c, last=0x10000f)
        runtime.request('resume')
        click(14, 98)  # Start, rather than Cancel at x76.
        wait(12)
        runtime.request('pause')
        transfer = runtime.request('bus_trace', enabled=False)[0]
        rows = transfer['rows']
        assert any(r['kind'] == 'w' and r['address'] == 0x11c and r['data'] == 0xa700 for r in rows)
        assert any(r['kind'] == 'w' and r['address'] == 0x118 and r['data'] == 0x2400 for r in rows)
        polls = [r for r in rows if r['kind'] == 'r' and r['address'] == 0x118 and r['pc'] == 0x7410]
        assert polls and all(r['data'] == 0 for r in polls), 'BUG-043: A7 count did not exhaust'
        completed = picture('postprocessed.png')
        # Completed waveform view contains a black plot with a white zero line.
        # The former stuck Now Working screen is solid blue in this rectangle.
        assert completed.getpixel((100, 300))[:3] == (0, 0, 0), 'Firmware did not reach waveform review'
        assert any(completed.getpixel((100, y))[:3] == (255, 255, 255)
                   for y in range(270, 375)), 'Waveform zero line is missing'
        assert len(json.dumps(transfer).encode()) < 65536
        runtime.request('resume')
        click(140, 98)  # End returns to Sampling.
        wait(2)
        picture('ended.png')
    result = {
        'result': 'pass', 'profile': 'OS 2.24 synchronous A7 sampling postprocessing DMA only',
        'count_exhausted': True, 'waveform_review_reached': True,
        'trace_capacity': 256, 'trace_dropped': transfer['dropped'],
        'trace_limit': 'Read polls are aggregated; writes after capacity are counted as dropped.',
        'unsupported_meter_read': '0x10001c returns 0xffff; ADC and recording position remain unimplemented.',
        'limitations': ['No external input, recorded PCM integrity, physical timing or sampling acceptance claim.'],
        'identities': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                       for p in (cfg.executable, cfg.boot_rom, cfg.system_disk,
                                 ROOT / 'scripts/s760_runtime.lua',
                                 ROOT / 'mame-source/src/mame/roland/s760.cpp')},
    }
    (state / 'trace.json').write_text(json.dumps(transfer, indent=2), encoding='utf-8')
    (state / 'result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
