"""Read back combined packaged workflow evidence without supplying guest state."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def audio(args):
    meta = json.loads(args.meta.read_text(encoding='utf-8'))
    pcm = np.fromfile(args.raw, dtype='<f4').reshape(-1, 2)
    assert len(pcm) == meta['frames'] and len(pcm) > meta['rate']*4
    assert np.isfinite(pcm).all()
    peak = float(np.max(abs(pcm)))
    assert 1e-6 < peak < .9, peak
    # Select a steady interior of the observed note, independently of UI timing.
    indices = np.flatnonzero(np.max(abs(pcm), axis=1) > peak*.1)
    start, end = int(indices[0]), int(indices[-1])
    assert end-start > meta['rate'], 'Held note was not sustained for one second'
    steady = pcm[start+(end-start)//4:start+(end-start)//4+meta['rate'], 0]
    n = max(131072, len(steady))
    frequency = float(np.argmax(abs(np.fft.rfft(steady*np.hanning(len(steady)), n=n)))*meta['rate']/n)
    assert abs(frequency-20004.5) < 4, frequency
    tail_peak = float(np.max(abs(pcm[-meta['rate']:])) )
    assert tail_peak < 1e-7, ('Device note failed to release', tail_peak)
    result = {'passed': True, 'endpoint_capture': meta, 'peak': peak,
              'frequency_hz': frequency, 'last_second_peak': tail_peak,
              'silent_release': True, 'raw_sha256': hashlib.sha256(args.raw.read_bytes()).hexdigest(),
              'domain': 'Selected Windows WASAPI shared-mode digital output, not analog converter output'}
    args.out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')


def verify(args):
    from s760_runtime import NativeRuntime, RuntimeConfig
    from s760_readiness import labels
    from verify_packaged_edit_audio import measure
    package, work = args.package.resolve(), args.work.resolve()
    verification_root=args.state_dir.resolve() if args.state_dir else work/'native-verification'
    assert not verification_root.exists(), 'Use a fresh native verification directory'
    verification_root.mkdir(parents=True)
    ui = json.loads((work/'result.json').read_text(encoding='utf-8'))
    assert ui['passed'] and ui['throttle'] and ui['interface'] == 'Packaged WebView2'
    original = (ROOT/'roms/FDD/ROBOFULL.IMG').read_bytes()
    disk_path = work/'library/CAPTURED.IMG'
    disk = disk_path.read_bytes()
    assert hashlib.sha256(disk).hexdigest() == ui['sample_disk_sha256']
    new = []
    for i in range(64):
        offset = 0x18e00+(i//10)*512+(i%10)*48
        record = disk[offset:offset+48]
        # Firmware New derives a fresh name from the selected sample when a
        # library is loaded; an empty machine instead uses NEW:Unnamed.
        if i >= 13 and record[15] in (ord('L'),ord('R')) and struct.unpack_from('<H',record,42)[0]:
            new.append((i, record))
    assert len(new) == 2 and [r[15] for _, r in new] == [ord('L'), ord('R')], new
    expected_old = original[0x2ac00:0x2ac00+13*9216]
    assert disk[0x2ac00:0x2ac00+len(expected_old)] == expected_old
    native = []
    for name in ('recorded', 'restored', 'cold'):
        state = verification_root/name
        assert not state.exists(), 'Use fresh verification directories'
        dump = state/'wave.bin'
        cfg = RuntimeConfig(package/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
                            ROOT/'roms/System/S760224.IMG',state,disk_path,
                            sound=False,throttle=False,wave_dump=dump,experimental_adc=True)
        with NativeRuntime(cfg) as rt:
            def wait(seconds):
                target=rt.request('status')[0]['seconds']+seconds;deadline=time.monotonic()+90
                while rt.request('status')[0]['seconds']<target:
                    assert time.monotonic()<deadline
                    time.sleep(.01)
            def click(x,y):
                rt.request('pointer',x=x,y=y);wait(.2)
                rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
                rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.2)
            if name == 'cold':
                wait(20)
                rt.request('button',port=':NATIVE_MEDIA',name='Insert Sample Floppy',down=True)
                rt.request('button',port=':NATIVE_MEDIA',name='Insert Sample Floppy',down=False)
                click(118,5);wait(2);click(80,22);wait(8)
                click(20,22);click(25,54);wait(2);click(10,98);click(76,98)
                # Loading fifteen samples individually takes longer than the
                # earlier two-sample case. Observe the real firmware idle label
                # instead of ending the machine after a fixed 35-second wait.
                loading=False;deadline=time.monotonic()+90
                while True:
                    info,frames=rt.request('frames');seen=labels(frames[0])
                    loading=loading or bool(seen & {'load','working'})
                    if loading and {'disk','idle'} <= seen:break
                    assert time.monotonic()<deadline, 'Cold Sample Load did not complete'
                    wait(2)
            else:
                rt.request('pause');rt.load_checkpoint(work/(name+'.s760state'));rt.request('resume');wait(1)
        wave=dump.read_bytes()
        assert wave[16:16+len(expected_old)]==expected_old, (name,'Original samples changed')
        channels=[]
        # Sample Save to the empty formatted disk allocates contiguous clusters;
        # locate each sample by its serialized cluster, rather than guessing an index.
        for channel,(index,record) in enumerate(new):
            cluster,count=struct.unpack_from('<HH',record,40)
            size=count*9216;offset=(cluster-5)*9216
            pcm=disk[0x2ac00+offset:0x2ac00+offset+size]
            assert wave[16+offset:16+offset+size]==pcm, (name,index,'Wave/disk differ')
            frames=(struct.unpack_from('<I',record,24)[0]>>8)+1
            loop_end=struct.unpack_from('<I',record,28)[0]>>8
            sample_end=struct.unpack_from('<I',record,32)[0]>>8
            assert 4410<frames<132300 and frames-1<=loop_end<=sample_end<size//2
            values=np.frombuffer(pcm[:frames*2],dtype='<i2').astype(float)
            trim=min(frames//10,4410);steady=values[trim:-trim];n=max(131072,len(steady))
            hz=float(np.argmax(abs(np.fft.rfft(steady*np.hanning(len(steady)),n=n)))*44100/n)
            assert abs(hz-(440 if channel==0 else 880))<3,(index,hz)
            assert 10<np.max(abs(values))<32767, 'Recorded input is silent or clipped'
            # The default loop-start marker can precede a final DMA block.
            # Preserve that block too; only bytes beyond serialized sample end
            # are required to be zero padding. All allocation bytes matched above.
            assert not any(pcm[(sample_end+1)*2:]), 'Nonzero bytes beyond sample end'
            nonzero=np.flatnonzero(np.frombuffer(pcm,dtype='<i2'))
            channels.append({'index':index,'name':record[:16].decode('ascii'),'recorded_marker_frames':frames,
                             'sample_end_frame':sample_end,'nonzero_extent_frames':int(nonzero[-1])+1,
                             'padding_after_sample_end_zero':True,'allocation_bytes':size,'frequency_hz':hz,
                             'pcm_sha256':hashlib.sha256(pcm).hexdigest(),'wave_disk_equal':True})
        native.append({'process':name,'channels':channels,'original_sample_bytes_preserved':len(expected_old)})
    assert native[0]['channels']==native[1]['channels']==native[2]['channels']
    baseline=measure(package,ROOT/'roms/FDD/ROBOFULL.IMG',verification_root/'pcm-baseline',60)[0]
    edited=measure(package,work/'library/EDITED.IMG',verification_root/'pcm-edited',60)[0]
    restored=measure(package,disk_path,verification_root/'pcm-restored',60,work/'restored.s760state',experimental_adc=True)[0]
    assert baseline['frequency_hz']==edited['frequency_hz']==restored['frequency_hz']
    assert abs(edited['peak']/baseline['peak']-64/127)<.01
    assert abs(restored['peak']-edited['peak'])<1e-6
    result={'passed':True,'ui':ui,'sample_readbacks':native,'native_state_directory':str(verification_root),
            'native_program_playback':{'baseline':baseline,'edited_disk':edited,'combined_restored_session':restored},
            'limits':['Native readback is accelerated; actual UI workflow and Windows endpoint playback are normal-speed',
                      'Windows digital loopback is not analog output parity or physical latency measurement',
                      'No clean-machine or final-release qualification is inferred']}
    (work/'verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'samples':native[0]['channels'],'native_program_playback':result['native_program_playback']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);commands=parser.add_subparsers(dest='command',required=True)
    p=commands.add_parser('audio')
    for flag in ('raw','meta','out'):p.add_argument('--'+flag,type=Path,required=True)
    p=commands.add_parser('verify');p.add_argument('--package',type=Path,required=True);p.add_argument('--work',type=Path,required=True)
    p.add_argument('--state-dir',type=Path,help='Optional fresh directory for an independent verification rerun')
    args=parser.parse_args();audio(args) if args.command=='audio' else verify(args)
