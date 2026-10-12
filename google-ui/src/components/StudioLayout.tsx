import React, { useEffect, useRef, useState } from 'react';

/** Fit both physical units inside a host-sized editor, without clipping controls. */
export function StudioLayout({embedded,children}:{embedded:boolean;children:React.ReactNode}) {
  const viewport=useRef<HTMLElement>(null);
  const content=useRef<HTMLDivElement>(null);
  const [scale,setScale]=useState(1);
  useEffect(()=>{
    if(!embedded || !viewport.current || !content.current)return;
    const fit=()=>{
      const box=viewport.current!, stack=content.current!;
      setScale(Math.min(1,(box.clientWidth-16)/stack.offsetWidth,(box.clientHeight-16)/stack.offsetHeight));
    };
    const observer=new ResizeObserver(fit);
    observer.observe(viewport.current);observer.observe(content.current);fit();
    return ()=>observer.disconnect();
  },[embedded]);
  if(!embedded)return <main className="flex-1 flex flex-col items-center justify-center p-4 lg:p-6 gap-5 overflow-x-hidden">{children}</main>;
  return <main ref={viewport} data-testid="embedded-studio" className="relative flex-1 min-h-0 overflow-hidden">
    <div ref={content} className="absolute flex flex-col items-center gap-5" style={{width:1480,left:'50%',top:'50%',transform:`translate(-50%, -50%) scale(${scale})`}}>{children}</div>
  </main>;
}
