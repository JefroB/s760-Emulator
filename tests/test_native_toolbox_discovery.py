"""Opt-in D1 device regression; synthetic SPC fixture, not firmware acceptance."""
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
emu.register_frame_done(function()
 emu.pause()
 local checked=0
 local ok,err=pcall(function()
  p:write_u16(0x10e,0x400)
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
  local function command(target,cdb,payload)
   p:write_u8(0xe408,0xff);p:write_u8(0xe416,0x80|(1<<target));p:write_u8(0xe404,0x24)
   assert(p:read_u8(0xe40a)==0x8a,'selection target '..target)
   for _,byte in ipairs(cdb) do
    assert(p:read_u8(0xe40a)==0x8a,'early CDB phase')
    p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   end
   if payload then
    for _,byte in ipairs(payload) do
     assert(p:read_u8(0xe40a)==0x88,'DATA OUT phase')
     p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
    end
   end
   local data={}
   while p:read_u8(0xe40a)==0x89 do
    assert(#data<4096,'unbounded response')
    data[#data+1]=p:read_u8(0xe416)
    p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   end
   assert(p:read_u8(0xe40a)==0x8b,'status phase')
   local status=p:read_u8(0xe416)
   p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   assert(p:read_u8(0xe40a)==0x8f and p:read_u8(0xe416)==0,'complete message')
   p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   assert(p:read_u8(0xe40a)==0,'bus release')
   return status,data
  end
  local function sense(target)
   local status,data=command(target,{3,0,0,0,18,0})
   assert(status==0 and #data==18,'sense payload');return data
  end
  local function vendor(op,sub,length,payload)
   return command(2,{op,sub or 0,0,0,0,0,0,0,length or 0,0},payload)
  end
  local function path(value)
   local payload={};for i=1,#value do payload[#payload+1]=value:byte(i) end
   return vendor(0xd9,2,#payload,payload)
  end
  local function text(data) local s='';for _,v in ipairs(data) do if v==0 then break end;s=s..string.char(v) end;return s end
  local status,data=command(2,{0x12,0,0,0,96,0})
  assert(status==0 and #data==50 and data[5]==45,'extended inquiry length')
  local name='';for i=37,49 do name=name..string.char(data[i]) end
  assert(name=='BlueSCSIvTEST' and data[50]==0,'fixture identification and API')
  status,data=command(2,{0x12,0,0,0,36,0});assert(status==0 and #data==36,'short inquiry')
  status,data=command(0,{0x12,0,0,0,96,0});assert(status==0 and #data==36,'ordinary target not advertised')
  status,data=command(2,{0x1a,8,0x31,0,64,0})
  assert(status==0 and #data==48 and data[1]==47 and data[4]==0 and data[5]==0x31 and data[6]==42,'vendor page header')
  local signature='';for i=7,48 do signature=signature..string.char(data[i]) end
  assert(signature=='BlueSCSI is the BEST STOLEN FROM BLUESCSI'..string.char(0),'vendor signature')
  status,data=command(2,{0x1a,8,0x31,0,8,0});assert(status==0 and #data==8,'short vendor page')
  status,data=command(2,{0x1a,8,0x71,0,64,0});assert(status==2 and #data==0,'unsupported page control')
  data=sense(2);assert(data[3]==5 and data[13]==0x24,'invalid field sense')
  status,data=command(0,{0x1a,8,0x31,0,64,0});assert(status==2,'ordinary target not advertised by mode page')
  status,data=vendor(0xd9,1,8);assert(status==0 and data[2]==4,'capability still usable')
  checked=9
 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),unsupported_cases=checked,qualification='Synthetic native SPC register fixture; no firmware/hardware acceptance.'}));f:close();m:exit()
end)
'''


def test_native_toolbox_discovery_fixture(tmp_path):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT/'mame-source/mames760.exe'))
    source = ROOT/'S760224.IMG'
    if not exe.is_file() or not source.is_file():
        pytest.skip('Local native executable and user-provided OS required')
    rom = tmp_path/'roms/s760'
    rom.mkdir(parents=True)
    shutil.copyfile(source, rom/'s760224.img')
    media = tmp_path/'roms/SCSI'
    media.mkdir()
    for name in ('HD00_512.img', 'HD20_512.img'):
        (media/name).write_bytes(bytes(8192))
    lua = tmp_path/'probe.lua'
    lua.write_text(LUA, encoding='utf-8')
    env = {k:v for k,v in os.environ.items() if not k.startswith('S760_')}
    env['S760_BANKED_OS'] = '1'
    fixture=tmp_path/'files';fixture.mkdir()
    (fixture/'0.wav').write_bytes(bytes(i%251 for i in range(5000)))
    (fixture/'1.wav').write_bytes(b'')
    (fixture/'Sub').mkdir()
    (fixture/'Sub/a.wav').write_bytes(bytes([17,34]))
    (fixture/'Sub/b.wav').write_bytes(b'')
    (fixture/'Sub/.hidden').write_bytes(b'ignored')
    for folder,count in [('Exact',100),('Overflow',101)]:
        (fixture/folder).mkdir()
        for n in range(count):(fixture/folder/f'{n:03}.wav').write_bytes(bytes([n]))
    env['S760_TOOLBOX_TEST_ROOT']=str(fixture)
    env['S760_TOOLBOX_TEST_TARGET']='2'
    command = [str(exe), 's760', '-rompath', str(tmp_path/'roms'),
               '-pluginspath', str(ROOT/'mame-source/plugins'),
               '-video', 'none', '-sound', 'none', '-nothrottle', '-skip_gameinfo',
               '-autoboot_delay', '0', '-autoboot_script', str(lua),
               '-cfg_directory', str(tmp_path/'cfg'), '-nvram_directory', str(tmp_path/'nvram')]
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, timeout=30,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    (tmp_path/'console.log').write_text(result.stdout+result.stderr, encoding='utf-8')
    assert result.returncode == 0, (result.stdout+result.stderr)[-2000:]
    observation = json.loads((tmp_path/'result.json').read_text())
    assert observation['passed'], observation
    assert observation['unsupported_cases'] == 9
    assert all((media/name).read_bytes() == bytes(8192) for name in ('HD00_512.img','HD20_512.img'))
