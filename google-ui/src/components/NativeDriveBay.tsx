import {useState,useEffect} from 'react';
import {RackKnob} from './RackKnob';
import {createPortal} from 'react-dom';
import {useBridgeClient,useBridgeStatus,useBridgeTelemetry} from '../bridge/BridgeContext';
/** UI-owned drive status: no fictitious FlashFloppy pixels or activity animation. */
export function NativeDriveBay() {
  const client=useBridgeClient(),status=useBridgeStatus(),telemetry=useBridgeTelemetry();
  const [editing,setEditing]=useState(false),[path,setPath]=useState(''),[folder,setFolder]=useState('');
  const [entered,setImages]=useState<string[]>([]),[selection,setSelection]=useState<string|null>(null);
  const images=[...new Set([...(telemetry?.mediaPaths||[]),...entered])];
  useEffect(()=>{setSelection(telemetry?.selectedMediaPath||telemetry?.lastInsertedPath||null);},[telemetry?.selectedMediaPath,telemetry?.lastInsertedPath]);
  const selected=Math.max(0,images.indexOf(selection||telemetry?.lastInsertedPath||''));
  const setSelected=(i:number)=>{const diskPath=images[i];setSelection(diskPath||null);if(diskPath)client?.send({type:'SELECT_MEDIA',payload:{diskPath}});};
  const browse=(delta:number)=>setSelected(images.length?Math.max(0,Math.min(images.length-1,selected+delta)):0);
  const mount=()=>{setPath(images[selected]||'');setFolder(telemetry?.mediaFolder||'');setEditing(true);};
  return <div className="w-56 p-2 rounded border-4 border-neutral-800 bg-[#15171b]" aria-label="Native drive bay">
    <div className="bg-black border border-neutral-700 p-2 h-12 text-cyan-300 font-mono" aria-label="Drive display">
      <p className="text-[8px] text-cyan-600">LAST INSERTED IMAGE</p>
      <p title={telemetry?.lastInsertedDisk} className="text-[10px] truncate">{status!=='connected'?'Disconnected':telemetry?.lastInsertedDisk||(telemetry?'Media identity unavailable':'Waiting for drive status')}</p>
      {images.length>0&&<p title={images[selected]} className="text-[8px] truncate">SELECT: {images[selected].split(/[\\/]/).pop()}</p>}
      {telemetry?.mediaError&&<p role="alert" title={telemetry.mediaError} className="text-[8px] text-amber-400 truncate">Insertion failed</p>}
    </div>
    <div className="flex items-end justify-between gap-2 mt-1">
      <div className="flex gap-1">
        <button aria-label="Gotek Up" disabled={status!=='connected'||selected===0} onClick={()=>browse(-1)} className="text-[9px] border border-neutral-600 rounded px-2 h-6 disabled:opacity-40">Up</button>
        <button aria-label="Gotek Down" disabled={status!=='connected'||selected>=images.length-1} onClick={()=>browse(1)} className="text-[9px] border border-neutral-600 rounded px-2 h-6 disabled:opacity-40">Down</button>
        <button aria-label="Gotek Select" disabled={status!=='connected'} onClick={mount} className="text-[9px] border border-neutral-600 rounded px-2 h-6 disabled:opacity-40">Select</button>
      </div>
      <RackKnob label="GOTEK" compact disabled={status!=='connected'||!images.length} onStep={browse}/>
    </div>
    {editing&&createPortal(<form role="dialog" aria-label="Insert disk image" className="fixed z-50 left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-neutral-100 bg-neutral-900 p-3 border border-neutral-600 rounded" onSubmit={e=>{e.preventDefault();const clean=path.trim();if(!images.includes(clean)){setImages([...entered,clean]);setSelection(clean);}else setSelected(images.indexOf(clean));client?.send({type:'MOUNT_DISK',payload:{diskPath:clean}});setEditing(false);}}>
      <div className="mb-3 text-xs">
        <label>Media folder <input value={folder} onChange={e=>setFolder(e.target.value)} className="bg-black p-2 w-80"/></label>
        <button type="button" disabled={!folder.trim()} className="ml-2" onClick={()=>client?.send({type:'CONFIGURE_MEDIA_LIBRARY',payload:{diskPath:folder.trim()}})}>Scan folder</button>
        <p className="text-neutral-400 mt-1">Includes subfolders. Scanning does not change the inserted disk.</p>
        {telemetry?.libraryError&&<p role="alert" className="text-amber-400">{telemetry.libraryError}</p>}
        <select aria-label="Library images" className="bg-black p-2 w-full mt-2" value={path} onChange={e=>{setPath(e.target.value);setSelected(images.indexOf(e.target.value));}}>
          <option value="">Choose an image</option>
          {images.map(image=><option key={image} value={image}>{image}</option>)}
        </select>
      </div>
      <label className="text-xs">Local image path <input autoFocus value={path} onChange={e=>setPath(e.target.value)} className="bg-black p-2 w-80"/></label>
      <button disabled={!path.trim()} className="ml-2">Insert</button>
      <button type="button" className="ml-2" onClick={()=>setEditing(false)}>Cancel</button>
    </form>,document.body)}
  </div>;
}
