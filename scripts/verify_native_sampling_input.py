"""Qualify opt-in offline ADC capture through firmware Save and cold Sample Load."""
import argparse,hashlib,struct,sys,time,json
from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from s760_runtime import NativeRuntime,RuntimeConfig
from PIL import Image
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--blank-disk',type=Path,required=True,help='Existing firmware-formatted 720KB disk; opened read-only')
parser.add_argument('--state-dir',type=Path,required=True,help='New private evidence directory')
parser.add_argument('--input-level',type=int,choices=(0,50,100),default=100,help='Recording gain to verify')
parser.add_argument('--cold-gain-recall',action='store_true',help='Record after restoring an armed session in a fresh native process')
args=parser.parse_args()
root=ROOT;work=args.state_dir.resolve();work.mkdir(parents=True,exist_ok=False)
blank=args.blank_disk.resolve();blank_bytes=blank.read_bytes()
assert len(blank_bytes)==737280 and blank_bytes[4096:]==bytes([15])*(737280-4096), 'Expected empty firmware-formatted disk'
blank_sha=hashlib.sha256(blank_bytes).hexdigest()
cfg=RuntimeConfig(root/'mame-source/mames760.exe',root/'roms/BOOT/Roland_S-760_v1.11.BIN',root/'roms/System/S760224.IMG',work,sound=False,throttle=False,experimental_adc=True,wave_dump=work/"wave.bin")
with ExitStack() as stack:
 rt=stack.enter_context(NativeRuntime(cfg))
 def wait(n):
  target=rt.request('status')[0]['seconds']+n;deadline=time.monotonic()+90
  while rt.request('status')[0]['seconds']<target:
   if time.monotonic()>deadline:raise TimeoutError('machine time')
   time.sleep(.02)
 def shot(name):Image.frombytes('RGBA',(640,480),rt.request('frames')[1][0][6:]).save(work/(name+'.png'))
 def click(x,y):
  rt.request('pointer',x=x,y=y);wait(.2)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.2)
 wait(20);shot('boot')

 click(100,5);wait(3);shot('sample-menu')
 click(80,22);wait(3);shot('sampling')

 click(76,98);wait(2);shot('ready')
 click(62,66);wait(3);shot('armed')

 rt.request('pause');rt.request('audio_capture',enabled=True)
 # Atomic rejection must not mutate the paused queue.
 for bad in ({'rate':48000,'channels':2,'samples':[1,2]},
             {'rate':44100,'channels':1,'samples':[1,2]},
             {'rate':44100,'channels':2,'samples':[1,40000]}):
  before=rt.request('input_status')[0]
  try:rt.request('input_audio',**bad)
  except RuntimeError:pass
  else:raise AssertionError('Unsupported input accepted')
  assert rt.request('input_status')[0]==before
 for _ in range(8):rt.queue_input_pcm(bytes(8192))
 before=rt.request('input_status')[0]
 assert before['queued']==16384
 try:rt.queue_input_pcm(bytes(4))
 except RuntimeError:pass
 else:raise AssertionError('Full queue accepted input')
 assert rt.request('input_status')[0]==before
 rt.render_audio(8192);rt.render_audio(8192)
 # Input gain must affect recording independently of muted playback output.
 for _ in range(4):rt.request('dial',id='VOLUME',delta=-32)
 remaining=100-args.input_level
 while remaining:
  delta=min(remaining,32);rt.request('dial',id='INPUT',delta=-delta);remaining-=delta
 assert rt.request('frames')[0]['input_level']==args.input_level
 if args.cold_gain_recall:
  rt.save_checkpoint(work/'armed-gain.s760state')
  expected_depth=rt.request('input_status')[0]['queued']
  rt.close()
  rt=stack.enter_context(NativeRuntime(replace(cfg,state_dir=work/'gain-recall')))
  rt.request('pause')
  for _ in range(4):rt.request('dial',id='INPUT',delta=-32)
  rt.load_checkpoint(work/'armed-gain.s760state')
  recalled=rt.request('frames')[0]
  assert recalled['input_level']==args.input_level and recalled['output_level']==0
  assert rt.request('input_status')[0]['queued']==expected_depth
 rt.request('bus_trace',enabled=True,first=0x100010,last=0x100013)
 fed=0
 def render(n):
  global fed
  while n:
   depth=rt.request('input_status')[0]['queued']
   while depth<10000:
    values=[]
    for i in range(fed,fed+2048):values.extend([((i%257)-128)*64,((i%509)-254)*32])
    depth=rt.request('input_audio',rate=44100,channels=2,samples=values)[0]['queued'];fed+=2048
   chunk=min(n,1024);rt.render_audio(chunk);n-=chunk
 def click_paused(x,y):
  rt.request('pointer',x=x,y=y);render(8820)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);render(4410)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);render(8820)
 click_paused(14,98);render(44100);shot('recording')
 print('recording',rt.request('input_status')[0],flush=True)
 rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Right',down=True);render(4410)
 rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Right',down=False);render(44100*3);shot('stopped')
 trace=rt.request('bus_trace',enabled=False)[0];(work/'trace.json').write_text(json.dumps(trace,indent=2))
 print('stopped',rt.request('input_status')[0],flush=True)
 click_paused(140,98);render(44100);shot('end')
 rt.request('resume')
 rt.insert_media(blank)
 click(118,5);wait(2);click(80,30);wait(8);shot('save-menu')
 click(20,22);wait(1);shot('target-menu')
 click(25,54);wait(2);shot('sample-list')
 click(10,98);wait(1);click(76,98);wait(3);shot('sample-save-choice')
 click(62,70);wait(3);shot('sample-save-confirm')
 click(66,70);wait(35);shot('sample-saved')
 print('media',rt.media_status(),flush=True)
 rt.export_media(work/'captured-stereo.img')
 rt.request('pause');rt.save_checkpoint(work/'recorded.s760state')
 assert rt.request('input_status')[0]['underruns']==0

