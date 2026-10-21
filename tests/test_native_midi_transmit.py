"""Native UART component fixture; separate from ordinary firmware acceptance."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
LUA = r'''
local m=manager.machine
local p=m.devices[':maincpu'].spaces['program']
local json=require('json')
local started=false
emu.register_frame_done(function()
 if started then return end
 started=true
 coroutine.wrap(function()
  local checked=0
  local ok,err=pcall(function()
   assert((p:read_u8(0x114)&2)==2,'MIDI transmitter never becomes ready')
   local output=assert(m.devices[':midiout'],'MIDI output endpoint missing')
   local received
   for name,index in pairs(output.items) do
    if name:match('/m_rcv_byte_received$') then received=emu.item(index) end
   end
   assert(received,'Output serial receiver unavailable')
   for _,byte in ipairs({0x00,0xff,0xf0,0x7e,0x00,0x7f,0x01,0xf7,0x90,0x3c,0x64}) do
    assert((p:read_u8(0x114)&3)==2,'Idle RX/TX status')
    p:write_u8(0x116,byte)
    assert((p:read_u8(0x114)&2)==0,'TX did not become busy')
    -- Attempts while busy cannot replace the in-flight serial frame.
    p:write_u8(0x116,byte~0xff)
    assert(emu.wait(0.0001))
    assert((p:read_u8(0x114)&2)==0,'TX completed before ten MIDI bits')
    assert(emu.wait(0.0003))
    assert((p:read_u8(0x114)&3)==2,'TX did not finish or echoed into RX')
    assert(received:read(0)==byte,'MIDI output byte differs')
    checked=checked+1
   end
   assert(emu.midi_send(':midiin',string.char(0x93,0x40,0x7f)))
   assert(emu.wait(0.002))
   for _,byte in ipairs({0x93,0x40,0x7f}) do
    assert((p:read_u8(0x114)&3)==3,'RX/TX status bits interfere')
    assert(p:read_u8(0x116)==byte,'RX FIFO changed by TX')
   end
   assert((p:read_u8(0x114)&3)==2,'RX did not drain')
  end)
  local f=assert(io.open('result.json','w'))
  f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),output_bytes=checked,qualification='Native UART register/component test, no forced guest state used as firmware acceptance.'}));f:close();m:exit()
 end)()
end)
'''


def test_native_midi_transmit_ready_serial_bytes_and_rx_isolation(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT / 'mame-source/mames760.exe'))
    source = ROOT / 'S760224.IMG'
    if not exe.is_file() or not source.is_file():
        pytest.skip('Local native executable and user-provided OS required')
    rom = tmp_path / 'roms/s760'
    rom.mkdir(parents=True)
    shutil.copyfile(source, rom / 's760224.img')
    lua = tmp_path / 'probe.lua'
    lua.write_text(LUA, encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
    env.update(S760_BANKED_OS='1', S760_IC4_MIDI_EXPERIMENT='1')
    command = [str(exe), 's760', '-rompath', str(tmp_path / 'roms'),
               '-pluginspath', str(ROOT / 'mame-source/plugins'),
               '-video', 'none', '-sound', 'none', '-nothrottle', '-skip_gameinfo',
               '-autoboot_delay', '0', '-autoboot_script', str(lua),
               '-cfg_directory', str(tmp_path / 'cfg'), '-nvram_directory', str(tmp_path / 'nvram')]
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, timeout=30,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    (tmp_path / 'console.log').write_text(result.stdout + result.stderr, encoding='utf-8')
    assert result.returncode == 0, (result.stdout + result.stderr)[-2000:]
    observation = json.loads((tmp_path / 'result.json').read_text())
    assert observation['passed'], observation
    assert observation['output_bytes'] == 11
