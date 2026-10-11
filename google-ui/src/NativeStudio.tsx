import React, {useEffect, useRef, useState} from 'react';
import {BridgeProvider, useSurfaceCanvas, backlightTint} from './bridge/BridgeContext';
import {S760BridgeClient, SurfaceId} from './bridge/S760BridgeClient';

// Real-machine mode deliberately has no simulated screens, disks or sample audio.
export default function NativeStudio() {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [status, setStatus] = useState('Connecting to sampler…');
  const [connectionAttempt, setConnectionAttempt] = useState(0);
  const [restartPrompt, setRestartPrompt] = useState(false);
  const [discard, setDiscard] = useState(false);
  const [savedSession, setSavedSession] = useState(false);
  const [restorePrompt, setRestorePrompt] = useState(false);
  const [media, setMedia] = useState<string[]>([]);
  const [midiDevices, setMidiDevices] = useState<string[]>([]);
  const [disk, setDisk] = useState('');
  const [error, setError] = useState('');
  const [mediaResult, setMediaResult] = useState('');
  const [client] = useState(() => new S760BridgeClient({autoSubscribeInput: false}));
  const [note, setNote] = useState(60);
  const heldNote = useRef<number | null>(null);
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
      const data = JSON.parse(event.data);
      if (data.type === 'SESSION') { setStatus('Connected; checking firmware…'); setMedia(data.media); setMidiDevices(data.midiDevices ?? []); setSavedSession(Boolean(data.savedSession)); if(data.warning) setError(data.warning); }
      if (data.type === 'SESSION_SAVED') {setSavedSession(true);setMediaResult(`Session saved to ${data.path}`);}
      if (data.type === 'SESSION_RESTORED') setMediaResult('Saved session restored.');
      if (data.type === 'FIRMWARE_STATUS') setStatus(data.message);
      if (data.type === 'ERROR') setError(data.message);
      if (data.type === 'MEDIA_EXPORTED') setMediaResult(`Disk exported to ${data.path}`);
      if (data.type === 'MEDIA_INSERTED') setMediaResult(`Disk inserted: ${data.name}`);
    };
    ws.onclose = () => setStatus('Sampler disconnected');
    ws.onerror = () => setError('Cannot connect to sampler');
    return () => { ws.onclose=null; ws.onmessage=null; ws.onerror=null; ws.close(); };
  }, [client, connectionAttempt]);
  useEffect(() => () => client.dispose(), [client]);
  const send = (type: string, payload: Record<string, unknown>) => {
    if (socket?.readyState === WebSocket.OPEN) socket.send(JSON.stringify({type, payload}));
  };
  const press = (id: string, down: boolean) => send(down ? 'BUTTON_PRESS' : 'BUTTON_RELEASE', {id});
  const releaseNote = () => {
    if (heldNote.current !== null) send('NOTE_OFF',{note:heldNote.current,velocity:0});
    heldNote.current = null;
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
    <main className="min-h-screen bg-[#0a0c0f] text-neutral-100 p-6 flex flex-col items-center gap-5">
      <header className="w-full max-w-5xl flex justify-between"><h1>Roland S-760 · Native Studio</h1><span role="status">{status}</span></header>
      {error && <div role="alert" className="text-amber-300">{error}<button onClick={() => setError('')} className="ml-4">Dismiss</button></div>}
      {mediaResult && <p aria-live="polite" className="text-sm break-all max-w-4xl">{mediaResult}</p>}
      <section aria-label="Sampler recovery" className="flex gap-3 items-center flex-wrap max-w-4xl">
        <button onClick={() => {releaseNote();setMediaResult('');send('SAVE_SESSION',{});}}>Save session</button>
        <button disabled={!savedSession} onClick={() => {setDiscard(false);setRestorePrompt(true);setRestartPrompt(false);}}>Restore saved session</button>
        {restorePrompt && <div role="dialog" aria-label="Restore session confirmation">
          <p>Restore replaces sampler memory with the last saved session. Changes made since that save will be lost. Export disk writes first and disconnect physical MIDI.</p>
          <label><input type="checkbox" checked={discard} onChange={e => setDiscard(e.target.checked)}/>Replace current sampler memory</label>
          <button disabled={!discard} onClick={() => {releaseNote();setMediaResult('');send('RESTORE_SESSION',{discard:true});setRestorePrompt(false);}}>Confirm restore</button>
          <button onClick={() => setRestorePrompt(false)}>Cancel</button>
        </div>}
        <button onClick={() => {setError('');setStatus('Reconnecting…');setConnectionAttempt(n => n+1);}}>Reconnect display</button>
        <button onClick={() => {setDiscard(false);setRestartPrompt(true);setRestorePrompt(false);}}>Restart sampler</button>
        {restartPrompt && <div role="dialog" aria-label="Restart sampler confirmation">
          <p>Restart boots the OS again and loses unsaved sampler memory. Export disk writes first. Restore saved session can recover your last checkpoint; changes since that save will be lost.</p>
          <label><input type="checkbox" checked={discard} onChange={e => setDiscard(e.target.checked)}/>Discard unsaved sampler memory</label>
          <button disabled={!discard} onClick={() => {releaseNote();send('RESTART_RUNTIME',{discard:true});setRestartPrompt(false);setStatus('Restart requested…');}}>Confirm restart</button>
          <button onClick={() => setRestartPrompt(false)}>Cancel</button>
        </div>}
      </section>
      <NativeDisplays send={send}/>
      <section aria-label="Front panel" className="flex flex-wrap justify-center gap-2 max-w-4xl">
        {['COMMAND','MODE','EXIT','UP','DOWN','LEFT','RIGHT','F1','F2','F3','S1','S2','SHIFT'].map(id =>
          <button key={id} className="bg-neutral-800 border border-neutral-600 rounded px-3 py-2"
            onPointerDown={e => { e.currentTarget.setPointerCapture(e.pointerId); press(id,true); }}
            onPointerUp={() => press(id,false)} onPointerCancel={() => press(id,false)}>{id}</button>)}
      </section>
      <section aria-label="Media and MIDI" className="flex flex-wrap gap-3 items-center">
        <label>MIDI input <select aria-label="MIDI input" defaultValue="" onChange={e => send('MIDI_DEVICE',{name:e.target.value})} className="bg-neutral-800 p-2">
          <option value="">Audition only</option>{midiDevices.map(name => <option key={name}>{name}</option>)}
        </select></label>
        <label>Sample disk <select aria-label="Sample disk" value={disk} onChange={e => setDisk(e.target.value)} className="bg-neutral-800 p-2">
          <option value="">Select a disk…</option>{media.map(name => <option key={name}>{name}</option>)}
        </select></label>
        <button disabled={!disk} onClick={() => {setMediaResult('');send('MOUNT_DISK',{diskPath:disk});}}>Insert disk</button>
        <button onClick={() => {setMediaResult('');send('EXPORT_DISK',{});}}>Export disk</button>
        <label>MIDI note <input aria-label="MIDI note" type="number" min="0" max="127" value={note}
          onChange={e => setNote(Math.max(0,Math.min(127,Number(e.target.value))))} className="w-16 bg-neutral-800 p-2"/></label>
        <button onPointerDown={e => {e.currentTarget.setPointerCapture(e.pointerId);heldNote.current=note;send('NOTE_ON',{note,velocity:100});}}
          onPointerUp={releaseNote} onPointerCancel={releaseNote}>Hold to audition</button>
      </section>
      <p className="text-sm text-neutral-400">Use the sampler’s Disk / Load or Disk / Save screen. After Save finishes, Export disk writes a new image in the session’s exports folder. Original library images are preserved. Audio comes from MAME.</p>
    </main>
  </BridgeProvider>;
}

