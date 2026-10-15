"""Native OS2.24 Akai S1000 Convert Load acceptance for one genuine CD1 fixture.

Read-only library; private CD10_2048.iso; firmware controls only. A narrow Lua
observer records guest wave-port writes to distinguish conversion from raw PCM.
No source samples, CPU state or guest memory are injected. Not SCSI Save acceptance.
"""
import argparse,hashlib,json,math,shutil,subprocess,time
from pathlib import Path
from dataclasses import replace
from unittest.mock import patch
import numpy as np
from PIL import Image
from s760_runtime import NativeRuntime,RuntimeConfig

ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='f1879343706559e38c6705148cb48e1bc23e50edc65aecea2a712eafe9fff144'
OBSERVER=(Path(__file__).with_name('s760_wave_tail_observer.lua')).read_text(encoding='utf-8')

def sha(data):return hashlib.sha256(data).hexdigest()
def akai_name(data):
    alphabet='0123456789 ABCDEFGHIJKLMNOPQRSTUVWXYZ#+-.'
    return ''.join(alphabet[b] if b<len(alphabet) else '?' for b in data).rstrip()

def read_samples(data):
    # Bounded reference for the fingerprinted first partition/volume, not a
    # general Akai importer. Layout checked against akaiutil's public structs:
    # https://github.com/Midi-In/akaiutil/tree/38fef03a12c2bdf870d286e0741a35ea923c0993
    assert sha(data)==SOURCE_SHA,'Use the documented genuine String.Ensembles fixture'
    volume=data[0xca:0xda]
    assert akai_name(volume[:12])=='01 VI LNG FF'
    directory=int.from_bytes(volume[14:16],'little')*8192
    rows=[]
    for i in range(128):
        e=data[directory+i*24:directory+(i+1)*24]
        if e[16]!=ord('s'):continue
        size=int.from_bytes(e[17:20],'little');block=int.from_bytes(e[20:22],'little');seen=set();parts=[]
        while len(parts)*8192<size:
            assert 3<=block<len(data)//8192 and block not in seen,'Invalid FAT chain'
            seen.add(block);parts.append(data[block*8192:(block+1)*8192])
            block=int.from_bytes(data[0x70a+block*2:0x70c+block*2],'little')
        file=b''.join(parts)[:size];count=int.from_bytes(file[26:30],'little')
        assert file[0]==3 and len(file)==150+count*2 and int.from_bytes(file[138:140],'little')==44100
        rows.append((akai_name(e[:12]),count,file[150:],int.from_bytes(file[38:42],'little')))
    assert len(rows)==30
    return rows

