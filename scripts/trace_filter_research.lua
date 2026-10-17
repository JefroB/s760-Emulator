-- Optional read-only filter research observers. Append after s760_runtime.lua.
-- Records the original firmware and scheduler fields with bounded row counts.
-- Host state handles are cached; no guest memory/register values are cached.
local machine=manager.machine
local cpu=machine.devices[':maincpu']
local pc_state=cpu.state['PC']
local mem=cpu.spaces['program']
local registers=cpu.spaces['register']
local rows={}
local controls={}
local dropped=0
local tap=mem:install_write_tap(0x0200,0xffff,'resonant-firmware-inputs',function(addr,data,mask)
 local page=mem:read_u16(0x108+2*(addr>>14))
 local physical=(page<<10)+(addr&0x3fff)
 -- Most writes are unrelated to the filter. Avoid allocating state views
 -- in this hot callback; the cached entry still exports the live PC.
 if physical~=0x101018 and physical~=0x101030 then return end
 local pc=pc_state.value
 if physical==0x101018 and #controls<10000 then
  local partial=registers:read_u16(0x7c)
  controls[#controls+1]=string.format('%.17g,%d,%d,%d,%d,%d,%d,%d,%d',
   machine.time:as_double(),pc,data,mask,mem:read_u16(0x10c),
   registers:read_u16(0x84),registers:read_u16(0x5c),registers:read_u16(0x5e),mem:read_u8((partial+0x4057)&0xffff))
 end
 if physical~=0x101030 or pc~=0x480b then return end
 if #rows>=10000 then dropped=dropped+1;return end
 local channel=registers:read_u16(0x84)
 local index=registers:read_u16(0x86)
 local partial=registers:read_u16(0x7c)
 rows[#rows+1]=string.format('%.17g,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d',
  machine.time:as_double(),channel,index,mem:read_u16(0x10a),mem:read_u16(0x10c),
  mem:read_u16((0x84b6+index)&0xffff),mem:read_u16((0x8516+index)&0xffff),
  mem:read_u8((0x8c36+channel)&0xffff),mem:read_u8((partial+0x4051)&0xffff),
  mem:read_u8((partial+0x405a)&0xffff),data,mask,registers:read_u16(0x5c)) ..
  string.format(',%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d',
   mem:read_u8((0x8c1e+channel)&0xffff),
   mem:read_u16(0x8306+index),mem:read_u16(0x8336+index),mem:read_u16(0x8366+index),mem:read_u16(0x8396+index),
   mem:read_u16(0x83c6+index),mem:read_u16(0x83f6+index),mem:read_u16(0x8426+index),mem:read_u16(0x8456+index),
   mem:read_u16(0x84e6+index),mem:read_u16(0x8486+index))
end)
_G.s760_firmware_observer={tap=tap}
_G.s760_firmware_observer.stop=emu.add_machine_stop_notifier(function()
 tap:remove()
 local path=os.getenv('S760_FIRMWARE_INPUT_TRACE')
 assert(path)
 local output=assert(io.open(path,'w'))
 output:write('# dropped=',tostring(dropped),'\n')
 output:write('seconds,channel,index,context_page,table_page,envelope,base_cutoff,velocity,sensitivity,depth,word,mask,result_register,stage,level0,level1,level2,level3,count0,count1,count2,count3,divisor,delta\n')
 output:write(table.concat(rows,'\n'),'\n')
 output:close()
 local control_output=assert(io.open(path..'.controls.csv','w'))
 control_output:write('seconds,pc,word,mask,table_page,channel,index_register,result_register,partial_time1\n')
 control_output:write(table.concat(controls,'\n'),'\n')
 control_output:close()
end)


local scheduler_rows={}
local scheduler_dropped=0
local function observe_scheduler(kind,addr,data,mask)
 if machine.time:as_double()<78 then return end
 if addr~=4 and addr~=6 and addr~=10 then return end
 if #scheduler_rows>=250000 then scheduler_dropped=scheduler_dropped+1;return end
 local pc=pc_state.value
 scheduler_rows[#scheduler_rows+1]=string.format('%.17g,%s,%d,%d,%d,%d,%d',machine.time:as_double(),kind,addr,data,mask,pc,mem:read_u16(0x108+2*(pc>>14)))
end
local sw=registers:install_write_tap(4,11,'scheduler-writes',function(a,d,m) observe_scheduler('w',a,d,m) end)
local sr=registers:install_read_tap(4,11,'scheduler-reads',function(a,d,m) observe_scheduler('r',a,d,m) end)
_G.s760_scheduler_observer={sw=sw,sr=sr}
_G.s760_scheduler_observer.stop=emu.add_machine_stop_notifier(function()
 sw:remove();sr:remove()
 local f=assert(io.open(os.getenv('S760_FIRMWARE_INPUT_TRACE')..'.scheduler.csv','w'))
 f:write('# dropped=',tostring(scheduler_dropped),'\nseconds,kind,address,data,mask,pc,page\n');f:write(table.concat(scheduler_rows,'\n'),'\n');f:close()
end)
