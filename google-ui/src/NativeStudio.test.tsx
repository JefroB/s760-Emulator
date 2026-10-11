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

describe('NativeStudio real-machine controls', () => {
  it('waits for saved-session acknowledgement and requires explicit restore', () => {
    render(<NativeStudio/>);
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
    render(<NativeStudio/>);
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:[]})}));
    expect(screen.getByRole('status')).toHaveTextContent('Connected; checking firmware');
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'FIRMWARE_STATUS',state:'loading',message:'Firmware disk operation in progress.'})}));
    expect(screen.getByRole('status')).toHaveTextContent('Firmware disk operation in progress.');
    fireEvent.click(screen.getByText('Restart sampler'));
    expect(Socket.current.sent).not.toContainEqual({type:'RESTART_RUNTIME',payload:{discard:true}});
    fireEvent.click(screen.getByLabelText('Discard unsaved sampler memory'));
    fireEvent.click(screen.getByText('Confirm restart'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'RESTART_RUNTIME',payload:{discard:true}});
  });
  it('exports only on request and waits for the backend result', () => {
    render(<NativeStudio/>);
    fireEvent.click(screen.getByText('Export disk'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'EXPORT_DISK',payload:{}});
    expect(screen.queryByText(/saved-to.img/)).not.toBeInTheDocument();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_EXPORTED',path:'saved-to.img'})}));
    expect(screen.getByText(/saved-to.img/)).toBeInTheDocument();
  });
  it('shows only the media reported by the runtime', () => {
    render(<NativeStudio/>);
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'SESSION',media:['Real.img']})}));
    expect(screen.getByRole('option',{name:'Real.img'})).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Sample disk'),{target:{value:'Real.img'}});
    fireEvent.click(screen.getByText('Insert disk'));
    expect(Socket.current.sent.at(-1)).toEqual({type:'MOUNT_DISK',payload:{diskPath:'Real.img'}});
    expect(screen.queryByText('Disk inserted: Real.img')).not.toBeInTheDocument();
    act(() => Socket.current.onmessage?.({data:JSON.stringify({type:'MEDIA_INSERTED',name:'Real.img'})}));
    expect(screen.getByText('Disk inserted: Real.img')).toBeInTheDocument();
  });
  it('releases the original note even if its selector changed while held', () => {
    render(<NativeStudio/>);
    fireEvent.pointerDown(screen.getByText('Hold to audition'));
    fireEvent.change(screen.getByLabelText('MIDI note'),{target:{value:'64'}});
    fireEvent.pointerUp(screen.getByText('Hold to audition'));
    expect(Socket.current.sent).toEqual([
      {type:'NOTE_ON',payload:{note:60,velocity:100}},
      {type:'NOTE_OFF',payload:{note:60,velocity:0}},
    ]);
  });
  it('releases a held note on window blur and closes transport on unmount', () => {
    const view=render(<NativeStudio/>);
    fireEvent.pointerDown(screen.getByText('Hold to audition'));
    fireEvent(window,new Event('blur'));
    expect(Socket.current.sent).toContainEqual({type:'NOTE_OFF',payload:{note:60,velocity:0}});
    view.unmount();expect(Socket.current.close).toHaveBeenCalled();
  });
});
