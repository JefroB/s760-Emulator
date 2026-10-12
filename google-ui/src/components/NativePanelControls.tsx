import {useEffect, useRef} from 'react';
import {RackKnob} from './RackKnob';
import type {NativeSend} from '../nativeKeyboard';

// Owner's Manual Basic 0-6/0-7 and 7-9; physical panel photograph.
const FUNCTIONS=[['F1','F1'],['F2','F2'],['F3','F3'],['F4','F1','shift'],['F5','F2','shift'],['F6','F3','shift']];
const MAIN=[['MODE','MODE'],['COMMAND','COMMAND'],['EXIT','EXIT']];
const NAV=[['S1/DEC','S1'],['UP','UP'],['S2/INC','S2'],['LEFT','LEFT'],['DOWN','DOWN'],['RIGHT','RIGHT']];
const SHORTCUTS=[['HOME','LEFT','shift'],['MARK','DOWN','shift'],['JUMP','RIGHT','shift']];
/** Named Shift functions send the original electrical chord. */
export function NativePanelControls({send,enabled=true,functionsOnly=false}:{send:NativeSend;enabled?:boolean;functionsOnly?:boolean}) {
  const latest=useRef(send);latest.current=send;
  const held=useRef<string[]>([]);
  const started=useRef(0);
  const timer=useRef<ReturnType<typeof setTimeout> | null>(null);
  const release=()=>{
    if(timer.current!==null){clearTimeout(timer.current);timer.current=null;}
    for(const id of [...held.current].reverse())latest.current('BUTTON_RELEASE',{id});
    held.current=[];
  };
  const press=(id:string,shift:boolean)=>{
    release();if(!enabled)return;
    held.current=shift?['SHIFT',id]:[id];started.current=Date.now();
    for(const key of held.current)latest.current('BUTTON_PRESS',{id:key});
  };
  const finish=()=>{timer.current=setTimeout(release,Math.max(0,120-(Date.now()-started.current)));};
  useEffect(()=>{
    window.addEventListener('blur',release);
    const hidden=()=>{if(document.hidden)release();};
    document.addEventListener('visibilitychange',hidden);
    return ()=>{release();window.removeEventListener('blur',release);document.removeEventListener('visibilitychange',hidden);};
  },[]);
  useEffect(()=>{if(!enabled)release();},[enabled]);
  const button=([label,id,modifier]:string[])=> <button key={label} disabled={!enabled} type="button" aria-label={label}
    className={`min-w-0 h-6 px-1 text-[9px] rounded border border-neutral-600 bg-gradient-to-b from-neutral-700 to-neutral-900 active:brightness-150 disabled:opacity-40 ${modifier?'text-sky-300':'text-neutral-200'}`}
    onPointerDown={e=>{if(e.button!==0)return;e.currentTarget.setPointerCapture(e.pointerId);press(id,!!modifier);}}
    onPointerUp={finish} onPointerCancel={release} onBlur={release}
    onKeyDown={e=>{if((e.key===' '||e.key==='Enter')&&!e.repeat){e.preventDefault();press(id,!!modifier);}}}
    onKeyUp={e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();finish();}}}>
    {({UP:'▲',DOWN:'▼',LEFT:'◀︎',RIGHT:'▶︎'} as Record<string,string>)[label]||label}
  </button>;
  if(functionsOnly)return <div aria-label="Function keys" className="grid grid-cols-6 gap-1 w-[240px] mt-1.5">{FUNCTIONS.map(button)}</div>;
  return <div aria-label="Native panel controls" className="px-4 flex flex-1 items-center justify-center gap-4 border-r border-neutral-700/60">
    <div className="grid grid-cols-3 gap-1 w-44">{MAIN.map(button)}</div>
    <div className="flex flex-col items-center gap-2">
      <RackKnob label="VALUE" disabled={!enabled} onStep={delta=>send('DIAL_DELTA',{id:'ALPHA',delta})} title="Turn to edit the parameter under the cursor"/>
      <div className="w-16 [&>button]:w-full">{button(['MENU','MENU'])}</div>
    </div>
    <div className="w-44 flex flex-col gap-2">
      <div aria-label="Navigation cluster" className="grid grid-cols-3 gap-x-1 gap-y-3">{NAV.map(button)}</div>
      <div aria-label="Shift navigation functions" className="grid grid-cols-3 gap-1">{SHORTCUTS.map(button)}</div>
    </div>
  </div>;
}
