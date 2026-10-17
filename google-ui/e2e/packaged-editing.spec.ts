import {chromium,expect,test,type Browser,type Locator} from '@playwright/test';
import {spawn,spawnSync, type ChildProcess} from 'node:child_process';
import {createServer} from 'node:net';
import {copyFileSync,existsSync,mkdirSync,readFileSync,writeFileSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {openNativeUtilities,closeNativeUtilities,selectNativeDisk} from './native-controls';

// Real frozen service, packaged React assets and MAME. No direct control socket,
// guest-memory writes or mock bridge. Private fixture copies only.
for(const scenario of ['perform','patch','partial','erase']) {
  test(`packaged ${scenario} edit, firmware Save, session restore and cold Load`,async({page:browserPage})=>{
    test.skip(!process.env.S760_EDIT_PACKAGE || !process.env.S760_EDIT_WORK,
      'Requires a built development package and fresh private work directory');
    test.setTimeout(240000);
    const desktop=process.env.S760_EDIT_WEBVIEW==='1';
    let page=browserPage;
    let webview:Browser|undefined;
    let crt:Locator=page.getByLabel('Native CRT');
    const renderers:string[]=[];
    const repo=resolve('..');
    const work=join(resolve(process.env.S760_EDIT_WORK!),scenario);
    expect(existsSync(work)).toBe(false);
    mkdirSync(work,{recursive:true});
    const library=join(work,'library');mkdirSync(library);
    const source=join(repo,'roms/FDD/ROBOFULL.IMG');
    const original=readFileSync(source);
    expect(createHash('sha256').update(original).digest('hex')).toBe(
      '8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae');
    copyFileSync(source,join(library,'ROBOFULL.IMG'));
    const malformedSizes=scenario==='perform'?[0,737279,737281,1474559,1474561]:[];
    for(const size of malformedSizes)writeFileSync(join(library,`INVALID-${size}.IMG`),Buffer.alloc(size));
    let child:ChildProcess|undefined;
    const stop=async()=>{
      if(child && child.exitCode===null) {
        spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true});
        await expect.poll(()=>child!.exitCode!==null || child!.signalCode!==null).toBe(true);
      }
      child=undefined;
      if(webview){await webview.close().catch(()=>{});webview=undefined;}
    };
    const launch=async(name:string)=>{
      const state=join(work,name);
      let cdpPort=0;
      if(desktop){
        const server=createServer();
        await new Promise<void>(done=>server.listen(0,'127.0.0.1',done));
        cdpPort=(server.address() as {port:number}).port;
        await new Promise<void>((done,fail)=>server.close(error=>error?fail(error):done()));
      }
      child=spawn(join(resolve(process.env.S760_EDIT_PACKAGE!),'S760Studio.exe'),[
        '--state-dir',state,'--media-dir',library,
        '--boot-rom',join(repo,'roms/BOOT/Roland_S-760_v1.11.BIN'),
        '--system-disk',join(repo,'roms/System/S760224.IMG'),
        ...(desktop?[]:['--no-browser']),'--no-sound','--fast','--seconds','230'],{
          windowsHide:true,env:{...process.env,...(desktop?{
            WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${cdpPort} --remote-debugging-address=127.0.0.1`,
          }:{})},
        });
      await expect.poll(()=>existsSync(join(state,'session.json')),{timeout:30000}).toBe(true);
      const url=JSON.parse(readFileSync(join(state,'session.json'),'utf8')).url;
      if(desktop){
        const endpoint=`http://127.0.0.1:${cdpPort}`;
        await expect.poll(async()=>{try{return (await fetch(endpoint+'/json/version')).ok;}catch{return false;}},{timeout:30000}).toBe(true);
        webview=await chromium.connectOverCDP(endpoint);
        await expect.poll(()=>webview!.contexts()[0]?.pages().length??0).toBeGreaterThan(0);
        page=webview.contexts()[0].pages()[0];
        await expect(page).toHaveURL(url,{timeout:20000});
        const version=await (await fetch(endpoint+'/json/version')).json();
        renderers.push(version.Browser);
      }else await page.goto(url);
      crt=page.getByLabel('Native CRT');
      await openNativeUtilities(page);
      await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
    };
    const select=async(name:string)=>{
      await closeNativeUtilities(page);
      const up=page.getByRole('button',{name:'Gotek Up',exact:true});
      for(let i=0;i<512 && await up.isEnabled();i++)await up.click();
      await selectNativeDisk(page,name);
    };
    const move=async(x:number,y:number)=>{
      await closeNativeUtilities(page);
      await crt.scrollIntoViewIfNeeded();
      const b=(await crt.boundingBox())!;
      await page.mouse.move(b.x+b.width*x/160,b.y+b.height*y/120);
      await page.waitForTimeout(250);
    };
    const click=async(x:number,y:number)=>{
      await move(x,y);await page.mouse.down();await page.waitForTimeout(120);
      await page.mouse.up();await page.waitForTimeout(300);
    };
    const perform=async()=>{await click(10,5);await click(15,22);await page.waitForTimeout(500);};
    const load=async(disk:string)=>{
      await select(disk);
      await page.getByRole('button',{name:'Gotek Select',exact:true}).click();
      await expect(page.getByLabel('Drive display')).toContainText(disk);
      await click(118,5);await click(80,22);
      await openNativeUtilities(page);
      await expect(page.getByRole('status')).toContainText('Disk Load ready',{timeout:15000});
      await page.waitForTimeout(1500);await click(50,34);await click(76,98);
      await openNativeUtilities(page);
      await expect(page.getByRole('status')).toHaveText('Firmware disk operation in progress.',{timeout:5000});
      await expect(page.getByRole('status')).toContainText('Disk Load ready',{timeout:60000});
      await perform();
    };
    const screen=async()=>{
      if(scenario==='patch'){await click(40,5);await click(60,39);}
      if(scenario==='partial'){await click(70,5);await click(75,22);}
      if(scenario==='erase'){await click(100,5);await click(60,62);}
      if(scenario==='perform')await move(110,30);
      if(scenario==='patch')await move(77,44);
      if(scenario==='partial')await move(77,46);
      // The approved CRT housing clips the extended canvas bottom. Park the
      // erase pointer on the visible header so it cannot contaminate wave pixels.
      await move(150,scenario==='erase'?10:110);await page.waitForTimeout(500);
    };
    const crop=scenario==='perform'?[416,112,56,16]:scenario==='patch'?[296,168,40,40]:
      scenario==='partial'?[296,176,40,16]:[32,232,448,144];
    const pixels=()=>crt.evaluate((c:HTMLCanvasElement,r:number[])=>{
      let h=2166136261;
      for(const byte of c.getContext('2d')!.getImageData(r[0],r[1],r[2],r[3]).data)
        h=Math.imul(h^byte,16777619);
      return h>>>0;
    },crop);
    const turn=async(x:number,y:number,count:number)=>{
      await move(x,y);
      const knob=page.getByRole('button',{name:'VALUE knob',exact:true});
      await knob.focus();
      for(let n=0;n<Math.abs(count);n++) {
        await knob.press(count>0?'ArrowUp':'ArrowDown');await page.waitForTimeout(50);
      }
    };
    try {
      await launch('edit');await load('ROBOFULL.IMG');await screen();
      const before=await pixels();
      for(const size of malformedSizes) {
        await select(`INVALID-${size}.IMG`);
        await page.getByRole('button',{name:'Gotek Select',exact:true}).click();
        await openNativeUtilities(page);
        await expect(page.getByRole('alert')).toContainText('Only 720KB/1.44MB raw floppy images are supported');
        await page.getByText('Dismiss',{exact:true}).click();
        await closeNativeUtilities(page);await expect.poll(pixels).toBe(before);
      }
      await select('ROBOFULL.IMG');
      await crt.screenshot({path:join(work,'before.png')});
      if(scenario==='perform')await turn(110,30,-63);
      if(scenario==='patch'){await turn(77,49,12);await turn(77,44,12);}
      if(scenario==='partial')await turn(77,46,12);
      if(scenario==='erase'){await click(140,98);await page.waitForTimeout(1500);}
      await move(150,scenario==='erase'?10:110);await page.waitForTimeout(500);
      const edited=await pixels();
      if(scenario!=='erase')expect(edited).not.toBe(before);
      await crt.screenshot({path:join(work,'edited.png')});
      await perform();
      await click(118,5);await page.waitForTimeout(500);await click(80,30);
      await page.waitForTimeout(2000);await click(50,34);await click(76,98);
      await page.waitForTimeout(800);await click(62,70);await page.waitForTimeout(800);
      await click(66,70);await page.waitForTimeout(6000);
      await openNativeUtilities(page);
      await page.getByRole('button',{name:'Export disk',exact:true}).click();
      const exported=page.getByText(/^Disk exported to /);
      await expect(exported).toBeVisible({timeout:15000});
      const path=(await exported.textContent())!.slice('Disk exported to '.length);
      const saved=readFileSync(path);expect(saved.length).toBe(737280);
      if(scenario==='perform')expect(saved[0x4e40]).toBe(192);
      if(scenario==='patch')expect([...saved.subarray(0x8ee0,0x8ee2)]).toEqual([12,12]);
      if(scenario==='partial')expect(saved[0x10e2d]).toBe(12);
      if(scenario==='erase')expect(saved.subarray(0x2ac00,0x2cc00).equals(Buffer.alloc(8192))).toBe(true);
      const start=scenario==='erase'?0x2ac00+9216:0x2ac00;
      expect(saved.subarray(start,0x2ac00+13*9216).equals(original.subarray(start,0x2ac00+13*9216))).toBe(true);
      copyFileSync(path,join(library,'EDITED.IMG'));
      await perform();await screen();
      const persisted=await pixels();
      await crt.screenshot({path:join(work,'saved-screen.png')});
      if(scenario!=='erase')expect(persisted).toBe(edited);
      await perform();await openNativeUtilities(page);
      await page.getByText('Save session',{exact:true}).click();
      await expect(page.getByText(/^Session saved to /)).toBeVisible({timeout:20000});
      await page.getByText('Restart sampler',{exact:true}).click();
      await page.getByLabel('Discard unsaved sampler memory').check();
      await page.getByText('Confirm restart',{exact:true}).click();
      await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
      await page.getByText('Restore saved session',{exact:true}).click();
      await page.getByLabel('Replace current sampler memory',{exact:true}).check();
      await page.getByText('Confirm restore',{exact:true}).click();
      await expect(page.getByText('Saved session restored.',{exact:true})).toBeVisible({timeout:20000});
      await screen();
      await crt.screenshot({path:join(work,'restore-before-check.png')});
      await expect.poll(pixels).toBe(persisted);
      await crt.screenshot({path:join(work,'restored.png')});
      await stop();await launch('cold');await load('EDITED.IMG');await screen();
      await expect.poll(pixels).toBe(persisted);
      await crt.screenshot({path:join(work,'cold.png')});
      await openNativeUtilities(page);await expect(page.getByRole('alert')).toHaveCount(0);
      expect(readFileSync(source).equals(original)).toBe(true);
      expect(readFileSync(join(library,'ROBOFULL.IMG')).equals(original)).toBe(true);
      writeFileSync(join(work,'result.json'),JSON.stringify({scenario,passed:true,before,edited,persisted,
        interface:desktop?'Packaged WebView2':'External Chromium',renderers,
        rejected_media_sizes:malformedSizes,
        saved_sha256:createHash('sha256').update(saved).digest('hex'),
        limits:`Packaged ${desktop?'WebView2':'browser'} controls and persistence; silent unthrottled development profile, no physical audio or clean-machine claim`},null,2));
    } finally {await stop();}
  });
}
