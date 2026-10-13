import {expect,type Page} from '@playwright/test';

export async function openNativeUtilities(page:Page) {
  if(!await page.getByRole('dialog',{name:'Standalone configuration'}).count())
    await page.getByRole('button',{name:'Configuration',exact:true}).click();
}
export async function closeNativeUtilities(page:Page) {
  if(await page.getByRole('dialog',{name:'Standalone configuration'}).count())
    await page.getByRole('button',{name:'Cancel settings',exact:true}).click();
}
export async function selectNativeDisk(page:Page,name:string) {
  const selected=page.getByLabel('Selected disk image');
  for(let i=0;i<512;i++) {
    if((await selected.textContent())?.trim()===`SELECT: ${name}`)return;
    const down=page.getByRole('button',{name:'Gotek Down'});
    if(!await down.isEnabled())break;
    await down.click();
  }
  await expect(selected).toHaveText(`SELECT: ${name}`);
}
