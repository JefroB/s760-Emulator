"""Qualify audible native firmware bend through actual VST3 parameter queues.

Requires original OS2.24, ROBOFULL and a WebView-enabled module in the privately
patched SoundCheck host. See docs/NATIVE_VST3_MIDI.md. Uses loopback4000 and the
selected debug port; captures remain in a new private --state-dir.
"""
import asyncio,json,os,subprocess,time,base64

from pathlib import Path

import websockets

from playwright.async_api import async_playwright


import argparse
parser=argparse.ArgumentParser(description='Configured firmware pitch-bend qualification in SoundCheck')
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
    await page.get_by_label('Local image path').fill('D:/S-760/roms/FDD/ROBOFULL.IMG')
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
    await click(40,5,1)
    await click(60,39,2)
    knob=page.get_by_role('button',name='VALUE knob',exact=True)
    # Coordinates are the OS2.24 Mouse+CRT field locations in this native profile.
    # Each field starts at0 in the immutable ROBOFULL fixture.
    for y in (49,44):
     await page.mouse.move(box['x']+box['width']*77/159,box['y']+box['height']*y/119)
     await page.wait_for_timeout(1200)
     for _ in range(12):
      await knob.press('ArrowUp');await page.wait_for_timeout(100)
    await page.wait_for_timeout(1000)
    await page.screenshot(path=str(w/'bend-up-down-12.png'))
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
  data_before=(await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1))['data']
  assert data_before['peak']==0, 'Expected silence before note'
  for n in range(350):
   args={'midiNote':60,'midiVelocity':127,'autoNoteOff':False} if n==0 else {}
   data=(await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1,**args))['data']
   audio.extend(data['waveform'])
   if n==150:
    await req('close_editor','editor_closed',instanceId=iid)
    await req('open_editor','editor_opening',instanceId=iid)
   await asyncio.sleep(.012)
  rate=data['waveformSampleRate']

  import numpy as np
  report={}
  async def render(label,seconds=1.5,**args):
   samples=[]
   for n in range(int(seconds*44100/512)):
    d=(await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1,**(args if n==0 else {})))['data']
    samples.extend(d['waveform']);await asyncio.sleep(.012)
   a=np.array(samples,dtype=np.float32);np.save(w/(label+'.npy'),a)
   assert np.isfinite(a).all()
   a=a[-22050:];spec=abs(np.fft.rfft(a*np.hanning(len(a))))
   report[label]={'peak':float(max(abs(a))),'rms':float(np.sqrt(np.mean(a*a))),'frequency':float(np.argmax(spec)*44100/len(a))}
   print(label,report[label],flush=True)
   return report[label]
  async def cc(number,value,channel=0):
   index=channel*129+(128 if number==129 else number)
   await req('set_param','param_updated',instanceId=iid,paramId=str(0x760000+index),value=value)
  await render('baseline')
  await cc(129,1);await render('bend-high')
  await cc(129,8192/16383);await render('bend-center')
  await cc(129,0);await render('bend-low')
  await cc(129,8192/16383);await render('bend-restored')
  await cc(123,0);await render('released')
  assert abs(report['baseline']['frequency']-20004)<=2
  assert abs(report['bend-high']['frequency']-4108)<=8
  assert abs(report['bend-low']['frequency']-10002)<=4
  assert report['bend-center']['frequency']==report['baseline']['frequency']
  assert report['bend-restored']['frequency']==report['baseline']['frequency']
  assert report['released']['peak']==0
  (w/'automation-report.json').write_text(json.dumps(report,indent=2))
  (w/'automation-report.txt').write_text('\n'.join(f'{key}: '+json.dumps(value) for key,value in report.items()))
  await req('remove_plugin','plugin_removed',instanceId=iid)
try:asyncio.run(main())
finally:host.terminate();host.wait(timeout=10);log.close()

