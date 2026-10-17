"""Build a private720KB midpoint/static calibration disk with ramp controls.
Template-derived media stays local, outside source distributions. No OS repacker.
"""
import argparse,hashlib,json,struct,wave
from pathlib import Path
import mido
from build_sample_disk import build
from build_tvf_transition_capture import make_spec as original_spec, CASES as ORIGINAL_CASES
ROOT=Path(__file__).resolve().parents[1]
LEVELS=[68,72,76,80,84,88,92]
CASES=list(ORIGINAL_CASES)+[dict(name=f'{8+i:02} HOLD L{level}',kind='midpoint',level=level) for i,level in enumerate(LEVELS)]
SEQUENCE=[0,1,2]+list(range(7,14))+[5,6,5,6,5,6,3,4,0]

def make_spec():
 spec,noise=original_spec();spec['volume_name']='CAL:TVF GRID';spec['performance_name']='TVF GRID'
 for i,level in enumerate(LEVELS,7):
  name=CASES[i]['name'];spec['patches'][i]=dict(name=name,partial=i)
  spec['partials'][i]=dict(name=name,tvf_mode='lpf',cutoff=0,resonance=64,lfo_depths=[0]*6,tvf_env=dict(levels=[level]*4,rates=[0,0,0,0],depth=63))
  spec['samples'][i]['pcm']={'samples':noise}
 return spec,noise

def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--out-dir',type=Path,required=True);a=ap.parse_args();out=a.out_dir.resolve()
 if out.exists() and any(out.iterdir()):ap.error('Use a fresh private output folder')
 out.mkdir(parents=True);spec,noise=make_spec();template=ROOT/'roms/FDD/waves760.sdk';before=hashlib.sha256(template.read_bytes()).hexdigest();(out/'spec.json').write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8')
 manifest=build(spec,template,out/'TVFGRID.IMG');image=out/'TVFGRID.IMG';data=bytearray(image.read_bytes());assert len(data)==737280 and data[4:14]==b'S770 MR25A'
 for part in range(32):
  address=0x4e30+part//2;shift=4*(part%2);channel=part if part<len(CASES) else 0
  data[address]=(data[address]&~(15<<shift))|(channel<<shift);data[0x4e40+part]=(data[0x4e40+part]&127)|(128 if part<len(CASES) else 0)
 assert data[0x4e10:0x4e10+len(CASES)]==bytes(range(len(CASES)));image.write_bytes(data)
 manifest.update(sha256=hashlib.sha256(data).hexdigest(),performance_channels=list(range(1,15)),calibration_levels=LEVELS);image.with_suffix('.IMG.manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
 assert hashlib.sha256(template.read_bytes()).hexdigest()==before
 with wave.open(str(out/'source-noise.wav'),'wb') as f:f.setparams((1,2,44100,0,'NONE','not compressed'));f.writeframes(struct.pack('<4096h',*noise))
 takes=[];cursor=0.
 for index,program in enumerate(SEQUENCE):
  hold=12. if program in [3,4,5,6] else 6.;takes.append(dict(take=index+1,channel=program+1,patch=CASES[program]['name'],note_on_seconds=cursor+1,note_off_seconds=cursor+1+hold,start_seconds=cursor,hold_seconds=hold));cursor+=hold+5
 midi=mido.MidiFile(type=1,ticks_per_beat=480)
 for channel,case in enumerate(CASES):
  track=mido.MidiTrack();midi.tracks.append(track);track.append(mido.MetaMessage('track_name',name=f'CH{channel+1} {case["name"][3:]}',time=0))
  if channel==0:track.append(mido.MetaMessage('set_tempo',tempo=500000,time=0))
  previous=0
  for take in takes:
   if take['channel']!=channel+1:continue
   start=take['start_seconds'];events=[(start+.05,mido.Message('control_change',channel=channel,control=64,value=0)),(start+.1,mido.Message('control_change',channel=channel,control=7,value=127)),(start+.15,mido.Message('control_change',channel=channel,control=10,value=64)),(take['note_on_seconds'],mido.Message('note_on',channel=channel,note=60,velocity=127)),(take['note_off_seconds'],mido.Message('note_off',channel=channel,note=60,velocity=0))]
   for seconds,message in events:tick=round(seconds*960);message.time=tick-previous;previous=tick;track.append(message)
  track.append(mido.MetaMessage('end_of_track',time=round(cursor*960)-previous))
 midi.save(out/'TVFGRID_CAPTURE.mid');sequence=dict(multichannel=True,note=60,velocity=127,duration_seconds=cursor,takes=takes,cases=CASES,limits='Private source/template-derived media; original seven controls plus seven static midpoint levels. Same source/patch gain as TVFSTEP; no system firmware edits.')
 (out/'capture-sequence.json').write_text(json.dumps(sequence,indent=2)+'\n',encoding='utf-8')
 (out/'README.txt').write_text('TVFGRID hardware calibration\nLoad TVFGRID.IMG on the S-760; select its TVF GRID performance.\nRoute all14 MIDI tracks to their original channels1..14 on the S-760. No program changes.\nRecord the whole '+str(round(cursor))+'second MIDI sequence into one continuous mono48kHz/24bit WAV.\nKeep the prior input gain; no normalization, dynamics, effects or sample-rate conversion.\nInclude the opening/closing bypass takes and release gaps.\nThe first10 takes measure bypass, low/high and seven midpoints; then three opening/closing ramp pairs and two fast steps.\nGenerated image is737280bytes; do not run the system-disk repacker.\n',encoding='utf-8')
 print(json.dumps(dict(image=str(image),sha256=manifest['sha256'],channels=14,takes=len(takes),duration_seconds=cursor)))
if __name__=='__main__':main()
