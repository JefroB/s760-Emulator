import {test,expect,type Page} from '@playwright/test';
import {spawn,spawnSync,type ChildProcess} from 'node:child_process';
import {copyFileSync,existsSync,mkdirSync,readFileSync,writeFileSync,rmSync,renameSync,readdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {createHash} from 'node:crypto';
import {openNativeUtilities,closeNativeUtilities,selectNativeDisk} from './native-controls';

const hash=(bytes:Buffer)=>createHash('sha256').update(bytes).digest('hex');

async function sampler(page:Page,name:string,recoverySeed?:string) {
  const repo=resolve('..'),work=join(resolve(process.env.S760_MEDIA_WORK!),name);
  expect(existsSync(work)).toBe(false);mkdirSync(work,{recursive:true});
  const library=join(work,'library');mkdirSync(library);
  const original=readFileSync(join(repo,'roms/FDD/ROBOFULL.IMG'));
  expect(hash(original)).toBe('8377fb7ce8370a4ffbe281fcd3934e9f9c2dc25612bd6f207bdaea7e660448ae');
  writeFileSync(join(library,'ROBOFULL.IMG'),original);
  const bad:string[]=[];
  for(const size of [737280,1474560])for(const fill of [0,255]) {
    const file=`Z-${size}-${fill}.IMG`;bad.push(file);
    writeFileSync(join(library,file),Buffer.alloc(size,fill));
  }
  const state=join(work,'state');
  if(recoverySeed){mkdirSync(join(state,'sessions'),{recursive:true});copyFileSync(recoverySeed,join(state,'sessions/recovery.s760state'));}
  let media:{dirty:boolean;busy:boolean;revision:number}|undefined;
  page.on('websocket',socket=>socket.on('framereceived',event=>{
    if(typeof event.payload!=='string')return;
    try {const data=JSON.parse(event.payload);if(data.mediaStatus)media=data.mediaStatus;}catch {/* Binary frames are separate. */}
  }));
  let child:ChildProcess|undefined;
  const close=async()=>{
    if(child && child.exitCode===null){
      spawnSync('taskkill',['/PID',String(child.pid),'/T','/F'],{windowsHide:true});
      await expect.poll(()=>child!.exitCode!==null||child!.signalCode!==null).toBe(true);
    }
    child=undefined;
  };
  const launch=async()=>{try {
    media=undefined;
    rmSync(join(state,'session.json'),{force:true});
    child=spawn(join(resolve(process.env.S760_MEDIA_PACKAGE!),'S760Studio.exe'),[
      '--state-dir',state,'--media-dir',library,'--boot-rom',join(repo,'roms/BOOT/Roland_S-760_v1.11.BIN'),
      '--system-disk',join(repo,'roms/System/S760224.IMG'),'--no-browser','--no-sound','--fast','--seconds','410'],{windowsHide:true});
    await expect.poll(()=>existsSync(join(state,'session.json')),{timeout:30000}).toBe(true);
    await page.goto(JSON.parse(readFileSync(join(state,'session.json'),'utf8')).url);
    await openNativeUtilities(page);
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  }catch(error){await close();throw error;}};
  await launch();
  const crash=async()=>{
    expect(child?.pid).toBeTruthy();
    // Only this test's frozen service and its descendants are terminated.
    const pid=child!.pid!;
    const result=spawnSync('taskkill',['/PID',String(pid),'/T','/F'],{windowsHide:true});
    expect(result.status,String(result.stderr)).toBe(0);
    await expect.poll(()=>child!.exitCode!==null||child!.signalCode!==null).toBe(true);
    child=undefined;
    return pid;
  };
  const crt=page.getByLabel('Native CRT');
  const move=async(x:number,y:number)=>{
    await closeNativeUtilities(page);await crt.scrollIntoViewIfNeeded();
    const b=(await crt.boundingBox())!;
    await page.mouse.move(b.x+b.width*x/160,b.y+b.height*y/120);await page.waitForTimeout(250);
  };
  const click=async(x:number,y:number)=>{
    await move(x,y);await page.mouse.down();await page.waitForTimeout(120);await page.mouse.up();await page.waitForTimeout(300);
  };
  const perform=async()=>{await click(10,5);await click(15,22);await move(150,10);await page.waitForTimeout(500);};
  const mount=async(file:string)=>{
    await closeNativeUtilities(page);
    const up=page.getByRole('button',{name:'Gotek Up',exact:true});
    for(let n=0;n<512 && await up.isEnabled();n++)await up.click();
    await selectNativeDisk(page,file);
    await page.getByRole('button',{name:'Gotek Select',exact:true}).click();
  };
  const disk=async()=>{
    await click(118,5);await click(80,22);await page.waitForTimeout(1800);await move(150,10);
  };
  const load=async(clearExisting=false)=>{
    await mount('ROBOFULL.IMG');await expect(page.getByLabel('Drive display')).toContainText('ROBOFULL.IMG');
    await disk();await click(50,34);await click(76,98);
    if(clearExisting) {
      // Original firmware asks before replacing an already loaded performance.
      await expect.poll(()=>region([144,176,336,32]),{timeout:15000}).toBe('96c78e8af1d2cccf9fa7a57f46f470cc1af160d4fec7bfbf650a8a0e56572032');
      await click(54,62); // Yes: Clear Internal Memory Before Loading.
    }
    await openNativeUtilities(page);
    await expect(page.getByRole('status')).toHaveText('Firmware disk operation in progress.',{timeout:5000});
    await expect(page.getByRole('status')).toContainText('Disk Load ready',{timeout:60000});await perform();
  };
  const table=()=>crt.evaluate((c:HTMLCanvasElement)=>{
    let h=2166136261;for(const b of c.getContext('2d')!.getImageData(112,112,256,128).data)h=Math.imul(h^b,16777619);
    return h>>>0;
  });
  const region=(rect:number[])=>crt.evaluate(async(canvas:HTMLCanvasElement,rect:number[])=>{
    const rgba=canvas.getContext('2d')!.getImageData(rect[0],rect[1],rect[2],rect[3]).data,rgb=new Uint8Array(rect[2]*rect[3]*3);
    for(let i=0,j=0;i<rgba.length;i+=4){rgb[j++]=rgba[i];rgb[j++]=rgba[i+1];rgb[j++]=rgba[i+2];}
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),b=>b.toString(16).padStart(2,'0')).join('');
  },rect);
  const directory=()=>region([0,112,160,16]);
  const session=async(name:string)=>{
    await openNativeUtilities(page);await page.getByText('Save session',{exact:true}).click();
    await expect(page.getByText(/^Session saved to /)).toBeVisible({timeout:20000});
    copyFileSync(join(state,'sessions/latest.s760state'),join(work,name));
  };
  const exportDisk=async()=>{
    await openNativeUtilities(page);await page.getByRole('button',{name:'Export disk',exact:true}).click();
    const result=page.getByText(/^Disk exported to /);await expect(result).toBeVisible({timeout:15000});
    return (await result.textContent())!.slice('Disk exported to '.length);
  };
  const unchanged=()=>{
    expect(readFileSync(join(repo,'roms/FDD/ROBOFULL.IMG')).equals(original)).toBe(true);
    expect(readFileSync(join(library,'ROBOFULL.IMG')).equals(original)).toBe(true);
  };
  return {work,library,original,bad,state,crt,move,click,perform,mount,disk,load,table,directory,session,exportDisk,unchanged,close,crash,launch,media:()=>media,pid:()=>child?.pid};
}

