"""Native scheduler acceptance: append, atomic rejection and capacity, no RAM forcing."""
import argparse
import json
import math
from pathlib import Path
from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    cfg = RuntimeConfig(ROOT/'mame-source/mames760.exe', ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
                        ROOT/'roms/System/S760224.IMG', args.state_dir, sound=False, throttle=False)
    with NativeRuntime(cfg) as runtime:
        now = runtime.request('pause')[0]['seconds']
        start = math.ceil(now*44100)+10000
        event = lambda timestamp: {'sample': timestamp, 'bytes': [248]}
        runtime.request('schedule_midi', events=[event(start)]*200)

        def reject(events, append=True):
            before = runtime.request('status')[0]['midi_pending']
            try:
                runtime.request('schedule_midi', events=events, append=append)
            except RuntimeError:
                pass
            else:
                raise AssertionError('Invalid schedule accepted')
            assert runtime.request('status')[0]['midi_pending'] == before

        reject([event(start+1)], append=False)
        reject([event(start-1)])
        reject([event(start+1)]*57)
        runtime.request('schedule_midi', events=[event(start+1)]*56, append=True)
        reject([event(start+2)])
        runtime.request('audio_capture', enabled=True)
        for _ in range(2):
            runtime.render_audio(8192)
        status = runtime.request('status')[0]
        assert status['midi_pending'] == 0 and status['midi_error'] == ''
        delivered = status['midi_delivered']
        assert len(delivered) == 256
        assert [e['sample'] for e in delivered] == [start]*200+[start+1]*56
        error = max(abs(e['seconds']*44100-e['sample']) for e in delivered)
        assert error < .001
        result = {'delivered': 256, 'enqueue_error_samples': error,
                  'invalid_append_atomic': True, 'capacity': 256}
    (args.state_dir/'result.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
