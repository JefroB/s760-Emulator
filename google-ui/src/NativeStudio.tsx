import {Settings2} from 'lucide-react';
import {SettingsLayer} from './components/SettingsLayer';
import {OP760Housing} from './components/OP760Housing';
import React, {useCallback, useEffect, useRef, useState} from 'react';
import {BridgeProvider, useSurfaceCanvas} from './bridge/BridgeContext';
import {S760BridgeClient, SurfaceId} from './bridge/S760BridgeClient';

import {NativeRack,NativeRackStack} from './components/NativeRack';
import {useNativeKeyboard} from './nativeKeyboard';
import {RuntimeSettings, type RuntimeConfiguration, type AsioDevice} from './components/RuntimeSettings';
import {StandaloneKeyboard} from './components/StandaloneKeyboard';

// Real-machine mode deliberately has no simulated screens, disks or sample audio.
export default function NativeStudio() {
  const [configuration,setConfiguration]=useState<RuntimeConfiguration | null>(null);
  const [settingsOpen,setSettingsOpen]=useState(false);
  const [needsConfiguration,setNeedsConfiguration]=useState(false);
  const [settingsPending,setSettingsPending]=useState(false);
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState('Connecting to sampler…');
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  const [restartPrompt, setRestartPrompt] = useState(false);
  const [discard, setDiscard] = useState(false);
  const [savedSession, setSavedSession] = useState(false);
  const [restorePrompt, setRestorePrompt] = useState(false);
  const [recovery,setRecovery]=useState<{available:boolean;pending:boolean;savedAt:number|null;message:string}|null>(null);
  const [recoveryAction,setRecoveryAction]=useState<'restore'|'start'|'quit'|null>(null);
  const [media, setMedia] = useState<string[]>([]);
  const [midiDevices, setMidiDevices] = useState<string[]>([]);
  const [midiInput,setMidiInput]=useState('');
  const [showKeyboard,setShowKeyboard]=useState(false);
  const [preferencePending,setPreferencePending]=useState(false);
  const [keyboardEpoch,setKeyboardEpoch]=useState(0);
  const [disk, setDisk] = useState('');
  const [mountedDisk, setMountedDisk] = useState('');
  const [mediaStatus,setMediaStatus]=useState<{inserted:boolean;writeProtected:boolean} | null>(null);
  const [protectionPending,setProtectionPending]=useState(false);
  const [error, setError] = useState('');
  const [mediaResult, setMediaResult] = useState('');
  const [client] = useState(() => new S760BridgeClient({autoSubscribeInput: false}));
  const [outputLevel,setOutputLevel]=useState(100);
  const [inputLevel,setInputLevel]=useState(100);
  const [recordingDevices,setRecordingDevices]=useState<{id:string;name:string}[]>([]);
  const [asioDevices,setAsioDevices]=useState<AsioDevice[]>([]);
  const [audioOutputDevices,setAudioOutputDevices]=useState<{id:string;name:string}[]>([]);
  const [recordingStatus,setRecordingStatus]=useState<{state:string;message:string;discardedFrames?:number;nativeUnderruns?:number;discontinuities?:number;backend?:string;outputUnderruns?:number;outputDiscardedFrames?:number;driverStatusFlags?:number;driverInputLatencyMs?:number;driverOutputLatencyMs?:number;outputQueuedMs?:number;outputTargetMs?:number}>({state:'disabled',message:'No recording device selected.'});
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    const port = Number(query.get('port'));
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      setError('Invalid sampler connection'); return;
    }
    const ws = new WebSocket(`ws://127.0.0.1:${port}/?token=${encodeURIComponent(query.get('token') ?? '')}`);
    ws.binaryType = 'arraybuffer';
    setSocket(ws);
    ws.onmessage = event => {
      if (event.data instanceof ArrayBuffer) { client.handleBinaryMessage(event.data); return; }
      let data;
      try {
        data = JSON.parse(event.data);
        if (!data || typeof data !== 'object' || typeof data.type !== 'string') throw new Error();
        if (data.type === 'SESSION' && (!Array.isArray(data.media) || !data.media.every((name: unknown)=>typeof name === 'string'))) throw new Error();
        if (['MEDIA_STATUS','MEDIA_PROTECTION'].includes(data.type) && (!data.mediaStatus || typeof data.mediaStatus.inserted!=='boolean' || typeof data.mediaStatus.writeProtected!=='boolean')) throw new Error();
        if (data.recovery && (typeof data.recovery.available!=='boolean' || typeof data.recovery.pending!=='boolean' || typeof data.recovery.message!=='string' || (data.recovery.savedAt!==null && (typeof data.recovery.savedAt!=='number' || !Number.isFinite(data.recovery.savedAt))))) throw new Error();
      } catch {setError('Invalid sampler response; reconnect the display if the problem persists.');setProtectionPending(false);return;}
      if (data.type === 'SESSION') { setStatus('Connected; checking firmware…'); setMedia(data.media); setMountedDisk(data.mountedDisk ?? ''); setMidiDevices(data.midiDevices ?? []); setSavedSession(Boolean(data.savedSession)); if(data.warning) setError(data.warning); }
      if (data.type === 'SESSION') {
        setShowKeyboard(data.preferences?.showKeyboard === true);
        setRecordingDevices(data.recordingDevices??[]);
        setAsioDevices(data.asioDevices??[]);
        setAudioOutputDevices(data.audioOutputDevices??[]);
        ws.send(JSON.stringify({type:'AUDIO_OUTPUT_DEVICES',payload:{}}));
        if(data.configuration?.audioBackend==='asio')ws.send(JSON.stringify({type:'ASIO_DEVICES',payload:{}}));
        setMidiInput(typeof data.midiInput==='string'?data.midiInput:'');
        setMediaStatus(null);
        setProtectionPending(false);
        if(!data.needsConfiguration) ws.send(JSON.stringify({type:'MEDIA_STATUS',payload:{}}));
        if(data.configuration) setConfiguration(data.configuration);
        setNeedsConfiguration(Boolean(data.needsConfiguration));
        if(data.needsConfiguration) setSettingsOpen(true);
      }
      if (data.type === 'CONFIGURATION_APPLIED') {
        setMidiInput('');
        setMediaStatus(null);ws.send(JSON.stringify({type:'MEDIA_STATUS',payload:{}}));
        setConfiguration(data.configuration);setMedia(data.media);setSettingsPending(false);setSettingsOpen(false);setNeedsConfiguration(false);
        setMountedDisk('');setDisk('');setError('');setMediaResult('Runtime settings saved; booting firmware.');
      }
      if (data.type === 'SESSION_SAVED') {setSavedSession(true);setMediaResult(`Session saved to ${data.path}`);}
      if(data.recovery) setRecovery(data.recovery);
      if(data.type==='RECOVERY_RESTORED') {setMediaResult('Recovery restored.');setMountedDisk('');setError('');setMediaStatus(null);ws.send(JSON.stringify({type:'MEDIA_STATUS',payload:{}}));}
      if (data.type === 'SESSION_RESTORED') {setMediaResult('Saved session restored.');setMountedDisk('');setError('');setMediaStatus(null);ws.send(JSON.stringify({type:'MEDIA_STATUS',payload:{}}));}
      if (data.type === 'FIRMWARE_STATUS') {setStatus(data.message);if(typeof data.outputLevel==='number')setOutputLevel(data.outputLevel);if(typeof data.inputLevel==='number')setInputLevel(data.inputLevel);if(typeof data.midiInput==='string')setMidiInput(data.midiInput);}
      if(data.type==='RECORDING_DEVICES')setRecordingDevices(data.recordingDevices??[]);
      if(data.type==='ASIO_DEVICES')setAsioDevices(data.asioDevices??[]);
      if(data.type==='AUDIO_OUTPUT_DEVICES')setAudioOutputDevices(data.audioOutputDevices??[]);
      if(data.type==='AUDIO_REOPENED'){setRecordingStatus(data.recordingStatus);setSettingsPending(false);setError('');}
      if(data.recordingStatus){setRecordingStatus(data.recordingStatus);if(data.recordingStatus.state==='failed')setError(data.recordingStatus.message);}
      if (data.type === 'ERROR') {setError(data.message);setSettingsPending(false);setProtectionPending(false);}
      if(data.type==='ERROR') setPreferencePending(false);
      if(data.type==='MIDI_DEVICE_SELECTED' && typeof data.name==='string') setMidiInput(data.name);
      if(data.type==='STANDALONE_PREFERENCES' && typeof data.preferences?.showKeyboard==='boolean') {
        setShowKeyboard(data.preferences.showKeyboard);setPreferencePending(false);
      }
      if (data.mediaStatus && typeof data.mediaStatus.inserted==='boolean' && typeof data.mediaStatus.writeProtected==='boolean') setMediaStatus(data.mediaStatus);
      if (data.type === 'MEDIA_PROTECTION') {setProtectionPending(false);setMediaResult(data.mediaStatus.writeProtected?'Disk write protection enabled.':'Disk write protection disabled.');}
      if (data.type === 'MEDIA_EXPORTED') setMediaResult(`Disk exported to ${data.path}`);
      if (data.type === 'MEDIA_INSERTED') {setMediaResult(`Disk inserted: ${data.name}`);setMountedDisk(data.name);}
      if (data.type === 'MEDIA_EJECTED') {setMediaResult('Disk ejected.');setMountedDisk('');setError('');setMediaStatus({inserted:false,writeProtected:false});}
    };
    ws.onclose = () => {setStatus('Sampler disconnected');setSettingsPending(false);setMediaStatus(null);setProtectionPending(false);};
    ws.onerror = () => setError('Cannot connect to sampler');
    return () => { ws.onclose=null; ws.onmessage=null; ws.onerror=null; ws.close(); };
  }, [client, connectionAttempt]);
  useEffect(() => () => client.dispose(), [client]);
  useEffect(()=>{if(error)setSettingsOpen(true);},[error]);
  const send = useCallback((type: string, payload: Record<string, unknown>) => {
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({type, payload}));
  }, [socket]);
  useNativeKeyboard(send);
  const press = (id: string, down: boolean) => send(down ? 'BUTTON_PRESS' : 'BUTTON_RELEASE', {id});
  const releaseNote = () => {
    setKeyboardEpoch(n=>n+1);
  };
  useEffect(() => {
    const release = () => {
      releaseNote();
      for (const id of ['COMMAND','MODE','EXIT','UP','DOWN','LEFT','RIGHT','F1','F2','F3','S1','S2','SHIFT']) press(id,false);
      send('MOUSE_BUTTON',{button:0,down:false});send('MOUSE_BUTTON',{button:2,down:false});
    };
    window.addEventListener('blur',release);
    return () => window.removeEventListener('blur',release);
  }, [socket]);
  return <BridgeProvider client={client} autoConnect={false}>
    <main className="bg-[#0a0c0f] text-neutral-100 p-6 flex flex-col items-center gap-5">
      <span role="status" className="sr-only">{status}</span>
      {configuration && <button type="button" aria-label="Configuration" title="Configuration" className="fixed top-4 right-4 z-20 p-2 rounded border border-neutral-700 bg-neutral-900 text-neutral-400 hover:text-white" onClick={()=>{releaseNote();setSettingsOpen(true);}}><Settings2 size={18}/></button>}
      {configuration && settingsOpen && <RuntimeSettings title="Standalone configuration" initialPanel={needsConfiguration?'firmware':undefined} configuration={configuration} pending={settingsPending} recordingDevices={recordingDevices} onRefreshRecordingDevices={()=>send('RECORDING_DEVICES',{})} asioDevices={asioDevices} onRefreshAsioDevices={()=>send('ASIO_DEVICES',{})} audioOutputDevices={audioOutputDevices} onRefreshAudioOutputDevices={()=>send('AUDIO_OUTPUT_DEVICES',{})}
        onCancel={()=>setSettingsOpen(false)} onApply={value=>{
          if(socket?.readyState!==WebSocket.OPEN){setError('Sampler disconnected. Reconnect display before applying settings.');return;}
          releaseNote();setError('');setSettingsPending(true);send('CONFIGURE_RUNTIME',{...value,discard:true});
        }} notices={<>
      <p aria-label="Recording input status" className="text-sm text-neutral-300">{recordingStatus.message}{(recordingStatus.discardedFrames??0)>0?` Input frames discarded: ${recordingStatus.discardedFrames}.`:''}{(recordingStatus.nativeUnderruns??0)>0?` Recording underrun frames: ${recordingStatus.nativeUnderruns}.`:''}{(recordingStatus.discontinuities??0)>0?` Capture restarts: ${recordingStatus.discontinuities}.`:''}</p>
      {recordingStatus.backend==='asio' && <p aria-label="ASIO audio status" className="text-sm text-neutral-300">Driver-reported latency: input {(recordingStatus.driverInputLatencyMs??0).toFixed(1)} ms, output {(recordingStatus.driverOutputLatencyMs??0).toFixed(1)} ms. Queued output: {(recordingStatus.outputQueuedMs??0).toFixed(1)} ms; transport target: {(recordingStatus.outputTargetMs??0).toFixed(1)} ms. Output underrun frames: {recordingStatus.outputUnderruns??0}; output discarded frames: {recordingStatus.outputDiscardedFrames??0}; driver flags: {recordingStatus.driverStatusFlags??0}. Driver latency excludes transport buffering and is not measured round-trip latency.</p>}
      {recordingStatus.state==='failed' && <button type="button" disabled={settingsPending} onClick={()=>{setSettingsPending(true);send('REOPEN_AUDIO',{});}}>Reopen audio</button>}
      {error && <div role="alert" className="text-amber-300">{error}<button type="button" onClick={() => setError('')} className="ml-4">Dismiss</button></div>}
      {mediaResult && <p aria-live="polite" className="text-sm break-all max-w-4xl">{mediaResult}</p>}
</>} utilityPanels={[
{id:'session',label:'Session & disks',content:<>
          <fieldset className="space-y-3 border-t border-neutral-600 pt-4"><legend>Session and media</legend>
      <section aria-label="Sampler recovery" className="grid grid-cols-1 gap-2 sm:grid-cols-2 [&>p]:sm:col-span-2 [&>button]:rounded-lg [&>button]:border [&>button]:border-neutral-600 [&>button]:px-3 [&>button]:py-2 [&>button]:text-left [&>button]:text-sm [&>button:disabled]:opacity-40">
        {recovery && <p aria-live="polite" className="w-full text-sm" aria-label="Automatic recovery status">{recovery.message}{recovery.savedAt!==null && ` Last recovery: ${new Date(recovery.savedAt*1000).toLocaleString()}.`}</p>}
        <button type="button" onClick={()=>{releaseNote();send('SAVE_RECOVERY',{});}}>Save recovery now</button>
        <button type="button" disabled={!recovery?.available} onClick={()=>{setDiscard(false);setRecoveryAction('restore');setRestorePrompt(false);setRestartPrompt(false);}}>Restore recovery</button>
        {recovery?.pending && <button type="button" onClick={()=>{setDiscard(false);setRecoveryAction('start');}}>Start new recovery history</button>}
        <button type="button" onClick={()=>{setDiscard(false);setRecoveryAction('quit');}}>Quit without recovery</button>
        {recoveryAction && <SettingsLayer title="Recovery confirmation" onClose={()=>setRecoveryAction(null)}>
          <p>{recoveryAction==='restore'?'Restore replaces sampler memory with the last automatic recovery. Later changes will be lost. Export current disk writes and disconnect physical MIDI first.':recoveryAction==='quit'?'Quit without saving a recovery checkpoint. Changes after the last successful recovery, including unexported disk writes, will be lost. Existing saved files are retained.':'Start a new recovery history replaces the existing recovery with the current sampler. Save the old recovery separately if you need it.'}</p>
          <label><input type="checkbox" checked={discard} onChange={e=>setDiscard(e.target.checked)}/>Confirm recovery replacement</label>
          <button type="button" disabled={!discard} onClick={()=>{releaseNote();send(recoveryAction==='restore'?'RESTORE_RECOVERY':recoveryAction==='quit'?'QUIT_WITHOUT_RECOVERY':'START_RECOVERY',{discard:true});setRecoveryAction(null);}}>Confirm recovery</button>
          <button type="button" onClick={()=>setRecoveryAction(null)}>Cancel</button>
        </SettingsLayer>}
        <button type="button" onClick={() => {releaseNote();setMediaResult('');send('SAVE_SESSION',{});}}>Save session</button>
        <button type="button" disabled={!savedSession} onClick={() => {setDiscard(false);setRestorePrompt(true);setRestartPrompt(false);}}>Restore saved session</button>
        {restorePrompt && <SettingsLayer title="Restore session confirmation" onClose={()=>setRestorePrompt(false)}>
          <p>Restore replaces sampler memory with the last saved session. Changes made since that save will be lost. Export disk writes first and disconnect physical MIDI.</p>
          <label><input type="checkbox" checked={discard} onChange={e => setDiscard(e.target.checked)}/>Replace current sampler memory</label>
          <button type="button" disabled={!discard} onClick={() => {releaseNote();setMediaResult('');send('RESTORE_SESSION',{discard:true});setRestorePrompt(false);}}>Confirm restore</button>
          <button type="button" onClick={() => setRestorePrompt(false)}>Cancel</button>
        </SettingsLayer>}
        <button type="button" onClick={() => {setError('');setStatus('Reconnecting…');setConnectionAttempt(n => n+1);}}>Reconnect display</button>
        <button type="button" onClick={() => {setDiscard(false);setRestartPrompt(true);setRestorePrompt(false);}}>Restart sampler</button>
        {restartPrompt && <SettingsLayer title="Restart sampler confirmation" onClose={()=>setRestartPrompt(false)}>
          <p>Restart boots the OS again and loses unsaved sampler memory. Export disk writes first. Restore saved session can recover your last checkpoint; changes since that save will be lost.</p>
          <label><input type="checkbox" checked={discard} onChange={e => setDiscard(e.target.checked)}/>Discard unsaved sampler memory</label>
          <button type="button" disabled={!discard} onClick={() => {releaseNote();send('RESTART_RUNTIME',{discard:true});setMediaStatus(null);setMountedDisk('');setRestartPrompt(false);setStatus('Restart requested…');send('MEDIA_STATUS',{});}}>Confirm restart</button>
          <button type="button" onClick={() => setRestartPrompt(false)}>Cancel</button>
        </SettingsLayer>}
      </section>
      <section aria-label="Disk actions" className="flex flex-wrap gap-3 items-center [&>button]:rounded-lg [&>button]:border [&>button]:border-neutral-600 [&>button]:px-3 [&>button]:py-2 [&>button]:text-sm">
        <button type="button" onClick={() => {setMediaResult('');send('EXPORT_DISK',{});}}>Export disk</button>
        <button type="button" onClick={() => {setMediaResult('');send('EJECT_DISK',{});}}>Eject disk</button>
        <label><input type="checkbox" aria-label="Write protect disk" checked={mediaStatus?.writeProtected ?? false}
          disabled={!mediaStatus?.inserted || protectionPending} onChange={e=>{setProtectionPending(true);send('MEDIA_WRITE_PROTECT',{enabled:e.target.checked});}}/>Write protect disk</label>
      </section>
          </fieldset>
</>},
{id:'midi',label:'MIDI & display',content:<>
          <fieldset className="space-y-3 border-b border-neutral-600 pb-4" disabled={settingsPending}>
            <legend className="font-medium">MIDI and display</legend>
            <label className="block">MIDI input <select aria-label="MIDI input" value={midiInput}
              onChange={e=>{releaseNote();send('MIDI_DEVICE',{name:e.target.value});}} className="bg-neutral-800 p-2">
              <option value="">On-screen keyboard only</option>{midiDevices.map(name=><option key={name}>{name}</option>)}
            </select></label>
            <label className="block"><input type="checkbox" checked={showKeyboard} disabled={preferencePending}
              onChange={e=>{setPreferencePending(true);send('SET_STANDALONE_PREFERENCES',{showKeyboard:e.target.checked});}}/>Show on-screen keyboard</label>
            <p className="text-sm text-neutral-300">MIDI selection and keyboard visibility apply immediately. Audio and firmware changes below require a sampler restart.</p>
          </fieldset>
</>},
]} />}
      <div className="contents" inert={settingsOpen}>
      <NativeDisplays send={send}/>
      <NativeRackStack>
          <NativeRack send={send} mountedDisk={mountedDisk} outputLevel={outputLevel} inputLevel={inputLevel} connected={socket?.readyState===WebSocket.OPEN} media={media} selectedDisk={disk} onSelectDisk={setDisk}/>
          {showKeyboard && !settingsOpen && <StandaloneKeyboard key={keyboardEpoch} send={send} connected={socket?.readyState===WebSocket.OPEN}/>}
      </NativeRackStack>
      </div>
    </main>
  </BridgeProvider>;
}

