import {chromium,expect,test,type Browser,type Page} from '@playwright/test';
import {spawn,spawnSync,type ChildProcess} from 'node:child_process';
import {createServer} from 'node:net';
import {copyFileSync,existsSync,mkdirSync,readFileSync,statSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {openNativeUtilities,closeNativeUtilities,selectNativeDisk} from './native-controls';

// No mocked bridge, direct native socket or guest-memory writes. Each repetition
// uses one frozen package and its actual normal-speed WebView2 window.
for(const cycle of [1,2])test(`frozen complete standalone workflow cycle ${cycle}`,async()=>{
  test.skip(!process.env.S760_WORKFLOW_PACKAGE || !process.env.S760_WORKFLOW_WORK ||
    !process.env.S760_WORKFLOW_BLANK || !process.env.S760_WORKFLOW_INPUT ||
    !process.env.S760_WORKFLOW_LOOPBACK || !process.env.S760_WORKFLOW_MANIFEST,
    'Requires frozen package manifest, private media, Windows loopback QA helper and physical MOTU input');
  test.setTimeout(600000);
  const repo=resolve('..'),packagePath=resolve(process.env.S760_WORKFLOW_PACKAGE!);
  const work=join(resolve(process.env.S760_WORKFLOW_WORK!),`cycle-${cycle}`);
  expect(existsSync(work)).toBe(false);mkdirSync(work,{recursive:true});
  const hash=(b:Buffer)=>createHash('sha256').update(b).digest('hex');
  const manifest=JSON.parse(readFileSync(resolve(process.env.S760_WORKFLOW_MANIFEST!),'utf8'));
  const frozen=()=>{for(const [name,info] of Object.entries(manifest.files) as [string,{sha256:string}][])
    expect(hash(readFileSync(join(packagePath,name))),name).toBe(info.sha256);};
  frozen();
  const library=join(work,'library');mkdirSync(library);
  const original=readFileSync(join(repo,'roms/FDD/ROBOFULL.IMG'));
  expect(hash(original)).toBe('8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae');
  writeFileSync(join(library,'ROBOFULL.IMG'),original);
  const blank=readFileSync(resolve(process.env.S760_WORKFLOW_BLANK!));
  expect(hash(blank)).toBe('f9fce7624a8ce5c68575c52994a3f3702a43cd4f19d30e8ec8c60ad4b9b9510b');
  writeFileSync(join(library,'BLANK.IMG'),blank);
  let app:ChildProcess|undefined,tone:ChildProcess|undefined,observer:ChildProcess|undefined;
  let page!:Page;
  let browser:Browser|undefined,endpoint='',output='';
  const renderers:string[]=[],playback:Record<string,any>={};
  const kill=(p:ChildProcess|undefined)=>{if(p && p.exitCode===null)
    spawnSync('taskkill',['/PID',String(p.pid),'/T','/F'],{windowsHide:true});};
  const stop=async()=>{kill(app);app=undefined;await browser?.close().catch(()=>{});browser=undefined;};
  const launch=async()=>{
    const state=join(work,'state');const fresh=!existsSync(join(state,'settings.json'));
    const server=createServer();await new Promise<void>(done=>server.listen(0,'127.0.0.1',done));
    const port=(server.address() as {port:number}).port;
    await new Promise<void>((done,fail)=>server.close(e=>e?fail(e):done()));
    app=spawn(join(packagePath,'S760Studio.exe'),['--state-dir',state,'--media-dir',library,
      '--boot-rom',join(repo,'roms/BOOT/Roland_S-760_v1.11.BIN'),'--system-disk',join(repo,'roms/System/S760224.IMG'),
      '--recording-device',process.env.S760_WORKFLOW_INPUT!,...(fresh?['--no-sound']:[]),'--seconds','550'],
      {cwd:work,windowsHide:true,env:{...process.env,WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:
        `--remote-debugging-port=${port} --remote-debugging-address=127.0.0.1`}});
    endpoint=`http://127.0.0.1:${port}`;
    await expect.poll(async()=>{try{return(await fetch(endpoint+'/json/version')).ok;}catch{return false;}},{timeout:30000}).toBe(true);
    browser=await chromium.connectOverCDP(endpoint);
    await expect.poll(()=>browser!.contexts()[0]?.pages().length??0).toBeGreaterThan(0);
    page=browser.contexts()[0].pages()[0];
    await expect.poll(()=>existsSync(join(state,'session.json')),{timeout:30000}).toBe(true);
    await expect(page).toHaveURL(JSON.parse(readFileSync(join(state,'session.json'),'utf8')).url);
    renderers.push((await(await fetch(endpoint+'/json/version')).json()).Browser);
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:45000});
  };
  const move=async(x:number,y:number)=>{
    await closeNativeUtilities(page);const crt=page.getByLabel('Native CRT');await crt.scrollIntoViewIfNeeded();
    const b=(await crt.boundingBox())!;await page.mouse.move(b.x+b.width*x/160,b.y+b.height*y/120);await page.waitForTimeout(250);
  };
  const click=async(x:number,y:number,right=false)=>{
    await move(x,y);await page.mouse.down({button:right?'right':'left'});await page.waitForTimeout(120);
    await page.mouse.up({button:right?'right':'left'});await page.waitForTimeout(350);
  };
  const perform=async()=>{await click(10,5);await click(15,22);await page.waitForTimeout(600);};
  const mount=async(name:string)=>{
    await closeNativeUtilities(page);const up=page.getByRole('button',{name:'Gotek Up',exact:true});
    for(let i=0;i<512 && await up.isEnabled();i++)await up.click();
    await selectNativeDisk(page,name);await page.getByRole('button',{name:'Gotek Select',exact:true}).click();
    await expect(page.getByLabel('Drive display')).toContainText(name);
  };
  const load=async(name:string)=>{
    await mount(name);await click(118,5);await click(80,22);await page.waitForTimeout(5000);
    await click(50,34);await click(76,98);await page.waitForTimeout(35000);await perform();
  };
  const levelPixels=async()=>{
    await move(150,110);await page.waitForTimeout(500);
    return page.getByLabel('Native CRT').evaluate((c:HTMLCanvasElement)=>{
      let h=2166136261;for(const v of c.getContext('2d')!.getImageData(416,112,56,16).data)h=Math.imul(h^v,16777619);return h>>>0;
    });
  };
  const play=async(name:string)=>{
    await perform();const raw=join(work,name+'.raw'),meta=join(work,name+'.json');let text='';
    observer=spawn(resolve(process.env.S760_WORKFLOW_LOOPBACK!),[output,raw,'8'],{windowsHide:true});
    observer.stdout!.on('data',b=>text+=String(b));
    await expect.poll(()=>existsSync(raw+'.ready'),{timeout:10000}).toBe(true);
    const key=page.getByRole('button',{name:'C4 MIDI 60',exact:true});await key.focus();
    await key.press('Space',{delay:3000});
    await expect.poll(()=>observer!.exitCode,{timeout:14000}).toBe(0);
    writeFileSync(meta,text);
    const out=join(work,name+'-analysis.json');
    const checked=spawnSync('python',[join(repo,'scripts/verify_packaged_workflow.py'),'audio','--raw',raw,'--meta',meta,'--out',out],{cwd:repo,encoding:'utf8'});
    expect(checked.status,checked.stderr).toBe(0);playback[name]=JSON.parse(readFileSync(out,'utf8'));
  };
  const exportDisk=async(name:string)=>{
    await openNativeUtilities(page);await page.getByRole('button',{name:'Export disk',exact:true}).click();
    const result=page.getByText(/^Disk exported to /);await expect(result).toBeVisible({timeout:20000});
    copyFileSync((await result.textContent())!.slice('Disk exported to '.length),join(library,name));
  };
  try {
    await launch();await openNativeUtilities(page);
    await page.getByRole('button',{name:'Audio',exact:true}).click();
    await page.getByLabel('Audio output backend').selectOption('wasapi');
    const option=page.getByLabel('Windows output device').locator('option').filter({hasText:'Realtek Digital Output'});
    await expect(option).toHaveCount(1);output=(await option.getAttribute('value'))!;
    await page.getByLabel('Windows output device').selectOption(output);
    await page.getByLabel('Audio buffer target (ms)').fill('60');await page.getByLabel('Enable audio output').check();
    await page.getByLabel('Replace current sampler memory and restart').check();await page.getByText('Apply settings and start',{exact:true}).click();
    await expect(page.getByRole('dialog')).toHaveCount(0,{timeout:25000});
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:45000});
    await openNativeUtilities(page);await page.getByRole('button',{name:'MIDI & display',exact:true}).click();
    await page.getByLabel('Show on-screen keyboard').click();
    await expect(page.getByLabel('Show on-screen keyboard')).toBeChecked();await closeNativeUtilities(page);
    await load('ROBOFULL.IMG');const before=await levelPixels();await play('baseline');
    await move(110,30);const value=page.getByRole('button',{name:'VALUE knob',exact:true});await value.focus();
    for(let i=0;i<63;i++){await value.press('ArrowDown');await page.waitForTimeout(50);}
    await perform(); // Compare the normal field view, not the active edit highlight.
    const edited=await levelPixels();expect(edited).not.toBe(before);await play('edited');
    expect(Math.abs(playback.edited.peak/playback.baseline.peak-64/127)).toBeLessThan(.04);
    await click(118,5);await click(80,30);await page.waitForTimeout(2500);
    await click(50,34);await click(76,98);await page.waitForTimeout(1000);await click(62,70);await page.waitForTimeout(1000);await click(66,70);await page.waitForTimeout(12000);
    await exportDisk('EDITED.IMG');expect(readFileSync(join(library,'EDITED.IMG'))[0x4e40]).toBe(192);
    // Retain the edited program in memory while recording new physical samples.
    tone=spawn('python',[join(repo,'scripts/verify_packaged_sampling.py'),'tone','--seconds','190','--ready',join(work,'tone.json')],{cwd:repo,windowsHide:true});
    await expect.poll(()=>existsSync(join(work,'tone.json')),{timeout:15000}).toBe(true);
    await click(100,5);await click(80,22);await page.waitForTimeout(3000);
    await click(14,98);await page.waitForTimeout(2000); // Firmware New: retain loaded sample slots.
    await click(76,98);await page.waitForTimeout(2000);
    await click(62,66);await page.waitForTimeout(2000);
    const volume=page.getByRole('button',{name:'OUTPUT LEVEL knob',exact:true});await volume.focus();
    for(let i=0;i<127;i++)await volume.press('ArrowDown');
    await click(14,98);await page.waitForTimeout(2500);await click(14,98,true);await page.waitForTimeout(3000);
    await page.getByLabel('Native CRT').screenshot({path:join(work,'recorded.png')});
    await click(140,98);kill(tone);tone=undefined;
    await volume.focus();for(let i=0;i<127;i++)await volume.press('ArrowUp');
    await mount('BLANK.IMG');await click(118,5);await click(80,30);await page.waitForTimeout(8000);
    await click(20,22);await click(25,54);await page.waitForTimeout(2000);
    await click(10,98);await click(76,98);await page.waitForTimeout(3000);await click(62,70);await page.waitForTimeout(3000);await click(66,70);await page.waitForTimeout(35000);
    await exportDisk('CAPTURED.IMG');await perform();expect(await levelPixels()).toBe(edited);
    await openNativeUtilities(page);const captureStatus=await page.getByLabel('Recording input status').textContent();
    expect(captureStatus).not.toContain('Recording underrun');
    await page.getByText('Save session',{exact:true}).click();const saved=page.getByText(/^Session saved to /);
    await expect(saved).toBeVisible({timeout:25000});const sessionPath=(await saved.textContent())!.slice('Session saved to '.length);
    copyFileSync(sessionPath,join(work,'recorded.s760state'));
    await page.getByText('Restart sampler',{exact:true}).click();await page.getByLabel('Discard unsaved sampler memory').check();await page.getByText('Confirm restart',{exact:true}).click();
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:45000});
    const restore=async()=>{await openNativeUtilities(page);await page.getByText('Restore saved session',{exact:true}).click();
      await page.getByLabel('Replace current sampler memory',{exact:true}).check();await page.getByText('Confirm restore',{exact:true}).click();
      await expect(page.getByText('Saved session restored.',{exact:true})).toBeVisible({timeout:25000});};
    await restore();await perform();expect(await levelPixels()).toBe(edited);await play('restored');
    expect(Math.abs(playback.restored.peak/playback.edited.peak-1)).toBeLessThan(.02);
    await openNativeUtilities(page);const timestamp=statSync(sessionPath).mtimeMs;await page.getByText('Save session',{exact:true}).click();
    await expect.poll(()=>statSync(sessionPath).mtimeMs,{timeout:25000}).toBeGreaterThan(timestamp);
    copyFileSync(sessionPath,join(work,'restored.s760state'));
    await stop();await launch();await restore();await perform();expect(await levelPixels()).toBe(edited);await play('cold-restored');
    expect(Math.abs(playback['cold-restored'].peak/playback.edited.peak-1)).toBeLessThan(.02);
    await page.screenshot({path:join(work,'cold-restored.png'),fullPage:true});
    expect(readFileSync(join(repo,'roms/FDD/ROBOFULL.IMG')).equals(original)).toBe(true);
    expect(readFileSync(resolve(process.env.S760_WORKFLOW_BLANK!)).equals(blank)).toBe(true);
    frozen();
    writeFileSync(join(work,'result.json'),JSON.stringify({passed:true,cycle,interface:'Packaged WebView2',renderers,
      throttle:true,playback,outputEndpoint:output,recordingDevice:process.env.S760_WORKFLOW_INPUT,captureStatus,
      before,edited,sample_disk_sha256:hash(readFileSync(join(library,'CAPTURED.IMG'))),
      edited_disk_sha256:hash(readFileSync(join(library,'EDITED.IMG'))),package_manifest_sha256:hash(readFileSync(resolve(process.env.S760_WORKFLOW_MANIFEST!)))},null,2));
  }catch(error){await page?.screenshot({path:join(work,'failed.png'),fullPage:true}).catch(()=>{});throw error;}
  finally {kill(observer);kill(tone);await stop();}
});
