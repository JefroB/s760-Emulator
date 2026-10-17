import {chromium,expect,test} from '@playwright/test';

test('configuration layers fit the viewport and keep confirmations above settings',async({page:browserPage})=>{
  test.skip(!process.env.S760_CONFIGURATION_URL,'Requires a real native standalone service');
  const desktop=process.env.S760_CONFIGURATION_CDP?await chromium.connectOverCDP(process.env.S760_CONFIGURATION_CDP):undefined;
  const page=desktop?desktop.contexts()[0].pages()[0]:browserPage;
  if(desktop)await expect(page).toHaveURL(process.env.S760_CONFIGURATION_URL!);
  else await page.goto(process.env.S760_CONFIGURATION_URL!);
  try {
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  for(const [width,height] of [[1366,768],[1024,768],[800,600],[640,480]]) {
    await page.setViewportSize({width,height});
    await page.getByRole('button',{name:'Configuration',exact:true}).click();
    const config=page.getByRole('dialog',{name:'Standalone configuration'});
    const box=(await config.boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(0);expect(box.y).toBeGreaterThanOrEqual(0);
    expect(box.x+box.width).toBeLessThanOrEqual(width);expect(box.y+box.height).toBeLessThanOrEqual(height);
    await expect(config.getByRole('button',{name:'Cancel settings',exact:true})).toBeInViewport();
    expect(await page.evaluate(()=>document.body.style.overflow)).toBe('hidden');
    for(const category of ['Session & disks','MIDI & display','Firmware & media','Audio']) {
      await config.getByRole('button',{name:category,exact:true}).click();
      await expect(config.getByRole('region',{name:category,exact:true})).toBeVisible();
      if(height>=768) {
        const overflow=await config.getByRole('region',{name:category,exact:true}).evaluate(el=>{
          const scroller=el.parentElement!;
          return scroller.scrollHeight-scroller.clientHeight;
        });
        expect(overflow,`${category} should fit without scrolling at ${width}x${height}`).toBeLessThanOrEqual(1);
      }
      await expect(config.getByRole('button',{name:'Apply settings and start',exact:true})).toBeInViewport();
      await page.screenshot({path:test.info().outputPath(`${width}-${category.replaceAll(/\W/g,'-')}.png`)});
    }
    await config.getByLabel('Audio output backend').selectOption('asio');
    await expect(config.getByLabel('ASIO driver')).toBeVisible();
    await expect(config.getByRole('button',{name:'Cancel settings',exact:true})).toBeInViewport();
    await page.screenshot({path:test.info().outputPath(`${width}-ASIO.png`)});
    await config.getByLabel('Audio output backend').selectOption('auto');
    await config.getByRole('button',{name:'Firmware & media',exact:true}).click();
    const boot=config.getByLabel('Boot ROM (32KB)');const original=await boot.inputValue();
    await boot.fill('draft-not-applied.bin');
    await config.getByRole('button',{name:'Audio',exact:true}).click();
    await config.getByRole('button',{name:'Firmware & media',exact:true}).click();
    await expect(boot).toHaveValue('draft-not-applied.bin');await boot.fill(original);
    await config.getByRole('button',{name:'Session & disks',exact:true}).click();
    await config.getByRole('button',{name:'Restart sampler',exact:true}).click();
    const confirm=page.getByRole('dialog',{name:'Restart sampler confirmation'});
    await expect(confirm).toBeVisible();
    await expect(confirm.getByRole('button',{name:'Confirm restart',exact:true})).toBeInViewport();
    await page.keyboard.press('Shift+Tab');
    expect(await confirm.evaluate(el=>el.contains(document.activeElement))).toBe(true);
    await page.keyboard.press('Escape');await expect(confirm).toHaveCount(0);await expect(config).toBeVisible();
    await expect(config.getByRole('button',{name:'Restart sampler',exact:true})).toBeFocused();
    await page.keyboard.press('Escape');await expect(config).toHaveCount(0);
    await expect(page.getByRole('button',{name:'Configuration',exact:true})).toBeFocused();
  }
  }finally {await desktop?.close();}
});
