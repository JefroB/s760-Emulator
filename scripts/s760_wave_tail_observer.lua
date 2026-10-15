-- Read-only verifier helper. Replace __WANTED__ with bounded source-derived word addresses.
-- Spliced into the normal runtime protocol; never writes CPU/guest memory or bus data.
local function start_bus_trace(first,last_address,include_fdc)
    local cpu=machine.devices[':maincpu'];local space=cpu.spaces['program']
    local trace={rows={},dropped=0,accesses=0};local regs={};local wanted={__WANTED__}
    for i=0,31 do regs[i]=space:read_u8(0x100+i) end
    local wave={0,0,0,0}
    trace.read=space:install_write_tap(0x100,0x11f,'observer-banks',function(a,d,m)
        if (m&255)~=0 then regs[a-0x100]=d&255 end
        if m>255 and a<0x11f then regs[a-0xff]=(d>>8)&255 end
    end)
    trace.write=space:install_write_tap(0xc008,0xc00f,'observer-wave',function(a,d,m)
        if (regs[14]|(regs[15]<<8))~=0x400 then return end
        local o=a-0xc000
        if o>=12 then
            if (m&255)~=0 then wave[o-12]=d&255 end
            if m>255 and o<15 then wave[o-11]=(d>>8)&255 end
        elseif o==8 and m==65535 then
            local word=wave[2]|(wave[3]<<8)|(wave[0]<<16)|(wave[1]<<24)
            if not wanted[word] then return end
            if #trace.rows>=4096 then trace.dropped=trace.dropped+1;return end
            trace.rows[#trace.rows+1]={word_address=word,data=d,pc=cpu.state['PC'].value,seconds=machine.time:as_double()}
            trace.accesses=trace.accesses+1
        end
    end)
    return trace
end
