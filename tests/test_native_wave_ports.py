"""Synthetic native wave-port register fixture, not firmware workflow QA."""
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
local done=false
emu.register_frame_done(function()
 if done then return end
 done=true;emu.pause()
 local ok,err=pcall(function()
  local wave
  for name,index in pairs(m.devices[':'].items) do
   if name:match('/m_native_wave$') then wave=emu.item(index) end
  end
  assert(wave and wave.count==0x2000000)
  p:write_u16(0x10e,0x400)
  local function address(n) p:write_u16(0xc00c,n>>16);p:write_u16(0xc00e,n&0xffff) end
  local function cursor() return p:read_u16(0xc00e)|(p:read_u16(0xc00c)<<16) end
  local function word(n) return wave:read(n*2)|(wave:read(n*2+1)<<8) end
  address(0xffff);p:write_u16(0xc008,0xa55a)
  assert(word(0xffff)==0xa55a and cursor()==0xffff,'Fixed port changed')
  p:write_u8(0xc00a,0x34)
  assert(word(0xffff)==0xa55a and cursor()==0xffff,'Low byte committed early')
  p:write_u8(0xc00b,0x12)
  assert(word(0xffff)==0x1234,'Sequential write discarded')
  assert(cursor()==0x10000,'Sequential cursor did not carry')
  p:write_u16(0xc00a,0x80ff)
  assert(word(0x10000)==0x80ff and cursor()==0x10001,'Sequential endian/increment')
  address(0xffffff);p:write_u16(0xc00a,0x7654)
  assert(word(0xffffff)==0x7654 and cursor()==0x1000000,'Last valid word')
  local first=word(0);p:write_u16(0xc00a,0x1122)
  assert(word(0)==first and word(0xffffff)==0x7654 and cursor()==0x1000001,'Out-of-range aliased')
  address(0xffff);p:write_u16(0xc008,0xbeef)
  assert(word(0xffff)==0xbeef and word(0x10000)==0x80ff and cursor()==0xffff,'Fixed/sequential isolation')
 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err)}));f:close();m:exit()
end)
'''


def test_native_fixed_and_sequential_wave_write_ports(tmp_path):
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
    env['S760_BANKED_OS'] = '1'
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
