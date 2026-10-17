import {chromium,expect,test,type Browser,type Page} from '@playwright/test';
import {spawn,spawnSync,type ChildProcess} from 'node:child_process';
import {createServer} from 'node:net';
import {copyFileSync,existsSync,mkdirSync,readFileSync,statSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {openNativeUtilities,closeNativeUtilities,selectNativeDisk} from './native-controls';

// Opt-in physical loopback acceptance. All sampler operations use the actual
// packaged window; CDP observes/operates it without navigating another browser.
test('packaged WebView normal-speed physical stereo sampling and persistence',async()=>{
  test.skip(!process.env.S760_SAMPLE_PACKAGE || !process.env.S760_SAMPLE_WORK ||
    !process.env.S760_SAMPLE_BLANK || !process.env.S760_SAMPLE_DEVICE,
    'Requires private formatted blank, package and connected MOTU outputs 3/4 to inputs 1/2');
  test.setTimeout(300000);
  const repo=resolve('..'),work=resolve(process.env.S760_SAMPLE_WORK!);
  expect(existsSync(work)).toBe(false);mkdirSync(work,{recursive:true});
  const library=join(work,'library');mkdirSync(library);
  const blank=readFileSync(resolve(process.env.S760_SAMPLE_BLANK!));
  const hash=(b:Buffer)=>createHash('sha256').update(b).digest('hex');
  expect(hash(blank)).toBe('f9fce7624a8ce5c68575c52994a3f3702a43cd4f19d30e8ec8c60ad4b9b9510b');
  writeFileSync(join(library,'BLANK.IMG'),blank);
  const state=join(work,'state');
  let child:ChildProcess|undefined,tone:ChildProcess|undefined,browser:Browser|undefined,page:Page;
  const kill=(p:ChildProcess|undefined)=>{if(p && p.exitCode===null)
    spawnSync('taskkill',['/PID',String(p.pid),'/T','/F'],{windowsHide:true});};
  try {
    const server=createServer();
    await new Promise<void>(done=>server.listen(0,'127.0.0.1',done));
    const port=(server.address() as {port:number}).port;
    await new Promise<void>((done,fail)=>server.close(e=>e?fail(e):done()));
    tone=spawn('python',[join(repo,'scripts/verify_packaged_sampling.py'),'tone','--seconds','270',
      '--ready',join(work,'tone.json')],{cwd:repo,windowsHide:true});
    tone.stderr?.on('data',b=>writeFileSync(join(work,'tone-error.txt'),b,{flag:'a'}));
    await expect.poll(()=>existsSync(join(work,'tone.json')),{timeout:20000}).toBe(true);
    child=spawn(join(resolve(process.env.S760_SAMPLE_PACKAGE!),'S760Studio.exe'),[
      '--state-dir',state,'--media-dir',library,'--boot-rom',join(repo,'roms/BOOT/Roland_S-760_v1.11.BIN'),
      '--system-disk',join(repo,'roms/System/S760224.IMG'),'--recording-device',process.env.S760_SAMPLE_DEVICE!,
      '--no-sound','--seconds','280'],{windowsHide:true,env:{...process.env,
        WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`}});
    await expect.poll(()=>existsSync(join(state,'session.json')),{timeout:30000}).toBe(true);
    const endpoint=`http://127.0.0.1:${port}`;
    await expect.poll(async()=>{try{return (await fetch(endpoint+'/json/version')).ok;}catch{return false;}},
      {timeout:30000}).toBe(true);
    browser=await chromium.connectOverCDP(endpoint);
    await expect.poll(()=>browser!.contexts()[0]?.pages().length??0).toBeGreaterThan(0);
    page=browser.contexts()[0].pages()[0];
    await expect(page).toHaveURL(JSON.parse(readFileSync(join(state,'session.json'),'utf8')).url);
    await openNativeUtilities(page);
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:45000});
    await expect(page.getByLabel('Recording input status')).toContainText('44.1 kHz stereo PCM16');
    const crt=page.getByLabel('Native CRT');
    const click=async(x:number,y:number,right=false)=>{
      await closeNativeUtilities(page);await crt.scrollIntoViewIfNeeded();
      const b=(await crt.boundingBox())!;
      await page.mouse.move(b.x+b.width*x/160,b.y+b.height*y/120);await page.waitForTimeout(250);
      await page.mouse.down({button:right?'right':'left'});await page.waitForTimeout(120);
      await page.mouse.up({button:right?'right':'left'});await page.waitForTimeout(300);
    };
    await closeNativeUtilities(page);await selectNativeDisk(page,'BLANK.IMG');
    await page.getByRole('button',{name:'Gotek Select',exact:true}).click();
    // Firmware Sampling -> ready -> stereo -> start, then right-button stop.
    await click(100,5);await page.waitForTimeout(500);await click(80,22);await page.waitForTimeout(3000);
    await click(76,98);await page.waitForTimeout(2000);await click(62,66);await page.waitForTimeout(2000);
    const volume=page.getByRole('button',{name:'OUTPUT LEVEL knob',exact:true});
    await volume.focus();for(let n=0;n<127;n++)await volume.press('ArrowDown');
    await crt.screenshot({path:join(work,'armed.png')});
    await click(14,98);await page.waitForTimeout(2500);await click(14,98,true);
    await page.waitForTimeout(3000);await crt.screenshot({path:join(work,'recorded.png')});
    await openNativeUtilities(page);
    const captureStatus=await page.getByLabel('Recording input status').textContent();
    expect(captureStatus).not.toContain('Recording underrun');
    writeFileSync(join(work,'capture-status.txt'),captureStatus!);
    await click(140,98);await page.waitForTimeout(1000);
    // Firmware Disk Save -> Sample -> all -> execute/confirm.
    await click(118,5);await page.waitForTimeout(1000);await click(80,30);await page.waitForTimeout(8000);
    await click(20,22);await click(25,54);await page.waitForTimeout(2000);
    await click(10,98);await click(76,98);await page.waitForTimeout(3000);
    await click(62,70);await page.waitForTimeout(3000);await click(66,70);await page.waitForTimeout(35000);
    await crt.screenshot({path:join(work,'saved.png')});
    await openNativeUtilities(page);await page.getByRole('button',{name:'Export disk',exact:true}).click();
    const exported=page.getByText(/^Disk exported to /);await expect(exported).toBeVisible({timeout:20000});
    const disk=(await exported.textContent())!.slice('Disk exported to '.length);
    copyFileSync(disk,join(library,'CAPTURED.IMG'));
    await page.getByText('Save session',{exact:true}).click();
    const saved=page.getByText(/^Session saved to /);await expect(saved).toBeVisible({timeout:20000});
    const sessionPath=(await saved.textContent())!.slice('Session saved to '.length);
    copyFileSync(sessionPath,join(work,'recorded.s760state'));
    await page.getByText('Restart sampler',{exact:true}).click();
    await page.getByLabel('Discard unsaved sampler memory').check();await page.getByText('Confirm restart',{exact:true}).click();
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:45000});
    await page.getByText('Restore saved session',{exact:true}).click();
    await page.getByLabel('Replace current sampler memory',{exact:true}).check();await page.getByText('Confirm restore',{exact:true}).click();
    await expect(page.getByText('Saved session restored.',{exact:true})).toBeVisible({timeout:20000});
    const beforeSave=statSync(sessionPath).mtimeMs;
    await page.getByText('Save session',{exact:true}).click();
    await expect.poll(()=>statSync(sessionPath).mtimeMs,{timeout:20000}).toBeGreaterThan(beforeSave);
    await expect(saved).toBeVisible({timeout:20000});
    copyFileSync(sessionPath,join(work,'restored.s760state'));
    await page.screenshot({path:join(work,'restored.png'),fullPage:true});
    expect(readFileSync(resolve(process.env.S760_SAMPLE_BLANK!)).equals(blank)).toBe(true);
    writeFileSync(join(work,'result.json'),JSON.stringify({passed:true,interface:'Packaged WebView2',
      renderer:(await (await fetch(endpoint+'/json/version')).json()).Browser,
      throttle:true,sound:false,recordingDevice:process.env.S760_SAMPLE_DEVICE,
      captureStatus,
      saved_sha256:hash(readFileSync(disk)),blank_sha256:hash(blank)},null,2));
  }finally {kill(child);kill(tone);await browser?.close().catch(()=>{});}
});
