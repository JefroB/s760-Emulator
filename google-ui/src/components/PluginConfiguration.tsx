import {useEffect,useRef,useState} from 'react';
import {Settings2} from 'lucide-react';
import {useBridgeClient,useBridgeTelemetry} from '../bridge/BridgeContext';
import {RuntimeSettings} from './RuntimeSettings';

export function PluginConfiguration() {
  const client=useBridgeClient(),configuration=useBridgeTelemetry()?.pluginConfiguration;
  const [open,setOpen]=useState(false),[pending,setPending]=useState(false),[epoch,setEpoch]=useState(0);
  const sentRevision=useRef(-1);
  const [root,setRoot]=useState(''),[stateRoot,setStateRoot]=useState('');
  useEffect(()=>{if(configuration?.needsConfiguration)setOpen(true);},[configuration?.needsConfiguration]);
  useEffect(()=>{
    if(configuration && configuration.revision!==sentRevision.current)setPending(false);
  },[configuration?.revision]);
  useEffect(()=>{
    if(open && configuration){setRoot(configuration.root);setStateRoot(configuration.stateRoot);}
  },[open]);
  if(!configuration)return null;
  return <>
    <button type="button" aria-label="Plugin configuration" title="Plugin configuration" className="fixed top-3 right-3 z-40 p-2 rounded border border-neutral-700 bg-neutral-900 text-neutral-300" onClick={()=>{setEpoch(n=>n+1);setOpen(true);}}><Settings2 size={18}/></button>
    {!open && configuration.needsConfiguration && <p role="alert" className="fixed top-14 right-3 z-40 max-w-md bg-neutral-900 text-amber-300 p-3">Sampler startup failed. Open Plugin configuration to correct settings and reload.</p>}
    {open && <div className="fixed inset-0 z-50 overflow-auto bg-black/80 flex items-start justify-center p-5 text-neutral-100">
      <RuntimeSettings key={epoch} title="Plugin configuration" hostDriven configuration={{bootRom:configuration.bootRom,systemDisk:configuration.systemDisk,mediaDirectory:configuration.mediaDirectory,sound:true,waveMemoryMb:configuration.waveMemoryMb??32}} pending={pending}
        onCancel={()=>setOpen(false)} onApply={draft=>{
          sentRevision.current=configuration.revision;setPending(true);
          client?.send({type:'CONFIGURE_PLUGIN',payload:{root,stateRoot,bootRom:draft.bootRom,systemDisk:draft.systemDisk,mediaDirectory:draft.mediaDirectory,waveMemoryMb:draft.waveMemoryMb??32,confirmReload:true}});
        }}>
        {configuration.startupError && <p role="alert" className="text-amber-300">Startup: {configuration.startupError}</p>}
        {configuration.error && <p role="alert" className="text-amber-300">{configuration.error}</p>}
        {configuration.saved && <p role="status" className="text-emerald-300">Settings saved. Reload the plugin in your host to apply.</p>}
        <label className="block">S-760 installation directory<input className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={root} disabled={pending} onChange={e=>setRoot(e.target.value)}/></label>
        <label className="block">Runtime state directory<input className="block w-full bg-neutral-800 border border-neutral-600 rounded p-2" value={stateRoot} disabled={pending} onChange={e=>setStateRoot(e.target.value)}/></label>
      </RuntimeSettings>
    </div>}
  </>;
}
