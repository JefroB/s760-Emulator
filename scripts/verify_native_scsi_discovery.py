"""Firmware SCSI Scan/unsupported-media recovery; successful SCSI Load is separate.

Uses absent, private zero-filled10MiB and truncated1024-byte HD0 profiles.
No firmware, guest RAM or PC changes. Pixel signatures identify visually checked
OS2.24 drive/error labels; read-only traces establish actual command/DMA activity.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
import time
from unittest.mock import patch

import numpy as np
from PIL import Image

from s760_runtime import NativeRuntime, RuntimeConfig

ROOT = Path(__file__).resolve().parents[1]
DRIVE_CROP = (256, 144, 560, 160)
ERROR_SIGNATURE = '7e9e3d6adf675b35166da6f205289c9b4afddb89fed74ddbdbf375c3eff4385e'
DRIVE_SIGNATURES = {
    'absent': 'ef1b224c9495e70cb7d1915b7f838304aeee8852e2b7fd26ff8a2bf08f85ec5e',
    'unformatted': '3d97c1db4e2e4031947e371452325d6fdd58272b5fcd6711e41bfc6b506090ff',
}


class LoggedRuntime(NativeRuntime):
    """Enable MAME's diagnostic log in this private runtime's working directory."""
    def _start(self, timeout):
        launch = subprocess.Popen
        def logged(command, **kwargs):
            return launch([*command, '-log'], **kwargs)
        with patch('s760_runtime.subprocess.Popen', side_effect=logged):
            super()._start(timeout)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    args = parser.parse_args()
    work = args.state_dir.resolve()
    if work.exists() and any(work.iterdir()):
        parser.error('Use a fresh private state directory')
    work.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'roms/FDD/ROBOFULL.IMG'
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    assert source_digest == '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae'
    rows = []
    for label, size in (('absent', None), ('blank-10MiB', 10*1024*1024), ('truncated-1024', 1024)):
        state = work / label
        state.mkdir()
        floppy = state / 'private-samples.img'
        shutil.copyfile(source, floppy)
        native = state / 'runtime'
        image = native / 'roms/SCSI/HD00_512.img'
        if size is not None:
            image.parent.mkdir(parents=True)
            image.write_bytes(bytes(size))
        cfg = RuntimeConfig(ROOT/'mame-source/mames760.exe', ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
                            ROOT/'roms/System/S760224.IMG', native, floppy,
                            sound=False, throttle=False, wave_dump=state/'wave.bin')
        with LoggedRuntime(cfg) as runtime:
            def wait(seconds):
                until = runtime.request('status')[0]['seconds'] + seconds
                deadline = time.monotonic() + 60
                while runtime.request('status')[0]['seconds'] < until:
                    assert time.monotonic() < deadline, 'Firmware clock stopped'
                    time.sleep(.005)

            def click(x, y):
                runtime.request('pointer', x=x, y=y); wait(.2)
                runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=True); wait(.1)
                runtime.request('button', port=':NATIVE_MOUSE_BUTTONS', name='Mouse Left', down=False); wait(.2)

            def screenshot(name):
                image = Image.frombytes('RGBA', (640,480), runtime.request('frames')[1][0][6:]).convert('RGB')
                image.save(state / (name+'.png'))
                return image

            wait(20)
            screenshot('boot')
            click(118,5); wait(1); click(80,22); wait(8); click(140,22); wait(2)
            runtime.request('pause')
            # Restrict to SCMD plus the observer's fixed gate-register subset,
            # avoiding a truncated trace of every data byte during full Scan.
            runtime.request('bus_trace', enabled=True, first=0x102404, last=0x102404)
            runtime.request('resume')
            click(96,78)
            runtime.request('button', port=':PANEL2', name='Panel F3', down=True); wait(.2)
            runtime.request('button', port=':PANEL2', name='Panel F3', down=False); wait(4)
            runtime.request('pause')
            trace = runtime.request('bus_trace', enabled=False)[0]
            commands = [r['data'] for r in trace['rows'] if r['kind']=='w' and r['address']==0x102404]
            if size is not None:
                assert any((c & 0xe0)==0x20 for c in commands), 'Scan did not issue SELECT'
            picture = screenshot('scan')
            signature = hashlib.sha256(picture.crop(DRIVE_CROP).tobytes()).hexdigest()
            expected = 'absent' if size is None else 'unformatted'
            assert signature == DRIVE_SIGNATURES[expected], 'Unexpected original-firmware target0 label'
            if size is not None:
                assert 0xe4 in commands and 0xc4 in commands and 0x84 in commands
            runtime.request('resume')
            if size is not None:
                click(100,38); wait(3)
                picture = screenshot('unsupported-selected')
                error_signature = hashlib.sha256(picture.crop((32,32,256,48)).tobytes()).hexdigest()
                # Visually reviewed original-firmware red "Not Formatted" message.
                assert error_signature == ERROR_SIGNATURE, 'Unsupported image did not report Not Formatted'
                click(140,22); wait(1)
            runtime.insert_media(floppy)
            click(100,70); wait(8)
            click(50,34); wait(2); click(76,98); wait(35)
            click(10,5); click(15,22); wait(3)
            screenshot('recovered-perform')
            runtime.request('pause'); runtime.request('audio_capture', enabled=True)
            start = math.ceil(runtime.request('status')[0]['seconds']*44100)+2048
            runtime.schedule_midi([{'sample':start,'bytes':[0x90,60,100]},
                                   {'sample':start+44100,'bytes':[0x80,60,0]}])
            audio = b''.join(runtime.render_audio(8192)[1] for _ in range(20))
            pcm = np.frombuffer(audio, dtype='<f4')
            assert np.isfinite(pcm).all() and 0 < np.max(np.abs(pcm)) < 1
            assert np.max(np.abs(pcm[-88200:])) == 0, 'Recovery left stuck notes'
            status = runtime.request('status')[0]
            assert status['midi_pending']==0 and not status['midi_error']
            runtime.request('audio_capture', enabled=False); runtime.request('resume')
            media = runtime.media_status()
            assert not media['dirty'] and not media['busy']
            exported = state/'recovered-floppy.img'
            runtime.export_media(exported)
            assert exported.read_bytes() == source.read_bytes()
        wave = (state/'wave.bin').read_bytes()
        dma = re.findall(r'\[NATIVESCSIDMA\] RAM=([0-9a-f]+) count=([0-9a-f]+) control=47',
                         (native/'error.log').read_text(encoding='utf-8'))
        assert bool(dma) == (size is not None), 'Unexpected original-firmware SPC DMA activity'
        original = source.read_bytes()
        for sample in range(13):
            assert wave[16+sample*9216:16+(sample+1)*9216] == original[0x2ac00+sample*9216:0x2ac00+(sample+1)*9216]
        if size is not None:
            assert image.read_bytes() == bytes(size), 'SCSI probe modified backing image'
        result = {'profile':label, 'scsi_bytes':size, 'firmware_label':expected,
                  'scan_label_sha256':signature, 'scan_trace':trace,
                  'firmware_dma47': [{'destination':int(a,16),'bytes':int(n,16)} for a,n in dma],
                  'recovered_floppy_sample_bytes':119808, 'recovery_peak':float(np.max(np.abs(pcm))),
                  'silent_release_frames':44100, 'media':media}
        rows.append(result)
        print(json.dumps({k:v for k,v in result.items() if k!='scan_trace'}), flush=True)
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_digest
    report = {'passed':True, 'rows':rows, 'source_sha256':source_digest,
              'scope':'Original-firmware F3 Scan, absence/unsupported-image handling and floppy Load/playback recovery',
              'limits':'HD0 512-byte-sector development target only; bounded traces may drop rows and do not establish exhaustive bus coverage. No successful SCSI sample Load, SCSI Save, hot-plug, full DMA/arbitration or physical timing claim'}
    (work/'discovery-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__ == '__main__':
    main()
