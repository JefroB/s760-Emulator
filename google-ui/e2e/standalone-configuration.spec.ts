import {test,expect} from '@playwright/test';

test('standalone config owns MIDI/audio and remembers hidden-by-default keyboard',async({page})=>{
  test.skip(!process.env.S760_CONFIGURATION_URL,'Requires native standalone service');
  test.setTimeout(90000);
  const sent:string[]=[];
  page.on('websocket',socket=>socket.on('framesent',event=>{if(typeof event.payload==='string')sent.push(event.payload);}));
  await page.goto(process.env.S760_CONFIGURATION_URL!);
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await expect(page.getByRole('region',{name:'On-screen keyboard'})).toHaveCount(0);
  await page.getByRole('button',{name:'Configuration',exact:true}).click();
  const config=page.getByRole('dialog',{name:'Standalone configuration'});
  await config.getByRole('button',{name:'Audio',exact:true}).click();
  await expect(config.getByLabel('Audio output backend')).toBeVisible();
  await expect(config.getByLabel('Audio buffer target (ms)')).toBeVisible();
  await config.getByRole('button',{name:'MIDI & display',exact:true}).click();
  await expect(config.getByLabel('MIDI input')).toBeVisible();
  await config.getByLabel('MIDI input').selectOption('');
  await config.getByLabel('Show on-screen keyboard').click();
  await expect(config.getByLabel('Show on-screen keyboard')).toBeChecked();
  await config.screenshot({path:test.info().outputPath('configuration.png')});
  await config.getByRole('button',{name:'Cancel settings'}).click();
  const keyboard=page.getByRole('region',{name:'On-screen keyboard'});
  await expect(keyboard).toBeVisible();
  await expect(keyboard.getByRole('button')).toHaveCount(61);
  const rack=(await page.getByLabel('Native sampler rack').boundingBox())!;
  const keys=(await keyboard.boundingBox())!;
  expect(Math.abs(rack.width-keys.width)).toBeLessThan(1);
  expect(Math.abs(rack.x-keys.x)).toBeLessThan(1);
  expect(keys.y-rack.y-rack.height).toBeLessThan(1);
  // Match the VST: display 200 firmware rows and clip 40 unused transport rows.
  const geometry=await page.getByLabel('Native CRT').evaluate(c=>({
    canvas:c.getBoundingClientRect().height,
    tube:c.parentElement!.getBoundingClientRect().height,
    overflow:getComputedStyle(c.parentElement!).overflow,
  }));
  expect(geometry.canvas/geometry.tube).toBeGreaterThan(1.19);
  expect(geometry.canvas/geometry.tube).toBeLessThan(1.21);
  expect(geometry.tube).toBeCloseTo(480);
  expect(geometry.overflow).toBe('hidden');
  await keyboard.screenshot({path:test.info().outputPath('keyboard.png')});
  await page.getByRole('button',{name:'C4 MIDI 60',exact:true}).focus();
  await page.keyboard.down('Space');await page.keyboard.up('Space');
  await expect.poll(()=>sent.some(s=>JSON.parse(s).type==='NOTE_OFF'&&JSON.parse(s).payload.note===60)).toBe(true);
  await page.reload();
  await expect(page.getByRole('region',{name:'On-screen keyboard'})).toBeVisible();
  await page.getByRole('button',{name:'Configuration',exact:true}).click();
  await config.getByRole('button',{name:'Audio',exact:true}).click();
  await config.getByLabel('Audio output backend').selectOption('wasapi');
  await config.getByLabel('Audio buffer target (ms)').fill('60');
  await config.getByLabel('Replace current sampler memory and restart').check();
  await config.getByRole('button',{name:'Apply settings and start'}).click();
  await expect(config).toHaveCount(0,{timeout:15000});
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await page.getByRole('button',{name:'Configuration',exact:true}).click();
  await config.getByRole('button',{name:'Audio',exact:true}).click();
  await expect(config.getByLabel('Audio output backend')).toHaveValue('wasapi');
  await expect(config.getByLabel('Audio buffer target (ms)')).toHaveValue('60');
  await config.getByRole('button',{name:'MIDI & display',exact:true}).click();
  await config.getByLabel('Show on-screen keyboard').click();
  await expect(config.getByLabel('Show on-screen keyboard')).not.toBeChecked();
  await config.getByRole('button',{name:'Cancel settings'}).click();
  await page.reload();
  await expect(page.getByRole('button',{name:'Configuration',exact:true})).toBeVisible();
  await expect(page.getByRole('region',{name:'On-screen keyboard'})).toHaveCount(0);
  await expect(page.getByRole('alert')).toHaveCount(0);
});
