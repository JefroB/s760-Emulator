// Actual frozen WebView2 exit and profile-location checks; fixtures remain private.
import {chromium} from '../google-ui/node_modules/playwright-core/index.mjs';
import fs from 'node:fs';
import path from 'node:path';
import {spawn,execFileSync} from 'node:child_process';
import {setTimeout as delay} from 'node:timers/promises';

const [packagePath,workPath]=process.argv.slice(2);
if(!packagePath || !workPath)throw new Error('Usage: node scripts/verify_packaged_exit.mjs PACKAGE FRESH_WORK');
const work=path.resolve(workPath), installed=path.join(work,'Private test package');
if(fs.existsSync(work))throw new Error('Use a fresh work directory');
fs.mkdirSync(work,{recursive:true});fs.cpSync(path.resolve(packagePath),installed,{recursive:true});
const psEnv=Object.fromEntries(Object.entries(process.env).filter(([k])=>k.toUpperCase()!=='PSMODULEPATH'));
const ps=code=>execFileSync('powershell.exe',['-NoProfile','-Command',code],{env:psEnv,encoding:'utf8'}).trim();
const ownedProcesses=pid=>JSON.parse(ps(`$all=@(Get-CimInstance Win32_Process); $owned=@(${pid}); do {$new=@($all | Where-Object {$_.ParentProcessId -in $owned -and $_.ProcessId -notin $owned}); $owned+=@($new | ForEach-Object {$_.ProcessId})} while ($new.Count -gt 0); ConvertTo-Json -Compress -InputObject @($all | Where-Object {$_.ProcessId -in $owned} | ForEach-Object {$p=Get-Process -Id $_.ProcessId -ErrorAction SilentlyContinue; @{pid=$_.ProcessId;name=$_.Name;window=[long]$p.MainWindowHandle}})`));
const results=[];

async function run(name,localName,mode,port){
  const local=path.join(work,localName), profile=path.join(local,'S760Studio','default');
  const child=spawn(path.join(installed,'S760Studio.exe'),['--no-sound','--fast'],{
    cwd:work,windowsHide:true,env:{...process.env,LOCALAPPDATA:local,
      WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:`--remote-debugging-port=${port}`},stdio:'ignore'});
  let browser;
  const exited=new Promise(resolve=>child.once('exit',(code)=>resolve(code)));
  try{
    const deadline=Date.now()+45000;
    while(Date.now()<deadline){
      if(child.exitCode!==null)throw new Error(`App exited before connection: ${child.exitCode}`);
      try{const response=await fetch(`http://127.0.0.1:${port}/json/version`);if(response.ok)break;}catch{}
      await delay(200);
    }
    browser=await chromium.connectOverCDP(`http://127.0.0.1:${port}`);
    const page=browser.contexts()[0].pages()[0];
    await page.getByRole('button',{name:'Configuration',exact:true}).waitFor({timeout:30000});
    if(mode!=='unconfigured')await page.getByRole('status').filter({hasText:'OS ready — Perform Play.'}).waitFor({timeout:40000});
    const owned=ownedProcesses(child.pid);
    const nativePids=owned.filter(p=>p.name==='mames760.exe').map(p=>p.pid);
    if(mode==='unconfigured' || mode==='blocked'){
      const close=ps(`Add-Type 'using System;using System.Text;using System.Runtime.InteropServices;public class OwnedClose{public delegate bool EnumProc(IntPtr h,IntPtr l);[DllImport("user32.dll")]public static extern bool EnumWindows(EnumProc p,IntPtr l);[DllImport("user32.dll")]public static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);[DllImport("user32.dll",CharSet=CharSet.Unicode)]public static extern int GetWindowText(IntPtr h,StringBuilder s,int n);[DllImport("user32.dll")]public static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);}'; $script:found=[IntPtr]::Zero; [OwnedClose]::EnumWindows({param($h,$l) [uint32]$p=0; [OwnedClose]::GetWindowThreadProcessId($h,[ref]$p)|Out-Null; $s=New-Object Text.StringBuilder 256; [OwnedClose]::GetWindowText($h,$s,256)|Out-Null; if($p -in @(${owned.map(p=>p.pid).join(',')}) -and $s.ToString() -eq 'Roland S-760'){$script:found=$h;return $false};return $true},[IntPtr]::Zero)|Out-Null; if($script:found -eq [IntPtr]::Zero){throw 'Owned desktop window not found'}; [OwnedClose]::PostMessage($script:found,0x0010,[IntPtr]::Zero,[IntPtr]::Zero)`);
      if(close.toLowerCase()!=='true')throw new Error('Native window close request failed');
    }else await page.getByRole('button',{name:'Quit application',exact:true}).click();
    const dialog=page.getByRole('dialog',{name:'Quit S760Studio',exact:true});
    await dialog.waitFor({timeout:10000});
    await page.screenshot({path:path.join(work,`${name}-quit-dialog.png`)});
    await dialog.getByRole('button',{name:'Save recovery and quit',exact:true}).click();
    if(mode==='blocked'){
      await dialog.getByRole('alert').waitFor({timeout:15000});
      if(child.exitCode!==null)throw new Error('App exited despite recovery failure');
      await dialog.getByRole('checkbox').check();
      await dialog.getByRole('button',{name:'Quit without saving',exact:true}).click();
    }
    const code=await Promise.race([exited,delay(25000,undefined,{ref:false}).then(()=>{throw new Error('App remained alive after confirmed quit');})]);
    if(code!==0)throw new Error(`Unexpected app exit ${code}`);
    for(const pid of nativePids){try{process.kill(pid,0);throw new Error(`Native child still alive: ${pid}`);}catch(error){if(error.code!=='ESRCH')throw error;}}
    if(!fs.existsSync(profile))throw new Error('Default Local AppData profile was not created');
    if(fs.existsSync(path.join(installed,'docs','ic20-hle-findings')))throw new Error('Runtime data appeared under package docs');
    results.push({name,mode,exitCode:code,nativeChildrenStopped:nativePids.length,profile,docsUnchanged:true});
  }finally{
    if(browser)await browser.close().catch(()=>{});
    if(child.exitCode===null){try{execFileSync('taskkill',['/PID',String(child.pid),'/T','/F'],{stdio:'ignore'});}catch{}}
  }
}

await run('missing-firmware-close','empty-local','unconfigured',48771);
fs.copyFileSync('roms/BOOT/Roland_S-760_v1.11.BIN',path.join(installed,'roms/BOOT/ic15.rom'));
fs.copyFileSync('S760224.IMG',path.join(installed,'roms/System/S760224.OUT'));
await run('boot-save-quit','boot-local','safe',48772);
await run('existing-recovery-close-discard','boot-local','blocked',48773);
fs.writeFileSync(path.join(work,'result.json'),JSON.stringify({passed:true,cases:results},null,2)+'\n');
console.log(JSON.stringify({passed:true,cases:results},null,2));
