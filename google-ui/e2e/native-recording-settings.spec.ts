import {expect, test} from '@playwright/test';

test('standalone selects a recording input and retains it after display reconnect', async ({page}) => {
  test.skip(!process.env.S760_NATIVE_RECORDING_URL, 'Requires a private normal-speed standalone and MOTU input');
  test.setTimeout(120000);
  await page.goto(process.env.S760_NATIVE_RECORDING_URL!);
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.', {timeout:40000});
  await page.getByRole('button', {name:'Configuration',exact:true}).click();
  await page.getByText('Refresh recording devices').click();
  const devices=page.getByLabel('Recording device');
  const input=devices.locator('option').filter({hasText:'Stereo In 1-2 (MOTU'});
  await expect(input).toHaveCount(1);
  const id=await input.getAttribute('value');
  await devices.selectOption(id!);
  await expect(page.getByText('Apply settings and start')).toBeDisabled();
  await page.getByLabel('Replace current sampler memory and restart').check();
  await page.getByText('Apply settings and start').click();
  await expect(page.getByRole('dialog')).toHaveCount(0, {timeout:20000});
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.', {timeout:40000});
  await page.reload();
  await page.getByRole('button', {name:'Configuration',exact:true}).click();
  await expect(devices).toHaveValue(id!);
  await expect(page.getByLabel('Recording input status')).toContainText('44.1 kHz stereo PCM16');
  await expect(page.getByRole('alert')).toHaveCount(0);
  await page.screenshot({path:test.info().outputPath('recording-settings.png'),fullPage:true});
});
