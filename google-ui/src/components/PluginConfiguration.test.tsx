import {fireEvent,render,screen} from '@testing-library/react';
import {beforeEach,describe,expect,it,vi} from 'vitest';
import {PluginConfiguration} from './PluginConfiguration';
const bridge=vi.hoisted(()=>({send:vi.fn(),configuration:{root:'D:/S760',stateRoot:'D:/State',bootRom:'D:/boot.bin',systemDisk:'D:/system.img',mediaDirectory:'D:/Media',needsConfiguration:true,saved:false,revision:0,error:'',startupError:'Missing Boot ROM'}}));
vi.mock('../bridge/BridgeContext',()=>({useBridgeClient:()=>({send:bridge.send}),useBridgeTelemetry:()=>({pluginConfiguration:bridge.configuration})}));
describe('Plugin configuration recovery',()=>{
  beforeEach(()=>{bridge.send.mockClear();Object.assign(bridge.configuration,{revision:0,saved:false,error:'',needsConfiguration:true});});
  it('shows startup errors and preserves the form after rejected settings',()=>{
    const {rerender}=render(<PluginConfiguration/>);
    expect(screen.getByRole('dialog',{name:'Plugin configuration'})).toBeVisible();
    expect(screen.getByText('Startup: Missing Boot ROM')).toBeVisible();
    expect(screen.queryByLabelText('Enable audio output')).toBeNull();
    expect(screen.getByLabelText('S-760 installation directory')).toHaveValue('D:/S760');
    fireEvent.change(screen.getByLabelText('Boot ROM (32KB)'),{target:{value:'relative.bin'}});
    fireEvent.click(screen.getByLabelText('Apply after reloading the plugin in the host'));
    fireEvent.click(screen.getByText('Save plugin settings'));
    expect(bridge.send).toHaveBeenCalledWith({type:'CONFIGURE_PLUGIN',payload:{root:'D:/S760',stateRoot:'D:/State',bootRom:'relative.bin',systemDisk:'D:/system.img',mediaDirectory:'D:/Media',waveMemoryMb:32,confirmReload:true}});
    expect(screen.getByText('Saving settings…')).toBeDisabled();
    Object.assign(bridge.configuration,{revision:1,error:'bootRom must be an absolute path'});rerender(<PluginConfiguration/>);
    expect(screen.getByText('bootRom must be an absolute path')).toBeVisible();
    expect(screen.getByLabelText('Boot ROM (32KB)')).toHaveValue('relative.bin');
    expect(screen.getByText('Save plugin settings')).toBeEnabled();
  });
});
