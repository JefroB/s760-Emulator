"""Native SPC device regression; synthetic register fixture, not firmware UI QA."""
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
  local function command(target,cdb)
   p:write_u8(0xe408,0xff);p:write_u8(0xe416,0x80|(1<<target));p:write_u8(0xe404,0x24)
   assert(p:read_u8(0xe40a)==0x8a,'selection target '..target)
   for _,byte in ipairs(cdb) do
    assert(p:read_u8(0xe40a)==0x8a,'early CDB phase')
    p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   end
   local data={}
   while p:read_u8(0xe40a)==0x89 do
    assert(#data<64,'unbounded response')
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
  for _,cdb in ipairs({{0x1f,0,0,0,0,0},{0x3f,0xa5,0x5a,0x12,0x34,0x56,0x78,0x9a,0xbc,0xde},{0xbf,0,0,0,0,0,0,0,0,0,0,0}}) do
   local status,data=command(0,cdb)
   assert(status==2 and #data==0,string.format('unsupported opcode %02x returned status %02x',cdb[1],status))
   local other=sense(2);assert(other[3]==0 and other[13]==0,'sense leaked across targets')
   local failed=sense(0);assert(failed[3]==5 and failed[13]==0x20 and failed[14]==0,'invalid-opcode sense missing')
   local cleared=sense(0);assert(cleared[3]==0 and cleared[13]==0,'sense did not clear')
   checked=checked+1
  end
  local status,data=command(0,{0,0,0,0,0,0});assert(status==0 and #data==0,'ready after errors')
  status,data=command(0,{0x1b,0,0,0,1,0});assert(status==0 and #data==0,'boot-ROM START UNIT rejected')
  status,data=command(0,{0x1b,0,0,0,3,0});assert(status==2 and #data==0,'unsupported load/eject accepted')
  local invalid=sense(0);assert(invalid[3]==5 and invalid[13]==0x24,'invalid START UNIT field sense')
  status,data=command(0,{0x25,0,0,0,0,0,0,0,0,0});assert(status==0 and #data==8 and data[4]==15 and data[7]==2,'capacity after errors')
 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),unsupported_cases=checked,qualification='Synthetic native SPC register fixture; no firmware/hardware acceptance.'}));f:close();m:exit()
end)
'''


def test_native_unsupported_command_status_and_per_target_sense(tmp_path):
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
    assert observation['unsupported_cases'] == 3
    assert all((media/name).read_bytes() == bytes(8192) for name in ('HD00_512.img','HD20_512.img'))
