import {fireEvent,render,screen} from '@testing-library/react';
import {describe,it,expect,vi} from 'vitest';
import {StandaloneKeyboard} from './StandaloneKeyboard';

describe('Standalone keyboard note lifetime',()=>{
  it('supports chords, suppresses keyboard repeats and releases every held note on unmount',()=>{
    const send=vi.fn();const view=render(<StandaloneKeyboard send={send} connected/>);
    const c=screen.getByRole('button',{name:'C4 MIDI 60'});
    const e=screen.getByRole('button',{name:'E4 MIDI 64'});
    fireEvent.keyDown(c,{key:'Enter'});fireEvent.keyDown(c,{key:'Enter',repeat:true});
    fireEvent.keyDown(e,{key:' '});
    expect(send.mock.calls).toEqual([['NOTE_ON',{note:60,velocity:100}],['NOTE_ON',{note:64,velocity:100}]]);
    fireEvent.keyUp(c,{key:'Enter'});view.unmount();
    expect(send.mock.calls.slice(2)).toEqual([['NOTE_OFF',{note:60,velocity:0}],['NOTE_OFF',{note:64,velocity:0}]]);
  });
  it('releases held notes when the window loses focus and disables disconnected input',()=>{
    const send=vi.fn();const view=render(<StandaloneKeyboard send={send} connected/>);
    fireEvent.keyDown(screen.getByRole('button',{name:'C3 MIDI 48'}),{key:'Enter'});
    fireEvent.blur(window);
    expect(send).toHaveBeenLastCalledWith('NOTE_OFF',{note:48,velocity:0});
    view.rerender(<StandaloneKeyboard send={send} connected={false}/>);
    expect(screen.getByRole('button',{name:'C3 MIDI 48'})).toBeDisabled();
  });
});