function NativeDisplays({send}: {send: (type: string, payload: Record<string, unknown>) => void}) {
  const crt = useSurfaceCanvas(SurfaceId.CRT);
  const pending = useRef<{x:number;y:number} | null>(null);
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (pending.current) {send('MOUSE_MOVE',pending.current);pending.current=null;}
    }, 50);
    return () => window.clearInterval(timer);
  }, [send]);
  return <>
    <OP760Housing>
      <canvas ref={crt} width={640} height={480} aria-label="Native CRT" className="bg-black cursor-crosshair max-w-full" style={{imageRendering:'pixelated',height:'120%'}}
        onPointerMove={e => {const r=e.currentTarget.getBoundingClientRect();pending.current={x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))};}}
        onPointerDown={e => {if(![0,2].includes(e.button))return;e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);const r=e.currentTarget.getBoundingClientRect();send('MOUSE_MOVE',{x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))});pending.current=null;send('MOUSE_BUTTON',{button:e.button,down:true});}}
        onPointerUp={e => send('MOUSE_BUTTON',{button:e.button,down:false})}
        onPointerCancel={() => {send('MOUSE_BUTTON',{button:0,down:false});send('MOUSE_BUTTON',{button:2,down:false});}}
        onLostPointerCapture={() => {send('MOUSE_BUTTON',{button:0,down:false});send('MOUSE_BUTTON',{button:2,down:false});}}
        onContextMenu={e => e.preventDefault()}/>
    </OP760Housing>
  </>;
}
