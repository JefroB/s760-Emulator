"""Boot original firmware at every supported wave-memory size; verify native dump capacity.

Private state and read-only original firmware. Screenshots retain firmware detection evidence.
"""
import argparse,json,time
from dataclasses import replace
from pathlib import Path
from PIL import Image
from s760_runtime import NativeRuntime,RuntimeConfig

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir',type=Path,required=True)
    args=parser.parse_args();base=args.state_dir.resolve()
    if base.exists() and any(base.iterdir()):parser.error('Use a fresh private state directory')
    root=Path(__file__).resolve().parents[1];rows=[]
    for size in (8,16,32):
        state=base/str(size);state.mkdir(parents=True)
        dump=state/'wave.bin'
        cfg=RuntimeConfig(root/'mame-source/mames760.exe',root/'roms/BOOT/Roland_S-760_v1.11.BIN',root/'roms/System/S760224.IMG',state,wave_memory_mb=size,wave_dump=dump,sound=False,throttle=False)
        with NativeRuntime(cfg) as runtime:
            def wait(seconds):
                target=runtime.request('status')[0]['seconds']+seconds;deadline=time.monotonic()+90
                while runtime.request('status')[0]['seconds']<target:
                    assert time.monotonic()<deadline,'Firmware stopped advancing'
                    time.sleep(.01)
            def click(x,y):
                runtime.request('pointer',x=x,y=y);wait(.3)
                runtime.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
                runtime.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.3)
            def screenshot(name):
                Image.frombytes('RGBA',(640,480),runtime.request('frames')[1][0][6:]).save(state/name)
            wait(30);screenshot('boot.png')
            click(152,5);wait(1);screenshot('system-menu.png')
            click(130,22);wait(3);screenshot('system-memory.png')
            runtime.request('pause');checkpoint=state/'session.bin'
            runtime.save_checkpoint(checkpoint);runtime.validate_checkpoint(checkpoint);runtime.load_checkpoint(checkpoint)
            other=NativeRuntime(replace(cfg,wave_memory_mb=16 if size!=16 else 32))
            try:other.validate_checkpoint(checkpoint)
            except ValueError as error:assert 'wave memory size' in str(error),str(error)
            else:raise AssertionError('Mismatched memory checkpoint accepted')
        assert dump.stat().st_size==size*1024*1024,'Native capacity differs from selected size'
        rows.append({'wave_memory_mb':size,'native_bytes':dump.stat().st_size,'checkpoint_round_trip':True,'different_size_rejected':True})
    (base/'result.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows))

if __name__=='__main__':main()
