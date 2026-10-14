"""Requires a WebView-enabled native instrument and the private SoundCheck QA patch.

The test writes only to a new --state-dir, uses ports4000 and --debug-port,
starts/stops its own hidden hosts, and keeps proprietary captures/state private.
See docs/NATIVE_PLUGIN_STATE.md for supported limits and the QA host patch.
"""
import asyncio,json,os,subprocess,time,base64,hashlib

from pathlib import Path

import websockets

from playwright.async_api import async_playwright


import argparse
parser=argparse.ArgumentParser(description='Cold native VST3 project reopen in a privately patched SoundCheck host')
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
from soundcheck_project import write_project, read_project, digest
settings=w/'plugin-settings.json'
import shutil,hashlib
media=w/'source-library';media.mkdir(exist_ok=True)
shutil.copyfile(r/'roms/FDD/ROBOFULL.IMG',media/'ROBOFULL.IMG')
save_config(settings,dict(version=1,root=str(r),stateRoot=str(w/'host-state'),bootRom=str(r/'roms/BOOT/Roland_S-760_v1.11.BIN'),systemDisk=str(r/'roms/System/S760224.IMG'),mediaDirectory=str(media)))
for key in ['S760_NATIVE_ROOT','S760_NATIVE_STATE_ROOT','S760_BOOT_ROM','S760_SYSTEM_DISK','S760_UI_URL']:env.pop(key,None)
env['S760_PLUGIN_CONFIG']=str(settings)
# A deliberately unusable global default must not win over project selection.
env['LOCALAPPDATA']=str(w/'global-defaults')
global_settings=w/'global-defaults/S760/plugin-settings.json'
global_settings.parent.mkdir(parents=True)
global_settings.write_text('{"version":1,"root":"missing-global-installation"}')
global_before=global_settings.read_bytes()

log=(w/'host.log').open('w');host=subprocess.Popen([str(host_path)],cwd=w,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)

