"""Opt-in MOTU loopback fixture and independent packaged-sampling readback.

Tone output requires physical MOTU outputs 3/4 connected to inputs 1/2.
The low-level source is separate from the sampler; no guest state is injected.
"""
import argparse
import hashlib
import json
from pathlib import Path
import os
import struct
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def tone(args):
    os.environ['SD_ENABLE_ASIO'] = '1'
    import sounddevice as sd
    apis = sd.query_hostapis()
    device = next(i for i, d in enumerate(sd.query_devices())
                  if d['name'] == 'MOTU Pro Audio v2' and apis[d['hostapi']]['name'] == 'ASIO')
    t = np.arange(int((args.seconds+1)*44100))/44100
    pcm = (np.column_stack((np.sin(2*np.pi*440*t), np.sin(2*np.pi*880*t))) * 256).astype('<i2')
    cursor = 0

    def callback(output, frames, timing, status):
        nonlocal cursor
        output.fill(0)
        count = min(frames, len(pcm)-cursor)
        output[:count] = pcm[cursor:cursor+count]
        cursor += count
        if count < frames:
            raise sd.CallbackStop

    with sd.OutputStream(device=device, samplerate=44100, channels=2, dtype='int16',
                         callback=callback, extra_settings=sd.AsioSettings(channel_selectors=[2, 3])):
        args.ready.write_text(json.dumps({'driver': 'MOTU Pro Audio v2 ASIO', 'outputs': [3, 4],
                                         'rate': 44100, 'tones_hz': [440, 880], 'amplitude_pcm16': 256}))
        time.sleep(args.seconds)


def verify(args):
    from s760_runtime import NativeRuntime, RuntimeConfig
    work, package = args.work.resolve(), args.package.resolve()
    assert (package/'scripts/s760_runtime.lua').read_bytes() == (ROOT/'scripts/s760_runtime.lua').read_bytes(), 'Package/source protocol differ'
    ui = json.loads((work/'result.json').read_text(encoding='utf-8'))
    assert ui['passed'] and ui['interface'] == 'Packaged WebView2' and ui['throttle']
    disk_path = work/'library/CAPTURED.IMG'
    disk = disk_path.read_bytes()
    assert hashlib.sha256(disk).hexdigest() == ui['saved_sha256']
    rows = []
    for name in ('recorded', 'restored', 'cold'):
        state = work/('native-'+name)
        assert not state.exists(), 'Use fresh native verification directories'
        dump = state/'wave.bin'
        cfg = RuntimeConfig(package/'mame-source/mames760.exe', ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
                            ROOT/'roms/System/S760224.IMG', state, disk_path,
                            sound=False, throttle=False, wave_dump=dump,
                            experimental_adc=True)
        with NativeRuntime(cfg) as rt:
            def wait(seconds):
                target = rt.request('status')[0]['seconds'] + seconds
                deadline = time.monotonic()+90
                while rt.request('status')[0]['seconds'] < target:
                    assert time.monotonic() < deadline, 'Native time stopped'
                    time.sleep(.01)

            def click(x, y):
                rt.request('pointer', x=x, y=y); wait(.2)
                rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
                rt.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.2)

            if name != 'cold':
                rt.request('pause'); rt.load_checkpoint(work/(name+'.s760state')); rt.request('resume'); wait(1)
            else:
                wait(20)
                rt.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=True)
                rt.request('button', port=':NATIVE_MEDIA', name='Insert Sample Floppy', down=False)
                click(118,5);wait(2);click(80,22);wait(8)
                click(20,22);click(25,54);wait(2);click(10,98);click(76,98);wait(35)
        wave = dump.read_bytes()
        offset, disk_offset = 16, 0x2ac00
        channels = []
        for channel, expected in enumerate((440, 880)):
            record = disk[0x18e00+channel*48:0x18e00+(channel+1)*48]
            assert record[:11] == b'NEW:Unnamed' and record[15] == ord('LR'[channel]), record.hex()
            frames = (struct.unpack_from('<I', record, 24)[0] >> 8)+1
            size = struct.unpack_from('<H', record, 42)[0]*9216
            # Require enough captured cycles for a meaningful tone check. UI
            # wall-clock waits do not promise a particular firmware duration.
            assert 4410 < frames < 132300 and size >= frames*2, (frames, size)
            pcm = wave[offset:offset+size]
            assert pcm == disk[disk_offset:disk_offset+size], (name, channel, 'Wave/disk differ')
            samples = np.frombuffer(pcm[:frames*2], dtype='<i2').astype(float)
            trim = min(4410, frames//10)
            steady = samples[trim:-trim]
            fft_size = max(131072, len(steady))
            frequency = float(np.argmax(abs(np.fft.rfft(steady*np.hanning(len(steady)), n=fft_size)))*44100/fft_size)
            assert abs(frequency-expected) < 3, (channel, frequency)
            peak = float(np.max(abs(samples)))
            assert 10 < peak < 32767 and not any(pcm[frames*2:])
            channels.append({'channel': channel, 'frames': frames, 'allocation_bytes': size,
                             'frequency_hz': frequency, 'peak_pcm16': peak,
                             'pcm_sha256': hashlib.sha256(pcm).hexdigest(), 'metadata_hex': record.hex(),
                             'wave_disk_equal': True})
            offset += size; disk_offset += size
        rows.append({'process': name, 'channels': channels})
    assert rows[0]['channels'] == rows[1]['channels'] == rows[2]['channels']
    result = {'passed': True, 'interface': ui, 'native_readback': rows,
              'scope': 'Physical MOTU stereo input, normal-speed packaged WebView sampling/Save/session restore; independent cold native Sample Load',
              'limitations': ['Windows MME does not measure physical driver losses or latency',
                              'No clean-machine, alternate-rate, long-duration or final-release claim',
                              'Device output playback is not measured by this sampling test']}
    (work/'verification.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    source = commands.add_parser('tone')
    source.add_argument('--seconds', type=float, default=180)
    source.add_argument('--ready', type=Path, required=True)
    check = commands.add_parser('verify')
    check.add_argument('--package', type=Path, required=True)
    check.add_argument('--work', type=Path, required=True)
    args = parser.parse_args()
    tone(args) if args.command == 'tone' else verify(args)