test('packaged incomplete checkpoint publication preserves the previous recovery across three interruptions',async({page})=>{
  test.skip(!process.env.S760_MEDIA_PACKAGE||!process.env.S760_MEDIA_WORK||!process.env.S760_INTERRUPT_SEED,
    'Requires the qualified package, its hash-identified recovery fixture and fresh private work');
  test.setTimeout(240000);
  const repo=resolve('..'),seed=process.env.S760_INTERRUPT_SEED!;
  const expected=JSON.parse(readFileSync(join(repo,'docs/condensed/validation/milestone-6-crash-recovery-2026-10-17.json'),'utf8'));
  const checkpointHash=hash(readFileSync(seed));expect(checkpointHash).toBe(expected.browser.results.checkpoint_sha256);
  const s=await sampler(page,'publication',seed);
  let watcher:ChildProcess|undefined;
  try{
    const archive=join(s.state,'sessions/recovery.s760state');
    const restore=async()=>{
      await openNativeUtilities(page);await page.getByText('Restore recovery',{exact:true}).click();
      await page.getByLabel('Confirm recovery replacement').check();await page.getByText('Confirm recovery',{exact:true}).click();
      await expect(page.getByText('Recovery restored.',{exact:true})).toBeVisible({timeout:20000});
      await expect.poll(()=>s.media()?.dirty).toBe(true);
      await s.move(150,10);
    };
    const field=()=>s.crt.evaluate((c:HTMLCanvasElement)=>{
      let h=2166136261;for(const b of c.getContext('2d')!.getImageData(416,112,56,16).data)h=Math.imul(h^b,16777619);
      return h>>>0;
    });
    await restore();const savedField=await field();
    const rows=[];
    for(let cycle=0;cycle<3;cycle++){
      await s.move(110,30);const knob=page.getByRole('button',{name:'VALUE knob',exact:true});
      await knob.focus();await knob.press('ArrowDown');await s.move(150,10);
      await expect.poll(field).not.toBe(savedField);const unsavedField=await field();
      await openNativeUtilities(page);
      const result=join(s.work,`interrupt-${cycle}.json`);
      watcher=spawn(process.env.S760_QA_PYTHON||'python',[join(repo,'scripts/interrupt_checkpoint_publication.py'),
        '--pid',String(s.pid()),'--archive',archive,'--result',result],{windowsHide:true});
      await expect.poll(()=>existsSync(result.replace(/\.json$/,'.ready')),{timeout:10000}).toBe(true);
      await page.getByText('Save recovery now',{exact:true}).click();
      await expect.poll(()=>existsSync(result),{timeout:35000}).toBe(true);
      await expect.poll(()=>watcher!.exitCode).toBe(0);watcher=undefined;
      const interrupted=JSON.parse(readFileSync(result,'utf8'));
      expect(interrupted.incomplete_archive).toBe(true);
      expect(hash(readFileSync(archive))).toBe(checkpointHash);
      renameSync(join(s.state,'sessions',interrupted.pending_name),join(s.work,`incomplete-${cycle}.tmp`));
      await s.launch();
      await expect(page.getByLabel('Automatic recovery status')).toContainText('Existing recovery preserved.');
      expect(hash(readFileSync(archive))).toBe(checkpointHash);
      await restore();await expect.poll(field).toBe(savedField);
      await s.crt.screenshot({path:join(s.work,`recovered-${cycle}.png`)});
      await openNativeUtilities(page);await page.getByRole('button',{name:'Eject disk',exact:true}).click();
      await expect(page.getByRole('alert')).toContainText('Export disk changes');await page.getByText('Dismiss',{exact:true}).click();
      await s.session(`recovered-${cycle}.s760state`);
      const exported=readFileSync(await s.exportDisk());expect(hash(exported)).toBe(expected.browser.results.edited_sha256);
      writeFileSync(join(s.work,'edited.img'),exported);s.unchanged();
      rows.push({...interrupted,cycle,pid:interrupted.service_pid,table:await s.table(),saved_field:savedField,
        unsaved_field:unsavedField,restored_field:await field(),export_sha256:hash(exported),recovery_sha256:checkpointHash});
      if(cycle<2)await restore();
    }
    copyFileSync(archive,join(s.work,'automatic.s760state'));
    await restore();await s.move(110,30);
    const knob=page.getByRole('button',{name:'VALUE knob',exact:true});await knob.focus();await knob.press('ArrowDown');
    await s.move(150,10);const retryField=await field();expect(retryField).not.toBe(savedField);
    await openNativeUtilities(page);
    const denied=join(s.work,'denied.json');
    watcher=spawn(process.env.S760_QA_PYTHON||'python',[join(repo,'scripts/interrupt_checkpoint_publication.py'),
      '--pid',String(s.pid()),'--archive',archive,'--result',denied,'--deny-replace'],{windowsHide:true});
    await expect.poll(()=>existsSync(denied.replace(/\.json$/,'.ready'))).toBe(true);
    await page.getByText('Save recovery now',{exact:true}).click();
    await expect(page.getByRole('alert')).toContainText(/denied|permission|WinError (5|32)/i,{timeout:20000});
    expect(hash(readFileSync(archive))).toBe(checkpointHash);
    expect(readdirSync(join(s.state,'sessions')).filter(n=>n.endsWith('.tmp'))).toEqual([]);
    await s.move(150,10);expect(await field()).toBe(retryField);await openNativeUtilities(page);
    writeFileSync(denied.replace(/\.json$/,'.release'),'release');
    await expect.poll(()=>watcher!.exitCode).toBe(0);watcher=undefined;
    await page.getByText('Dismiss',{exact:true}).click();await page.getByText('Save recovery now',{exact:true}).click();
    // Observe completion through the UI before opening the destination again;
    // Windows readers may deny replacement while their file handle is open.
    await expect(page.getByLabel('Automatic recovery status')).toContainText('Recovery saved.',{timeout:20000});
    expect(hash(readFileSync(archive))).not.toBe(checkpointHash);
    copyFileSync(archive,join(s.work,'retry.s760state'));
    // Clear controller writes before replacing live sampler memory through the UI.
    await s.exportDisk();await restore();await expect.poll(field).toBe(retryField);
    writeFileSync(join(s.work,'result.json'),JSON.stringify({passed:true,cycles:rows,checkpoint_sha256:checkpointHash,
      edited_sha256:expected.browser.results.edited_sha256,unchanged_sample_bytes:119808,
      replace_denied_preserves_previous:true,failed_save_preserves_live_field:retryField,retry_restored_field:await field(),
      retry_sha256:hash(readFileSync(join(s.work,'retry.s760state'))),
      scope:'Unmodified frozen writer interrupted after pending file creation, before publication; prior Level64 checkpoint survives unsaved Level63 replacement'},null,2));
  }finally{
    if(watcher&&watcher.exitCode===null)watcher.kill();
    await s.close();
  }
});

