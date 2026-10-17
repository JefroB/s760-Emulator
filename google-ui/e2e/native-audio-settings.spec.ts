import {openNativeUtilities} from './native-controls';
import {expect, test} from '@playwright/test';

test('standalone audio settings apply and survive display reconnect', async ({page}) => {
  test.skip(!process.env.S760_NATIVE_AUDIO_SETTINGS_URL, 'Requires a private native standalone instance');
  test.setTimeout(90000);
  await page.goto(process.env.S760_NATIVE_AUDIO_SETTINGS_URL!);
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.', {timeout:40000});
  await page.getByRole('button', {name:'Configuration',exact:true}).click();
  await page.getByRole('button',{name:'Audio',exact:true}).click();
  await page.getByLabel('Audio output backend').selectOption('wasapi');
  await page.getByLabel('Audio buffer target (ms)').fill('60');
  await expect(page.getByText('Apply settings and start')).toBeDisabled();
  await page.getByLabel('Replace current sampler memory and restart').check();
  await page.screenshot({path:test.info().outputPath('audio-settings.png'),fullPage:true});
  await page.getByText('Apply settings and start').click();
  await expect(page.getByRole('dialog')).toHaveCount(0, {timeout:20000});
  await expect(page.getByRole('status')).toHaveText('OS ready — Perform Play.', {timeout:40000});
  await openNativeUtilities(page);
  await page.getByText('Reconnect display').click();
  await openNativeUtilities(page);
  await page.getByRole('button',{name:'Audio',exact:true}).click();
  await expect(page.getByLabel('Audio output backend')).toHaveValue('wasapi');
  await expect(page.getByLabel('Audio buffer target (ms)')).toHaveValue('60');
  await expect(page.getByRole('alert')).toHaveCount(0);
});
