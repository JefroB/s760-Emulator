"""Original firmware HD0 initialize/Save/export/fresh Load on a private HD00_512.img.
No guest RAM/PC injection. Named 10 MiB Roland HD0 profile, not hardware timing.
"""
import argparse,hashlib,json,shutil,struct,time
from pathlib import Path
from dataclasses import replace
from PIL import Image
from s760_runtime import NativeRuntime,RuntimeConfig
from verify_native_roland_load import audition
ROOT=Path(__file__).resolve().parents[1]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def controls(r,folder):
 def wait(seconds):
  end=r.request('status')[0]['seconds']+seconds;deadline=time.monotonic()+120
  while r.request('status')[0]['seconds']<end:
   assert time.monotonic()<deadline,'Firmware stopped advancing'
   time.sleep(.01)
 def button(port,name):
  r.request('button',port=port,name=name,down=True);wait(.2)
  r.request('button',port=port,name=name,down=False);wait(.2)
 def click(x,y):
  r.request('pointer',x=x,y=y);wait(.3);button(':NATIVE_MOUSE_BUTTONS','Mouse Left');wait(.3)
 def screenshot(name):Image.frombytes('RGBA',(640,480),r.request('frames')[1][0][6:]).save(folder/name)
 def select_hd():
  click(140,22);wait(2);click(96,78);button(':PANEL2','Panel F3');wait(20);click(100,38);wait(8)
 return wait,button,click,screenshot,select_hd
def samples(path):
 d=path.read_bytes();assert d[4:14]==b'S770 MR25A';result=[]
 for i in range(struct.unpack_from('<H',d,0x11c)[0]):
  e=d[1644*512+i*32:1644*512+(i+1)*32];assert e[16]==0x44
  c,n=struct.unpack_from('<HH',e,28);parts=[];seen=set()
  for _ in range(n):
   assert 2<=c<0xfff6 and c not in seen;seen.add(c);off=5548*512+(c-2)*9216
   assert off+9216<=len(d);parts.append(d[off:off+9216]);c=struct.unpack_from('<H',d,1028*512+c*2)[0]
  assert c>=0xfff6;result.append(b''.join(parts))
 return result
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--state-dir',type=Path,required=True);a=ap.parse_args();base=a.state_dir.resolve()
 if base.exists() and any(base.iterdir()):ap.error('Use a fresh private state directory')
 base.mkdir(parents=True,exist_ok=True);source=ROOT/'roms/SCSI/HD00_512.img';floppy=ROOT/'roms/FDD/ROBOFULL.IMG'
 hashes={str(p):digest(p) for p in [source,floppy,ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG']}
 assert hashes[str(source)]=='8a940c7f114326aedbeb457ed3ed83bc7dbc4b2000ac552d8ff7c410bba43a6c'
 cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',base/'save',floppy,sound=False,throttle=False)
 media=cfg.state_dir/'roms/SCSI';media.mkdir(parents=True);shutil.copyfile(source,media/source.name);saved=base/'saved-hd.img'
 with NativeRuntime(cfg) as r:
  wait,button,click,shot,select_hd=controls(r,base);wait(25);button(':NATIVE_MEDIA','Insert Sample Floppy')
  click(118,5);click(80,22);wait(8);click(50,34);click(76,98);wait(35)
  click(10,5);click(15,22);wait(3)
  r.request('pause');r.request('audio_capture',enabled=True);before,audio=audition(r,0,60);r.request('audio_capture',enabled=False);r.request('resume');wait(1)
  click(118,5);click(80,54);wait(4);select_hd();click(76,98);wait(3);click(54,62);wait(3);click(80,62);wait(3);click(54,62);wait(45);shot('initialized.png')
  click(118,5);click(80,30);wait(5);click(50,34);click(76,98);wait(3);click(62,70);wait(3);click(66,70);wait(60);shot('saved.png');r.export_scsi_hd0(saved)
  try:r.export_scsi_hd0(saved)
  except FileExistsError:pass
  else:raise AssertionError('Existing output accepted')
  r.export_scsi_hd0(base/'second-export.img');assert saved.read_bytes()==(base/'second-export.img').read_bytes()
 allocations=samples(saved);assert len(allocations)==13
 expected=floppy.read_bytes()[0x2ac00:0x2ac00+119808];assert b''.join(allocations)==expected
 assert digest(media/source.name)==hashes[str(source)] and digest(saved)!=hashes[str(source)]
 cold=replace(cfg,state_dir=base/'reload',sample_disk=None,wave_dump=base/'wave.bin');media=cold.state_dir/'roms/SCSI';media.mkdir(parents=True);shutil.copyfile(saved,media/source.name)
 with NativeRuntime(cold) as r:
  wait,button,click,shot,select_hd=controls(r,base);wait(25);click(118,5);click(80,22);wait(8);select_hd();shot('cold-list.png');click(50,34);click(76,98);wait(60)
  click(10,5);click(15,22);wait(3);shot('cold-perform.png');r.request('pause');r.request('audio_capture',enabled=True);after,cold_audio=audition(r,0,60)
 wave=(base/'wave.bin').read_bytes();assert wave[16:16+119808]==expected,'Fresh HD Load sample mismatch'
 # Firmware free-running voice phase can differ across independent boots; compare level and spectrum separately.
 import numpy as np
 def spectrum(pcm):
  v=np.frombuffer(pcm,dtype='<f4').reshape(-1,2);return int(np.argmax(np.abs(np.fft.rfft(v[:,0]*np.hanning(len(v))))))
 assert spectrum(before)==spectrum(after)
 assert abs(audio['peak']-cold_audio['peak'])<1e-6
 for name,h in hashes.items():assert digest(Path(name))==h,'Original media changed'
 report=dict(passed=True,source_hashes=hashes,saved_sha256=digest(saved),image_bytes=saved.stat().st_size,sample_count=13,exact_sample_bytes=119808,cold_frequency_bin=spectrum(after),audio=cold_audio,existing_output_rejected=True,repeat_export_exact=True,limits='Named HD0/512-sector 10 MiB quick initialization and performance Save; explicit Python export, fresh original-firmware Load. No automatic library writeback, GUI/VST export, physical timing or arbitrary media claim.')
 (base/'save-results.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