cfg=RuntimeConfig(root/'mame-source/mames760.exe',root/'roms/BOOT/Roland_S-760_v1.11.BIN',root/'roms/System/S760224.IMG',work/'reload',work/'captured-stereo.img',sound=False,throttle=False,wave_dump=work/'reloaded-wave.bin')
with NativeRuntime(cfg) as rt:
 def wait(n):
  target=rt.request('status')[0]['seconds']+n;deadline=time.monotonic()+90
  while rt.request('status')[0]['seconds']<target:
   if time.monotonic()>deadline:raise TimeoutError('Reload machine time')
   time.sleep(.01)
 def click(x,y):
  rt.request('pointer',x=x,y=y);wait(.2)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.2)
 def shot(name):Image.frombytes('RGBA',(640,480),rt.request('frames')[1][0][6:]).save(work/(name+'.png'))
 wait(20)
 rt.request('button',port=':NATIVE_MEDIA',name='Insert Sample Floppy',down=True)
 rt.request('button',port=':NATIVE_MEDIA',name='Insert Sample Floppy',down=False)
 click(118,5);wait(2);click(80,22);wait(8)
 click(20,22);wait(1);shot('reload-target')
 click(25,54);wait(2);shot('reload-list')
 click(10,98);wait(1);click(76,98);wait(35);shot('reloaded')

assert hashlib.sha256(blank.read_bytes()).hexdigest()==blank_sha
before=(work/'wave.bin').read_bytes();after=(work/'reloaded-wave.bin').read_bytes()
disk=(work/'captured-stereo.img').read_bytes();samples=[];wave_offset=16;disk_offset=0x2ac00
for channel,(period,step) in enumerate(((257,64),(509,32))):
 record=disk[0x18e00+channel*48:0x18e00+(channel+1)*48]
 assert record[:11]==b'NEW:Unnamed' and record[15]==ord('L' if channel==0 else 'R')
 # Sample address fields use 8 fractional bits. OS sets the initial
 # loop-start marker to the final recorded word, followed by zero padding.
 recorded_last_word=struct.unpack_from('<I',record,24)[0] >> 8
 frames=recorded_last_word+1
 allocation=struct.unpack_from('<H',record,42)[0]*9216
 assert 44100<=frames<=88200 and frames*2<=allocation
 pcm=before[wave_offset:wave_offset+allocation]
 assert pcm==after[wave_offset:wave_offset+allocation]
 assert pcm==disk[disk_offset:disk_offset+allocation]
 values=struct.unpack_from('<'+'h'*frames,pcm)
 phase=values[0]//step+period//2
 if args.input_level:
  scaled_step=step*args.input_level//100
  phase=values[0]//scaled_step+period//2
  assert all(value==((phase+i)%period-period//2)*scaled_step for i,value in enumerate(values))
 else:
  assert not any(values), 'Muted recording contains nonzero PCM'
 assert not any(pcm[frames*2:]), 'Nonzero allocation padding'
 samples.append({'channel':channel,'frames':frames,'allocation_bytes':allocation,
                 'pcm_sha256':hashlib.sha256(pcm).hexdigest(),
                 'metadata_hex':record.hex(),'exact_input_pattern':True,
                 'wave_disk_cold_reload_equal':True})
 wave_offset+=allocation;disk_offset+=allocation
result={'profile':'experimental offline 44100Hz stereo PCM16','samples':samples,
        'input_level':args.input_level,'output_level_during_recording':0,
        'cold_gain_recall':args.cold_gain_recall,
        'input_underruns':0,'invalid_format_and_atomic_overflow_rejection':True,
        'blank_sha256':blank_sha,'source_preserved':True,
        'saved_sha256':hashlib.sha256(disk).hexdigest(),
        'identities':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
          for p in (cfg.executable,cfg.boot_rom,cfg.system_disk,root/'mame-source/src/mame/roland/s760.cpp',root/'scripts/s760_runtime.lua',root/'scripts/s760_runtime.py')},
        'limitations':['No physical input device or realtime timing qualification',
          'Analog gain taper/headroom, other recording rates and hardware register semantics remain open',
          'Experimental ADC remains disabled by default']}
(work/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
