"""Full JMD native Roland CD1 Scan/Load, exact allocations, playback and cold recall.

Original firmware/pointer/MIDI controls only; private full CD copy; no guest state
injection except normal checkpoint restore. Not SCSI Save or physical timing proof.
"""
import argparse,hashlib,json,mmap,shutil,struct,time
from pathlib import Path
from dataclasses import replace
import numpy as np
from PIL import Image
from s760_runtime import NativeRuntime,RuntimeConfig
ROOT=Path(__file__).resolve().parents[1]
SOURCE_SHA='1e3e25be27366d9499927417cf9a8194cc66269bca263466ce576e26b8291618'
def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def source_samples(source):
    # Independent bounded FAT reader for the fingerprinted native fixture.
    # Reference: https://github.com/bmxcode/samplerdisc (Roland S770 MR25A).
    assert digest(source)==SOURCE_SHA
    result=[]
    with source.open('rb') as f:
        d=mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ)
        try:
            assert d[4:14]==b'S770 MR25A'
            for index in range(struct.unpack_from('<H',d,0x11c)[0]):
                e=d[1644*512+index*32:1644*512+(index+1)*32]
                if not e[:16].startswith(b'K4 :'):continue
                assert e[16]==0x44
                cluster,count=struct.unpack_from('<HH',e,28);parts=[];seen=set()
                for _ in range(count):
                    assert 2<=cluster<0xfff6 and cluster not in seen,'Invalid sample FAT chain'
                    seen.add(cluster);offset=5548*512+(cluster-2)*9216
                    assert offset+9216<=len(d)
                    parts.append(d[offset:offset+9216]);cluster=struct.unpack_from('<H',d,1028*512+cluster*2)[0]
                assert cluster>=0xfff6,'Sample FAT chain exceeds declared allocation'
                result.append((index,e[:16].decode('ascii').rstrip(),b''.join(parts)))
        finally:d.close()
    assert len(result)==79
    return result
def render(runtime,n):
    blocks=[]
    while n:
        count=min(n,8192);blocks.append(runtime.render_audio(count)[1]);n-=count
    return b''.join(blocks)
def audition(runtime,channel,note):
    runtime.request('midi',bytes=[0x90|channel,note,100]);pcm=render(runtime,65536)
    values=np.frombuffer(pcm,dtype='<f4');assert np.isfinite(values).all() and 0<np.max(np.abs(values))<1
    runtime.request('midi',bytes=[0x80|channel,note,0]);tail=render(runtime,132300)
    assert np.max(np.abs(np.frombuffer(tail,dtype='<f4')[-88200:]))==0,'Loaded note failed to release'
    return pcm,{'channel':channel+1,'note':note,'peak':float(np.max(np.abs(values))),'silent_release_frames':44100}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state-dir',type=Path,required=True)
    parser.add_argument('--image',type=Path,default=ROOT/'sample_cds/roland/JMD_S760_Freeware_CD.iso')
    args=parser.parse_args();base=args.state_dir.resolve();source=args.image.resolve()
    if base.exists() and any(base.iterdir()):parser.error('Use a fresh private state directory')
    samples=source_samples(source);state=base/'load';folder=state/'roms/SCSI';folder.mkdir(parents=True)
    target=folder/'CD10_2048.iso';shutil.copyfile(source,target)
    cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',state,sound=False,throttle=False,wave_dump=base/'wave.bin')
    report={}
    with NativeRuntime(cfg) as runtime:
        def wait(seconds):
            end=runtime.request('status')[0]['seconds']+seconds;deadline=time.monotonic()+120
            while runtime.request('status')[0]['seconds']<end:
                assert time.monotonic()<deadline,'Firmware stopped advancing'
                time.sleep(.01)
        def click(x,y):
            runtime.request('pointer',x=x,y=y);wait(.3)
            runtime.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
            runtime.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.3)
        def screenshot(name):Image.frombytes('RGBA',(640,480),runtime.request('frames')[1][0][6:]).save(base/name)
        wait(25);click(118,5);click(80,22);wait(8);click(140,22);wait(2)
        click(96,78);runtime.request('button',port=':PANEL2',name='Panel F3',down=True);wait(.2)
        runtime.request('button',port=':PANEL2',name='Panel F3',down=False);wait(20);screenshot('scan.png')
        click(100,42);wait(8);screenshot('volumes.png');click(50,34);wait(1);click(76,98);wait(180);screenshot('loaded.png')
        click(10,5);click(15,22);wait(5);screenshot('perform.png')
        runtime.request('pause');runtime.save_checkpoint(base/'session.bin');runtime.request('audio_capture',enabled=True)
        rows=[]
        for channel,note in [(0,36),(0,38),(0,42),(1,60)]:
            pcm,row=audition(runtime,channel,note);rows.append(row)
            (base/f'channel{channel+1}-note{note}.pcm').write_bytes(pcm)
        runtime.request('audio_capture',enabled=False);runtime.request('resume');wait(1)
        report['audio']=rows;report['floppy_status']=runtime.media_status()
    wave=(base/'wave.bin').read_bytes();offset=16;rows=[]
    for index,name,expected in samples:
        actual=wave[offset:offset+len(expected)]
        assert actual==expected,f'Native sample allocation mismatch: {index} {name}'
        rows.append({'index':index,'name':name,'bytes':len(expected),'wave_byte_offset':offset,'sha256':hashlib.sha256(expected).hexdigest()});offset+=len(expected)
    report['samples']=rows
    # CD is excluded from the native checkpoint but required by its content identity.
    assert (base/'session.bin').stat().st_size<257*1024*1024
    cold_pcm=[]
    for index in range(2):
        cold=base/f'cold{index}';media=cold/'roms/SCSI';media.mkdir(parents=True)
        shutil.copyfile(target,media/target.name)
        with NativeRuntime(replace(cfg,state_dir=cold,wave_dump=None)) as runtime:
            runtime.request('pause');runtime.load_checkpoint(base/'session.bin');runtime.request('audio_capture',enabled=True)
            pcm,_=audition(runtime,0,36);cold_pcm.append(pcm)
    assert cold_pcm[0]==cold_pcm[1]==(base/'channel1-note36.pcm').read_bytes(),'Cold native Roland replay differs'
    # Preflight must reject changed external CD content before touching native state.
    altered=base/'cold0/roms/SCSI/CD10_2048.iso'
    with altered.open('r+b') as f:f.seek(-1,2);value=f.read(1);f.seek(-1,2);f.write(bytes([value[0]^1]))
    try:
        other=NativeRuntime(replace(cfg,state_dir=base/'cold0',wave_dump=None))
        try:other.validate_checkpoint(base/'session.bin')
        except ValueError as error:assert 'SCSI backing media' in str(error)
        else:raise AssertionError('Changed CD checkpoint accepted')
    finally:
        with altered.open('r+b') as f:f.seek(-1,2);f.write(value)
    assert digest(source)==digest(target)==SOURCE_SHA
    report.update(passed=True,source_sha256=SOURCE_SHA,source_bytes=source.stat().st_size,volume='K4 :KAWAI K4',sample_count=len(samples),allocation_bytes_verified=sum(len(v) for _,_,v in samples),checkpoint_bytes=(base/'session.bin').stat().st_size,cold_exact_stereo_frames=65536,cold_processes=2,changed_cd_rejected=True,limits='One full native JMD CD1/2048-sector image and first K4 performance; no SCSI Save, hot-plug, arbitrary libraries, physical timing or final packaged-interface claim')
    (base/'load-results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='samples'},indent=2))
if __name__=='__main__':main()
