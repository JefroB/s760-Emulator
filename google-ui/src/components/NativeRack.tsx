import {useEffect,useRef,useState,type ReactNode} from 'react';
import {useSurfaceCanvas, backlightTint} from '../bridge/BridgeContext';
import {SurfaceId} from '../bridge/S760BridgeClient';
import type {NativeSend} from '../nativeKeyboard';
import type {SamplerState} from '../types/sampler';
import {S760FrontPanel} from './S760FrontPanel';
import {NativeDriveBay} from './NativeDriveBay';

// These presentation values never draw simulated displays or select demo media.
// Native hardware supplies the live LCD, real transport and acknowledged drive state.
const presentation:SamplerState={powerOn:true,volume:100,volumeAngle:0,alphaDialAngle:0,
  mode:'PERF',subMode:'',activeCursorField:0,cursorRow:0,cursorCol:0,backlightColor:'emerald',
  currentPatchIndex:0,currentPerfIndex:0,sampleZoom:1,sampleScrub:0,
  gotek:{selectedImageIndex:0,mountedImageIndex:null,isBusy:false,currentTrack:0,currentSide:0,usbInserted:false,dialAngle:0,statusText:''},
  peakL:false,peakR:false,midiRx:false};
const unused=()=>{};

export function NativeRack({send,mountedDisk,outputLevel=100,inputLevel=100,connected=true,media=[],selectedDisk='',onSelectDisk=unused}:{
  send:NativeSend;mountedDisk:string;outputLevel?:number;inputLevel?:number;connected?:boolean;
  media?:string[];selectedDisk?:string;onSelectDisk?:(name:string)=>void;
}) {
  const lcd=useSurfaceCanvas(SurfaceId.LCD,{tint:backlightTint('emerald')});
  return <section aria-label="Native sampler rack" className="w-full">
    <S760FrontPanel state={presentation} diskList={[]} nativeHardware={{send,enabled:connected,outputLevel,inputLevel,
      lcd:<div className="p-1 rounded-sm bg-neutral-900 border border-neutral-700/80 shadow-inner">
        <div className="relative overflow-hidden rounded-[2px] lcd-green-glow border border-emerald-500/40 bg-[#12280f]" style={{width:240,height:96}}>
          <canvas ref={lcd} width={160} height={64} aria-label="Native LCD" className="w-full h-full" style={{imageRendering:'pixelated'}}/>
        </div>
      </div>,
      driveBay:<NativeDriveBay standalone={{send,enabled:connected,media,selected:selectedDisk,mounted:mountedDisk,onSelect:onSelectDisk}}/>
    }} onTogglePower={unused} onSetVolume={unused} onSetMode={unused} onAlphaDialStep={unused}
      onNavigate={unused} onIncDec={unused} onEnter={unused} onExit={unused} onSoftKey={unused}
      onSelectDiskIndex={unused} onMountDisk={unused} onToggleUsb={unused} onEventEmit={unused} onTriggerAudition={unused}/>
  </section>;
}

/** Scale the complete rack and keyboard together so no controls are clipped. */
export function NativeRackStack({children}:{children:ReactNode}) {
  const viewport=useRef<HTMLDivElement>(null);
  const [zoom,setZoom]=useState(1);
  useEffect(()=>{
    if(!viewport.current || typeof ResizeObserver==='undefined')return;
    const fit=()=>setZoom(Math.min(1,viewport.current!.clientWidth/1440));
    const observer=new ResizeObserver(fit);observer.observe(viewport.current);fit();
    return ()=>observer.disconnect();
  },[]);
  return <div ref={viewport} className="w-full"><div className="mx-auto w-[1440px]" style={{zoom}}>{children}</div></div>;
}
