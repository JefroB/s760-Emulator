import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {NativeDriveBay} from './NativeDriveBay';
const mock=vi.hoisted(()=>({send:vi.fn(),telemetry:{lastInsertedDisk:'S760224.IMG',mediaError:'',mediaPaths:[] as string[],lastInsertedPath:'',selectedMediaPath:'',mediaFolder:'',libraryError:''}}));
vi.mock('../bridge/BridgeContext',()=>({useBridgeClient:()=>({send:mock.send}),useBridgeStatus:()=> 'connected',useBridgeTelemetry:()=>mock.telemetry}));
afterEach(()=>{cleanup();mock.send.mockClear();mock.telemetry.mediaError='';mock.telemetry.mediaPaths=[];mock.telemetry.lastInsertedPath='';mock.telemetry.selectedMediaPath='';mock.telemetry.mediaFolder='';mock.telemetry.libraryError='';});
it('restores host-owned media paths and last confirmed selection after editor recreation',()=>{
 mock.telemetry.mediaPaths=['D:/one.img','D:/two.img'];mock.telemetry.lastInsertedPath='D:/two.img';
 const first=render(<NativeDriveBay/>);
 expect(screen.getByText('SELECT: two.img')).toBeInTheDocument();
 first.unmount();render(<NativeDriveBay/>);
 fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
 expect(screen.getByLabelText('Local image path')).toHaveValue('D:/two.img');
 expect(mock.send).not.toHaveBeenCalled();
});
it('shows confirmed media; a request does not optimistically replace it',()=>{
 render(<NativeDriveBay/>);expect(screen.getByText('S760224.IMG')).toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
 fireEvent.change(screen.getByLabelText('Local image path'),{target:{value:'D:/samples/test.img'}});
 fireEvent.click(screen.getByRole('button',{name:'Insert'}));
 expect(mock.send).toHaveBeenCalledWith({type:'MOUNT_DISK',payload:{diskPath:'D:/samples/test.img'}});
 expect(screen.getByText('S760224.IMG')).toBeInTheDocument();
 expect(screen.queryByText('test.img')).toBeNull();
});
it('keeps the last successful name and shows an insertion error',()=>{
 mock.telemetry.mediaError='Native media operation rejected';render(<NativeDriveBay/>);
 expect(screen.getByRole('alert')).toHaveTextContent('Insertion failed');
 expect(screen.getByText('S760224.IMG')).toBeInTheDocument();
});
it('browses entered paths with both Gotek buttons and its separate encoder, then mounts on Select',()=>{
 render(<NativeDriveBay/>);
 for(const path of ['D:/samples/one.img','D:/samples/two.img']) {
  fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
  fireEvent.change(screen.getByLabelText('Local image path'),{target:{value:path}});
  fireEvent.click(screen.getByRole('button',{name:'Insert'}));
 }
 mock.send.mockClear();
 fireEvent.click(screen.getByRole('button',{name:'Gotek Up'}));
 expect(screen.getByText('SELECT: one.img')).toBeInTheDocument();
 fireEvent.keyDown(screen.getByRole('button',{name:'GOTEK knob'}),{key:'ArrowRight'});
 expect(screen.getByText('SELECT: two.img')).toBeInTheDocument();
 expect(mock.send.mock.calls.every(([message])=>message.type==='SELECT_MEDIA')).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
 expect(screen.getByLabelText('Local image path')).toHaveValue('D:/samples/two.img');
 fireEvent.click(screen.getByRole('button',{name:'Insert'}));
 expect(mock.send).toHaveBeenCalledWith({type:'MOUNT_DISK',payload:{diskPath:'D:/samples/two.img'}});
});


it('configures a folder without inserting media and restores a separate browse selection',()=>{
 mock.telemetry.mediaPaths=['D:/one.img','D:/two.img'];mock.telemetry.lastInsertedPath='D:/one.img';mock.telemetry.selectedMediaPath='D:/two.img';
 render(<NativeDriveBay/>);expect(screen.getByText('SELECT: two.img')).toBeInTheDocument();
 fireEvent.click(screen.getByRole('button',{name:'Gotek Select'}));
 fireEvent.change(screen.getByLabelText('Media folder'),{target:{value:'D:/library'}});
 fireEvent.click(screen.getByRole('button',{name:'Scan folder'}));
 expect(mock.send).toHaveBeenCalledExactlyOnceWith({type:'CONFIGURE_MEDIA_LIBRARY',payload:{diskPath:'D:/library'}});
 expect(screen.getByLabelText('Local image path')).toHaveValue('D:/two.img');
});