def verify_payloads(samples,wave,writes):
    assert len(wave)==32*1024*1024
    # Every non-source byte must be a specific observed original-firmware
    # write, in the four-word region after the source loop marker's64-frame boundary.
    history={}
    for r in writes['rows']:history.setdefault(r['word_address'],[]).append(r['data'])
    final={address:values[-1] for address,values in history.items()}
    assert writes['dropped']==0
    offset=16;rows=[]
    for name,count,pcm,loop_at in samples:
        expected=bytearray(pcm);changed=[];allowed=set(range((loop_at//64)*64+1,min(count,(loop_at//64)*64+5)))
        actual=wave[offset:offset+len(pcm)]
        for index in np.flatnonzero(np.frombuffer(actual,dtype='<u2')!=np.frombuffer(pcm,dtype='<u2')):
            index=int(index);address=offset//2+index
            assert index in allowed,f'Unexpected sample alteration: {name} word{index}'
            assert address in final,f'Missing guest conversion write: {name} word{index}'
            assert history[address][0]==int.from_bytes(pcm[index*2:index*2+2],'little'),f'Source transfer mismatch: {name} word{index}'
            expected[index*2:index*2+2]=final[address].to_bytes(2,'little');changed.append(index)
        assert actual==expected,f'Sample mismatch: {name}'
        rows.append({'name':name,'frames':count,'wave_byte_offset':offset,'bytes_verified':len(pcm),
                     'source_sha256':sha(pcm),'converted_sha256':sha(actual),'firmware_tail_words':changed})
        offset+=math.ceil(len(pcm)/9216)*9216
    return rows

def verify_cold_recall(cfg,base):
    buffers=[];rows=[]
    for index in range(2):
        state=base/f'cold{index}';scsi=state/'roms/SCSI';scsi.mkdir(parents=True)
        shutil.copyfile(cfg.state_dir/'roms/SCSI/CD10_2048.iso',scsi/'CD10_2048.iso')
        with NativeRuntime(replace(cfg,state_dir=state,wave_dump=None)) as runtime:
            runtime.request('pause');runtime.load_checkpoint(base/'session.bin')
            runtime.request('audio_capture',enabled=True);runtime.request('midi',bytes=[0x90,55,100])
            pcm=b''.join(runtime.render_audio(8192)[1] for _ in range(8))
            values=np.frombuffer(pcm,dtype='<f4')
            assert np.isfinite(values).all() and 0<np.max(np.abs(values))<1
            runtime.request('midi',bytes=[0x80,55,0])
            tail=b''.join(runtime.render_audio(8192)[1] for _ in range(18))
            assert np.max(np.abs(np.frombuffer(tail,dtype='<f4')[-88200:]))==0
            rows.append({'frames':65536,'pcm_sha256':sha(pcm),'peak':float(np.max(np.abs(values))),'silent_release_frames':44100})
            buffers.append(pcm)
    assert buffers[0]==buffers[1],'Cold imported sample playback differs'
    return {'passed':True,'fresh_processes':2,'exact_stereo_frames':65536,'rows':rows}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--image',type=Path,default=ROOT/"sample_cds/s1000/Best Service - Peter Siedleczek's Advance Orchestra (DISC 1) - String.Ensembles.iso")
    args=parser.parse_args();base=args.state_dir.resolve()
    if base.exists() and any(base.iterdir()):parser.error('Use a fresh private state directory')
    source=args.image.resolve();data=source.read_bytes();samples=read_samples(data)
    base.mkdir(parents=True);state=base/'load';scsi=state/'roms/SCSI';scsi.mkdir(parents=True)
    target=scsi/'CD10_2048.iso';shutil.copyfile(source,target)
    protocol=(ROOT/'scripts/s760_runtime.lua').read_text(encoding='utf-8')
    start=protocol.index('local function start_bus_trace(');end=protocol.index('checkpoint_pause.notifier',start)
    wanted=[];offset=16
    for _,count,pcm,loop_at in samples:
        wanted.extend(offset//2+i for i in range((loop_at//64)*64+1,min(count,(loop_at//64)*64+5)))
        offset+=math.ceil(len(pcm)/9216)*9216
    observer=OBSERVER.replace('__WANTED__',','.join(f'[{address}]=true' for address in wanted))
    private=base/'observer.lua';private.write_text(protocol[:start]+observer+protocol[end:],encoding='utf-8')
    cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',state,sound=False,throttle=False,wave_dump=base/'wave.bin')
    original_popen=subprocess.Popen
    def observed(command,**kwargs):
        command=list(command);command[command.index('-autoboot_script')+1]=str(private)
        return original_popen(command,**kwargs)
    report={}
    with patch('s760_runtime.subprocess.Popen',observed),NativeRuntime(cfg) as runtime:
        def wait(seconds):
            until=runtime.request('status')[0]['seconds']+seconds;deadline=time.monotonic()+180
            while runtime.request('status')[0]['seconds']<until:
                assert time.monotonic()<deadline,'Firmware stopped advancing'
                time.sleep(.01)
        def move(x,y):runtime.request('pointer',x=x,y=y);wait(.3)
        def click(x,y):
            move(x,y);runtime.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
            runtime.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.3)
        def screenshot(name):Image.frombytes('RGBA',(640,480),runtime.request('frames')[1][0][6:]).save(base/name)
        wait(20);click(118,5);click(80,22);wait(8);click(140,22);wait(2)
        click(96,78);runtime.request('button',port=':PANEL2',name='Panel F3',down=True);wait(.2)
        runtime.request('button',port=':PANEL2',name='Panel F3',down=False);wait(20);screenshot('scanned.png')
        click(100,42);wait(3);click(118,5);click(100,78);wait(8);screenshot('volumes.png')
        click(50,34);wait(1);runtime.request('pause');runtime.request('bus_trace',enabled=True,first=0x100008,last=0x10000f)
        runtime.request('resume');click(76,98);wait(400);runtime.request('pause')
        writes=runtime.request('bus_trace',enabled=False)[0];runtime.request('resume');screenshot('converted.png')
        (base/'wave-writes.json').write_text(json.dumps(writes,indent=2),encoding='utf-8')
        click(10,5);click(15,22);wait(5);move(50,30);runtime.request('dial',id='ALPHA',delta=1);wait(3);screenshot('assigned.png')
        runtime.request('pause');runtime.save_checkpoint(base/'session.bin')
        def render(n):
            blocks=[]
            while n:
                count=min(n,8192);blocks.append(np.frombuffer(runtime.render_audio(count)[1],dtype='<f4').reshape(-1,2).copy());n-=count
            return np.concatenate(blocks)
        runtime.request('audio_capture',enabled=True);audio=[]
        for note in (55,72,96):
            runtime.request('midi',bytes=[0x90,note,100]);pcm=render(65536)
            assert np.isfinite(pcm).all() and 0<np.max(np.abs(pcm))<1
            runtime.request('midi',bytes=[0x80,note,0]);tail=render(132300)
            assert np.max(np.abs(tail[-44100:]))==0,'Stuck imported note'
            audio.append({'note':note,'peak':float(np.max(np.abs(pcm))),'silent_release_frames':44100})
        runtime.request('audio_capture',enabled=False);runtime.request('resume');wait(1)
        report['audio']=audio;report['media_status']=runtime.media_status()
    report['samples']=verify_payloads(samples,(base/'wave.bin').read_bytes(),writes)
    assert sha(source.read_bytes())==SOURCE_SHA and sha(target.read_bytes())==SOURCE_SHA
    report['cold_recall']=verify_cold_recall(cfg,base)
    report.update(passed=True,source_sha256=SOURCE_SHA,source_bytes=len(data),sample_count=len(samples),
                  bytes_verified=sum(len(pcm) for _,_,pcm,_ in samples),observer_sha256=sha(private.read_bytes()),
                  limits='One genuine CD1/2048-byte-sector S1000 volume; original-firmware conversion includes observed four-word tail adjustments. Not arbitrary CDs, SCSI Save, hot-plug, concurrent voices or physical timing.')
    (base/'load-results.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))

if __name__=='__main__':main()
