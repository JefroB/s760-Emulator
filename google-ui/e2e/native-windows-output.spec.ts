import {expect,test} from '@playwright/test';

test('Windows output selection applies through native WASAPI and survives reconnect',async({page})=>{
  test.skip(!process.env.S760_NATIVE_WINDOWS_URL,'Requires private native standalone and Realtek digital output');
  test.setTimeout(120000);
  await page.goto(process.env.S760_NATIVE_WINDOWS_URL!);
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await page.getByRole('button',{name:'Configuration',exact:true}).click();
  await page.getByLabel('Audio output backend').selectOption('wasapi');
  const option=page.getByLabel('Windows output device').locator('option').filter({hasText:'Realtek Digital Output'});
  await expect(option).toHaveCount(1,{timeout:15000});
  const endpoint=await option.getAttribute('value');
  await page.getByLabel('Windows output device').selectOption(endpoint!);
  await page.getByLabel('Enable audio output').check();
  await expect(page.getByText('Apply settings and start')).toBeDisabled();
  await page.getByLabel('Replace current sampler memory and restart').check();
  await page.getByText('Apply settings and start').click();
  await expect(page.getByRole('dialog')).toHaveCount(0,{timeout:20000});
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.',{timeout:40000});
  await page.reload();
  await page.getByRole('button',{name:'Configuration',exact:true}).click();
  await expect(page.getByLabel('Audio output backend')).toHaveValue('wasapi');
  await expect(page.getByLabel('Windows output device')).toHaveValue(endpoint!);
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.screenshot({path:test.info().outputPath('windows-output.png'),fullPage:true});
});
