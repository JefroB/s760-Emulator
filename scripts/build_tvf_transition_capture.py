"""Build the private720KB TVFSTEP analog-capture fixture and MIDI sequence.
Uses original local template read-only; generated disk contains template data and
must remain outside source distributions. No system-disk repacker is applicable.
"""
import argparse,hashlib,json,random,struct,wave
from pathlib import Path
import mido
from build_sample_disk import build
ROOT=Path(__file__).resolve().parents[1]
CASES=[
 dict(name='01 BYPASS',kind='bypass'),
 dict(name='02 LOW HOLD',kind='low'),
 dict(name='03 HIGH HOLD',kind='high'),
 dict(name='04 STEP UP',kind='step_up'),
 dict(name='05 STEP DOWN',kind='step_down'),
 dict(name='06 RAMP UP',kind='ramp_up'),
 dict(name='07 RAMP DOWN',kind='ramp_down')]
SEQUENCE=list(range(7))+[3,4,3,4]

def assign_capture_channels(image):
 """Assign parts1..7 to channels1..7; leave unused parts disabled.

 Original-firmware UI/Save confirms packed zero-based channel nibbles at
 performance+0x30 and receive-enable in bit7 of each level byte at+0x40.
 Channel14 on part2 changes4E30= D0 and4E41= FF from00/7F.
 """
 data=bytearray(image)
 assert len(data)==737280
 for part in range(32):
  address=0x4e30+part//2;shift=4*(part%2)
  channel=part if part<7 else 0
  data[address]=(data[address]&~(15<<shift))|(channel<<shift)
  data[0x4e40+part]=(data[0x4e40+part]&127)|(128 if part<7 else 0)
 assert data[0x4e10:0x4e17]==bytes(range(7))
 return bytes(data)
def make_spec():
 noise=[-1024]*2048+[1024]*2048;random.Random(760211).shuffle(noise)
 spec=dict(volume_name='CAL:TVF STEP',performance_name='TVF STEP',patches=[],partials=[],samples=[])
 for i in range(23):
  case=CASES[i] if i<len(CASES) else dict(name=f'{i+1:02} UNUSED',kind='unused')
  kind=case['kind'];name=case['name']
  if i<22:
   spec['patches'].append(dict(name=name,partial=i))
   partial=dict(name=name,tvf_mode='bypass' if kind in ['bypass','unused'] else 'lpf',cutoff=127 if kind in ['bypass','unused'] else 0,resonance=0 if kind in ['bypass','unused'] else 64,lfo_depths=[0]*6)
   levels={'low':[64]*4,'high':[96]*4,'step_up':[96,65,64,96],'step_down':[64,95,96,64],'ramp_up':[96,64,96,96],'ramp_down':[64,96,64,64]}.get(kind)
   if levels:
    partial['tvf_env']=dict(levels=levels,rates=[0,96 if kind.startswith('step') else 80 if kind.startswith('ramp') else 0,0,0],depth=63)
   spec['partials'].append(partial)
  spec['samples'].append(dict(name=f'CAL:NOISE{i:02}',root_key=60,start=0,loop_start=4096,loop_end=4106,end=4110,loop_enable=1,pcm={'samples':noise if i<len(CASES) else [0]*4096}))
 return spec,noise

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out-dir',type=Path,required=True);ap.add_argument('--multichannel',action='store_true',help='Seven performance parts/channels and seven MIDI tracks; no program changes');a=ap.parse_args();out=a.out_dir.resolve()
 if out.exists() and any(out.iterdir()):ap.error('Use a fresh private output folder')
 out.mkdir(parents=True,exist_ok=True);spec,noise=make_spec();template=ROOT/'roms/FDD/waves760.sdk';before=hashlib.sha256(template.read_bytes()).hexdigest()
 (out/'spec.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8');manifest=build(spec,template,out/'TVFSTEP.IMG')
 if a.multichannel:
  image=out/'TVFSTEP.IMG';image.write_bytes(assign_capture_channels(image.read_bytes()))
  manifest.update(sha256=hashlib.sha256(image.read_bytes()).hexdigest(),performance_channels=list(range(1,8)))
  image.with_suffix('.IMG.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 assert (out/'TVFSTEP.IMG').stat().st_size==737280 and hashlib.sha256(template.read_bytes()).hexdigest()==before
 with wave.open(str(out/'source-noise.wav'),'wb') as w:w.setparams((1,2,44100,0,'NONE','not compressed'));w.writeframes(struct.pack('<4096h',*noise))
 midi=mido.MidiFile(type=1);track=mido.MidiTrack();midi.tracks.append(track);track.append(mido.MetaMessage('set_tempo',tempo=500000,time=0));events=[];takes=[]
 for take,program in enumerate(SEQUENCE):
  start=take*17;events.extend([(start,mido.Message('program_change',channel=0,program=program)),(start+.05,mido.Message('control_change',channel=0,control=64,value=0)),(start+.1,mido.Message('control_change',channel=0,control=7,value=127)),(start+.15,mido.Message('control_change',channel=0,control=10,value=64)),(start+1,mido.Message('note_on',channel=0,note=60,velocity=127)),(start+13,mido.Message('note_off',channel=0,note=60,velocity=0))]);takes.append(dict(take=take+1,program_change=program,display_program=program+1,patch=CASES[program]['name'],note_on_seconds=start+1,note_off_seconds=start+13))
 if a.multichannel:
  midi.tracks.clear()
  for channel,case in enumerate(CASES):
   track=mido.MidiTrack();midi.tracks.append(track)
   track.append(mido.MetaMessage('track_name',name=f'CH{channel+1} {case["name"][3:]}',time=0))
   if channel==0:track.append(mido.MetaMessage('set_tempo',tempo=500000,time=0))
   previous=0
   for take,program in enumerate(SEQUENCE):
    if program!=channel:continue
    start=take*17
    for sec,msg in [(start+.05,mido.Message('control_change',channel=channel,control=64,value=0)),(start+.1,mido.Message('control_change',channel=channel,control=7,value=127)),(start+.15,mido.Message('control_change',channel=channel,control=10,value=64)),(start+1,mido.Message('note_on',channel=channel,note=60,velocity=127)),(start+13,mido.Message('note_off',channel=channel,note=60,velocity=0))]:
     tick=round(sec*960);msg.time=tick-previous;previous=tick;track.append(msg)
   track.append(mido.MetaMessage('end_of_track',time=187*960-previous))
  for take,program in zip(takes,SEQUENCE):take.pop('program_change');take['channel']=program+1
 previous=0
 for sec,msg in ([] if a.multichannel else sorted(events,key=lambda x:x[0])):
  tick=round(sec*960);msg.time=tick-previous;previous=tick;track.append(msg)
 if not a.multichannel:track.append(mido.MetaMessage('end_of_track',time=4*960))
 midi.save(out/'TVFSTEP_CAPTURE.mid')
 (out/'capture-sequence.json').write_text(json.dumps(dict(channel=None if a.multichannel else 1,multichannel=a.multichannel,note=60,velocity=127,hold_seconds=12,release_seconds=4,duration_seconds=187,takes=takes),indent=2)+'\n',encoding='utf-8')
 print('Built',out/'TVFSTEP.IMG',manifest['sha256'])
if __name__=='__main__':main()