test('packaged abrupt process-tree termination preserves automatic dirty recovery across three cold launches',async({page})=>{
  test.skip(!process.env.S760_MEDIA_PACKAGE||!process.env.S760_MEDIA_WORK,'Requires Windows native package and fresh private work');
  test.setTimeout(360000);
  const s=await sampler(page,'crash');
  try {
    const dirty=async()=>{
      // MEDIA_STATUS is sent on connection/restore, not streamed after firmware
      // writes. Reconnect the display to request a current controller response.
      await openNativeUtilities(page);
      if(!s.media()?.dirty)await page.getByText('Reconnect display',{exact:true}).click();
      await expect.poll(()=>s.media(),{timeout:60000}).toMatchObject({dirty:true,busy:false});
    };
    await s.session('manual-before-load.s760state');
    const manual=hash(readFileSync(join(s.state,'sessions/latest.s760state')));
    let expectedManual=manual;
    await s.load();await s.move(110,30);
    const knob=page.getByRole('button',{name:'VALUE knob',exact:true});await knob.focus();
    for(let n=0;n<63;n++){await knob.press('ArrowDown');await page.waitForTimeout(50);}
    await s.click(118,5);await page.waitForTimeout(500);await s.click(80,30);await page.waitForTimeout(2000);
    await s.click(50,34);await s.click(76,98);await page.waitForTimeout(800);
    await s.click(62,70);await page.waitForTimeout(800);await s.click(66,70);
    await dirty();
    await s.perform();await openNativeUtilities(page);
    const recovery=join(s.state,'sessions/recovery.s760state');
    const priorRecovery=existsSync(recovery)?hash(readFileSync(recovery)):null;
    await s.move(150,10);const editedTable=await s.table();await openNativeUtilities(page);
    // Exercise the production timer: never press Save recovery now.
    await expect(page.getByLabel('Automatic recovery status')).toContainText('Recovery saved.',{timeout:75000});
    await expect.poll(()=>existsSync(recovery)?hash(readFileSync(recovery)):null,{timeout:75000}).not.toBe(priorRecovery);
    const checkpoint=readFileSync(recovery),checkpointHash=hash(checkpoint);
    copyFileSync(recovery,join(s.work,'automatic.s760state'));
    const edited=readFileSync(await s.exportDisk());expect(edited[0x4e40]).toBe(192);
    writeFileSync(join(s.work,'edited.img'),edited);
    const restore=async()=>{
      await openNativeUtilities(page);await page.getByText('Restore recovery',{exact:true}).click();
      await page.getByLabel('Confirm recovery replacement').check();
      await page.getByText('Confirm recovery',{exact:true}).click();
      await expect(page.getByText('Recovery restored.',{exact:true})).toBeVisible({timeout:20000});
      await dirty();
    };
    await restore();
    const cycles=[];
    for(let cycle=0;cycle<3;cycle++){
      const pid=await s.crash();expect(hash(readFileSync(recovery))).toBe(checkpointHash);
      await s.launch();
      await expect(page.getByLabel('Automatic recovery status')).toContainText('Existing recovery preserved.');
      if(cycle===0)await page.waitForTimeout(61000);
      expect(hash(readFileSync(recovery))).toBe(checkpointHash);
      await restore();await s.move(150,10);
      const pixels=await s.table();
      expect(pixels).toBe(editedTable);
      await s.crt.screenshot({path:join(s.work,`recovered-${cycle}.png`)});
      await openNativeUtilities(page);await page.getByRole('button',{name:'Eject disk',exact:true}).click();
      await expect(page.getByRole('alert')).toContainText('Export disk changes');
      await page.getByText('Dismiss',{exact:true}).click();
      expect(hash(readFileSync(join(s.state,'sessions/latest.s760state')))).toBe(expectedManual);
      await s.session(`recovered-${cycle}.s760state`);
      expectedManual=hash(readFileSync(join(s.state,'sessions/latest.s760state')));
      const recalled=readFileSync(await s.exportDisk());expect(recalled.equals(edited)).toBe(true);
      expect(recalled.subarray(0x2ac00,0x2ac00+13*9216).equals(s.original.subarray(0x2ac00,0x2ac00+13*9216))).toBe(true);
      // Session-save is deliberate after recovery; the original manual slot
      // must have survived the abrupt shutdown before that explicit overwrite.
      cycles.push({cycle,pid,table:pixels,export_sha256:hash(recalled),recovery_sha256:hash(readFileSync(recovery))});
      await restore();s.unchanged();
    }
    writeFileSync(join(s.work,'result.json'),JSON.stringify({passed:true,cycles,checkpoint_sha256:checkpointHash,
      original_manual_sha256:manual,edited_sha256:hash(edited),timer_seconds:60,startup_preservation_seconds:61,
      unchanged_sample_bytes:13*9216,scope:'Abrupt Windows process-tree termination; no physical power loss or device audio'},null,2));
  }finally{await s.close();}
});

