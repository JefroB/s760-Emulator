"""Isolated CPU state-time regression against Intel KB Table3-3B.

Private synthetic instruction blocks only; not original-firmware acceptance.
Differential timestamps cancel the identical marker instructions. No IRQ source
is enabled, including during the EI block.
"""
from verify_bmovi_fetch import main

LUA = r'''
local m=manager.machine local cpu=m.devices[':maincpu']
local p=cpu.spaces['program'] local r=cpu.spaces['register'] local json=require('json')
local cases={{name='marker_baseline',opcode=0xfd,count=0},
 {name='CLRC',opcode=0xf8,count=2048},{name='SETC',opcode=0xf9,count=2048},
 {name='DI',opcode=0xfa,count=2048},{name='EI',opcode=0xfb,count=2048},
 {name='CLRVT',opcode=0xfc,count=2048},{name='NOP',opcode=0xfd,count=2048}}
local index=1 local begin_time=nil local end_time=nil local results={}
local function setup()
 for slot=0,3 do p:write_u16(0x100+slot*2,slot*16);p:write_u16(0x108+slot*2,slot*16) end
 r:write_u8(0x14,0);r:write_u8(8,0);r:write_u8(0x13,0);cpu.state['PSW'].value=0;r:write_u8(0x48,1)
 local code={0xc7,1,0,0x60,0x48}
 for i=1,cases[index].count do code[#code+1]=cases[index].opcode end
 for _,b in ipairs({0xc7,1,2,0x60,0x48,0x27,0xfe}) do code[#code+1]=b end
 for i,b in ipairs(code) do p:write_u8(0x3000+i-1,b) end
 begin_time=nil end_time=nil cpu.state['PC'].value=0x3000
end
marker=p:install_write_tap(0x6000,0x6003,'state-time-markers',function(a,d,mask)
 if a==0x6000 then begin_time=m.time:as_double() elseif a==0x6002 then end_time=m.time:as_double() end
end)
setup()
emu.register_frame_done(function()
 if not end_time then return end
 local elapsed=end_time-begin_time
 results[#results+1]={name=cases[index].name,count=cases[index].count,elapsed_seconds=elapsed}
 if index<#cases then index=index+1 setup() return end
 local passed=true
 for i=2,#results do
  local measured=results[i].elapsed_seconds-results[1].elapsed_seconds
  results[i].differential_seconds=measured
  results[i].expected_seconds=results[i].count*2*2/16000000
  if math.abs(measured-results[i].expected_seconds)>1e-9 then passed=false end
 end
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=passed,cpu='I80C196KB',clock_hz=16000000,
  states_per_instruction=2,oscillator_cycles_per_state=2,results=results,error=passed and '' or 'instruction state times differ from Intel KB Table3-3B'}));f:close();m:exit()
end)
'''

if __name__ == '__main__':
    main(LUA, native_only=True)
