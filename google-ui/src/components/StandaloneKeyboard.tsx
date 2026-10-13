import {useEffect, useRef} from 'react';

const notes = Array.from({length:61}, (_, i) => 36+i);
const black = (note:number) => [1,3,6,8,10].includes(note%12);
const label = (note:number) => `${['C','C♯','D','D♯','E','F','F♯','G','G♯','A','A♯','B'][note%12]}${Math.floor(note/12)-1}`;

export function StandaloneKeyboard({send, connected}:{
  send:(type:string,payload:Record<string,unknown>)=>void; connected:boolean;
}) {
  const holds = useRef(new Map<string,number>());
  const sender = useRef(send);
  sender.current = send;
  const release = (source:string) => {
    const note = holds.current.get(source);
    holds.current.delete(source);
    if(note!==undefined && ![...holds.current.values()].includes(note)) sender.current('NOTE_OFF',{note,velocity:0});
  };
  const press = (source:string,note:number) => {
    if(!connected || holds.current.has(source)) return;
    const sounding = [...holds.current.values()].includes(note);
    holds.current.set(source,note);
    if(!sounding) sender.current('NOTE_ON',{note,velocity:100});
  };
  useEffect(()=>{
    const releaseAll = () => {
      for(const note of new Set(holds.current.values())) sender.current('NOTE_OFF',{note,velocity:0});
      holds.current.clear();
    };
    const hidden = () => {if(document.hidden) releaseAll();};
    if(!connected) releaseAll();
    window.addEventListener('blur',releaseAll);
    document.addEventListener('visibilitychange',hidden);
    return ()=>{releaseAll();window.removeEventListener('blur',releaseAll);document.removeEventListener('visibilitychange',hidden);};
  },[connected]);
  let whites = 0;
  return <section aria-label="On-screen keyboard" className="w-full rounded-sm border border-neutral-700 bg-[#17191b] px-3 pt-3 pb-2 shadow-xl">
    <div className="relative flex h-32 select-none touch-none">
      {notes.map(note=>{
        const isBlack=black(note);
        const left=whites*100/36;
        if(!isBlack) whites++;
        return <button key={note} aria-label={`${label(note)} MIDI ${note}`} disabled={!connected}
          className={isBlack?'absolute top-0 z-10 h-20 w-[1.75%] bg-gradient-to-r from-[#101112] via-[#303235] to-[#101112] border border-black rounded-b-sm shadow-md active:bg-cyan-900 focus-visible:outline-2 focus-visible:outline-cyan-400':'flex-1 h-32 bg-gradient-to-b from-[#d5d5d1] via-[#f0f0ec] to-[#c7c7c2] border-r border-[#555653] first:border-l rounded-b-sm active:from-cyan-100 active:to-cyan-300 focus-visible:outline-2 focus-visible:outline-cyan-400'}
          style={isBlack?{left:`${left-.875}%`}:undefined}
          onPointerDown={e=>{e.preventDefault();e.currentTarget.setPointerCapture(e.pointerId);press(`p${e.pointerId}`,note);}}
          onPointerUp={e=>release(`p${e.pointerId}`)} onPointerCancel={e=>release(`p${e.pointerId}`)}
          onLostPointerCapture={e=>release(`p${e.pointerId}`)}
          onKeyDown={e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();press(`k${note}`,note);}}}
          onKeyUp={e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();release(`k${note}`);}}}
          onBlur={()=>release(`k${note}`)}>
        </button>;
      })}
    </div>
  </section>;
}
