import { render, fireEvent } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { useNativePointer } from './useNativePointer';
import type { S760BridgeClient } from './S760BridgeClient';

describe('native CRT held mouse input', () => {
  it('sends absolute position before press and releases on blur/unmount', () => {
    const send=vi.fn(); const client={send} as unknown as S760BridgeClient;
    function Canvas(){const {release,...handlers}=useNativePointer(client,true);return <canvas {...handlers}/>;}
    const view=render(<Canvas/>); const canvas=view.container.querySelector('canvas')!;
    canvas.setPointerCapture=vi.fn();
    canvas.getBoundingClientRect=()=>({left:10,top:20,width:320,height:240}) as DOMRect;
    // jsdom's default pointer event has no mouse coordinates.
    const down=(button:number)=>{const event=new MouseEvent('pointerdown',{bubbles:true,button,clientX:170,clientY:80});fireEvent(canvas,event);};
    down(0);
    expect(send.mock.calls.map(c=>c[0])).toEqual([
      {type:'MOUSE_MOVE',payload:{x:.5,y:.25}},
      {type:'MOUSE_BUTTON',payload:{button:0,down:true}},
    ]);
    fireEvent(window,new Event('blur'));
    expect(send).toHaveBeenLastCalledWith({type:'MOUSE_BUTTON',payload:{button:0,down:false}});
    down(2); view.unmount();
    expect(send).toHaveBeenLastCalledWith({type:'MOUSE_BUTTON',payload:{button:2,down:false}});
  });
  it('ignores unsupported buttons and disconnected input',()=>{
    const send=vi.fn(); const client={send} as unknown as S760BridgeClient;
    function Canvas(){const {release,...handlers}=useNativePointer(client,false);return <canvas {...handlers}/>;}
    const view=render(<Canvas/>);fireEvent(view.container.querySelector('canvas')!,new MouseEvent('pointerdown',{bubbles:true,button:1}));
    expect(send).not.toHaveBeenCalled();
  });
});
