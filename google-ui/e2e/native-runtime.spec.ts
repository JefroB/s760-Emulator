import {expect, test} from '@playwright/test';

// Explicit opt-in: real firmware and native process, never a mock bridge.
test('native firmware readiness, loading, reconnect and confirmed restart', async ({page}) => {
  test.skip(!process.env.S760_NATIVE_URL, 'Requires local native standalone service and firmware');
  test.setTimeout(180000);
  await page.goto(process.env.S760_NATIVE_URL!);
  const status=page.getByRole('status');
  await expect(status).toHaveText('OS ready — Perform Play.',{timeout:40000});
  const crt=page.getByLabel('Native CRT');
  const click=async(x:number,y:number) => {
    await crt.scrollIntoViewIfNeeded();
    const box=(await crt.boundingBox())!;
    await page.mouse.move(box.x+box.width*x/160,box.y+box.height*y/120);
    await page.waitForTimeout(250);
    await page.mouse.down();await page.waitForTimeout(120);await page.mouse.up();await page.waitForTimeout(250);
  };
  await page.getByLabel('Sample disk').selectOption('ROBOFULL.IMG');
  await page.getByRole('button',{name:'Insert disk',exact:true}).click();
  await expect(page.getByText('Disk inserted: ROBOFULL.IMG')).toBeVisible();
  await click(118,5);await click(80,22);
  await expect(status).toContainText('Disk Load ready',{timeout:15000});
  await page.waitForTimeout(2000);
  await click(50,34);await click(76,98);
  await expect(status).toHaveText('Firmware disk operation in progress.',{timeout:5000});
  await expect(status).toContainText('Disk Load ready',{timeout:60000});
  await click(10,5);await click(15,22);
  await expect(status).toHaveText('OS ready — Perform Play.');
  // Status and pixels are separate packets; wait for this screen to paint.
  await expect.poll(()=>crt.evaluate(async(c:HTMLCanvasElement)=> {
    const rgba=c.getContext('2d')!.getImageData(16,48,224,16).data;
    const rgb=new Uint8Array(224*16*3);
    for(let i=0,j=0;i<rgba.length;i+=4) {rgb[j++]=rgba[i];rgb[j++]=rgba[i+1];rgb[j++]=rgba[i+2];}
    return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',rgb)),b=>b.toString(16).padStart(2,'0')).join('');
  })).toBe('40ebee098ea2b92bfba2d7da412f2fd3c39b5a08cf56822c0a9b880f3bef7f36');
  // Patch-name table excludes the pointer's old/new positions when clicking
  // the reconnect control above the CRT. Reconnection must retain this data.
  const pixels=()=>crt.evaluate((c:HTMLCanvasElement)=> {
    let hash=2166136261;
    for(const byte of c.getContext('2d')!.getImageData(112,112,256,128).data)
      hash=Math.imul(hash^byte,16777619);
    return hash>>>0;
  });
  // Native ROBOFULL fixture table. Firmware paints its title before the rows;
  // wait for the observed complete table, not just for a transport message.
  await expect.poll(pixels).toBe(3384624565);
  const before=await pixels();
  await page.getByText('Save session',{exact:true}).click();
  await expect(page.getByText(/^Session saved to /)).toBeVisible({timeout:15000});
  await crt.screenshot({path:test.info().outputPath('before-reconnect.png')});
  await page.getByText('Reconnect display').click();
  await expect(status).toHaveText('OS ready — Perform Play.',{timeout:10000});
  await page.waitForTimeout(300);
  await crt.screenshot({path:test.info().outputPath('after-reconnect.png')});
  await expect.poll(pixels).toBe(before);
  await page.getByRole('button',{name:'Export disk',exact:true}).click();
  await expect(page.getByText(/^Disk exported to /)).toBeVisible({timeout:10000});
  await page.getByText('Restart sampler',{exact:true}).click();
  await expect(page.getByText('Confirm restart')).toBeDisabled();
  await page.getByLabel('Discard unsaved sampler memory').check();
  await page.getByText('Confirm restart').click();
  await expect(status).toContainText(/Restart|Booting/,{timeout:10000});
  await expect(status).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await expect.poll(pixels).not.toBe(before); // Reset lost loaded patch as warned.
  await page.getByText('Restore saved session',{exact:true}).click();
  await expect(page.getByText('Confirm restore')).toBeDisabled();
  await page.getByLabel('Replace current sampler memory').check();
  await page.getByText('Confirm restore').click();
  await expect(page.getByText('Saved session restored.')).toBeVisible({timeout:15000});
  await expect(status).toHaveText('OS ready — Perform Play.',{timeout:15000});
  await crt.screenshot({path:test.info().outputPath('session-restored-crt.png')});
  await expect.poll(pixels).toBe(before);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.screenshot({path:test.info().outputPath('ready-after-session-restore.png'),fullPage:true});
  await expect(page.getByLabel('Native sampler rack')).toBeVisible();
  // A real keyboard panel edge must change firmware pixels, not React mode state.
  await page.locator('body').click({position:{x:5,y:5}});
  const panelPixels=()=>crt.evaluate((c:HTMLCanvasElement)=> {
    let hash=2166136261;
    for(const byte of c.getContext('2d')!.getImageData(0,0,640,480).data) hash=Math.imul(hash^byte,16777619);
    return hash>>>0;
  });
  await page.waitForTimeout(300);
  const beforeKey=await panelPixels();
  await page.keyboard.down('m');await page.waitForTimeout(150);await page.keyboard.up('m');
  await expect.poll(panelPixels).not.toBe(beforeKey);
  await page.screenshot({path:test.info().outputPath('keyboard-mode-rack.png'),fullPage:true});
});
