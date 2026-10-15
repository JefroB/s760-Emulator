"""Normal native filter/stereo/state functional acceptance in offline SoundCheck mode.
Realtime scheduling/deadline acceptance is kept in separate paced native-host tests.
"""
import asyncio,json,os,subprocess

from pathlib import Path

import websockets

from playwright.async_api import async_playwright


import argparse
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--host',type=Path,required=True)
parser.add_argument('--module',type=Path,required=True)
parser.add_argument('--state-dir',type=Path,required=True)
parser.add_argument('--debug-port',type=int,default=9231)
options=parser.parse_args()
if not 1<=options.debug_port<=65535 or options.debug_port==4000:
 raise SystemExit('Choose a debug port in1..65535 other than4000')
import socket
for port in (4000,options.debug_port):
 with socket.socket() as probe:
  probe.settimeout(.2)
  if probe.connect_ex(('127.0.0.1',port))==0:
   raise SystemExit(f'Loopback port{port} is in use; stop its owner or choose a different debug port')
r=Path(__file__).resolve().parents[1]
w=options.state_dir.resolve()
if w.exists():raise SystemExit('Choose a new private state directory')
w.mkdir(parents=True)
host_path=options.host.resolve();module=options.module.resolve()
if not host_path.is_file() or not module.is_file():raise SystemExit('Host and module must be existing files')
env=os.environ.copy()
env['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']=f'--remote-debugging-port={options.debug_port}'

import sys
sys.path.insert(0,str(r/'scripts'))
from configure_vst3 import save_config
settings=w/'plugin-settings.json'
save_config(settings,dict(version=1,root=str(r),stateRoot=str(w/'host-state'),bootRom=str(r/'roms/BOOT/Roland_S-760_v1.11.BIN'),systemDisk=str(r/'roms/System/S760224.IMG')))
for key in ['S760_NATIVE_ROOT','S760_NATIVE_STATE_ROOT','S760_BOOT_ROM','S760_SYSTEM_DISK','S760_UI_URL']:env.pop(key,None)
env['S760_PLUGIN_CONFIG']=str(settings)

import hashlib
source=r/'roms/FDD/ROBO_TVF.IMG'
original=source.read_bytes()
assert hashlib.sha256(original).hexdigest()=='1bcbd06688769883ad0f1477608fd80a134e4b22e7bea76709a98283007f3fad'
disk=bytearray(original)
for note,partial in ((60,0),(61,13),(62,15)):
 disk[0x8e20+note-21]=partial
 disk[0x10e00+partial*128+0x15]=(60-note)&255
assert disk[0x18e00:]==original[0x18e00:]
fixture=w/'normal-filter.img';fixture.write_bytes(disk)
(w/'fixture.json').write_text(json.dumps(dict(source_sha256=hashlib.sha256(original).hexdigest(),fixture_sha256=hashlib.sha256(disk).hexdigest(),mapping={'60':'bypass','61':'LP C32 R0','62':'LP C96 R0'},changes='First patch keymap and partial coarse compensation only; all sample/PCM bytes unchanged'),indent=2),encoding='utf-8')

log=(w/'host.log').open('w');host=subprocess.Popen([str(host_path)],cwd=w,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)

