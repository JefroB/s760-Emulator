import {useEffect,useRef,type ReactNode} from 'react';
import {createPortal} from 'react-dom';

let openLayers=0;
let previousOverflow='';

/** A viewport-bound layer. Only the top layer owns keyboard focus. */
export function SettingsLayer({title,onClose,children,wide=false}:{
  title:string;onClose?:()=>void;children:ReactNode;wide?:boolean;
}) {
  const ref=useRef<HTMLDivElement>(null);
  const close=useRef(onClose);close.current=onClose;
  useEffect(()=>{
    const previous=document.activeElement as HTMLElement|null;
    if(openLayers++===0){previousOverflow=document.body.style.overflow;document.body.style.overflow='hidden';}
    const top=()=>Array.from(document.querySelectorAll<HTMLElement>('[data-settings-layer]'))
      .sort((a,b)=>Number(a.dataset.settingsLayer)-Number(b.dataset.settingsLayer)).at(-1)===ref.current;
    const focusable=()=>Array.from(ref.current?.querySelectorAll<HTMLElement>('button,input,select,textarea,[tabindex="0"]')??[])
      .filter(el=>!el.closest('[hidden]') && !el.hasAttribute('disabled'));
    (focusable()[0]??ref.current)?.focus();
    const key=(event:KeyboardEvent)=>{
      if(!top())return;
      if(event.key==='Escape' && close.current){event.preventDefault();event.stopImmediatePropagation();close.current();}
      if(event.key==='Tab'){
        const items=focusable(),first=items[0],last=items.at(-1);
        if(!first){event.preventDefault();ref.current?.focus();}
        else if(event.shiftKey && (document.activeElement===first || !ref.current?.contains(document.activeElement))){event.preventDefault();last?.focus();}
        else if(!event.shiftKey && (document.activeElement===last || !ref.current?.contains(document.activeElement))){event.preventDefault();first.focus();}
      }
    };
    document.addEventListener('keydown',key,true);
    return ()=>{document.removeEventListener('keydown',key,true);if(--openLayers===0)document.body.style.overflow=previousOverflow;previous?.isConnected && previous.focus();};
  },[]);
  return createPortal(<div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-3 sm:p-5 text-neutral-100" style={{zIndex:wide?50:60}}>
    <div ref={ref} data-settings-layer={wide?50:60} role="dialog" aria-modal="true" aria-label={title} tabIndex={-1}
      className={`flex min-h-0 w-full flex-col overflow-hidden rounded-xl border border-neutral-600 bg-[#171a20] shadow-2xl ${wide?'max-w-4xl':'max-w-lg'}`}
      style={{maxHeight:'calc(100dvh - 24px)',...(wide?{height:'min(660px, calc(100dvh - 24px))'}:{})}}>
      <header className="flex shrink-0 items-center justify-between gap-4 border-b border-neutral-700 px-5 py-3">
        <h2 className="text-lg font-medium">{title}</h2>
        {onClose && <button type="button" aria-label={`Close ${title}`} onClick={onClose} className="rounded px-2 py-1 text-neutral-300 hover:bg-neutral-700">✕</button>}
      </header>
      {wide?children:<div className="overflow-y-auto p-5 space-y-4 [&>button]:rounded-lg [&>button]:border [&>button]:border-neutral-600 [&>button]:px-3 [&>button]:py-2 [&>button]:mr-3 [&>button:disabled]:opacity-40">{children}</div>}
    </div>
  </div>,document.body);
}