async def main():
 global host

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

  await asyncio.sleep(3)

  audio=[]
  async def ui_check():
   async with async_playwright() as pw:
    browser=await pw.chromium.connect_over_cdp(f'http://127.0.0.1:{options.debug_port}')
    page=browser.contexts[0].pages[0]
    page.set_default_timeout(30000)
    await page.get_by_role('button',name='Gotek Select',exact=True).wait_for()
    await page.get_by_role('button',name='MENU',exact=True).click()
    await page.wait_for_timeout(500)
    await page.get_by_role('button',name='EXIT',exact=True).click()
    await page.wait_for_timeout(500)
    await page.get_by_role('button',name='Gotek Select',exact=True).click()
    await page.get_by_label('Local image path').fill(str(media/'ROBOFULL.IMG'))
    await page.get_by_role('button',name='Insert',exact=True).click()
    await page.get_by_text('ROBOFULL.IMG',exact=True).wait_for()
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
    await click(10,5,1)
    await click(15,22,4)
    await page.mouse.move(box['x']+box['width']*153/159,box['y']+box['height']*18/119)
    await page.wait_for_timeout(700)
    await page.screenshot(path=str(w/'value-127.png'))
    knob=page.get_by_role('button',name='VALUE knob',exact=True)
    for _ in range(3): await knob.press('ArrowDown'); await page.wait_for_timeout(150)
    await page.wait_for_timeout(600)
    await page.screenshot(path=str(w/'value-124.png'))
    for _ in range(3): await knob.press('ArrowUp'); await page.wait_for_timeout(150)
    await page.wait_for_timeout(600)
    await page.screenshot(path=str(w/'value-restored.png'))
    await browser.close()
  check=None
  for n in range(2200):
   await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1)
   await asyncio.sleep(.012)
  print('booted',flush=True)
  check=asyncio.create_task(ui_check())
  while not check.done():
   await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1)
   await asyncio.sleep(.012)
  await check
  import numpy as np
  project=w/'session.s760-state'
  saved=await req('qa_project_file','qa_project_file',instanceId=iid,action='save',path=str(project))
  async def render(label, varied=False):
   samples=[]
   cursor=0;index=0
   while cursor<432*512:
    count=(64,127,256,511,512)[index%5] if varied else 512
    # Split exactly at note-off so both block patterns schedule the same wire event.
    boundary=258*512 if cursor<258*512 else 432*512
    count=min(count,boundary-cursor)
    args={'midiNote':60,'midiVelocity':127,'autoNoteOff':False} if cursor==0 else ({'midiNoteOff':60} if cursor==258*512 else {})
    d=(await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1,blockSize=count,**args))['data']
    samples.extend(d['waveform']);await asyncio.sleep(.012)
    cursor+=count;index+=1
   a=np.array(samples,dtype=np.float32);np.save(w/(label+'.npy'),a)
   assert len(a)==432*512 and np.isfinite(a).all()
   assert max(abs(a))>.01 and max(abs(a[-22050:]))==0
   return a
  reference=await render('before-host-exit')
  await req('remove_plugin','plugin_removed',instanceId=iid)
  await ws.close();host.terminate();host.wait(timeout=10)
  moved=w/'relocated-firmware';moved.mkdir(exist_ok=True)
  shutil.copyfile(r/'roms/BOOT/Roland_S-760_v1.11.BIN',moved/'boot.bin')
  shutil.copyfile(r/'roms/System/S760224.IMG',moved/'system.img')
  media.rename(w/'relocated-library')
  (w/'host-state').rename(w/'relocated-old-host-state')
  save_config(settings,dict(version=1,root=str(r),stateRoot=str(w/'fresh-host-state'),bootRom=str(moved/'boot.bin'),systemDisk=str(moved/'system.img'),mediaDirectory=str(w/'relocated-library')))
  document=w/'session.soundcheck-project.json'
  write_project(document,project,module,json.loads(settings.read_text()))
  metadata,project,project_settings=read_project(document,module,w/'project-owned-runtime')
  save_config(settings,project_settings)
  assert global_settings.read_bytes()==global_before
  # Resolve the saved project profile instead of silently using host defaults.
  assert metadata['sampleRate']==44100 and metadata['maxBlock']==512
  altered=w/'different-build.vst3'
  shutil.copyfile(module,altered)
  with altered.open('ab') as out:out.write(b'project-identity-rejection-probe')
  try:read_project(document,altered,w/'unused-runtime')
  except ValueError as error:assert 'module identity mismatch' in str(error)
  else:raise AssertionError('Cross-build project accepted')
  assert not media.exists()
  host=subprocess.Popen([str(host_path)],cwd=w,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW)
  await asyncio.sleep(2)
  ws=await websockets.connect('ws://127.0.0.1:4000',max_size=20_000_000)
  loaded=await req('load_plugin','plugin_loaded',path=str(module),sampleRate=48000,maxBlock=512);iid=loaded['data']['instanceId']
  try:await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(project))
  except RuntimeError as error:assert 'Project restore rejected' in str(error)
  else:raise AssertionError('Different-rate project accepted')
  await req('remove_plugin','plugin_removed',instanceId=iid)
  loaded=await req('load_plugin','plugin_loaded',path=str(module),sampleRate=metadata['sampleRate'],maxBlock=metadata['maxBlock']);iid=loaded['data']['instanceId']
  await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(project))
  restored=await render('after-cold-host-reopen')
  assert np.array_equal(reference,restored),'Cold host reopen changed PCM'
  await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(project))
  varied=await render('after-varied-block-reopen',varied=True)
  assert np.array_equal(reference,varied),'Actual callback block variation changed PCM'
  await req('qa_processing','qa_processing',instanceId=iid,action='setup',sampleRate=44100,maxBlock=1024)
  try:await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(project))
  except RuntimeError as error:assert 'Project restore rejected' in str(error)
  else:raise AssertionError('Different negotiated maximum project accepted')
  await req('qa_processing','qa_processing',instanceId=iid,action='setup',sampleRate=44100,maxBlock=512)
  await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(project))
  corrupt=w/'corrupt.s760-state';damaged=bytearray(project.read_bytes());damaged[-1]^=1;corrupt.write_bytes(damaged)
  try:
   await req('qa_project_file','qa_project_file',instanceId=iid,action='restore',path=str(corrupt))
  except RuntimeError as error:
   assert 'Project restore rejected' in str(error),str(error)
  else:raise AssertionError('Corrupted project was accepted')
  await req('qa_processing','qa_processing',instanceId=iid,action='resume')
  preserved=await render('after-corrupt-rejection')
  assert np.array_equal(reference,preserved),'Rejected archive changed the live timeline'
  await asyncio.sleep(2)
  async with async_playwright() as pw:
   browser=await pw.chromium.connect_over_cdp(f'http://127.0.0.1:{options.debug_port}');page=browser.contexts[0].pages[0]
   await page.get_by_text('ROBOFULL.IMG',exact=True).wait_for()
   await page.get_by_role('button',name='Plugin configuration',exact=True).click()
   assert await page.get_by_label('Boot ROM (32KB)').input_value()==str(moved/'boot.bin')
   assert await page.get_by_label('Media directory',exact=True).input_value()==str(w/'relocated-library')
   await page.screenshot(path=str(w/'cold-reopen-relocated-settings.png'));await browser.close()
  report=dict(host='SoundCheck 1.0.0 Windows x64 native SDK QA host',sampleRate=44100,blockSize=512,frames=len(restored),exact_pcm=True,corrupt_rejection_preserves_pcm=True,release_tail_peak=float(max(abs(restored[-22050:]))),original_library_missing=True,original_native_state_directory_missing=True,firmware_relocated=True,settings_persisted=True,project_bytes=project.stat().st_size,project_sha256=hashlib.sha256(project.read_bytes()).hexdigest(),module_sha256=hashlib.sha256((module).read_bytes()).hexdigest())
  report.update(project_document_sha256=digest(document),host_sha256=digest(host_path),project_configuration_override=True,global_settings_unchanged=global_settings.read_bytes()==global_before,variable_callback_blocks_exact=True,different_negotiated_maximum_rejected=True,different_rate_rejected=True,cross_build_rejected=True,host_matrix=['SoundCheck 1.0.0 Windows x64 private SDK adapter'])
  (w/'report.json').write_text(json.dumps(report,indent=2));print(json.dumps(report),flush=True)
  await req('remove_plugin','plugin_removed',instanceId=iid);await ws.close()

try:asyncio.run(main())
finally:host.terminate();host.wait(timeout=10);log.close()

