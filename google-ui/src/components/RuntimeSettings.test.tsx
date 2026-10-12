import {act,fireEvent,render,screen} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import {RuntimeSettings} from './RuntimeSettings';

describe('Runtime settings',()=>{
  const configuration={bootRom:'boot.bin',systemDisk:'system.img',mediaDirectory:'samples',sound:true};
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
});