test('packaged correct-size unformatted media, eight firmware recovery cycles and retained sample sessions',async({page})=>{
  test.skip(!process.env.S760_MEDIA_PACKAGE||!process.env.S760_MEDIA_WORK,'Requires native package and fresh private media work');
  test.setTimeout(420000);
  const s=await sampler(page,'unformatted');
  try {
    await s.load();await expect.poll(s.table).toBe(3384624565);await s.session('baseline.s760state');
    const rows=[];
    for(let round=0;round<2;round++)for(const file of s.bad) {
      await s.mount(file);await s.disk();
      // Independently inspected OS2.24 native captures show xxxxxfiles with
      // unknown Disk/Marked statistics. This is not a successful directory.
      await expect.poll(s.directory,{timeout:15000}).toBe('17f623a13cbcd13333ccc406494b2b2977a34f39352d7f1506ecea7ed79c3d3d');
      await s.click(76,98);await page.waitForTimeout(700);await s.move(150,10);
      await expect.poll(s.directory).toBe('17f623a13cbcd13333ccc406494b2b2977a34f39352d7f1506ecea7ed79c3d3d');
      await s.crt.screenshot({path:join(s.work,`${round}-${file}.png`)});
      const exported=await s.exportDisk();
      expect(readFileSync(exported).equals(readFileSync(join(s.library,file)))).toBe(true);
      await s.perform();await expect.poll(s.table).toBe(3384624565);
      const archive=`retained-${round}-${file}.s760state`;await s.session(archive);
      await s.load(true);await expect.poll(s.table).toBe(3384624565);
      // Positive directory content after reinsertion must differ from the bad-media sentinel.
      await s.disk();expect(await s.directory()).not.toBe('17f623a13cbcd13333ccc406494b2b2977a34f39352d7f1506ecea7ed79c3d3d');
      await s.perform();rows.push({round,file,archive,fixture_sha256:hash(readFileSync(join(s.library,file))),export_sha256:hash(readFileSync(exported)),loaded_table:await s.table()});
    }
    s.unchanged();await openNativeUtilities(page);await expect(page.getByRole('alert')).toHaveCount(0);
    writeFileSync(join(s.work,'result.json'),JSON.stringify({passed:true,cycles:rows,scope:'Four correct-size unformatted profiles twice; firmware sentinel, exact unchanged exports, retained-memory sessions and good-disk reload'},null,2));
  }finally{
    if(!existsSync(join(s.work,'result.json')) && !page.isClosed()) {
      try {await closeNativeUtilities(page);await s.crt.screenshot({path:join(s.work,'failure.png')});}catch {/* Preserve the original failure. */}
    }
    await s.close();
  }
});

