"""Isolated KB baseline state-time tests, Intel270651-003 Table3.3B.
Private synthetic RAM/PC fixture; not original firmware or physical bus timing.
Stack cases use unambiguously internal register RAM or external RAM, no crossing.
"""
from verify_bmovi_fetch import main
LUA = r'''
local m=manager.machine local cpu=m.devices[':maincpu']
local p=cpu.spaces['program'] local r=cpu.spaces['register'] local json=require('json')
local cases={{name='marker_baseline',code={},count=0,states=0}}
local function add(name,code,count,states,extra)
 local c={name=name,code=code,count=count,states=states};for k,v in pairs(extra or {}) do c[k]=v end;cases[#cases+1]=c
end
add('SKIP',{0,0},256,3)
for _,v in ipairs({{'CLR',1},{'NOT',2},{'NEG',3},{'DEC',5},{'INC',7},{'CLRB',0x11},{'NOTB',0x12},{'NEGB',0x13},{'DECB',0x15},{'INCB',0x17}}) do add(v[1],{v[2],0x50},256,3) end
add('EXT',{6,0x50},256,4);add('EXTB',{0x16,0x50},256,4)
for _,v in ipairs({{'SHR',8},{'SHL',9},{'SHRA',10},{'SHRB',0x18},{'SHLB',0x19},{'SHRAB',0x1a}}) do
 add(v[1]..'_zero',{v[2],0,0x50},256,7);add(v[1]..'_one',{v[2],1,0x50},256,7)
end
add('SHRL_one',{0x0c,1,0x50},256,8)
add('NORML_zero',{0x0f,0x58,0x50},256,9)
add('SJMP',{0x20,0},256,7);add('LJMP',{0xe7,0,0},256,7)
add('BR',{0xe3,0x2c},1,7,{to_end=true})
add('DJNZ_taken',{0xe0,0x50,0},128,9,{value=200})
add('DJNZW_taken',{0xe1,0x50,0},128,9,{value=0x500})
add('DJNZW_not_taken',{0xe1,0x50,0},1,5,{value=1})
for _,stack in ipairs({'internal','external'}) do
 local sp=stack=='internal' and 0xe0 or 0x7000
 add('SCALL_RET_'..stack,{0x28,2,0x20,1,0xf0},128,stack=='internal' and 29 or 34,{sp=sp})
 add('LCALL_RET_'..stack,{0xef,2,0,0x20,1,0xf0},128,stack=='internal' and 29 or 34,{sp=sp})
 add('RET_'..stack,{0xf0},1,stack=='internal' and 11 or 14,{sp=sp,to_end=true,return_address=true})
 add('TRAP_'..stack,{0xf7},1,stack=='internal' and 16 or 18,{sp=sp,to_end=true})
 for _,v in ipairs({{'PUSHF',0xf2,6,8,-2},{'POPF',0xf3,7,10,2},{'PUSHA',0xf4,12,18,-4},{'POPA',0xf5,12,18,4}}) do
  add(v[1]..'_'..stack,{v[2]},8,stack=='internal' and v[3] or v[4],{sp=(v[5]>0 and stack=='internal') and 0xb0 or sp,sp_step=v[5]})
 end
end
local index=1 local begin_time=nil local end_time=nil local results={}
local startmark={0xc7,1,0,0x60,0x48} local endmark={0xc7,1,2,0x60,0x48,0x27,0xfe}
local function writecode(address,code) for i,b in ipairs(code) do p:write_u8(address+i-1,b) end end
local function setup()
 for slot=0,3 do p:write_u16(0x100+slot*2,slot*16);p:write_u16(0x108+slot*2,slot*16) end
 r:write_u8(0x14,0);r:write_u8(8,0);r:write_u8(0x13,0);cpu.state['PSW'].value=0
 for a=0x80,0xff do r:write_u8(a,0) end
 for a=0x6f00,0x7100 do p:write_u8(a,0) end
 local c=cases[index];r:write_u8(0x48,1);r:write_u16(0x50,c.value or 1);r:write_u16(0x52,0x8000);r:write_u16(0x2c,0x5000);r:write_u16(0x18,c.sp or 0x7000)
 if c.return_address then if c.sp<0x100 then r:write_u16(c.sp,0x5000) else p:write_u16(c.sp,0x5000) end end
 p:write_u16(0x2010,0x5000);writecode(0x5000,endmark)
 local code={};for _,b in ipairs(startmark) do code[#code+1]=b end
 for i=1,c.count do for _,b in ipairs(c.code) do code[#code+1]=b end end
 if not c.to_end then for _,b in ipairs(endmark) do code[#code+1]=b end end
 writecode(0x3000,code);begin_time=nil;end_time=nil;cpu.state['PC'].value=0x3000
end
marker=p:install_write_tap(0x6000,0x6003,'control-state-markers',function(a,d,mask)
 if a==0x6000 then begin_time=m.time:as_double() elseif a==0x6002 then end_time=m.time:as_double() end
end)
setup()
emu.register_frame_done(function()
 if not end_time then return end
 local c=cases[index];local elapsed=end_time-begin_time
 local expected_sp=(c.sp or 0x7000)+(c.sp_step or 0)*c.count
 if c.return_address then expected_sp=expected_sp+2 elseif c.code[1]==0xf7 then expected_sp=expected_sp-2 end
 results[#results+1]={name=c.name,count=c.count,states=c.states,elapsed_seconds=elapsed,final_sp=r:read_u16(0x18),expected_sp=expected_sp,stack_balanced=r:read_u16(0x18)==expected_sp}
 if index<#cases then index=index+1;setup();return end
 local passed=true;local failures={}
 for i=2,#results do
  local v=results[i];v.differential_seconds=v.elapsed_seconds-results[1].elapsed_seconds;v.expected_seconds=v.count*v.states*2/16000000
  v.state_error_per_unit=(v.differential_seconds-v.expected_seconds)*8000000/v.count
  if not v.stack_balanced or math.abs(v.differential_seconds-v.expected_seconds)>1e-9 then passed=false;failures[#failures+1]=v.name end
 end
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=passed,cpu='I80C196KB',clock_hz=16000000,results=results,failures=failures,error=passed and '' or 'KB Table3.3B state-time mismatch'}));f:close();m:exit()
end)
'''
if __name__=='__main__': main(LUA,native_only=True)
