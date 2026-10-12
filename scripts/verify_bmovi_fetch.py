"""Isolated MAME CPU decode regression, NOT firmware/hardware acceptance.

Uses scratch RAM/PC and disables interrupts. Does not qualify BMOVI timing,
interrupt restart, count semantics, or applicability to physical 80C196KB.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LUA = r'''
local m=manager.machine
local cpu=m.devices[':maincpu']
local p=cpu.spaces['program']; local r=cpu.spaces['register']
local json=require('json')
local cases={0,1,3}
local index=1
local frames=0
local function setup()
 if os.getenv('S760_BANKED_OS') then
  -- Synthetic fixture only: map code/data to the same private RAM pages.
  for slot=0,3 do
   p:write_u16(0x100+slot*2,slot*16)
   p:write_u16(0x108+slot*2,slot*16)
  end
 end
 r:write_u8(0x14,0);r:write_u8(8,0);r:write_u8(0x13,0)
 cpu.state['PSW'].value=0
 -- BMOVI RW28,RW2C; LD RW30,#BEEF; SJMP self.
 local code={0xcd,0x2c,0x28,0xa1,0xef,0xbe,0x30,0x27,0xfe}
 for i,b in ipairs(code) do p:write_u8(0x3000+i-1,b) end
 for i=0,4 do p:write_u16(0x4000+i*2,0x1230+i);p:write_u16(0x4200+i*2,0xa5a5) end
 r:write_u16(0x28,0x4000);r:write_u16(0x2a,0x4200)
 r:write_u16(0x2c,cases[index]);r:write_u16(0x30,0)
 cpu.state['PC'].value=0x3000
end
setup()
emu.register_frame_done(function()
 frames=frames+1;if frames%2~=0 then return end
 local ok,err=pcall(function()
  assert(r:read_u16(0x30)==0xbeef,'following instruction skipped, count='..cases[index])
  for i=0,4 do
   local expected=i<cases[index] and (0x1230+i) or 0xa5a5
   assert(p:read_u16(0x4200+i*2)==expected,'copy/bounds mismatch')
  end
  assert(r:read_u16(0x28)==0x4000+2*cases[index],'source operand mismatch')
  assert(r:read_u16(0x2a)==0x4200+2*cases[index],'destination operand mismatch')
 end)
 if not ok or index==#cases then
  local f=assert(io.open('result.json','w'))
  f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),cases=cases,interrupts=false,
   cpu=os.getenv('S760_BANKED_OS') and 'I80C196KB' or 'N8097BH'}));f:close()
  m:exit()
 else index=index+1;setup() end
end)
'''


def main(lua=LUA, native_only=False):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state-dir', type=Path, required=True)
    parser.add_argument('--banked', action='store_true', default=native_only, help='Exercise the native I80C196KB core')
    args = parser.parse_args()
    work = args.state_dir.resolve()
    if work.exists() and any(work.iterdir()):
        parser.error('Use a fresh empty private state directory')
    rom = work / 'roms/s760'
    rom.mkdir(parents=True)
    shutil.copyfile(ROOT / 'roms/System/S760224.IMG', rom / 's760224.img')
    script = work / 'probe.lua'
    script.write_text(lua, encoding='utf-8')
    command = [str(ROOT / 'mame-source/mames760.exe'), 's760', '-rompath',
               str(work / 'roms'), '-pluginspath', str(ROOT / 'mame-source/plugins'),
               '-video', 'none', '-sound', 'none', '-nothrottle', '-skip_gameinfo',
               '-autoboot_delay', '0', '-autoboot_script', str(script),
               '-cfg_directory', str(work / 'cfg'), '-nvram_directory', str(work / 'nvram')]
    env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
    if args.banked:
        env['S760_BANKED_OS'] = '1'
    with (work / 'mame.log').open('wb') as log:
        subprocess.run(command, cwd=work, env=env, stdout=log,
                       stderr=subprocess.STDOUT, timeout=60, check=True,
                       creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    result = json.loads((work / 'result.json').read_text())
    print(json.dumps(result))
    assert result['passed'], result


if __name__ == '__main__':
    main()
