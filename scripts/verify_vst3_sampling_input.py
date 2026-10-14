"""Record deterministic stereo host buses through native firmware in SoundCheck.

Requires the private sampling QA host patch. Saves the actual SDK getState archive,
then inspects its native checkpoint in a diagnostic child and cold-loads the saved
sample disk. Diagnostic replay is separate from DAW project acceptance.
"""
import argparse, asyncio, hashlib, json, os, socket, struct, subprocess, sys, time
from pathlib import Path
import websockets
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from configure_vst3 import save_config
from s760_runtime import NativeRuntime, RuntimeConfig

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host',type=Path,required=True)
parser.add_argument('--module',type=Path,required=True)
parser.add_argument('--blank-disk',type=Path,required=True)
parser.add_argument('--state-dir',type=Path,required=True)
parser.add_argument('--debug-port',type=int,default=9231)
args=parser.parse_args()
work=args.state_dir.resolve();work.mkdir(parents=True,exist_ok=False)
blank=args.blank_disk.resolve();blank_hash=digest(blank)
assert len(blank.read_bytes())==737280 and blank.read_bytes()[4096:]==bytes([15])*(737280-4096)
for port in (4000,args.debug_port):
 with socket.socket() as probe:
  assert probe.connect_ex(('127.0.0.1',port))!=0, f'Port {port} in use'
