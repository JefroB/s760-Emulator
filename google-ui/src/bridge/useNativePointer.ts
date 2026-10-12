import { useEffect, useMemo } from 'react';
import type { PointerEvent } from 'react';
import type { S760BridgeClient } from './S760BridgeClient';

/** Absolute CRT coordinates and explicit, releasable native mouse buttons. */
export function useNativePointer(client: S760BridgeClient | null, enabled: boolean) {
  const input = useMemo(() => {
    const held = new Set<number>();
    const release = () => {
      for (const button of held) client?.send({type:'MOUSE_BUTTON',payload:{button,down:false}});
      held.clear();
    };
    const move = (event: PointerEvent<HTMLCanvasElement>) => {
      if (!enabled || !client) return;
      const rect = event.currentTarget.getBoundingClientRect();
      if (!rect.width || !rect.height) return;
      const clamp = (v: number) => Math.max(0,Math.min(1,v));
      client.send({type:'MOUSE_MOVE',payload:{x:clamp((event.clientX-rect.left)/rect.width),y:clamp((event.clientY-rect.top)/rect.height)}});
    };
    return {
      release,
      onPointerMove: move,
      onPointerDown(event: PointerEvent<HTMLCanvasElement>) {
        if (!enabled || !client || ![0,2].includes(event.button)) return;
        event.preventDefault(); move(event);
        event.currentTarget.setPointerCapture(event.pointerId);
        if (!held.has(event.button)) {
          held.add(event.button);
          client.send({type:'MOUSE_BUTTON',payload:{button:event.button,down:true}});
        }
      },
      onPointerUp(event: PointerEvent<HTMLCanvasElement>) {
        if (held.delete(event.button)) client?.send({type:'MOUSE_BUTTON',payload:{button:event.button,down:false}});
      },
      onPointerCancel: release,
      onLostPointerCapture: release,
    };
  }, [client,enabled]);
  useEffect(() => {
    window.addEventListener('blur',input.release);
    return () => { window.removeEventListener('blur',input.release); input.release(); };
  },[input]);
  return input;
}