test('packaged dirty-session restore preserves unexported edits and media replacement guards',async({page})=>{
  test.skip(!process.env.S760_MEDIA_PACKAGE||!process.env.S760_MEDIA_WORK,'Requires native package and fresh private media work');
  test.setTimeout(180000);
  const s=await sampler(page,'dirty');
  try {
    await s.load();await s.move(110,30);
    const knob=page.getByRole('button',{name:'VALUE knob',exact:true});await knob.focus();
    for(let n=0;n<63;n++){await knob.press('ArrowDown');await page.waitForTimeout(50);}
    await s.click(118,5);await page.waitForTimeout(500);await s.click(80,30);await page.waitForTimeout(2000);
    await s.click(50,34);await s.click(76,98);await page.waitForTimeout(800);await s.click(62,70);
    await page.waitForTimeout(800);await s.click(66,70);await page.waitForTimeout(6000);await s.perform();
    await s.mount(s.bad[0]);await openNativeUtilities(page);
    await expect(page.getByRole('alert')).toContainText('unexported changes');await page.getByText('Dismiss',{exact:true}).click();
    await page.getByRole('button',{name:'Eject disk',exact:true}).click();
    await expect(page.getByRole('alert')).toContainText('Export disk changes');await page.getByText('Dismiss',{exact:true}).click();
    await page.getByText('Restart sampler',{exact:true}).click();await page.getByLabel('Discard unsaved sampler memory').check();
    await page.getByText('Confirm restart',{exact:true}).click();
    await expect(page.getByRole('alert')).toContainText('Export disk writes');await page.getByText('Dismiss',{exact:true}).click();
    await expect.poll(()=>s.media()?.dirty).toBe(true);
    await s.session('dirty.s760state');
    const first=readFileSync(await s.exportDisk());expect(first[0x4e40]).toBe(192);
    expect(first.subarray(0x2ac00,0x2ac00+13*9216).equals(s.original.subarray(0x2ac00,0x2ac00+13*9216))).toBe(true);
    await page.getByText('Restart sampler',{exact:true}).click();await page.getByLabel('Discard unsaved sampler memory').check();
    await page.getByText('Confirm restart',{exact:true}).click();
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
    await page.getByText('Restore saved session',{exact:true}).click();await page.getByLabel('Replace current sampler memory',{exact:true}).check();
    await page.getByText('Confirm restore',{exact:true}).click();await expect(page.getByText('Saved session restored.',{exact:true})).toBeVisible({timeout:20000});
    await s.mount(s.bad[0]);await openNativeUtilities(page);
    await expect(page.getByRole('alert')).toContainText('unexported changes');await page.getByText('Dismiss',{exact:true}).click();
    const recalled=readFileSync(await s.exportDisk());expect(recalled.equals(first)).toBe(true);
    writeFileSync(join(s.work,'edited.img'),recalled);s.unchanged();
    await s.move(150,10);await s.crt.screenshot({path:join(s.work,'recalled-dirty.png')});
    writeFileSync(join(s.work,'result.json'),JSON.stringify({passed:true,guards:['mount','eject','restart','mount after dirty recall'],saved_sha256:hash(first),recalled_sha256:hash(recalled),unchanged_sample_bytes:13*9216},null,2));
  }finally{await s.close();}
});
