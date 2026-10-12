import {useRef,useState} from 'react';

/** Relative encoder: drag vertically, wheel, or use arrow keys. */
export function RackKnob({label,onStep,disabled=false,title,compact=false,value}:{label:string;onStep?:(delta:number)=>void;disabled?:boolean;title?:string;compact?:boolean;value?:number}) {
  const [angle,setAngle]=useState(0);
  const drag=useRef<number|null>(null);
  const step=(delta:number)=>{if(disabled||!delta)return;delta=Math.max(-32,Math.min(32,delta));setAngle(a=>a+delta*15);onStep?.(delta);};
  return <div className="flex flex-col items-center gap-1 shrink-0">
    <span className="text-[8px] font-bold tracking-wide text-neutral-300">{label}</span>
    <button type="button" aria-label={`${label} knob`} disabled={disabled} title={value===undefined?title:`${title||label}: ${value}%`}
      className={`${compact?'w-8 h-8':'w-10 h-10'} rounded-full border-2 border-neutral-600 bg-gradient-to-br from-neutral-500 via-neutral-800 to-black shadow-lg touch-none disabled:opacity-40`}
      onPointerDown={e=>{if(e.button!==0)return;drag.current=e.clientY;e.currentTarget.setPointerCapture(e.pointerId);}}
      onPointerMove={e=>{if(drag.current===null)return;const n=Math.trunc((drag.current-e.clientY)/5);if(n){drag.current-=n*5;step(n);}}}
      onPointerUp={()=>{drag.current=null;}} onPointerCancel={()=>{drag.current=null;}} onBlur={()=>{drag.current=null;}}
      onWheel={e=>step(e.deltaY<0?1:e.deltaY>0?-1:0)}
      onKeyDown={e=>{if(['ArrowUp','ArrowRight','ArrowDown','ArrowLeft'].includes(e.key)){e.preventDefault();step(e.key==='ArrowUp'||e.key==='ArrowRight'?1:-1);}}}>
      <span className="block h-full w-full" style={{transform:`rotate(${value===undefined?angle:-135+value*2.7}deg)`}}><span className="block mx-auto mt-1 w-0.5 h-2 bg-neutral-200"/></span>
    </button>
  </div>;
}