function NativeDisplays({send}: {send: (type: string, payload: Record<string, unknown>) => void}) {
  const crt = useSurfaceCanvas(SurfaceId.CRT);
  const lcd = useSurfaceCanvas(SurfaceId.LCD,{tint:backlightTint('emerald')});
  const pending = useRef<{x:number;y:number} | null>(null);
  useEffect(() => {
    const timer = window.setInterval(() => {
      if (pending.current) {send('MOUSE_MOVE',pending.current);pending.current=null;}
    }, 50);
    return () => window.clearInterval(timer);
  }, [send]);
  return <>
    <div className="bg-neutral-800 border-8 border-neutral-700 rounded-2xl p-4 shadow-xl">
      <div className="text-xs text-neutral-400 mb-2">ROLAND OP-760</div>
      <canvas ref={crt} width={640} height={480} aria-label="Native CRT" className="bg-black cursor-crosshair max-w-full" style={{imageRendering:'pixelated'}}
        onPointerMove={e => {const r=e.currentTarget.getBoundingClientRect();pending.current={x:Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)),y:Math.max(0,Math.min(1,(e.clientY-r.top)/r.height))};}}
        onPointerDown={e => {e.currentTarget.setPointerCapture(e.pointerId);if(pending.current){send('MOUSE_MOVE',pending.current);pending.current=null;}send('MOUSE_BUTTON',{button:e.button,down:true});}}
        onPointerUp={e => send('MOUSE_BUTTON',{button:e.button,down:false})}
        onPointerCancel={() => {send('MOUSE_BUTTON',{button:0,down:false});send('MOUSE_BUTTON',{button:2,down:false});}}
        onContextMenu={e => e.preventDefault()}/>
    </div>
    <div className="bg-neutral-800 p-4 rounded border border-neutral-600"><canvas ref={lcd} width={160} height={64} aria-label="Native LCD" style={{width:320,height:128,imageRendering:'pixelated',background:'#132c10'}}/></div>
  </>;
}
