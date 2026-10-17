"""Isolated native CPU stack regression; no original firmware is executed.

Qualifies the KB-mode flag-stack contract against Intel270651-003 and the
original ROM's manual WSR-low/INT_MASK1-high frame. The legacy flat-mode
compatibility stubs are intentionally outside this test.
"""
from verify_bmovi_fetch import main

LUA = r'''
local m=manager.machine
local cpu=m.devices[':maincpu']
local p=cpu.spaces['program'];local r=cpu.spaces['register']
local json=require('json')
local all=false
local manual=false
local phase=0
local frames=0
local function setup()
 for slot=0,3 do
  p:write_u16(0x100+slot*2,slot*16);p:write_u16(0x108+slot*2,slot*16)
 end
 r:write_u8(8,0);r:write_u8(0x12,0)
 r:write_u16(0x18,0x5000)
 p:write_u16(0x4ffa,0xdead);p:write_u16(0x5000,0xbeef)
 p:write_u8(0x3000,all and 0xf4 or 0xf2)
 p:write_u8(0x3001,0x27);p:write_u8(0x3002,0xfe)
 p:write_u8(0x3020,all and 0xf5 or 0xf3)
 p:write_u8(0x3021,0x27);p:write_u8(0x3022,0xfe)
 if manual then
  -- Original ROM1A0..1AA: PUSHF; saveWSR/mask inRW3E; PUSH; clear mask.
  local code={0xf2,0xb0,0x14,0x3e,0xb0,0x13,0x3f,0xc8,0x3e,0x11,0x13,0x27,0xfe}
  for i,b in ipairs(code) do p:write_u8(0x3000+i-1,b) end
 end
 r:write_u8(0x13,0x45);r:write_u8(0x14,0x0e) -- documented valid SFR window14
 cpu.state['PSW'].value=0x8005 -- interrupt enable clear
 cpu.state['PC'].value=0x3000
 phase=0
end
setup()
emu.register_frame_done(function()
 frames=frames+1;if frames%2~=0 then return end
 local ok,err=pcall(function()
  if phase==0 then
   assert(r:read_u16(0x18)==(all and 0x4ffc or 0x4ffe),'PUSH stack pointer')
   assert(p:read_u16(0x4ffe)==0x8005,'PUSH PSW word')
   assert(cpu.state['PSW'].value==0,'PUSH PSW not cleared')
   if all then
    assert(p:read_u16(0x4ffc)==0x450e,'Mask/window word: WSR must be low byte')
    assert(r:read_u8(0x13)==0,'PUSHA/manual frame did not clear mask')
    assert(r:read_u8(0x14)==0x0e,'PUSHA/manual frame must retain WSR')
   else
    assert(r:read_u8(0x13)==0x45 and r:read_u8(0x14)==0x0e,'PUSHF changed mask/window')
   end
   cpu.state['PC'].value=0x3020
  else
   assert(r:read_u16(0x18)==0x5000,'POP stack pointer')
   assert(cpu.state['PSW'].value==0x8005,'POP PSW restore')
   assert(r:read_u8(0x13)==0x45 and r:read_u8(0x14)==0x0e,'POP mask/window restore')
   assert(p:read_u16(0x4ffa)==0xdead and p:read_u16(0x5000)==0xbeef,'Stack guard damaged')
  end
 end)
 if not ok or (phase==1 and manual) then
  local f=assert(io.open('result.json','w'))
  f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),cpu='I80C196KB',
   pushf_popf=true,pusha_popa=true,manual_frame=manual,interrupts=false,
   saved_extension=p:read_u16(0x4ffc),wsr=r:read_u8(0x14),mask1=r:read_u8(0x13)}));f:close();m:exit()
 elseif phase==0 then phase=1
 else if all then manual=true else all=true end setup() end
end)
'''

if __name__ == '__main__':
    main(LUA, native_only=True)
