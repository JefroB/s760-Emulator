import {useState} from 'react';
import type {ReactNode} from 'react';
import {SettingsLayer} from './SettingsLayer';

export interface RuntimeConfiguration {
  bootRom: string;
  systemDisk: string;
  mediaDirectory: string;
  sound: boolean;
  waveMemoryMb?: 8 | 16 | 32;
  audioBackend?: 'auto' | 'wasapi' | 'xaudio2' | 'asio';
  audioLatencyMs?: number;
  audioOutputDevice?: string;
  recordingDevice?: string;
  asioDriver?: string;
  asioOutputChannel?: number;
  asioInputChannel?: number;
  asioBufferFrames?: number;
}

export interface AsioDevice {name:string;inputs:number;outputs:number}

// Transport-independent: hosts own validation, persistence and lifecycle.
export function RuntimeSettings({configuration, pending, onApply, onCancel, children, utilityPanels=[], notices, initialPanel, hostDriven=false, recordingDevices=[], onRefreshRecordingDevices, asioDevices=[], onRefreshAsioDevices, audioOutputDevices=[],onRefreshAudioOutputDevices,title='Runtime settings'}: {
  configuration: RuntimeConfiguration;
  pending: boolean;
  onApply: (configuration: RuntimeConfiguration) => void;
  onCancel: () => void;
  children?: ReactNode;
  utilityPanels?: {id:string;label:string;content:ReactNode}[];
  notices?: ReactNode;
  initialPanel?: string;
  title?: string;
  hostDriven?: boolean;
  recordingDevices?: {id:string;name:string}[];
  onRefreshRecordingDevices?: ()=>void;
  asioDevices?: AsioDevice[];
  onRefreshAsioDevices?: ()=>void;
  audioOutputDevices?: {id:string;name:string}[];
  onRefreshAudioOutputDevices?: ()=>void;
}) {
  const [draft,setDraft]=useState(configuration);
  const [confirmed,setConfirmed]=useState(false);
  const [active,setActive]=useState(initialPanel??utilityPanels[0]?.id??'firmware');
  const panels=[...utilityPanels,{id:'firmware',label:'Firmware & media'},...(!hostDriven?[{id:'audio',label:'Audio'}]:[])];
  const driver=asioDevices.find(d=>d.name===draft.asioDriver);
  const pairs=(count:number)=>Array.from({length:Math.floor(count/2)},(_,i)=>i*2+1);
  return <SettingsLayer title={title} wide onClose={pending?undefined:onCancel}>
    <div className="flex min-h-0 flex-1 flex-col sm:flex-row">
      <nav aria-label="Settings categories" className="flex shrink-0 gap-1 overflow-x-auto border-b border-neutral-700 p-2 sm:w-44 sm:flex-col sm:border-b-0 sm:border-r">
        {panels.map(panel=><button key={panel.id} type="button" aria-current={active===panel.id?'page':undefined}
          onClick={()=>setActive(panel.id)} className={`whitespace-nowrap rounded-lg px-3 py-2 text-left text-sm ${active===panel.id?'bg-cyan-950 text-cyan-200':'text-neutral-300 hover:bg-neutral-800'}`}>{panel.label}</button>)}
      </nav>
      <div className="min-h-0 min-w-0 flex-1 overflow-y-auto p-4 sm:p-5">
        {notices && <div className="mb-4 space-y-2 text-sm break-words" aria-live="polite">{notices}</div>}
        {children}
        {utilityPanels.map(panel=><section key={panel.id} hidden={active!==panel.id} aria-label={panel.label} className="space-y-4">{panel.content}</section>)}
        <section hidden={active!=='firmware'} aria-label="Firmware & media" className="space-y-3">
    <p className="text-sm text-neutral-300">{hostDriven?'Use your own Roland firmware files. Save your project and export disk writes before reloading the plugin to apply these settings. Audio and MIDI are supplied by the host.':'Use your own Roland firmware files. Applying settings boots the sampler again and replaces unsaved memory. Export disk writes and save your session first.'}</p>
    {([['bootRom','Boot ROM (32KB)'],['systemDisk','System disk (1.44MB)'],['mediaDirectory','Media directory']] as const).map(([key,label])=>
      <label key={key} className="block">{label}<input className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft[key]} disabled={pending}
        onChange={e=>{setDraft({...draft,[key]:e.target.value});setConfirmed(false);}}/></label>)}
    <label className="block">Wave memory<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.waveMemoryMb??32} disabled={pending}
      onChange={e=>{setDraft({...draft,waveMemoryMb:Number(e.target.value) as 8|16|32});setConfirmed(false);}}>
      {[8,16,32].map(n=><option key={n} value={n}>{n} MB</option>)}
    </select></label>
    </section>
    <section hidden={active!=='audio'} aria-label="Audio" className="grid grid-cols-1 gap-3 sm:grid-cols-2">
    {!hostDriven && <label className="block"><input type="checkbox" checked={draft.sound} disabled={pending} onChange={e=>{setDraft({...draft,sound:e.target.checked});setConfirmed(false);}}/> Enable audio output</label>}
    {draft.audioBackend !== undefined && <>
      <label className="block">Audio output backend<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.audioBackend} disabled={pending}
        onChange={e=>{setDraft({...draft,audioBackend:e.target.value as RuntimeConfiguration['audioBackend']});setConfirmed(false);if(e.target.value==='asio')onRefreshAsioDevices?.();}}>
        <option value="auto">Automatic</option><option value="wasapi">WASAPI</option><option value="xaudio2">XAudio2</option><option value="asio">ASIO</option>
      </select></label>
      {(draft.audioBackend==='auto'||draft.audioBackend==='wasapi') && <div>
        <label className="block">Windows output device<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.audioOutputDevice??''} disabled={pending}
          onChange={e=>{setDraft({...draft,audioOutputDevice:e.target.value});setConfirmed(false);}}>
          <option value="">Windows default output</option>
          {draft.audioOutputDevice && !audioOutputDevices.some(d=>d.id===draft.audioOutputDevice) && <option value={draft.audioOutputDevice}>Unavailable selected output</option>}
          {audioOutputDevices.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}
        </select></label>
        <button type="button" disabled={pending} onClick={onRefreshAudioOutputDevices}>Refresh Windows outputs</button>
      </div>}
      {draft.audioBackend==='asio' ? <fieldset className="grid grid-cols-1 gap-3 sm:col-span-2 sm:grid-cols-2 [&>legend]:mb-2 [&>p]:sm:col-span-2">
        <legend>ASIO audio</legend>
        <label className="block">ASIO driver<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.asioDriver??''} disabled={pending}
          onChange={e=>{setDraft({...draft,asioDriver:e.target.value,asioOutputChannel:1,asioInputChannel:0});setConfirmed(false);}}>
          <option value="">Select a driver</option>
          {draft.asioDriver && !driver && <option value={draft.asioDriver}>Unavailable: {draft.asioDriver}</option>}
          {asioDevices.map(d=><option key={d.name} value={d.name}>{d.name}</option>)}
        </select></label>
        <button type="button" disabled={pending} onClick={onRefreshAsioDevices}>Refresh ASIO drivers</button>
        <label className="block">ASIO output pair<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.asioOutputChannel??1} disabled={pending||!driver}
          onChange={e=>{setDraft({...draft,asioOutputChannel:Number(e.target.value)});setConfirmed(false);}}>
          {pairs(driver?.outputs??2).map(n=><option key={n} value={n}>Outputs {n}/{n+1}</option>)}
        </select></label>
        <label className="block">ASIO input pair<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.asioInputChannel??0} disabled={pending||!driver}
          onChange={e=>{setDraft({...draft,asioInputChannel:Number(e.target.value)});setConfirmed(false);}}>
          <option value={0}>No audio input</option>
          {pairs(driver?.inputs??0).map(n=><option key={n} value={n}>Inputs {n}/{n+1}</option>)}
        </select></label>
        <label className="block">ASIO buffer (frames)<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.asioBufferFrames??512} disabled={pending}
          onChange={e=>{setDraft({...draft,asioBufferFrames:Number(e.target.value)});setConfirmed(false);}}>
          {[64,128,256,512,1024,2048].map(n=><option key={n} value={n}>{n}</option>)}
        </select></label>
        <p className="text-sm text-neutral-300">44.1 kHz stereo. The selected driver handles playback and recording. Unsupported driver, channel or buffer settings report an error. Input Level controls recording gain.</p>
      </fieldset> : <>
      <label className="block">Audio buffer target (ms)<input type="number" min={0} max={1000} step="any" className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={Number.isNaN(draft.audioLatencyMs)?'':draft.audioLatencyMs ?? 0} disabled={pending}
        onChange={e=>{setDraft({...draft,audioLatencyMs:e.target.valueAsNumber});setConfirmed(false);}}/></label>
      <p className="text-sm text-neutral-300">0 uses the backend default. Larger buffers may reduce glitches. This target is not measured audible latency. Auto and WASAPI use the selected Windows output device.</p>
      </>}
    </>}
    {draft.recordingDevice !== undefined && draft.audioBackend!=='asio' && <fieldset className="grid grid-cols-1 gap-3 sm:col-span-2 sm:grid-cols-2 [&>legend]:mb-2 [&>p]:sm:col-span-2">
      <legend>Audio recording</legend>
      <label className="block">Recording device<select className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={draft.recordingDevice} disabled={pending}
        onChange={e=>{setDraft({...draft,recordingDevice:e.target.value});setConfirmed(false);}}>
        <option value="">No audio input</option>
        {draft.recordingDevice && !recordingDevices.some(d=>d.id===draft.recordingDevice) && <option value={draft.recordingDevice}>Unavailable: {draft.recordingDevice}</option>}
        {recordingDevices.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}
      </select></label>
      <button type="button" disabled={pending} onClick={onRefreshRecordingDevices}>Refresh recording devices</button>
      <p className="text-sm text-neutral-300">Windows MME · 44.1 kHz stereo. Input Level controls recording gain. Selecting a device enables audio input after restart.</p>
    </fieldset>}
    </section>
      </div>
    </div>
    <footer className="shrink-0 border-t border-neutral-700 bg-neutral-900 px-5 py-3 space-y-2">
    <label className="block text-sm"><input type="checkbox" checked={confirmed} disabled={pending} onChange={e=>setConfirmed(e.target.checked)}/> {hostDriven?'Apply after reloading the plugin in the host':'Replace current sampler memory and restart'}</label>
    <div className="flex gap-3 [&>button]:rounded-lg [&>button]:border [&>button]:border-neutral-600 [&>button]:px-3 [&>button]:py-2 [&>button]:text-sm [&>button:disabled]:opacity-40"><button disabled={pending||!confirmed||!draft.bootRom.trim()||!draft.systemDisk.trim()||!draft.mediaDirectory.trim()||
      (draft.audioBackend==='asio' && !driver) ||
      (draft.audioBackend !== undefined && draft.audioBackend!=='asio' && (!Number.isFinite(draft.audioLatencyMs ?? 0)||(draft.audioLatencyMs ?? 0)<0||(draft.audioLatencyMs ?? 0)>1000))}
      onClick={()=>onApply(draft)}>{pending?(hostDriven?'Saving settings…':'Starting sampler…'):(hostDriven?'Save plugin settings':'Apply settings and start')}</button>
      <button disabled={pending} onClick={onCancel}>Cancel settings</button></div>
    </footer>
  </SettingsLayer>;
}
