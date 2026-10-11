"""Real-firmware readiness and failed-process recovery acceptance."""
import argparse,json,time
from pathlib import Path
from s760_runtime import NativeRuntime,RuntimeConfig
from s760_standalone import StandaloneSession
ROOT=Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--state-dir',type=Path,required=True);args=parser.parse_args()
    work=args.state_dir.resolve();work.mkdir(parents=True,exist_ok=True)
    cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',work,sound=False,throttle=True)
    states=[]
    with NativeRuntime(cfg) as r:
        session=StandaloneSession(r,ROOT/'roms/FDD')
        def poll():
            session.poll();state=session.firmware_status['state']
            if not states or states[-1]!=state: states.append(state)
            return state
        def until(state,timeout=60):
            deadline=time.monotonic()+timeout
            while poll()!=state:
                assert time.monotonic()<deadline,(state,session.firmware_status,states)
                time.sleep(.02)
        def wait(seconds):
            end=time.monotonic()+seconds
            while time.monotonic()<end:poll();time.sleep(.02)
        def click(x,y):
            r.request('pointer',x=x,y=y);wait(.2)
            r.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
            r.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.2)
        until('ready')
        session.input({'type':'MOUNT_DISK','payload':{'diskPath':'ROBOFULL.IMG'}})
        click(118,5);wait(.3);click(80,22);until('disk_ready');wait(2)
        click(50,34);wait(.3);before=len(states);click(76,98);until('loading');until('disk_ready')
        assert 'loading' in states[before:],states
        click(10,5);click(15,22);until('ready')
        # Verify readiness corresponds to a usable native patch, not just pixels.
        r.request('pause');r.request('audio_capture',enabled=True)
        r.request('midi',bytes=[144,60,127])
        import numpy as np
        pcm=b''.join(r.render_audio(8192)[1] for _ in range(8))
        assert np.max(np.abs(np.frombuffer(pcm,dtype='<f4')))>.001
        r.request('midi',bytes=[128,60,0])
        tail=b''.join(r.render_audio(8192)[1] for _ in range(12))
        assert np.max(np.abs(np.frombuffer(tail[-8192*8:],dtype='<f4')))==0
        r.request('resume')
        old_pid=r.process.pid;r.process.kill();r.process.wait(timeout=10)
        until('failed',10)
        assert not session.stop.is_set(),'Failure killed recovery service'
        session.input({'type':'RESTART_RUNTIME','payload':{'discard':True}})
        assert r.process.pid!=old_pid
        until('ready')
        result={'states':states,'normal_speed':True,'loaded_audio_peak':float(np.max(np.abs(np.frombuffer(pcm,dtype='<f4')))),
                'note_off_silent':True,'crash_recovered':True,'replacement_pid':r.process.pid,'previous_pid':old_pid}
    (work/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
if __name__=='__main__': main()
