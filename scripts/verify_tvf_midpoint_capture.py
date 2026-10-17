"""Qualify all 14 TVFGRID parts, exact samples and capture references.
Original firmware/MIDI controls only. Observer raises the bounded read-only row
capacity in a private protocol copy; no guest memory writes or hardware claims.
"""
import argparse,hashlib,json,math,subprocess,time,sys
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
from s760_runtime import NativeRuntime,RuntimeConfig
from verify_native_scsi_save import controls
from verify_native_roland_load import render
from build_tvf_midpoint_capture import CASES,SEQUENCE,make_spec
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--short',action='store_true');ap.add_argument('--research-observers',action='store_true',help='Attach bounded read-only firmware and scheduler probes');ap.add_argument('--pack',type=Path,required=True);ap.add_argument('--state-dir',type=Path,required=True);a=ap.parse_args();pack=a.pack.resolve();base=a.state_dir.resolve()
 if base.exists() and any(base.iterdir()):ap.error('Use a fresh native state directory')
 base.mkdir(parents=True,exist_ok=True);refs=pack/'native-reference';refs.mkdir(exist_ok=True)
 sequence=json.loads((pack/'capture-sequence.json').read_text());multichannel=sequence.get('multichannel',False)
 image=pack/'TVFGRID.IMG';inputs=[image,ROOT/'roms/FDD/waves760.sdk',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG'];hashes={str(p):digest(p) for p in inputs}
 lua=base/'observer.lua'
 protocol=(ROOT/'scripts/s760_runtime.lua').read_text(encoding='utf-8').replace('#trace.rows < 256','#trace.rows < 8192')
 if a.research_observers:protocol+='\n'+(ROOT/'scripts/trace_filter_research.lua').read_text(encoding='utf-8')
 lua.write_text(protocol+'\nemu.pause()\n',encoding='utf-8');launch=subprocess.Popen
 def observe(command,**kwargs):
  command=list(command);command[command.index('-autoboot_script')+1]=str(lua);kwargs['env']=dict(kwargs['env'],S760_FIRMWARE_INPUT_TRACE=str(base/'firmware-inputs.csv'));
  if a.short:kwargs['env']['S760_NATIVE_CUTOFF_SHORT_CANDIDATE']='1'
  return launch(command,**kwargs)
 cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',base,image,sound=False,throttle=False,wave_dump=base/'wave.bin');rows=[]
 with patch('s760_runtime.subprocess.Popen',observe),NativeRuntime(cfg) as r:
  wait,button,click,shot,_=controls(r,base)
  r.request('pause');r.request('audio_capture',enabled=True)
  def wait(seconds):render(r,round(seconds*44100))
  def button(port,name):
   r.request('button',port=port,name=name,down=True);wait(.2);r.request('button',port=port,name=name,down=False);wait(.2)
  def click(x,y):
   r.request('pointer',x=x,y=y);wait(.3);button(':NATIVE_MOUSE_BUTTONS','Mouse Left');wait(.3)
  wait(25);button(':NATIVE_MEDIA','Insert Sample Floppy');click(118,5);click(80,22);wait(8);click(50,34);click(76,98);wait(35);click(10,5);click(15,22);wait(3);shot('loaded.png');r.request('pause');r.request('audio_capture',enabled=True)
  for take,program in enumerate(range(14)):
   r.request('bus_trace',enabled=True,first=0x101030,last=0x101031)
   origin=r.request('status')[0]['seconds'];start=math.ceil(origin*44100)+2048;on=start+44100;off=on+12*44100
   channel=program if multichannel else 0
   events=([] if multichannel else [dict(sample=start,bytes=[0xc0,program])])+[dict(sample=start+2205,bytes=[0xb0|channel,64,0]),dict(sample=start+4410,bytes=[0xb0|channel,7,127]),dict(sample=start+6615,bytes=[0xb0|channel,10,64]),dict(sample=on,bytes=[0x90|channel,60,127]),dict(sample=off,bytes=[0x80|channel,60,0])]
   r.schedule_midi(events)
   audio=np.frombuffer(render(r,17*44100),dtype='<f4').reshape(-1,2);trace=r.request('bus_trace',enabled=False)[0];status=r.request('status')[0]
   assert trace['dropped']==0 and status['midi_pending']==0 and not status['midi_error']
   assert len(status['midi_delivered'])==len(events) and [v['sample'] for v in status['midi_delivered']]==[e['sample'] for e in events]
   assert np.isfinite(audio).all() and 0<np.max(np.abs(audio))<1 and np.max(np.abs(audio[-44100:]))==0
   cutoff=[dict(seconds=x['seconds']-on/44100,word=x['data']) for x in trace['rows'] if x['kind']=='w' and x['address']==0x101030 and x['data']<0x4000 and on/44100+.02<x['seconds']<off/44100]
   summary=dict(take=take+1,program=program+1,channel=channel+1,name=CASES[program]['name'],note_on_seconds=on/44100,peak=float(np.max(np.abs(audio))),silent_tail_frames=44100,cutoff=cutoff,trace_dropped=0)
   (base/f'take{take+1}-trace.json').write_text(json.dumps(trace),encoding='utf-8')
   if program:
    words=np.array([x['word'] for x in cutoff]);assert len(words)>100
    summary.update(first_word=int(words[0]),last_word=int(words[-1]),distinct_words=len(set(words.tolist())))
    if program in [1,2] or program>=7:assert len(set(words.tolist()))==1,'Static control moved'
    if program in [3,4]:
     changes=np.diff(words);index=int(np.argmax(np.abs(changes)))+1
     summary['step_seconds']=cutoff[index]['seconds'];summary['step_words']=[int(words[index-1]),int(words[index])]
     assert 1<summary['step_seconds']<10 and abs(changes[index-1])>1000,'Delayed abrupt transition missing'
    if program in [5,6]:assert summary['distinct_words']>50 and abs(int(words[-1])-int(words[0]))>1000,'Ramp did not span endpoints'
   sf.write(refs/f'{take+1:02}-{CASES[program]["name"].replace(" ","-")}.wav',audio,44100,subtype='FLOAT');(base/f'take{take+1}-trace.json').write_text(json.dumps(trace),encoding='utf-8');rows.append(summary);print({k:v for k,v in summary.items() if k!='cutoff'},flush=True)
  wait(.5);r.request('audio_capture',enabled=False);r.request('resume');time.sleep(.05);media=r.media_status();assert not media['busy'] and not media['dirty'];r.export_media(base/'unchanged-export.img');assert digest(base/'unchanged-export.img')==hashes[str(image)]
 wave=(base/'wave.bin').read_bytes();spec,noise=make_spec();payload=image.read_bytes()
 for i in range(14):assert wave[16+i*9216:16+(i+1)*9216]==payload[0x2ac00+i*9216:0x2ac00+(i+1)*9216],'Loaded sample allocation changed'
 for p,h in hashes.items():assert digest(Path(p))==h
 report=dict(passed=True,image_bytes=737280,source_hashes=hashes,cases=rows,exact_loaded_sample_bytes=14*9216,media=media,multichannel=multichannel,midi_events_per_take=5 if multichannel else 6,limits='Original-firmware native reference and verified capture stimulus. Low-amplitude lead-in precedes delayed step; hardware timing/response remains unmeasured. Reference WAVs are native float PCM, not analog predictions.')
 (pack/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print('PASSED',pack/'native-validation.json')
if __name__=='__main__':main()
