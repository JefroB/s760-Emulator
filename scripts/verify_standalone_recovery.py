"""Real firmware dirty-media automatic recovery, child failure and normal close.

Uses private ROBOFULL copies. Timer is expedited for this native QA; the browser
acceptance separately waits the production 60-second interval.
"""
import argparse
from dataclasses import replace
import hashlib,json,math,time
from pathlib import Path
import numpy as np
from s760_runtime import NativeRuntime,RuntimeConfig
from s760_standalone import StandaloneSession

ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--state-dir',type=Path,required=True)
    work=parser.parse_args().state_dir.resolve();work.mkdir(parents=True,exist_ok=True)
    source=ROOT/'roms/FDD/ROBOFULL.IMG';original=digest(source)
    cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',
        ROOT/'roms/System/S760224.IMG',work,sound=False,throttle=False)
    with NativeRuntime(cfg) as r:
        def wait(s):
            end=r.request('status')[0]['seconds']+s;deadline=time.monotonic()+max(30,s+15)
            while r.request('status')[0]['seconds']<end:
                assert time.monotonic()<deadline,'Native clock stalled'
                time.sleep(.01)
        def click(x,y):
            r.request('pointer',x=x,y=y);wait(.2)
            r.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
            r.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.2)
        wait(20);session=StandaloneSession(r,ROOT/'roms/FDD')
        session.input({'type':'SAVE_SESSION','payload':{}});manual=digest(session.session_path)
        r.insert_media(source)
        click(118,5);wait(2);click(80,22);wait(8);click(50,34);wait(2);click(76,98);wait(35)
        click(118,5);wait(2);click(80,30);wait(8);click(50,34);wait(1);click(76,98);wait(3)
        click(62,70);wait(3);click(66,70);wait(35)
        dirty=r.media_status();assert dirty['dirty'] and dirty['revision']==134,dirty
        click(10,5);click(15,22);wait(3);session.poll()
        assert session.firmware_status['state']=='ready',session.firmware_status
        r.request('pause');session.next_recovery=0;session.automatic_recovery()
        assert session.recovery_path.is_file(),session.recovery_message
        assert r.request('status')[0]['state']=='paused'
        checkpoint_hash=digest(session.recovery_path)
        now=r.request('status')[0]['seconds'];stamp=math.ceil(now*44100)+4096
        events=[{'sample':stamp,'bytes':[144,60,127]},{'sample':stamp+44100,'bytes':[128,60,0]}]
        r.request('audio_capture',enabled=True);r.schedule_midi(events)
        reference=b''.join(r.render_audio(8192)[1] for _ in range(16));display=r.request('frames')[1]
        assert np.max(np.abs(np.frombuffer(reference,dtype='<f4')))>.001
        r.request('resume');r.export_media(work/'reference.img')
        old_pid=r.process.pid;r.process.kill();r.process.wait(timeout=10)
        assert session.poll()==[]
        assert session.input({'type':'RESTORE_RECOVERY','payload':{'discard':True}})['type']=='RECOVERY_RESTORED'
        assert r.process.pid!=old_pid
        restored=r.media_status();assert restored['dirty'] and restored['revision']==134,restored
        r.request('pause');r.load_checkpoint(session.recovery_path)
        r.request('audio_capture',enabled=True);r.schedule_midi(events)
        replay=b''.join(r.render_audio(8192)[1] for _ in range(16))
        assert replay==reference,'Automatic recovery PCM differs'
        assert r.request('frames')[1]==display,'Automatic recovery displays differ'
        assert np.max(np.abs(np.frombuffer(replay[-8192*8:],dtype='<f4')))==0
        r.request('resume');r.export_media(work/'crash-recovered.img')
        assert digest(work/'crash-recovered.img')==digest(work/'reference.img')
        assert digest(session.session_path)==manual and digest(session.recovery_path)==checkpoint_hash
        # Recover dirty state again, then exercise a real normal-close checkpoint.
        r.request('pause');r.load_checkpoint(session.recovery_path);r.request('resume')
        saved_recovery=digest(session.recovery_path)
        original_save=r.save_checkpoint
        def fail_save(_):raise OSError('Injected disk-full publication failure')
        r.save_checkpoint=fail_save
        try:
            assert session.prepare_close() is False
            assert digest(session.recovery_path)==saved_recovery
            assert r.request('status')[0]['state']=='running'
            assert r.media_status()['dirty']
        finally:r.save_checkpoint=original_save
        assert session.prepare_close() is True
        assert digest(session.session_path)==manual
    with NativeRuntime(replace(cfg,sample_disk=None)) as r:
        session=StandaloneSession(r,ROOT/'roms/FDD');preserved=digest(session.recovery_path)
        assert session.recovery_pending
        session.next_recovery=0;session.automatic_recovery()
        assert digest(session.recovery_path)==preserved
        assert session.input({'type':'RESTORE_RECOVERY','payload':{'discard':True}})['type']=='RECOVERY_RESTORED'
        status=r.media_status();assert status['dirty'] and status['revision']==134,status
        r.export_media(work/'close-recovered.img')
        assert digest(work/'close-recovered.img')==digest(work/'reference.img')
        assert digest(session.session_path)==manual
        r.request('pause');r.request('audio_capture',enabled=True);r.request('midi',bytes=[144,60,127])
        active=b''.join(r.render_audio(8192)[1] for _ in range(4))
        r.request('midi',bytes=[128,60,0]);release=b''.join(r.render_audio(8192)[1] for _ in range(8))
        assert np.max(np.abs(np.frombuffer(active,dtype='<f4')))>.001
        assert np.max(np.abs(np.frombuffer(release[-8192*8:],dtype='<f4')))==0
    assert digest(source)==original
    result={'dirty_revision':134,'automatic_recovery_pcm_frames_exact':len(replay)//8,'displays_exact':True,
        'child_failure_new_process':True,'normal_close_reopen_dirty_bytes_exact':True,
        'manual_save_preserved':True,'startup_recovery_preserved':True,'original_media_preserved':True,
        'failed_close_preserves_running_dirty_state_and_previous_archive':True,
        'recovered_play_release':True,'export_sha256':digest(work/'reference.img'),
        'timer':'expedited host deadline; production interval tested separately in browser'}
    (work/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
