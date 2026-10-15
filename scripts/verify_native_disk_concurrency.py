"""Firmware Disk Save restriction under incoming MIDI, intact media and cold Load.

Owner's manual Advanced1-3 excludes sound in Disk/Quick Load/Sampling displays.
This qualifies supported restriction/recovery, never three-source arbitration.
"""
import argparse,json,math,shutil
from pathlib import Path
from dataclasses import replace
import numpy as np
from s760_runtime import NativeRuntime,RuntimeConfig
from verify_native_scsi_save import controls,digest
from verify_native_roland_load import audition,render
ROOT=Path(__file__).resolve().parents[1]
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--state-dir',type=Path,required=True);a=ap.parse_args();base=a.state_dir.resolve()
 if base.exists() and any(base.iterdir()):ap.error('Use a fresh private state directory')
 base.mkdir(parents=True,exist_ok=True);source=ROOT/'roms/FDD/ROBOFULL.IMG';working=base/'working.img';shutil.copyfile(source,working)
 hashes={str(p):digest(p) for p in [source,ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG']}
 cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',base/'save',working,sound=False,throttle=False,wave_dump=base/'saved-wave.bin')
 with NativeRuntime(cfg) as r:
  wait,button,click,shot,_=controls(r,base);wait(25);button(':NATIVE_MEDIA','Insert Sample Floppy');click(118,5);click(80,22);wait(8);click(50,34);click(76,98);wait(35);click(10,5);click(15,22);wait(3)
  r.request('pause');r.request('audio_capture',enabled=True)
  for note in [48,55,60,63]:r.request('midi',bytes=[0x90,note,100])
  playing=render(r,22050);assert 0<np.max(np.abs(np.frombuffer(playing,dtype='<f4')))<1
  # Capture the ordinary mode transition separately, so every observed voice write is retained.
  r.request('bus_trace',enabled=True,first=0x100000,last=0x100003)
  r.request('audio_capture',enabled=False);r.request('resume');click(118,5);click(80,30);wait(3);shot('disk-save-muted.png');r.request('pause');transition=r.request('bus_trace',enabled=False)[0]
  assert transition['dropped']==0
  writes=[v for v in transition['rows'] if v['kind']=='w' and v['address'] in [0x100000,0x100002]]
  assert writes and all(v['data']==0 for v in writes[-2:]),'Disk Save did not clear playable pool'
  r.request('audio_capture',enabled=True);assert np.max(np.abs(np.frombuffer(render(r,44100),dtype='<f4')))==0
  r.request('audio_capture',enabled=False);r.request('resume');click(50,34);click(76,98);wait(3);click(62,70);wait(3)
  # The final confirmation starts the write. Schedule through this operation;
  # offsets are recorded separately from claims about firmware handling.
  r.request('pause');start=math.ceil(r.request('status')[0]['seconds']*44100)+512;events=[]
  for i in range(120):
   t=start+i*11025;note=48+i%24;events.extend([dict(sample=t,bytes=[0x90,note,100]),dict(sample=t+8000,bytes=[0x80,note,0])])
  events.sort(key=lambda e:e['sample']);r.schedule_midi(events);r.request('bus_trace',enabled=True,first=0x102002,last=0x102002);r.request('resume');click(66,70);wait(1);r.request('pause');disk_trace=r.request('bus_trace',enabled=False)[0]
  r.request('audio_capture',enabled=True);disk_audio=render(r,35*44100);status=r.request('status')[0]
  assert status['midi_pending']==0 and not status['midi_error'] and len(status['midi_delivered'])==240
  assert [x['sample'] for x in status['midi_delivered']]==[x['sample'] for x in events]
  assert np.max(np.abs(np.frombuffer(disk_audio,dtype='<f4')))==0,'Unexpected Disk-mode sound'
  commands=[v for v in disk_trace['rows'] if v['kind']=='w' and v['address']==0x102002]
  delivered=status['midi_delivered'];overlap=[v for v in commands if delivered[0]['seconds']<=v['seconds']<=delivered[-1]['seconds']]
  assert overlap,'No observed disk request during MIDI delivery'
  r.request('audio_capture',enabled=False);r.request('resume');wait(2);media=r.media_status();assert media['dirty'] and not media['busy'];saved=base/'saved.img';r.export_media(saved);shot('saved.png')
  for note in range(48,72):r.request('midi',bytes=[0x80,note,0])
  wait(2);click(10,5);click(15,22);wait(3);r.request('pause');r.request('audio_capture',enabled=True)
  assert np.max(np.abs(np.frombuffer(render(r,65536),dtype='<f4')))==0,'Stuck voice after Disk Save'
  pcm,recovered=audition(r,0,60);r.request('audio_capture',enabled=False)
 cold=replace(cfg,state_dir=base/'reload',sample_disk=saved,wave_dump=base/'cold-wave.bin')
 with NativeRuntime(cold) as r:
  wait,button,click,shot,_=controls(r,base);wait(25);button(':NATIVE_MEDIA','Insert Sample Floppy');click(118,5);click(80,22);wait(8);click(50,34);click(76,98);wait(35);click(10,5);click(15,22);wait(3);shot('cold-perform.png');r.request('pause');r.request('audio_capture',enabled=True);cold_pcm,cold_audio=audition(r,0,60)
 expected=source.read_bytes()[0x2ac00:0x2ac00+119808]
 for path in ['saved-wave.bin','cold-wave.bin']:assert (base/path).read_bytes()[16:16+119808]==expected
 assert abs(cold_audio['peak']-recovered['peak'])<1e-6
 for p,h in hashes.items():assert digest(Path(p))==h
 assert digest(working)==hashes[str(source)]
 report=dict(passed=True,source_hashes=hashes,source_artifacts={str(p):digest(p) for p in [ROOT/'mame-source/mames760.exe',ROOT/'mame-source/src/mame/roland/s760.cpp',ROOT/'scripts/s760_runtime.lua',ROOT/'scripts/s760_runtime.py',ROOT/'scripts/verify_native_disk_concurrency.py']},active_notes_before_disk=4,transition_trace=transition,disk_trace=disk_trace,observed_disk_writes_during_midi=len(overlap),serial_delivered=delivered,serial_events=240,disk_audio_silent_frames=35*44100,post_disk_silent_frames=65536,exact_cold_sample_bytes=119808,recovered_audio=recovered,cold_audio=cold_audio,media_before_export=media,saved_sha256=digest(saved),manual=dict(path='manuals/S-760_OM.pdf',sha256=digest(ROOT/'manuals/S-760_OM.pdf'),pdf_page=11,printed_page='Advanced1-3',rule='Disk, Quick Load and Sampling displays have no sound output, Copy commands also suppress sound.'),limits='Native original-firmware floppy performance Save under incoming MIDI; partial disk trace is positive overlap evidence only. Serial delivery is not event preservation. Disk-mode mute/recovery is supported; no simultaneous disk/MIDI/voice arbitration or physical timing claim.')
 (base/'concurrency-results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps({k:v for k,v in report.items() if k not in ['transition_trace','disk_trace','serial_delivered']},indent=2))
if __name__=='__main__':main()
