import {act,fireEvent,render,screen} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import {RuntimeSettings} from './RuntimeSettings';

describe('Runtime settings',()=>{
  const configuration={bootRom:'boot.bin',systemDisk:'system.img',mediaDirectory:'samples',sound:true};
  it('uses host-driven plugin settings without standalone audio controls',()=>{
    render(<RuntimeSettings configuration={configuration} hostDriven pending={false} onApply={()=>{}} onCancel={()=>{}}/>);
    expect(screen.queryByLabelText('Enable audio output')).toBeNull();
    expect(screen.getByText('Save plugin settings')).toBeDisabled();
    fireEvent.click(screen.getByLabelText('Apply after reloading the plugin in the host'));
    expect(screen.getByText('Save plugin settings')).toBeEnabled();
  });
  it('selects a Windows output endpoint with fresh restart confirmation',()=>{
    const apply=vi.fn(),refresh=vi.fn();
    render(<RuntimeSettings configuration={{...configuration,audioBackend:'wasapi'}} audioOutputDevices={[{id:'endpoint',name:'MOTU Stereo Out 3-4'}]} onRefreshAudioOutputDevices={refresh} pending={false} onApply={apply} onCancel={()=>{}}/>);
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.change(screen.getByLabelText('Windows output device'),{target:{value:'endpoint'}});
    expect(screen.getByText('Apply settings and start')).toBeDisabled();
    fireEvent.click(screen.getByText('Refresh Windows outputs'));expect(refresh).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.click(screen.getByText('Apply settings and start'));
    expect(apply).toHaveBeenCalledWith({...configuration,audioBackend:'wasapi',audioOutputDevice:'endpoint'});
  });
  it('configures ASIO driver, stereo pairs and buffer without exposing MME input',()=>{
    const apply=vi.fn(),refresh=vi.fn();
    render(<RuntimeSettings configuration={{...configuration,audioBackend:'auto',recordingDevice:''}} asioDevices={[{name:'MOTU',inputs:4,outputs:8}]} onRefreshAsioDevices={refresh} pending={false} onApply={apply} onCancel={()=>{}}/>);
    fireEvent.change(screen.getByLabelText('Audio output backend'),{target:{value:'asio'}});
    expect(refresh).toHaveBeenCalledOnce();
    expect(screen.queryByLabelText('Recording device')).toBeNull();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    expect(screen.getByText('Apply settings and start')).toBeDisabled();
    fireEvent.change(screen.getByLabelText('ASIO driver'),{target:{value:'MOTU'}});
    fireEvent.change(screen.getByLabelText('ASIO output pair'),{target:{value:'3'}});
    fireEvent.change(screen.getByLabelText('ASIO input pair'),{target:{value:'1'}});
    fireEvent.change(screen.getByLabelText('ASIO buffer (frames)'),{target:{value:'256'}});
    expect(screen.getByText('Apply settings and start')).toBeDisabled();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.click(screen.getByText('Apply settings and start'));
    expect(apply).toHaveBeenCalledWith({...configuration,audioBackend:'asio',recordingDevice:'',asioDriver:'MOTU',asioOutputChannel:3,asioInputChannel:1,asioBufferFrames:256});
  });
  it('selects an explicit recording device and refreshes the available inputs',()=>{
    const apply=vi.fn(), refresh=vi.fn();
    render(<RuntimeSettings configuration={{...configuration,recordingDevice:''}} recordingDevices={[{id:'motu',name:'Stereo In 1-2'}]} onRefreshRecordingDevices={refresh} pending={false} onApply={apply} onCancel={()=>{}}/>);
    expect(screen.getByLabelText('Recording device')).toHaveValue('');
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.change(screen.getByLabelText('Recording device'),{target:{value:'motu'}});
    expect(screen.getByText('Apply settings and start')).toBeDisabled();
    fireEvent.click(screen.getByText('Refresh recording devices'));
    expect(refresh).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.click(screen.getByText('Apply settings and start'));
    expect(apply).toHaveBeenCalledWith({...configuration,recordingDevice:'motu'});
  });
  it('requires confirmation for the current draft and delegates validated intent',()=>{
    const apply=vi.fn();render(<RuntimeSettings configuration={configuration} pending={false} onApply={apply} onCancel={()=>{}}/>);
    const button=screen.getByText('Apply settings and start');expect(button).toBeDisabled();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.change(screen.getByLabelText('Boot ROM (32KB)'),{target:{value:'other.bin'}});
    expect(button).toBeDisabled();
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.click(button);expect(apply).toHaveBeenCalledWith({...configuration,bootRom:'other.bin'});
  });
  it('locks fields while the host applies settings',()=>{
    render(<RuntimeSettings configuration={configuration} pending onApply={()=>{}} onCancel={()=>{}}/>);
    expect(screen.getByLabelText('Boot ROM (32KB)')).toBeDisabled();
    expect(screen.getByText('Starting sampler…')).toBeDisabled();
    expect(screen.getByText('Cancel settings')).toBeDisabled();
  });
  it('requires confirmation after audio edits and rejects an empty buffer target',()=>{
    const apply=vi.fn();render(<RuntimeSettings configuration={{...configuration,audioBackend:'auto',audioLatencyMs:0}} pending={false} onApply={apply} onCancel={()=>{}}/>);
    const button=screen.getByText('Apply settings and start');
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.change(screen.getByLabelText('Audio output backend'),{target:{value:'wasapi'}});
    expect(button).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Audio buffer target (ms)'),{target:{value:''}});
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    expect(button).toBeDisabled();
    fireEvent.change(screen.getByLabelText('Audio buffer target (ms)'),{target:{value:'60'}});
    fireEvent.click(screen.getByLabelText('Replace current sampler memory and restart'));
    fireEvent.click(button);
    expect(apply).toHaveBeenCalledWith({...configuration,audioBackend:'wasapi',audioLatencyMs:60});
  });
});
