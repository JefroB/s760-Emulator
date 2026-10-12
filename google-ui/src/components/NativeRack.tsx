import {useSurfaceCanvas, backlightTint} from '../bridge/BridgeContext';
import {SurfaceId} from '../bridge/S760BridgeClient';
import {RackEar} from './RackEars';
import type {NativeSend} from '../nativeKeyboard';
import {RackKnob} from './RackKnob';

export function NativeRack({send, mountedDisk,outputLevel=100}: {send: NativeSend; mountedDisk: string;outputLevel?:number}) {
  const lcd=useSurfaceCanvas(SurfaceId.LCD,{tint:backlightTint('emerald')});
  return <section aria-label="Native sampler rack" className="w-full overflow-x-auto py-4">
    <div className="mx-auto flex items-stretch bg-brushed-metal-horizontal border-y border-neutral-600 rounded shadow-2xl select-none" style={{minWidth:940,maxWidth:1440,height:160}}>
      <RackEar side="left"/>
      <div className="flex items-center justify-around gap-5 px-5 grow">
        <div><p className="text-xl font-bold tracking-tight">Roland</p><p className="font-bold">S-760</p><p className="text-[10px] text-neutral-400">DIGITAL SAMPLER</p></div>
        <div className="bg-black border-4 border-neutral-800 rounded p-1"><canvas ref={lcd} width={160} height={64} aria-label="Native LCD" style={{width:240,height:96,imageRendering:'pixelated',background:'#132c10'}}/></div>
        <div aria-label="Front panel" className="grid grid-cols-5 gap-2">
          {['COMMAND','MODE','EXIT','SHIFT','S1','UP','DOWN','LEFT','RIGHT','S2','F1','F2','F3'].map(id =>
            <button key={id} className="bg-gradient-to-b from-neutral-600 to-neutral-900 border border-neutral-600 rounded px-2 py-1 text-xs active:brightness-150"
              onPointerDown={e=>{e.currentTarget.setPointerCapture(e.pointerId);send('BUTTON_PRESS',{id});}}
              onPointerUp={()=>send('BUTTON_RELEASE',{id})} onPointerCancel={()=>send('BUTTON_RELEASE',{id})}
              onKeyDown={e=>{if((e.key===' '||e.key==='Enter')&&!e.repeat){e.preventDefault();send('BUTTON_PRESS',{id});}}}
              onKeyUp={e=>{if(e.key===' '||e.key==='Enter'){e.preventDefault();send('BUTTON_RELEASE',{id});}}}
              onBlur={()=>send('BUTTON_RELEASE',{id})}>{id}</button>)}
        </div>
        <div className="flex gap-3">
          <RackKnob label="VALUE" onStep={delta=>send('DIAL_DELTA',{id:'ALPHA',delta})}/>
          <RackKnob label="OUTPUT LEVEL" value={outputLevel} onStep={delta=>send('DIAL_DELTA',{id:'VOLUME',delta})}/>
        </div>
        <div aria-label="Drive media status" className="w-44 bg-black border-4 border-neutral-800 rounded p-3 text-xs">
          <span className="text-neutral-500">SAMPLE DRIVE</span>
          <p className="text-emerald-300 break-all mt-2">{mountedDisk || 'No sample disk confirmed'}</p>
        </div>
      </div>
      <RackEar side="right"/>
    </div>
  </section>;
}
