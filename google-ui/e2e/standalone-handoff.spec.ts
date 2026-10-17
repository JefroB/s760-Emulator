import {chromium,expect,test} from '@playwright/test';
import {readFileSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {openNativeUtilities} from './native-controls';

test('extracted acceptance kit launches the packaged interface without development-tool paths',async()=>{
  test.skip(!process.env.S760_HANDOFF_REPORT || !process.env.S760_HANDOFF_CDP || !process.env.S760_HANDOFF_MANIFEST,
    'Requires Start-Acceptance.ps1 to launch an extracted private kit');
  test.setTimeout(70000);
  const report=resolve(process.env.S760_HANDOFF_REPORT!),endpoint=process.env.S760_HANDOFF_CDP!;
  const environment=JSON.parse(readFileSync(join(report,'environment.json'),'utf8').replace(/^\uFEFF/,''));
  expect(environment.verify_only).toBe(false);expect(environment.clean_machine_claimed).toBe(false);
  const manifestBytes=readFileSync(resolve(process.env.S760_HANDOFF_MANIFEST!));
  const manifest=JSON.parse(manifestBytes.toString('utf8'));
  expect(environment.package_manifest_sha256).toBe(createHash('sha256').update(manifestBytes).digest('hex'));
  expect(environment.package_files_verified).toBe(Object.keys(manifest.files).length);
  await expect.poll(async()=>{try{return(await fetch(endpoint+'/json/version')).ok;}catch{return false;}},{timeout:30000}).toBe(true);
  const browser=await chromium.connectOverCDP(endpoint);
  try {
    await expect.poll(()=>browser.contexts()[0]?.pages().length??0).toBeGreaterThan(0);
    const page=browser.contexts()[0].pages()[0];
    await expect(page).toHaveURL(JSON.parse(readFileSync(join(report,'profile/session.json'),'utf8')).url);
    await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:45000});
    const colored=await page.getByLabel('Native CRT').evaluate((c:HTMLCanvasElement)=>{
      const p=c.getContext('2d')!.getImageData(0,0,640,480).data;let count=0;
      for(let i=0;i<p.length;i+=4)if(p[i]||p[i+1]||p[i+2])count++;return count;
    });
    expect(colored).toBeGreaterThan(100000);
    await openNativeUtilities(page);await expect(page.getByRole('navigation',{name:'Settings categories'})).toBeVisible();
    await page.screenshot({path:join(report,'configuration.png'),fullPage:true});
    const version=await(await fetch(endpoint+'/json/version')).json();
    writeFileSync(join(report,'boot-verification.json'),JSON.stringify({passed:true,interface:'Packaged WebView2',
      renderer:version.Browser,coloredPixels:colored,packageManifest:environment.package_manifest_sha256,
      scope:'Extracted archive, default kit paths, Windows PowerShell launcher, unrelated working directory and stripped child development environment; workstation boot/UI smoke only',
      cleanMachine:false,completeWorkflow:false},null,2));
  }finally{await browser.close();}
});
