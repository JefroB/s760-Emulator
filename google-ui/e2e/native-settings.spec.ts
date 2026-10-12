import {expect,test} from '@playwright/test';

test('recover missing firmware through graphical settings',async({page})=>{
  test.skip(!process.env.S760_SETUP_URL,'Requires a native service started with missing firmware');
  test.setTimeout(120000);
  await page.goto(process.env.S760_SETUP_URL!);
  const dialog=page.getByRole('dialog',{name:'Runtime settings'});
  await expect(dialog).toBeVisible();
  await expect(page.getByRole('status')).toContainText('needs configuration');
  await page.getByLabel('Boot ROM (32KB)').fill(process.env.S760_TEST_BOOT!);
  await page.getByLabel('System disk (1.44MB)').fill(process.env.S760_TEST_SYSTEM!);
  await page.getByLabel('Media directory').fill(process.env.S760_TEST_MEDIA!);
  await page.getByLabel('Replace current sampler memory and restart').check();
  await page.getByRole('button',{name:'Apply settings and start'}).click();
  await expect(dialog).toHaveCount(0,{timeout:40000});
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await expect(page.getByLabel('Sample disk').locator('option')).not.toHaveCount(1);
  await expect.poll(()=>page.getByLabel('Native CRT').evaluate((c:HTMLCanvasElement)=>{
    const pixels=c.getContext('2d')!.getImageData(0,0,640,480).data;
    let count=0;for(let i=0;i<pixels.length;i+=4)if(pixels[i]||pixels[i+1]||pixels[i+2])count++;
    return count;
  })).toBeGreaterThan(10000);
  // Invalid replacement must leave this running firmware intact.
  await page.getByRole('button',{name:'Runtime settings',exact:true}).click();
  await page.getByLabel('Boot ROM (32KB)').fill('missing-boot-image.bin');
  await page.getByLabel('Replace current sampler memory and restart').check();
  await page.getByRole('button',{name:'Apply settings and start'}).click();
  await expect(page.getByRole('alert')).toContainText('Boot ROM must be');
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.');
  await expect(page.getByRole('button',{name:'Apply settings and start'})).toBeEnabled();
  await page.screenshot({path:test.info().outputPath('settings-invalid-preserves-machine.png'),fullPage:true});
});