async def main():

 await asyncio.sleep(1)

 async with websockets.connect('ws://127.0.0.1:4000',max_size=20_000_000) as ws:

  async def req(command,expected,**args):

   await ws.send(json.dumps(dict(command=command,**args)))

   while True:

    msg=json.loads(await asyncio.wait_for(ws.recv(),60))

    if msg.get('type')=='error': raise RuntimeError(msg)

    if msg.get('type')==expected:return msg

  loaded=await req('load_plugin','plugin_loaded',path=str(module))

  print("loaded parameters",len(loaded["data"]["parameters"]),flush=True);(w/'loaded.json').write_text(json.dumps(loaded,indent=2));iid=loaded['data']['instanceId']
  setup=await req('qa_processing','qa_processing',instanceId=iid,action='mode',mode=2)
  assert setup['data']['mode']==2,'Functional QA requires negotiated offline processing'
  (w/'processing-contract.json').write_text(json.dumps(setup,indent=2),encoding='utf-8')

  await asyncio.sleep(3)

  async def ui_check():
   async with async_playwright() as pw:
    browser=await pw.chromium.connect_over_cdp(f'http://127.0.0.1:{options.debug_port}')
    pages=[p for c in browser.contexts for p in c.pages]
    print('editor pages',[(p.url) for p in pages],flush=True)
    page=next((p for p in pages if 'index.html' in p.url),pages[0])
    await page.screenshot(path=str(w/'initial-editor.png'))
    (w/'initial-editor.html').write_text(await page.content(),encoding='utf-8')
    page.set_default_timeout(30000)
    await page.get_by_role('button',name='Gotek Select',exact=True).wait_for()
    await page.get_by_role('button',name='MENU',exact=True).click()
    await page.wait_for_timeout(500)
    await page.get_by_role('button',name='EXIT',exact=True).click()
    await page.wait_for_timeout(500)
    await page.get_by_role('button',name='Gotek Select',exact=True).click()
    await page.get_by_label('Local image path').fill(str(fixture))
    await page.get_by_role('button',name='Insert',exact=True).click()
    await page.get_by_text('normal-filter.img',exact=True).wait_for()
    canvas=page.locator('canvas[width="640"][height="480"]')
    box=await canvas.bounding_box();assert box
    async def click(x,y,pause):
     await page.mouse.move(box['x']+box['width']*x/159,box['y']+box['height']*y/119)
     await page.wait_for_timeout(600)
     await page.mouse.down();await page.wait_for_timeout(200);await page.mouse.up()
     await page.wait_for_timeout(pause*1000)
    await click(118,5,3)
    await click(80,22,10)
    await click(50,34,3)
    await click(76,98,42)
    await page.screenshot(path=str(w/'loaded.png'))

    await click(10,5,1);await click(15,22,2)
    await browser.close()
  for _ in range(2200):
   await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1)
   await asyncio.sleep(.012)
  task=asyncio.create_task(ui_check())
  while not task.done():
   await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012)
  await task
  import numpy as np
  report=[]
  async def render(note,pan,label,varied=False):
   await req('set_param','param_updated',instanceId=iid,paramId=str(0x760000+10),value=pan/127)
   for _ in range(8):
    await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.02)
   frames=0;parts=[];index=0
   while frames<5*44100:
    size=(64,127,256,511,512)[index%5] if varied else 512
    boundary=3*44100 if frames<3*44100 else 5*44100
    size=min(size,boundary-frames)
    args={'midiNote':note,'midiVelocity':100,'autoNoteOff':False} if frames==0 else ({'midiNoteOff':note} if frames==3*44100 else {})
    d=(await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1,blockSize=size,**args))['data']
    parts.append(np.column_stack((d['waveformLeft'],d['waveformRight'])).astype(np.float32))
    frames+=size;index+=1;await asyncio.sleep(.02)
   a=np.concatenate(parts);np.save(w/(label+'.npy'),a)
   assert len(a)==5*44100 and np.isfinite(a).all() and 0<np.max(np.abs(a))<1
   assert np.max(np.abs(a[-44100:]))==0,'Filter failed to release'
   held=a[44100:2*44100];peaks=np.max(np.abs(held),axis=0)
   if pan==0:assert peaks[0]>0 and peaks[1]==0
   elif pan==127:assert peaks[1]>0 and peaks[0]==0
   else:assert np.array_equal(held[:,0],held[:,1])
   mono=held[:,int(pan==127)];power=abs(np.fft.rfft(mono*np.hanning(len(mono))))**2;freq=np.fft.rfftfreq(len(mono),1/44100)
   report.append(dict(note=note,pan=pan,rms=float(np.sqrt(np.mean(mono**2))),low_high=float(sum(power[freq<2000])/max(sum(power[freq>8000]),1e-30)),silent_release_frames=44100))
   print(label,report[-1],flush=True)
   return a
  for note in (60,61,62):
   for pan in (0,64,127):await render(note,pan,f'n{note}-pan{pan}')
  rows={row['note']:row for row in report if row['pan']==64}
  assert rows[61]['rms']<rows[60]['rms']*.8,'LP C32 did not attenuate'
  assert rows[61]['low_high']>rows[62]['low_high']*2,'Cutoff change did not alter spectrum'
  project=w/'filter.s760state'
  await req('qa_project_file','qa_project_file',instanceId=iid,action='save',path=str(project))
  reference=await render(61,64,'state-reference')
  await req('remove_plugin','plugin_removed',instanceId=iid)
  loaded=await req('load_plugin','plugin_loaded',path=str(module));iid=loaded['data']['instanceId']
  setup=await req('qa_processing','qa_processing',instanceId=iid,action='mode',mode=2)
  assert setup['data']['mode']==2
  await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(project))
  replay=await render(61,64,'state-replay',varied=True)
  assert np.array_equal(reference,replay),'Filter state/variable blocks changed PCM'
  await req('close_editor','editor_closed',instanceId=iid)
  await req('open_editor','editor_opening',instanceId=iid)
  await req('remove_plugin','plugin_removed',instanceId=iid)
  result=dict(passed=True,profile='SoundCheck native SDK VST3 offline44100Hz, normal filter defaults',cases=9,rows=report,exact_replay_frames=len(reference),variable_blocks=[64,127,256,511,512],limits='Three named patches; no physical fidelity or other DAW claim')
  (w/'filter-results.json').write_text(json.dumps(result,indent=2),encoding='utf-8');print(json.dumps(result,indent=2))
try:asyncio.run(main())
finally:host.terminate();host.wait(timeout=10);log.close()
