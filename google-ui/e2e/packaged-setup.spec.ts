import {test,expect} from '@playwright/test';
import {spawn,type ChildProcess} from 'node:child_process';
import {cpSync,copyFileSync,existsSync,mkdirSync,readFileSync,unlinkSync,writeFileSync} from 'node:fs';
import {resolve,join} from 'node:path';

test('relocated package setup, invalid firmware recovery and persisted profile without development environment',async({page})=>{
  test.skip(!process.env.S760_SETUP_PACKAGE || !process.env.S760_SETUP_WORK,'Requires a fresh package and private work directory');
  test.setTimeout(150000);
  const repo=resolve('..'),work=resolve(process.env.S760_SETUP_WORK!);
  expect(existsSync(work)).toBe(false);mkdirSync(work,{recursive:true});
  const packageDir=join(work,'S760 Studio'),files=join(work,'My sampler files');
  cpSync(resolve(process.env.S760_SETUP_PACKAGE!),packageDir,{recursive:true});
  mkdirSync(files);mkdirSync(join(files,'disks'));mkdirSync(join(work,'unrelated cwd'));
  copyFileSync(join(repo,'roms/BOOT/Roland_S-760_v1.11.BIN'),join(files,'boot.bin'));
  copyFileSync(join(repo,'roms/System/S760224.IMG'),join(files,'system.img'));
  copyFileSync(join(repo,'roms/FDD/ROBOFULL.IMG'),join(files,'disks/ROBOFULL.IMG'));
  writeFileSync(join(files,'invalid.bin'),Buffer.alloc(256));
  const state=join(files,'profile'),session=join(state,'session.json');
  const env={...process.env};
  for(const key of Object.keys(env))if(/^(PYTHON|NODE_|S760_)/i.test(key))delete env[key];
  env.PATH=join(env.SystemRoot!,'System32');
  let child:ChildProcess|undefined;
  const stop=async()=>{
    if(child && child.exitCode===null){child.kill();await expect.poll(()=>child!.exitCode!==null||child!.signalCode!==null).toBe(true);}
    child=undefined;
  };
  const launch=async()=>{
    if(existsSync(session))unlinkSync(session);
    child=spawn(join(packageDir,'S760Studio.exe'),['--state-dir',state,'--no-browser','--fast','--seconds','140'],
      {cwd:join(work,'unrelated cwd'),env,windowsHide:true});
    await expect.poll(()=>existsSync(session),{timeout:30000}).toBe(true);
    await page.goto(JSON.parse(readFileSync(session,'utf8')).url);
  };
  const config=page.getByRole('dialog',{name:'Standalone configuration'});
  try {
    await launch();
    await expect(config).toBeVisible({timeout:10000});
    await expect(page.getByRole('status')).toContainText('Sampler needs configuration');
    await config.getByRole('button',{name:'Firmware & media',exact:true}).click();
    await config.getByLabel('Boot ROM (32KB)').fill(join(files,'invalid.bin'));
    await config.getByLabel('System disk (1.44MB)').fill(join(files,'system.img'));
    await config.getByLabel('Media directory').fill(join(files,'disks'));
    await config.getByRole('button',{name:'Audio',exact:true}).click();
    await config.getByLabel('Enable audio output').uncheck();
    await expect(config.getByLabel('Recording device')).toHaveValue('');
    await config.getByLabel('Replace current sampler memory and restart').check();
    await config.getByRole('button',{name:'Apply settings and start'}).click();
    await expect(page.getByRole('alert')).toContainText('Boot ROM must be a readable 32KB IC15 image');
    expect(existsSync(join(state,'settings.json'))).toBe(false);
    await page.getByText('Dismiss',{exact:true}).click();
    await config.getByRole('button',{name:'Firmware & media',exact:true}).click();
    await config.getByLabel('Boot ROM (32KB)').fill(join(files,'boot.bin'));
    await config.getByLabel('Replace current sampler memory and restart').check();
    await config.getByRole('button',{name:'Apply settings and start'}).click();
    await expect(config).toHaveCount(0,{timeout:15000});
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
    await expect(page.getByLabel('Selected disk image')).toHaveText('SELECT: ROBOFULL.IMG');
    await page.screenshot({path:join(work,'first-setup.png'),fullPage:true});
    const saved=JSON.parse(readFileSync(join(state,'settings.json'),'utf8'));
    expect(saved.bootRom).toBe(join(files,'boot.bin'));expect(saved.sound).toBe(false);
    await stop();await launch();
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
    await page.getByRole('button',{name:'Configuration',exact:true}).click();
    await config.getByRole('button',{name:'Firmware & media',exact:true}).click();
    await expect(config.getByLabel('Boot ROM (32KB)')).toHaveValue(join(files,'boot.bin'));
    await expect(config.getByLabel('Media directory')).toHaveValue(join(files,'disks'));
    await expect(config.getByLabel('Enable audio output')).not.toBeChecked();
    await expect(page.getByRole('alert')).toHaveCount(0);
    await page.screenshot({path:join(work,'reopened-profile.png'),fullPage:true});
    writeFileSync(join(work,'result.json'),JSON.stringify({passed:true,relocated:true,paths_with_spaces:true,
      stripped_environment:['PYTHON*','NODE_*','S760_*'],path:'Windows System32 only',
      invalid_boot_rejected:true,settings_persisted:true,os_ready_after_reopen:true,
      limits:'Development workstation, silent/unthrottled browser; not a clean-machine or audio-device test'},null,2));
  } finally {await stop();}
});
