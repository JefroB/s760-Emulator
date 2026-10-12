import {act,fireEvent,render,screen,cleanup} from '@testing-library/react';
import {afterEach,describe,expect,it,vi} from 'vitest';
import {NativePanelControls} from './NativePanelControls';

afterEach(()=>{cleanup();vi.useRealTimers();});
describe('native panel chords',()=>{
 it('routes Value wheel and keyboard steps through the encoder rather than S1/S2',()=>{
  const send=vi.fn();render(<NativePanelControls send={send}/>);
  const knob=screen.getByRole('button',{name:'VALUE knob'});
  expect(knob).toBeEnabled();
  fireEvent.wheel(knob,{deltaY:1});
  fireEvent.keyDown(knob,{key:'ArrowUp'});
  expect(send.mock.calls).toEqual([['DIAL_DELTA',{id:'ALPHA',delta:-1}],['DIAL_DELTA',{id:'ALPHA',delta:1}]]);
 });
 it('routes the separate Menu button to the encoder push input and releases it on blur',()=>{
  const send=vi.fn();render(<NativePanelControls send={send}/>);
  fireEvent.keyDown(screen.getByRole('button',{name:'MENU'}),{key:'Enter'});
  fireEvent(window,new Event('blur'));
  expect(send.mock.calls).toEqual([['BUTTON_PRESS',{id:'MENU'}],['BUTTON_RELEASE',{id:'MENU'}]]);
 });
 it('holds Shift and target together, then releases target before Shift',()=>{
  vi.useFakeTimers();const send=vi.fn();render(<NativePanelControls send={send} functionsOnly/>);
  const b=screen.getByRole('button',{name:'F4'});
  fireEvent.keyDown(b,{key:'Enter'});fireEvent.keyUp(b,{key:'Enter'});
  expect(send.mock.calls).toEqual([['BUTTON_PRESS',{id:'SHIFT'}],['BUTTON_PRESS',{id:'F1'}]]);
  act(()=>vi.advanceTimersByTime(120));
  expect(send.mock.calls.slice(2)).toEqual([['BUTTON_RELEASE',{id:'F1'}],['BUTTON_RELEASE',{id:'SHIFT'}]]);
 });
 it('releases a chord on lost window focus and unmount without stuck Shift',()=>{
  const send=vi.fn();const view=render(<NativePanelControls send={send}/>);
  fireEvent.keyDown(screen.getByRole('button',{name:'HOME'}),{key:' '});
  fireEvent(window,new Event('blur'));
  expect(send.mock.calls.slice(-2)).toEqual([['BUTTON_RELEASE',{id:'LEFT'}],['BUTTON_RELEASE',{id:'SHIFT'}]]);
  fireEvent.keyDown(screen.getByRole('button',{name:'JUMP'}),{key:'Enter'});view.unmount();
  expect(send.mock.calls.slice(-2)).toEqual([['BUTTON_RELEASE',{id:'RIGHT'}],['BUTTON_RELEASE',{id:'SHIFT'}]]);
 });
 it('preserves the physical navigation order and disables disconnected input',()=>{
  const send=vi.fn();render(<NativePanelControls send={send} enabled={false}/>);
  expect(screen.queryByRole('button',{name:'PERF'})).toBeNull();
  expect(Array.from(screen.getByLabelText('Navigation cluster').querySelectorAll('button')).map(b=>b.getAttribute('aria-label'))).toEqual(['S1/DEC','UP','S2/INC','LEFT','DOWN','RIGHT']);
  expect(screen.getByRole('button',{name:'COMMAND'})).toBeDisabled();
 });
});
