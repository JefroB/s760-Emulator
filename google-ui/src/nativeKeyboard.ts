import {useEffect, useRef} from 'react';

export type NativeSend = (type: string, payload: Record<string, unknown>) => void;
// Match the native driver's documented panel matrix, not the demo mode shortcuts.
export const PANEL_KEYS: Record<string, string> = {
  ArrowUp:'UP', ArrowDown:'DOWN', ArrowLeft:'LEFT', ArrowRight:'RIGHT',
  KeyC:'COMMAND', KeyM:'MODE', Backspace:'EXIT', KeyA:'F1', KeyS:'F2',
  KeyD:'F3', KeyZ:'S1', KeyX:'S2', ShiftLeft:'SHIFT',
};

export function useNativeKeyboard(send: NativeSend) {
  const latest = useRef(send);
  latest.current = send;
  useEffect(() => {
    const held = new Map<string,string>();
    const release = () => {
      for (const id of held.values()) latest.current('BUTTON_RELEASE',{id});
      held.clear();
    };
    const down = (event: KeyboardEvent) => {
      const target = event.target;
      if (event.ctrlKey || event.altKey || event.metaKey ||
          (target instanceof Element && target.closest('input,select,textarea,button,[contenteditable="true"],[role="dialog"]')) ||
          document.querySelector('[role="dialog"]')) return;
      const id=PANEL_KEYS[event.code];
      if (!id) return;
      event.preventDefault();
      if (held.has(event.code)) return;
      held.set(event.code,id);
      latest.current('BUTTON_PRESS',{id});
    };
    const up = (event: KeyboardEvent) => {
      const id=held.get(event.code);
      if (!id) return;
      event.preventDefault(); held.delete(event.code);
      latest.current('BUTTON_RELEASE',{id});
    };
    const visibility=() => {if(document.hidden) release();};
    window.addEventListener('keydown',down);window.addEventListener('keyup',up);
    window.addEventListener('blur',release);document.addEventListener('visibilitychange',visibility);
    return () => {
      release();window.removeEventListener('keydown',down);window.removeEventListener('keyup',up);
      window.removeEventListener('blur',release);document.removeEventListener('visibilitychange',visibility);
    };
  },[]);
}