env=os.environ.copy()
for key in ('S760_NATIVE_ROOT','S760_NATIVE_STATE_ROOT','S760_BOOT_ROM','S760_SYSTEM_DISK','S760_UI_URL'):env.pop(key,None)
env['S760_PLUGIN_CONFIG']=str(work/'settings.json')
env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']=f'--remote-debugging-port={args.debug_port}'
save_config(work/'settings.json',dict(version=1,root=str(ROOT),stateRoot=str(work/'host-state'),bootRom=str(ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN'),systemDisk=str(ROOT/'roms/System/S760224.IMG')))

async def host_record():
 await asyncio.sleep(1)
 async with websockets.connect('ws://127.0.0.1:4000',max_size=20_000_000) as ws:
  async def req(command,expected,**values):
   await ws.send(json.dumps(dict(command=command,**values)))
   while True:
    reply=json.loads(await asyncio.wait_for(ws.recv(),60))
    if reply.get('type')=='error':raise RuntimeError(reply)
    if reply.get('type')==expected:return reply
  loaded=await req('load_plugin','plugin_loaded',path=str(args.module.resolve()),samplingInput=True)
  (work/'loaded.json').write_text(json.dumps(loaded,indent=2),encoding='utf-8')
  assert loaded['data']['type']=='instrument',loaded
  iid=loaded['data']['instanceId']
  blocks=0
  async def tick():
   nonlocal blocks
   count=(64,127,256,511,1024)[blocks%5];blocks+=1
   await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1,blockSize=count,inPlace=True,midiNote=-1,autoNoteOff=False)
   await asyncio.sleep(count/44100*1.05)
  for _ in range(2800):await tick()
  print('Native host booted with varying input blocks',flush=True)
  async def operate():
   async with async_playwright() as pw:
    browser=await pw.chromium.connect_over_cdp(f'http://127.0.0.1:{args.debug_port}')
    page=browser.contexts[0].pages[0]
    canvas=page.locator('canvas[width="640"][height="480"]')
    await canvas.wait_for();box=await canvas.bounding_box();assert box
    async def shot(name):
     await page.screenshot(path=str(work/(name+'.png')));print(name,flush=True)
    async def click(x,y,pause=2,button='left'):
     await page.mouse.move(box['x']+box['width']*x/159,box['y']+box['height']*y/119)
     await page.wait_for_timeout(600)
     await page.mouse.down(button=button);await page.wait_for_timeout(200);await page.mouse.up(button=button)
     await page.wait_for_timeout(pause*1000)
    await shot('boot')
    await click(100,5);await click(80,22);await shot('sampling')
    await click(76,98);await shot('ready');await click(62,66,3);await shot('armed')
    await click(14,98,1);await shot('recording')
    await click(14,98,3,button='right');await shot('stopped')
    await click(140,98);await shot('end')
    await page.get_by_role('button',name='Gotek Select',exact=True).click()
    await page.get_by_label('Local image path').fill(str(blank))
    await page.get_by_role('button',name='Insert',exact=True).click();await page.wait_for_timeout(2000)
    await click(118,5);await click(80,30,8);await click(20,22,1);await click(25,54);await shot('sample-list')
    await click(10,98,1);await click(76,98,3);await shot('save-choice')
    await click(62,70,3);await click(66,70,35);await shot('saved')
    await browser.close()
  operation=asyncio.create_task(operate())
  try:
   while not operation.done():await tick()
   await operation
  finally:
   if not operation.done():operation.cancel()
  await req('qa_project_file','qa_project_file',instanceId=iid,action='save',path=str(work/'recorded-host-state.bin'))
  await req('remove_plugin','plugin_removed',instanceId=iid)

with (work/'host.log').open('w',encoding='utf-8') as log:
 host=subprocess.Popen([str(args.host.resolve())],cwd=work,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
 try:asyncio.run(host_record())
 finally:
  host.terminate()
  try:host.wait(timeout=10)
  except subprocess.TimeoutExpired:host.kill();host.wait()

# Extract the native machine section; keep the original SDK archive as evidence.
archive=(work/'recorded-host-state.bin').read_bytes()[4:]
assert archive[:8]==b'S760NPS1' and hashlib.sha256(archive[40:]).digest()==archive[8:40]
payload=archive[40:];offset=24
identity_size,=struct.unpack_from('<I',payload,offset);offset+=4+identity_size
size,=struct.unpack_from('<I',payload,offset);machine=payload[offset+4:offset+4+size];assert len(machine)==size
os.environ['S760_NATIVE_STEREO_MONITOR']='1'
cfg=RuntimeConfig(ROOT/'mame-source/mames760.exe',ROOT/'roms/BOOT/Roland_S-760_v1.11.BIN',ROOT/'roms/System/S760224.IMG',work/'inspect',sound=False,throttle=False,experimental_adc=True,wave_dump=work/'checkpoint-wave.bin')
with NativeRuntime(cfg) as rt:
 rt.request('pause');(cfg.state_dir/'runtime-checkpoint.bin').write_bytes(machine);rt.request('checkpoint_load')
 status=rt.request('input_status')[0];assert status['underruns']==0,status
 rt.request('resume');rt.export_media(work/'captured-stereo.img')

cfg=RuntimeConfig(cfg.executable,cfg.boot_rom,cfg.system_disk,work/'reload',work/'captured-stereo.img',sound=False,throttle=False,wave_dump=work/'reloaded-wave.bin')
with NativeRuntime(cfg) as rt:
 def wait(seconds):
  until=rt.request('status')[0]['seconds']+seconds;deadline=time.monotonic()+90
  while rt.request('status')[0]['seconds']<until:
   assert time.monotonic()<deadline,'Native timeout'
   time.sleep(.01)
 def click(x,y):
  rt.request('pointer',x=x,y=y);wait(.2)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=True);wait(.1)
  rt.request('button',port=':NATIVE_MOUSE_BUTTONS',name='Mouse Left',down=False);wait(.2)
 wait(20)
 rt.request('button',port=':NATIVE_MEDIA',name='Insert Sample Floppy',down=True)
 rt.request('button',port=':NATIVE_MEDIA',name='Insert Sample Floppy',down=False)
 click(118,5);wait(2);click(80,22);wait(8);click(20,22);click(25,54);wait(2);click(10,98);click(76,98);wait(35)

disk=(work/'captured-stereo.img').read_bytes();before=(work/'checkpoint-wave.bin').read_bytes();after=(work/'reloaded-wave.bin').read_bytes()
samples=[];wave_offset=16;disk_offset=0x2ac00
for channel,(period,step) in enumerate(((257,64),(509,32))):
 record=disk[0x18e00+channel*48:0x18e00+(channel+1)*48]
 assert record[:11]==b'NEW:Unnamed' and record[15]==ord('L' if channel==0 else 'R'),record.hex()
 frames=(struct.unpack_from('<I',record,24)[0]>>8)+1
 allocation=struct.unpack_from('<H',record,42)[0]*9216
 assert 10000<frames<150000 and frames*2<=allocation,(frames,allocation)
 pcm=before[wave_offset:wave_offset+allocation]
 assert pcm==after[wave_offset:wave_offset+allocation]==disk[disk_offset:disk_offset+allocation]
 values=struct.unpack_from('<'+'h'*frames,pcm);phase=values[0]//step+period//2
 assert all(value==((phase+i)%period-period//2)*step for i,value in enumerate(values)),f'Channel {channel} input discontinuity/gain/routing error'
 assert not any(pcm[frames*2:])
 samples.append(dict(channel=channel,frames=frames,allocation_bytes=allocation,pcm_sha256=hashlib.sha256(pcm).hexdigest(),exact_host_input=True,wave_disk_cold_reload_equal=True,metadata_hex=record.hex()))
 wave_offset+=allocation;disk_offset+=allocation
assert digest(blank)==blank_hash
result=dict(profile='SoundCheck actual VST3 stereo input, float32 44100Hz, varying 64/127/256/511/1024-frame paced realtime-mode callbacks',samples=samples,in_place_host_buffers=True,input_underruns=status['underruns'],source_preserved=True,blank_sha256=blank_hash,identities={str(p.relative_to(ROOT)):digest(p) for p in (args.module.resolve(),args.host.resolve(),cfg.executable,cfg.boot_rom,cfg.system_disk)},limitations=['No physical ADC/analog hardware parity claim','No third-party DAW recording acceptance','Input buses at 48000/96000 explicitly unsupported; output-only remains supported','Live Sampler FX class remains unadvertised'])
(work/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
