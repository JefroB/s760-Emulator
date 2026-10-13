import {openNativeUtilities,closeNativeUtilities,selectNativeDisk} from './native-controls';
import {expect,test} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('production recovery timer captures loaded firmware state and restores through the UI',async({page})=>{
  test.skip(!process.env.S760_AUTO_RECOVERY_URL,'Requires a fresh private packaged native service');
  test.setTimeout(150000);
  await page.goto(process.env.S760_AUTO_RECOVERY_URL!);
  await openNativeUtilities(page);
  const status=page.getByRole('status');
  await expect(status).toHaveText('OS ready — Perform Play.',{timeout:40000});
  const crt=page.getByLabel('Native CRT');
  const click=async(x:number,y:number)=>{
    await closeNativeUtilities(page);
    await crt.scrollIntoViewIfNeeded();const box=(await crt.boundingBox())!;
    await page.mouse.move(box.x+box.width*x/160,box.y+box.height*y/120);await page.waitForTimeout(250);
    await page.mouse.down();await page.waitForTimeout(120);await page.mouse.up();await page.waitForTimeout(250);
  };
  await closeNativeUtilities(page);
  await selectNativeDisk(page,'ROBOFULL.IMG');
  await page.getByRole('button',{name:'Gotek Select',exact:true}).click();
  await expect(page.getByLabel('Drive display')).toContainText('ROBOFULL.IMG');
  await click(118,5);await click(80,22);await page.waitForTimeout(2000);await click(50,34);await click(76,98);
  await expect(status).toContainText('Disk Load ready',{timeout:60000});
  await click(10,5);await click(15,22);
  const table=()=>crt.evaluate((c:HTMLCanvasElement)=>{
    let hash=2166136261;for(const b of c.getContext('2d')!.getImageData(112,112,256,128).data)hash=Math.imul(hash^b,16777619);
    return hash>>>0;
  });
  await expect.poll(table).toBe(3384624565);
  await openNativeUtilities(page);
  // No Save session/Save recovery action: this waits the real 60-second host timer.
  await expect(page.getByLabel('Automatic recovery status')).toContainText('Recovery saved.',{timeout:75000});
  await expect(page.getByText('Restore saved session',{exact:true})).toBeDisabled();
  await page.getByText('Restart sampler',{exact:true}).click();
  await page.getByLabel('Discard unsaved sampler memory').check();await page.getByText('Confirm restart',{exact:true}).click();
  await expect(status).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await expect.poll(table).not.toBe(3384624565);
  await page.getByText('Restore recovery',{exact:true}).click();
  await expect(page.getByText('Confirm recovery',{exact:true})).toBeDisabled();
  await page.getByLabel('Confirm recovery replacement').check();await page.getByText('Confirm recovery',{exact:true}).click();
  await expect(page.getByText('Recovery restored.',{exact:true})).toBeVisible({timeout:20000});
  await expect.poll(table).toBe(3384624565);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.screenshot({path:test.info().outputPath('automatic-recovery-restored.png'),fullPage:true});
  const retained=process.env.S760_AUTO_ARCHIVE ? readFileSync(process.env.S760_AUTO_ARCHIVE) : null;
  await page.getByText('Quit without recovery',{exact:true}).click();
  await expect(page.getByText('Confirm recovery',{exact:true})).toBeDisabled();
  await page.getByLabel('Confirm recovery replacement').check();await page.getByText('Confirm recovery',{exact:true}).click();
  await expect(status).toHaveText('Sampler disconnected',{timeout:15000});
  if(retained) expect(readFileSync(process.env.S760_AUTO_ARCHIVE!).equals(retained)).toBe(true);
});

test('startup preserves previous recovery and exposes explicit new-history choice',async({page})=>{
  test.skip(!process.env.S760_AUTO_PENDING_URL || !process.env.S760_AUTO_PENDING_ARCHIVE,'Requires copied recovery in a fresh normal-start instance');
  test.setTimeout(100000);
  const original=readFileSync(process.env.S760_AUTO_PENDING_ARCHIVE!);
  await page.goto(process.env.S760_AUTO_PENDING_URL!);
  await openNativeUtilities(page);
  await expect(page.getByLabel('Automatic recovery status')).toContainText('Existing recovery preserved.');
  await page.waitForTimeout(61000);
  expect(readFileSync(process.env.S760_AUTO_PENDING_ARCHIVE!).equals(original)).toBe(true);
  await page.getByText('Restore recovery',{exact:true}).click();
  await page.getByLabel('Confirm recovery replacement').check();await page.getByText('Confirm recovery',{exact:true}).click();
  await expect(page.getByText('Recovery restored.',{exact:true})).toBeVisible({timeout:20000});
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:15000});
  await expect(page.getByText('Start new recovery history',{exact:true})).toHaveCount(0);
  expect(readFileSync(process.env.S760_AUTO_PENDING_ARCHIVE!).equals(original)).toBe(true);
  await page.screenshot({path:test.info().outputPath('startup-recovery-restored.png'),fullPage:true});
});
