import {openNativeUtilities,closeNativeUtilities} from './native-controls';
import {expect, test} from '@playwright/test';
import {readFileSync, writeFileSync} from 'node:fs';

test('saved session survives missing library and explains rejected version/build', async ({page}) => {
  test.skip(!process.env.S760_RECOVERY_URL || !process.env.S760_RECOVERY_ARCHIVE,
    'Requires private native service with a copied saved session and missing source library');
  test.setTimeout(90000);
  const path = process.env.S760_RECOVERY_ARCHIVE!;
  const original = readFileSync(path);
  const manifestSize = original.readUInt32LE(8);
  const manifest = JSON.parse(original.subarray(12,12+manifestSize).toString());
  const payload = original.subarray(12+manifestSize);
  const publish = (metadata: unknown) => {
    const encoded = Buffer.from(JSON.stringify(metadata));
    const header = Buffer.alloc(12);header.write('S760CKP2');header.writeUInt32LE(encoded.length,8);
    writeFileSync(path,Buffer.concat([header,encoded,payload]));
  };
  const restore = async () => {
    await openNativeUtilities(page);
    await page.getByText('Restore saved session',{exact:true}).click();
    await page.getByLabel('Replace current sampler memory',{exact:true}).check();
    await page.getByText('Confirm restore',{exact:true}).click();
  };
  try {
    await page.goto(process.env.S760_RECOVERY_URL!);
  await openNativeUtilities(page);
    const status = page.getByRole('status');
    await expect(status).toContainText('Sampler needs configuration',{timeout:10000});
    await expect(page.getByLabel('Selected disk image')).toHaveCount(0);
    // A missing configured library blocks normal launch, but the embedded
    // floppy session must recover without requiring that source directory.
    await restore();
    await expect(page.getByText('Saved session restored.',{exact:true})).toBeVisible({timeout:20000});
    await expect(status).toHaveText('OS ready — Perform Play.',{timeout:20000});
    await closeNativeUtilities(page);
    await expect(page.getByRole('dialog',{name:'Standalone configuration'})).toHaveCount(0);
    const table = () => page.getByLabel('Native CRT').evaluate((canvas:HTMLCanvasElement) => {
      let hash=2166136261;
      for(const byte of canvas.getContext('2d')!.getImageData(112,112,256,128).data)
        hash=Math.imul(hash^byte,16777619);
      return hash>>>0;
    });
    await expect.poll(table).toBe(3384624565);
    const before = await table();
    publish({...manifest,version:999});await restore();
    await expect(page.getByRole('alert')).toContainText('Session format version is unsupported');
    await expect(status).toHaveText('OS ready — Perform Play.');
    await expect.poll(table).toBe(before);
    await page.getByText('Dismiss',{exact:true}).click();
    publish({...manifest,identity:{...manifest.identity,mame:'different-build'}});await restore();
    await expect(page.getByRole('alert')).toContainText('Session identity mismatch: MAME build');
    await expect(page.getByRole('alert')).toContainText('Current sampler memory has not been replaced');
    await expect.poll(table).toBe(before);
    await page.screenshot({path:test.info().outputPath('identity-mismatch.png'),fullPage:true});
    writeFileSync(path,original);await restore();
    await expect(page.getByText('Saved session restored.',{exact:true})).toBeVisible({timeout:20000});
    await expect(status).toHaveText('OS ready — Perform Play.',{timeout:20000});
    await expect.poll(table).toBe(3384624565);
    await expect(page.getByRole('alert')).toHaveCount(0);
    expect(readFileSync(path).equals(original)).toBe(true);
    await page.screenshot({path:test.info().outputPath('missing-library-restored.png'),fullPage:true});
  } finally {writeFileSync(path,original);}
});
