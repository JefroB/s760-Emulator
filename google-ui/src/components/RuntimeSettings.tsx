import {useState} from 'react';

export interface RuntimeConfiguration {
  bootRom: string;
  systemDisk: string;
  mediaDirectory: string;
  sound: boolean;
}

// Transport-independent: hosts own validation, persistence and lifecycle.
export function RuntimeSettings({configuration, pending, onApply, onCancel}: {
  configuration: RuntimeConfiguration;
  pending: boolean;
  onApply: (configuration: RuntimeConfiguration) => void;
  onCancel: () => void;
}) {
  const [draft,setDraft]=useState(configuration);
  const [confirmed,setConfirmed]=useState(false);
  return <section role="dialog" aria-label="Runtime settings" className="w-full max-w-3xl rounded border border-neutral-600 bg-neutral-900 p-5 space-y-3">
    <h2 className="text-lg">Runtime settings</h2>
    <p className="text-sm text-neutral-300">Use your own Roland firmware files. Applying settings boots the sampler again and replaces unsaved memory. Export disk writes and save your session first.</p>
    {([['bootRom','Boot ROM (32KB)'],['systemDisk','System disk (1.44MB)'],['mediaDirectory','Media directory']] as const).map(([key,label])=>
      <label key={key} className="block">{label}<input className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft[key]} disabled={pending}
        onChange={e=>{setDraft({...draft,[key]:e.target.value});setConfirmed(false);}}/></label>)}
    <label className="block"><input type="checkbox" checked={draft.sound} disabled={pending} onChange={e=>{setDraft({...draft,sound:e.target.checked});setConfirmed(false);}}/> Enable MAME audio output</label>
    <label className="block"><input type="checkbox" checked={confirmed} disabled={pending} onChange={e=>setConfirmed(e.target.checked)}/> Replace current sampler memory and restart</label>
    <div className="flex gap-4"><button disabled={pending||!confirmed||!draft.bootRom.trim()||!draft.systemDisk.trim()||!draft.mediaDirectory.trim()}
      onClick={()=>onApply(draft)}>{pending?'Starting sampler…':'Apply settings and start'}</button>
      <button disabled={pending} onClick={onCancel}>Cancel settings</button></div>
  </section>;
}
