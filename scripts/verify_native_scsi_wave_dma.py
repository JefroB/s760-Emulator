"""Isolated native SCSI-to-wave DMA84 counters and bounds; not firmware Load proof."""
from verify_bmovi_fetch import main
def prepare(work):
    folder=work/'roms/SCSI';folder.mkdir(parents=True)
    (folder/'CD60_2048.iso').write_bytes(bytes((i*17+3)&255 for i in range(131072)))
LUA=r'''
local m=manager.machine;local p=m.devices[':maincpu'].spaces['program'];local json=require('json')
emu.register_frame_done(function()
 emu.pause();local ok,err=pcall(function()
  p:write_u16(0x10e,0x0400)
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
  p:write_u8(0xe416,0xc0);p:write_u8(0xe404,0x20)
  for _,byte in ipairs({0x12,0,0,0,36,0}) do
   p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  p:write_u8(0xe418,0);p:write_u8(0xe41a,0);p:write_u8(0xe41c,36)
  p:write_u8(0xe408,0xff);p:write_u8(0xe404,0x84)
  -- Last18 words of32MiB wave RAM; oversized/odd transfer must not consume input.
  p:write_u16(0xc00e,0xffee);p:write_u16(0xc00c,0xff)
  p:write_u16(0x118,37);p:write_u8(0x11d,0x84)
  assert(p:read_u16(0x118)==37 and p:read_u8(0xe41c)==36,'Oversized DMA consumed input')
  p:write_u16(0x118,36);p:write_u16(0xc00e,0);p:write_u16(0xc00c,0x100)
  p:write_u8(0x11d,0x84)
  assert(p:read_u16(0x118)==36 and p:read_u8(0xe41c)==36,'Out-of-wave DMA consumed input')
  p:write_u16(0xc00e,0xffee);p:write_u16(0xc00c,0xff);p:write_u8(0x11d,0x84)
  assert(p:read_u16(0x118)==0,'Wave DMA count did not exhaust')
  assert(p:read_u8(0xe41c)==0 and p:read_u8(0xe408)&0x10~=0,'SPC completion missing')
  assert(p:read_u16(0xc00e)==0 and p:read_u16(0xc00c)==0x100,'Wave address did not advance')
  p:write_u16(0xc00e,0xffee);p:write_u16(0xc00c,0xff)
  local bytes={};for i=1,18 do bytes[#bytes+1]=p:read_u8(0xc00a);bytes[#bytes+1]=p:read_u8(0xc00b) end
  assert(bytes[1]==5 and bytes[9]==string.byte('S') and bytes[10]==string.byte('O'),'Wave payload differs from INQUIRY')
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
  p:write_u8(0xe416,0xc0);p:write_u8(0xe404,0x20)
  for _,byte in ipairs({0x28,0,0,0,0,0,0,0,32,0}) do
   p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  p:write_u8(0xe418,1);p:write_u8(0xe41a,0);p:write_u8(0xe41c,0)
  p:write_u8(0xe408,0xff);p:write_u8(0xe404,0x84)
  p:write_u16(0xc00e,0);p:write_u16(0xc00c,0);p:write_u16(0x118,0);p:write_u8(0x11d,0x84)
  assert(p:read_u8(0xe418)==0,'Zero-encoded64KiB transfer did not complete')
  assert(p:read_u16(0xc00e)==0x8000,'64KiB wave address did not advance')
  p:write_u16(0xc00e,0);p:write_u16(0xc00c,0)
  assert(p:read_u8(0xc00a)==3 and p:read_u8(0xc00b)==20,'64KiB first word incorrect')
  p:write_u16(0xc00e,0x7fff)
  assert(p:read_u8(0xc00a)==225 and p:read_u8(0xc00b)==242,'64KiB last word incorrect')
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
  p:write_u8(0xe416,0xc0);p:write_u8(0xe404,0x20)
  for _,byte in ipairs({0x28,0,0,0,0,0,0,0,58,0}) do
   p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  p:write_u8(0xe418,1);p:write_u8(0xe41a,0xd0);p:write_u8(0xe41c,0)
  p:write_u8(0xe408,0xff);p:write_u8(0xe404,0x80)
  p:write_u16(0xc00e,0);p:write_u16(0xc00c,0);p:write_u16(0x118,0xd000);p:write_u8(0x11d,0x84)
  assert(p:read_u8(0xe418)==0 and p:read_u8(0xe41a)==0,'24-bit SPC count was truncated to16 bits')
  assert(p:read_u16(0xc00e)==0xe800,'118784-byte wave address did not advance')
  p:write_u16(0xc00e,0xe7ff)
  assert(p:read_u8(0xc00a)==225 and p:read_u8(0xc00b)==242,'Large-transfer last word incorrect')
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
  p:write_u8(0xe416,0xc0);p:write_u8(0xe404,0x20)
  for _,byte in ipairs({0x2a,0,0,0,0,0,0,0,1,0}) do
   p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  assert(p:read_u8(0xe40a)&7==3 and p:read_u8(0xe416)==2,'CD WRITE was not rejected before DATA OUT')



 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),transfer_sizes={36,65536,118784},cd_write_protected=true,dma=0x84,firmware_load=false}));f:close();m:exit()
end)
'''
if __name__=='__main__':main(LUA,native_only=True,prepare_work=prepare)
