import {act, fireEvent, render, screen} from '@testing-library/react';
import {afterEach, beforeEach, describe, expect, it, vi} from 'vitest';
import NativeStudio from './NativeStudio';

class Socket {
  static OPEN = 1;
  static current: Socket;
  readyState = 1;
  sent: any[] = [];
  onmessage?: (event: {data: string}) => void;
  close = vi.fn();
  constructor() { Socket.current=this; }
  send(raw: string) {this.sent.push(JSON.parse(raw));}
}
beforeEach(() => {
  window.history.replaceState({},'', '/?native=1&port=12345&token=test');
  vi.stubGlobal('WebSocket',Socket);
  HTMLButtonElement.prototype.setPointerCapture = vi.fn();
  vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue(null);
});
afterEach(() => {vi.restoreAllMocks();vi.unstubAllGlobals();});

function renderStudio(settings=true){
  const view=render(<NativeStudio/>);
  act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[],configuration:{bootRom:'boot',systemDisk:'sys',mediaDirectory:'media',sound:false}})}));
  if(settings)fireEvent.click(screen.getByRole('button',{name:'Configuration'}));
  Socket.current.sent=[];return view;
}

describe('NativeStudio real-machine controls', () => {
  it('offers visible quit with acknowledged recovery and explicit discard',()=>{
    renderStudio(false);
    fireEvent.click(screen.getByRole('button',{name:'Quit application'}));
    expect(screen.getByRole('dialog',{name:'Quit S760Studio'})).toBeInTheDocument();
    expect(screen.getByRole('button',{name:'Quit without saving'})).toBeDisabled();
    fireEvent.click(screen.getByRole('button',{name:'Save recovery and quit'}));
    expect(Socket.current.sent.at(-1)).toEqual({type:'QUIT_APPLICATION',payload:{}});
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'QUIT_BLOCKED',message:'Existing recovery retained'})}));
    expect(screen.getByRole('alert')).toHaveTextContent('Existing recovery retained');
    fireEvent.click(screen.getByLabelText('I understand changes since the last save or recovery will be lost.'));
    fireEvent.click(screen.getByRole('button',{name:'Quit without saving'}));
    expect(Socket.current.sent.at(-1)).toEqual({type:'QUIT_WITHOUT_RECOVERY',payload:{discard:true}});
  });
  it('opens the same quit dialog for a desktop close request',()=>{
    renderStudio(false);
    const event=new Event('s760-request-quit',{cancelable:true});
    act(()=>window.dispatchEvent(event));
    expect(event.defaultPrevented).toBe(true);
    expect(screen.getByRole('dialog',{name:'Quit S760Studio'})).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Keep working'}));
    expect(screen.queryByRole('dialog',{name:'Quit S760Studio'})).not.toBeInTheDocument();
  });
  it('reopens failed audio only on request and waits for acknowledgement',()=>{
    renderStudio();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'FIRMWARE_STATUS',message:'Ready',recordingStatus:{state:'failed',message:'Sampler paused; reconnect audio.'}})}));
    fireEvent.click(screen.getByRole('button',{name:'Reopen audio'}));
    expect(Socket.current.sent.at(-1)).toEqual({type:'REOPEN_AUDIO',payload:{}});
    expect(screen.getByRole('button',{name:'Reopen audio'})).toBeDisabled();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'ERROR',message:'Device still unavailable'})}));
    expect(screen.getByRole('button',{name:'Reopen audio'})).toBeEnabled();
    fireEvent.click(screen.getByRole('button',{name:'Reopen audio'}));
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'AUDIO_REOPENED',recordingStatus:{state:'active',message:'Audio restored.'}})}));
    expect(screen.queryByRole('button',{name:'Reopen audio'})).not.toBeInTheDocument();
    expect(screen.getByLabelText('Recording input status')).toHaveTextContent('Audio restored.');
  });
  it('routes Input Level to native gain and displays only acknowledged values',()=>{
    renderStudio(false);
    const knob=screen.getByRole('button',{name:'INPUT LEVEL knob'});
    expect(knob).toBeEnabled();
    expect(knob).toHaveAttribute('title','Recording input gain: 100%');
    fireEvent.keyDown(knob,{key:'ArrowDown'});
    expect(Socket.current.sent.at(-1)).toEqual({type:'DIAL_DELTA',payload:{id:'INPUT',delta:-1}});
    expect(knob).toHaveAttribute('title','Recording input gain: 100%');
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'FIRMWARE_STATUS',message:'Ready',inputLevel:50})}));
    expect(knob).toHaveAttribute('title','Recording input gain: 50%');
  });
  it('restores shared Gotek browsing and Shift function controls without optimistic insertion',()=>{
    vi.useFakeTimers();
    try {
      renderStudio(false);
      act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:['First.img','Second.img']})}));
      fireEvent.click(screen.getByRole('button',{name:'Gotek Down'}));
      expect(screen.getByLabelText('Selected disk image')).toHaveTextContent('Second.img');
      expect(screen.getByLabelText('Drive display')).toHaveTextContent('No sample disk inserted');
      fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
      expect(Socket.current.sent.at(-1)).toEqual({type:'MOUNT_DISK',payload:{diskPath:'Second.img'}});
      expect(screen.getByLabelText('Drive display')).toHaveTextContent('No sample disk inserted');
      fireEvent.keyDown(screen.getByRole('button',{name:/^F4$/}),{key:'Enter'});
      expect(Socket.current.sent.slice(-2)).toEqual([{type:'BUTTON_PRESS',payload:{id:'SHIFT'}},{type:'BUTTON_PRESS',payload:{id:'F1'}}]);
      fireEvent.keyUp(screen.getByRole('button',{name:/^F4$/}),{key:'Enter'});
      act(()=>vi.advanceTimersByTime(120));
      expect(Socket.current.sent.slice(-2)).toEqual([{type:'BUTTON_RELEASE',payload:{id:'F1'}},{type:'BUTTON_RELEASE',payload:{id:'SHIFT'}}]);
    } finally {vi.useRealTimers();}
  });
  it('offers separate recovery with explicit replacement and preserves manual-save availability',()=>{
    renderStudio();
    expect(screen.getByText('Restore recovery',{exact:true})).toBeDisabled();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[],savedSession:false,
      recovery:{available:true,pending:true,savedAt:100,message:'Existing recovery preserved.'}})}));
    expect(screen.getByText('Restore saved session',{exact:true})).toBeDisabled();
    fireEvent.click(screen.getByText('Restore recovery',{exact:true}));
    expect(screen.getByText('Confirm recovery',{exact:true})).toBeDisabled();
    fireEvent.click(screen.getByLabelText('Confirm recovery replacement'));
    fireEvent.click(screen.getByText('Confirm recovery',{exact:true}));
    expect(Socket.current.sent.at(-1)).toEqual({type:'RESTORE_RECOVERY',payload:{discard:true}});
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'RECOVERY_RESTORED',
      recovery:{available:true,pending:false,savedAt:100,message:'Recovery restored.'}})}));
    expect(screen.queryByText('Start new recovery history')).not.toBeInTheDocument();
    expect(screen.getByText('Restore saved session',{exact:true})).toBeDisabled();
    expect(Socket.current.sent.at(-1)).toEqual({type:'MEDIA_STATUS',payload:{}});
  });
  it('keeps write protection unchanged until acknowledgement and refreshes after recall',()=>{
    renderStudio();
    const checkbox=screen.getByLabelText('Write protect disk');
    expect(checkbox).toBeDisabled();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_STATUS',mediaStatus:{inserted:true,writeProtected:false}})}));
    fireEvent.click(checkbox);
    expect(Socket.current.sent.at(-1)).toEqual({type:'MEDIA_WRITE_PROTECT',payload:{enabled:true}});
    expect(checkbox).not.toBeChecked();expect(checkbox).toBeDisabled();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'ERROR',message:'Floppy controller is busy'})}));
    expect(checkbox).toBeEnabled();expect(checkbox).not.toBeChecked();
    fireEvent.click(checkbox);
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_PROTECTION',mediaStatus:{inserted:true,writeProtected:true}})}));
    expect(checkbox).toBeChecked();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION_RESTORED'})}));
    expect(checkbox).toBeDisabled();
    expect(Socket.current.sent.at(-1)).toEqual({type:'MEDIA_STATUS',payload:{}});
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_STATUS',mediaStatus:{inserted:true,writeProtected:true}})}));
    expect(checkbox).toBeChecked();expect(checkbox).toBeEnabled();
  });
  it('opens setup after startup failure and waits for the backend acknowledgement',()=>{
    renderStudio(false);
    const configuration={bootRom:'boot.bin',systemDisk:'system.img',mediaDirectory:'media',sound:false};
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[],configuration,needsConfiguration:true})}));
    expect(screen.getByRole('dialog',{name:'Standalone configuration'})).toBeVisible();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.click(screen.getByText('Apply settings and start'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'CONFIGURE_RUNTIME',payload:{...configuration,discard:true}});
    expect(screen.getByText('Starting sampler…')).toBeDisabled();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'ERROR',message:'Boot ROM must be readable'})}));
    expect(screen.getByRole('dialog',{name:'Standalone configuration'})).toBeVisible();
    expect(screen.getByText('Apply settings and start')).toBeEnabled();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'CONFIGURATION_APPLIED',configuration,media:['Real.img']})}));
    expect(screen.queryByRole('dialog',{name:'Standalone configuration'})).not.toBeInTheDocument();
    expect(screen.getByLabelText('Selected disk image')).toHaveTextContent('Real.img');
  });
  it('releases keyboard holds on blur and suppresses shortcuts in confirmation dialogs',()=>{
    renderStudio(false);
    fireEvent.keyDown(window,{code:'KeyC'});fireEvent.blur(window);
    expect(Socket.current.sent.filter(x=>x.type==='BUTTON_RELEASE'&&x.payload.id==='COMMAND').length).toBeGreaterThan(0);
    fireEvent.click(screen.getByRole('button',{name:'Configuration'}));
    fireEvent.click(screen.getByText('Restart sampler'));
    Socket.current.sent=[];fireEvent.keyDown(window,{code:'KeyM'});
    expect(Socket.current.sent).toHaveLength(0);
  });
  it('reports malformed session messages and keeps accepting valid messages',()=>{
    renderStudio();
    expect(()=>act(()=>Socket.current.onmessage?.({data:'{bad'}))).not.toThrow();
    expect(screen.getByRole('alert')).toHaveTextContent('Invalid sampler response');
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'FIRMWARE_STATUS',message:'OS ready'})}));
    expect(screen.getByRole('status')).toHaveTextContent('OS ready');
  });
  it('routes panel keyboard input once and releases across focus changes', () => {
    renderStudio(false);
    fireEvent.keyDown(window,{code:'ArrowUp'});
    fireEvent.keyDown(window,{code:'ArrowUp',repeat:true});
    const input=document.createElement('input');document.body.append(input);
    fireEvent.keyUp(input,{code:'ArrowUp'});
    expect(Socket.current.sent).toEqual([{type:'BUTTON_PRESS',payload:{id:'UP'}},{type:'BUTTON_RELEASE',payload:{id:'UP'}}]);
    fireEvent.keyDown(input,{code:'KeyM'});input.remove();
    expect(Socket.current.sent).toHaveLength(2);
  });
  it('does not present selected media as mounted before acknowledgement', () => {
    renderStudio();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:['Real.img']})}));
    expect(screen.getByLabelText('Drive display')).toHaveTextContent('No sample disk inserted');
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_INSERTED',name:'Real.img'})}));
    expect(screen.getByLabelText('Drive display')).toHaveTextContent('Real.img');
  });
  it('waits for saved-session acknowledgement and requires explicit restore', () => {
    renderStudio();
    expect(screen.getByText('Restore saved session')).toBeDisabled();
    fireEvent.click(screen.getByText('Save session'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'SAVE_SESSION',payload:{}});
    expect(screen.getByText('Restore saved session')).toBeDisabled();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION_SAVED',path:'latest.s760state'})}));
    fireEvent.click(screen.getByText('Restore saved session'));
    expect(screen.getByText('Confirm restore')).toBeDisabled();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory'));
    fireEvent.click(screen.getByText('Confirm restore'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'RESTORE_SESSION',payload:{discard:true}});
    expect(screen.queryByText('Saved session restored.')).not.toBeInTheDocument();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION_RESTORED'})}));
    expect(screen.getByText('Saved session restored.')).toBeInTheDocument();
  });
  it('does not confuse a session with OS readiness and exposes confirmed restart', () => {
    renderStudio();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[]})}));
    expect(screen.getByRole('status')).toHaveTextContent('Connected; checking firmware');
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'FIRMWARE_STATUS',state:'loading',message:'Firmware disk operation in progress.'})}));
    expect(screen.getByRole('status')).toHaveTextContent('Firmware disk operation in progress.');
    fireEvent.click(screen.getByText('Restart sampler'));
    expect(Socket.current.sent).not.toContainEqual({type:'RESTART_RUNTIME',payload:{discard:true}});
    fireEvent.click(screen.getByLabelText('Discard unsaved sampler memory'));
    fireEvent.click(screen.getByText('Confirm restart'));
    expect(Socket.current.sent).toContainEqual({type:'RESTART_RUNTIME',payload:{discard:true}});
  });
  it('exports only on request and waits for the backend result', () => {
    renderStudio();
    fireEvent.click(screen.getByText('Export disk'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'EXPORT_DISK',payload:{}});
    expect(screen.queryByText(/saved-to.img/)).not.toBeInTheDocument();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_EXPORTED',path:'saved-to.img'})}));
    expect(screen.getByText(/saved-to.img/)).toBeInTheDocument();
  });
  it('keeps inserted media visible until ejection is acknowledged', () => {
    renderStudio();
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_INSERTED',name:'Real.img'})}));
    fireEvent.click(screen.getByText('Eject disk'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'EJECT_DISK',payload:{}});
    expect(screen.getByLabelText('Drive display')).toHaveTextContent('Real.img');
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'ERROR',message:'Export disk changes first'})}));
    expect(screen.getByLabelText('Drive display')).toHaveTextContent('Real.img');
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_EJECTED'})}));
    expect(screen.getByLabelText('Drive display')).toHaveTextContent('No sample disk inserted');
    expect(screen.getByText('Disk ejected.')).toBeVisible();
  });
  it('shows only the media reported by the runtime', () => {
    renderStudio();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:['Real.img']})}));
    expect(screen.getByLabelText('Selected disk image')).toHaveTextContent('Real.img');
    fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
    expect(Socket.current.sent.at(-1)).toEqual({type:'MOUNT_DISK',payload:{diskPath:'Real.img'}});
    expect(screen.queryByText('Disk inserted: Real.img')).not.toBeInTheDocument();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_INSERTED',name:'Real.img'})}));
    expect(screen.getByText('Disk inserted: Real.img')).toBeInTheDocument();
  });
  it('keeps keyboard hidden by default and changes visibility only after saved acknowledgement', () => {
    renderStudio(false);
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[],midiDevices:['USB MIDI'],configuration:{bootRom:'boot',systemDisk:'sys',mediaDirectory:'media',sound:true,audioBackend:'auto'}})}));
    expect(screen.queryByRole('region',{name:'On-screen keyboard'})).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole('button',{name:'Configuration'}));
    fireEvent.click(screen.getByRole('button',{name:'Audio'}));
    expect(screen.getByLabelText('Audio output backend')).toBeVisible();
    fireEvent.click(screen.getByRole('button',{name:'MIDI & display'}));
    fireEvent.change(screen.getByLabelText('MIDI input'),{target:{value:'USB MIDI'}});
    expect(Socket.current.sent.at(-1)).toEqual({type:'MIDI_DEVICE',payload:{name:'USB MIDI'}});
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'MIDI_DEVICE_SELECTED',name:'USB MIDI'})}));
    expect(screen.getByLabelText('MIDI input')).toHaveValue('USB MIDI');
    fireEvent.click(screen.getByLabelText('Show on-screen keyboard'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'SET_STANDALONE_PREFERENCES',payload:{showKeyboard:true}});
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'STANDALONE_PREFERENCES',preferences:{showKeyboard:true}})}));
    fireEvent.click(screen.getByText('Cancel settings'));
    expect(screen.getByRole('region',{name:'On-screen keyboard'})).toBeVisible();
  });
  it('releases a held note on window blur and closes transport on unmount', () => {
    const view=renderStudio(false);
    act(()=>Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[],preferences:{showKeyboard:true}})}));
    fireEvent.pointerDown(screen.getByRole('button',{name:'C4 MIDI 60'}),{pointerId:1});
    fireEvent(window,new Event('blur'));
    expect(Socket.current.sent).toContainEqual({type:'NOTE_OFF',payload:{note:60,velocity:0}});
    view.unmount();expect(Socket.current.close).toHaveBeenCalled();
  });
});
