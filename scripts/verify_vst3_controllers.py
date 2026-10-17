"""Native SDK host acceptance for configured expression, bend/RPN, stereo pan,
sustain, documented channel modes and explicit all-channel panic/reset macros.
Requires the private SoundCheck QA patch with separate stereo waveform capture.
Functional controller checks negotiate offline processing by default; use the
separate paced native-host tests for realtime deadlines. --burst-check verifies
unpaced blocks under the chosen contract without retrying rejected blocks.
RawCC120/121 remain original-firmware passthrough; see docs/emulator/runtime/native-vst3-midi.md.
"""
"""Qualify audible native firmware bend through actual VST3 parameter queues.

Requires original OS2.24, ROBOFULL and a WebView-enabled module in the privately
patched SoundCheck host. See docs/emulator/runtime/native-vst3-midi.md. Uses loopback4000 and the
selected debug port; captures remain in a new private --state-dir.
"""
import asyncio,json,os,subprocess,time,base64

from pathlib import Path

import websockets

from playwright.async_api import async_playwright


import argparse
parser=argparse.ArgumentParser(description='Native firmware controller/panic qualification in SoundCheck')
parser.add_argument('--host',type=Path,required=True)
parser.add_argument('--module',type=Path,required=True)
parser.add_argument('--state-dir',type=Path,required=True)
parser.add_argument('--debug-port',type=int,default=9231)
parser.add_argument('--processing-mode',choices=('realtime','offline'),default='offline',help='Negotiate the host processing contract explicitly')
parser.add_argument('--burst-check',action='store_true',help='Exercise64 unpaced host blocks before the controller matrix')
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
  mode=2 if options.processing_mode=='offline' else 0
  setup=await req('qa_processing','qa_processing',instanceId=iid,action='mode',mode=mode)
  assert setup['data']['mode']==mode,'Host did not negotiate requested processing mode'
  (w/'processing-contract.json').write_text(json.dumps(dict(mode=options.processing_mode,host=setup,burst_check=options.burst_check),indent=2),encoding='utf-8')
  if options.burst_check:
   await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=64)
   print('64 unpaced blocks passed',flush=True)

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
    for x,y,steps in ((77,40,11),(153,69,63)):
     await page.mouse.move(box['x']+box['width']*x/159,box['y']+box['height']*y/119)
     await page.wait_for_timeout(1200)
     for _ in range(steps):
      await knob.press('ArrowUp');await page.wait_for_timeout(80)
    await page.wait_for_timeout(1000)
    await page.screenshot(path=str(w/'assigned-expression.png'))
    await click(10,5,1);await click(15,22,2)
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
   samples=[];left=[];right=[]
   for n in range(int(seconds*44100/512)):
    d=(await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1,**(args if n==0 else {})))['data']
    samples.extend(d['waveform']);left.extend(d['waveformLeft']);right.extend(d['waveformRight']);await asyncio.sleep(.012)
   a=np.array(samples,dtype=np.float32);np.save(w/(label+'.npy'),a)
   assert np.isfinite(a).all()
   a=a[-22050:];spec=abs(np.fft.rfft(a*np.hanning(len(a))))
   report[label]={'peak':float(max(abs(a))),'rms':float(np.sqrt(np.mean(a*a))),'frequency':float(np.argmax(spec)*44100/len(a)),'left_peak':float(np.max(np.abs(left[-22050:]))),'right_peak':float(np.max(np.abs(right[-22050:])))}
   print(label,report[label],flush=True)
   return report[label]
  async def cc(number,value,channel=0):
   index=channel*129+(128 if number==129 else number)
   await req('set_param','param_updated',instanceId=iid,paramId=str(0x760000+index),value=value)
  async def select_assigned_controller(value,previous):
   async def edit():
    async with async_playwright() as pw:
     browser=await pw.chromium.connect_over_cdp(f'http://127.0.0.1:{options.debug_port}');page=browser.contexts[0].pages[0]
     canvas=page.locator('canvas[width="640"][height="480"]');box=await canvas.bounding_box()
     async def click(x,y):
      await page.mouse.move(box['x']+box['width']*x/159,box['y']+box['height']*y/119)
      await page.wait_for_timeout(800);await page.mouse.down();await page.wait_for_timeout(200);await page.mouse.up();await page.wait_for_timeout(800)
     await click(40,5);await click(60,39)
     await page.mouse.move(box['x']+box['width']*77/159,box['y']+box['height']*40/119);await page.wait_for_timeout(1000)
     knob=page.get_by_role('button',name='VALUE knob',exact=True)
     for _ in range(abs(value-previous)):
      await knob.press('ArrowUp' if value>previous else 'ArrowDown');await page.wait_for_timeout(100)
     await page.wait_for_timeout(700);await page.screenshot(path=str(w/('assigned-controller-'+str(value)+'.png')))
     await click(10,5);await click(15,22);await browser.close()
   task=asyncio.create_task(edit())
   while not task.done():
    await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012)
   await task
  await render('baseline')
  await cc(11,1);await render('expression-full')
  await cc(11,64/127);await render('expression-half')
  await cc(11,0);await render('expression-zero')
  await cc(11,1);await render('expression-restored')
  await cc(129,1);await render('configured-bend-high')
  await cc(129,0);await render('configured-bend-low')
  await cc(129,8192/16383);await render('configured-bend-centre')
  await cc(123,0);await render('before-pan-left-release');await cc(10,0);await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012);await render('pan-left',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(123,0);await render('before-pan-right-release');await cc(10,1);await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012);await render('pan-right',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(123,0);await render('before-pan-centre-release');await cc(10,64/127);await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012);await render('pan-centre',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(7,64/127);await render('volume-half')
  await cc(7,1);await render('volume-restored')
  for number,value in ((100,0),(101,0),(6,2/127),(38,0)):
   await cc(number,value);await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012)
  await cc(129,1);await render('rpn-two-semitones-up')
  await cc(129,0);await render('rpn-two-semitones-down')
  await cc(129,8192/16383);await render('rpn-centre')
  for number,value in ((100,1),(101,1),(6,12/127),(38,0)):
   await cc(number,value);await req('process_test_chunk','audio_metrics',instanceId=iid,numBlocks=1);await asyncio.sleep(.012)
  await cc(129,1);await render('rpn-null-preserves-range')
  await cc(129,8192/16383);await render('restored-centre')
  await cc(64,1);await render('pedal-down',.5)
  await render('sustain-held',1.5,midiNoteOff=60)
  await cc(120,0);await render('cc120-unsupported')
  await cc(121,0);await render('cc121-unsupported')
  await cc(123,0,15);await render('other-channel-notes-off')
  await cc(64,0);await cc(123,0);await render('native-panic')
  for mode in (123,124,125,126,127):
   await render('note-before-'+str(mode),.8,midiNote=60,midiVelocity=127,autoNoteOff=False)
   await cc(mode,0);await render('released-by-'+str(mode))
  await render('reset-note',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(64,1);await render('reset-pedal-down',.5)
  await render('reset-held-note',1.5,midiNoteOff=60)
  await cc(129,1);await cc(11,64/127);await render('reset-nondefault-controls')
  # Explicit neutral-controller macro; rawCC121 is not an S-760 command.
  for channel in range(16):
   await cc(1,0,channel);await cc(11,1,channel);await cc(64,0,channel);await cc(129,8192/16383,channel)
  await render('explicit-reset-released')
  await render('explicit-reset-fresh-note',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(64,1);await render('panic-pedal-down',.5)
  await render('panic-held-note',1.5,midiNoteOff=60)
  for channel in range(16):
   await cc(64,0,channel);await cc(123,0,channel)
  await render('all-channel-panic')
  await render('post-panic-note',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(123,0);await render('final-release')
  await select_assigned_controller(1,11)
  await cc(1,1);await render('assigned-modulation-full',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  await cc(1,64/127);await render('assigned-modulation-half')
  await cc(1,0);await render('assigned-modulation-zero')
  await cc(1,1);await render('assigned-modulation-restored')
  await cc(64,0);await cc(123,0);await render('modulation-test-release')
  await select_assigned_controller(11,1)
  await cc(11,1);await render('final-retrigger',1.5,midiNote=60,midiVelocity=127,autoNoteOff=False)
  for channel in range(16):
   await cc(64,0,channel);await cc(123,0,channel)
  await render('final-all-channel-panic')
  assert report['assigned-modulation-full']['peak']>report['assigned-modulation-half']['peak']>report['assigned-modulation-zero']['peak']
  assert abs(report['assigned-modulation-restored']['peak']/report['assigned-modulation-full']['peak']-1)<.01
  assert report['modulation-test-release']['peak']==0 and report['final-retrigger']['peak']>.01 and report['final-all-channel-panic']['peak']==0
  assert report['expression-full']['peak']>report['expression-half']['peak']>report['expression-zero']['peak']
  assert abs(report['expression-restored']['peak']/report['expression-full']['peak']-1)<.01
  assert report['pan-left']['left_peak']>.01 and report['pan-left']['right_peak']==0, 'BUG-056 left pan'
  assert report['pan-right']['right_peak']>.01 and report['pan-right']['left_peak']==0, 'BUG-056 right pan'
  assert report['pan-centre']['left_peak']==report['pan-centre']['right_peak']
  assert .50<report['volume-half']['peak']/report['volume-restored']['peak']<.51
  assert abs(report['configured-bend-high']['frequency']-4108)<8
  assert abs(report['configured-bend-low']['frequency']-10002)<4
  assert report['configured-bend-centre']['frequency']==20004
  assert abs(report['rpn-two-semitones-up']['frequency']-21654)<8
  assert abs(report['rpn-two-semitones-down']['frequency']-17822)<8
  assert report['rpn-null-preserves-range']['frequency']==report['rpn-two-semitones-up']['frequency']
  assert report['sustain-held']['peak']>.01 and report['cc120-unsupported']['peak']>.01 and report['cc121-unsupported']['peak']>.01
  assert report['other-channel-notes-off']['peak']>.01
  assert report['native-panic']['left_peak']==report['native-panic']['right_peak']==0
  for mode in (123,124,125,126,127):
   assert report['note-before-'+str(mode)]['peak']>.01 and report['released-by-'+str(mode)]['left_peak']==report['released-by-'+str(mode)]['right_peak']==0
  assert report['reset-held-note']['peak']>.01 and report['explicit-reset-released']['peak']==0
  assert report['explicit-reset-fresh-note']['frequency']==20004
  assert report['panic-held-note']['peak']>.01 and report['all-channel-panic']['left_peak']==report['all-channel-panic']['right_peak']==0
  assert report['post-panic-note']['peak']>.01 and report['final-release']['peak']==0
  (w/'automation-report.json').write_text(json.dumps(report,indent=2))
  (w/'automation-report.txt').write_text('\n'.join(f'{key}: '+json.dumps(value) for key,value in report.items()))
  await req('remove_plugin','plugin_removed',instanceId=iid)
try:asyncio.run(main())
finally:host.terminate();host.wait(timeout=10);log.close()

