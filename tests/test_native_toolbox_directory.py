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
  local status,data=vendor(0xd9,1,8);assert(status==0 and #data==8 and data[1]==0 and data[2]==4,'capability subset')
  status,data=vendor(0xd9,0,8);assert(status==0 and data[3]==0 and data[1]==255,'fixture target group')
  status,data=vendor(0xd9,3,64);assert(status==0 and text(data)=='/Files','default directory')
  status,data=vendor(0xd2);assert(status==0 and data[1]==5,'root count')
  status,data=vendor(0xd0);assert(status==0 and #data==200 and data[1]==0 and data[2]==1 and data[82]==0,'root listing types')
  assert(data[39]==19 and data[40]==136,'5000-byte big endian size')
  status,data=path('/Files/Sub'..string.char(0));assert(status==0,'set directory DATA OUT')
  status,data=vendor(0xd9,3,64);assert(text(data)=='/Files/Sub','get changed directory')
  status,data=vendor(0xd9,2,0);assert(status==0,'zero length set no-op')
  status,data=vendor(0xd2);assert(status==0 and data[1]==2,'subdirectory count skips hidden')
  status,data=command(2,{0xd1,0,0,0,0,0,0,0,0,0});assert(status==0 and #data==2 and data[1]==17 and data[2]==34,'listed file read')
  status,data=path('/Files/../escape');assert(status==2,'parent escape accepted')
  local err=sense(2);assert(err[3]==5 and err[13]==0x24,'invalid path sense')
  status,data=vendor(0xd9,3,64);assert(text(data)=='/Files/Sub','bad path changed directory')
  status,data=path('/Files/Missing');assert(status==2,'missing path created')
  status,data=path(string.char(0));assert(status==0,'reset default')
  status,data=path('/Files/Exact');assert(status==0,'exact100 directory')
  status,data=vendor(0xd2);assert(status==0 and data[1]==100,'100 entry count')
  status,data=vendor(0xd0);assert(status==0 and #data==4000,'100 entry payload')
  for i=0,99 do assert(data[i*40+1]==i and data[i*40+2]==1,'index/type mismatch') end
  status,data=command(2,{0xd1,99,0,0,0,0,0,0,0,0});assert(status==0 and #data==1 and data[1]==99,'last index read')
  status,data=path('/Files/Overflow');assert(status==0,'overflow directory')
  status,data=vendor(0xd2);assert(status==2 and #data==0,'101 entry count must reject')
  status,data=vendor(0xd0);assert(status==2 and #data==0,'profile rejects overflow listing')
  status,data=vendor(0xd9,1,9);assert(status==2,'invalid capability length')
  status,data=vendor(0xd9,255,8);assert(status==2,'unknown subcommand')
  status,data=command(2,{0x28,0,0,0,0,0,0,0,1,0});assert(status==0 and #data==512,'ordinary disk after DATA OUT')
  for _,v in ipairs(data) do assert(v==0,'directory command modified disk') end
  checked=25
 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),unsupported_cases=checked,qualification='Synthetic native SPC register fixture; no firmware/hardware acceptance.'}));f:close();m:exit()
end)
'''


def test_native_toolbox_directory_fixture(tmp_path):
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
    assert observation['unsupported_cases'] == 25
    assert all((media/name).read_bytes() == bytes(8192) for name in ('HD00_512.img','HD20_512.img'))
