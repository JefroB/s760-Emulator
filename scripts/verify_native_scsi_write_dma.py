"""Isolated native SCSI RAM78/waveA0 output, round-trip, bounds and interrupted WRITE."""
from verify_bmovi_fetch import main

def prepare(work):
    folder=work/'roms/SCSI';folder.mkdir(parents=True)
    (folder/'HD00_512.img').write_bytes(bytes([0xa5])*131072)
LUA=r'''
local m=manager.machine;local p=m.devices[':maincpu'].spaces['program'];local json=require('json')
emu.register_frame_done(function()
 emu.pause();local ok,err=pcall(function()
  p:write_u16(0x10e,0x0400);p:write_u16(0x10a,0x10)
  local function command(op,lba)
   p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
   p:write_u8(0xe416,0x81);p:write_u8(0xe404,0x20)
   for _,b in ipairs({op,0,0,0,0,lba,0,0,1,0}) do
    p:write_u8(0xe416,b);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   end
  end
  local function transfer_count()
   p:write_u8(0xe418,0);p:write_u8(0xe41a,2);p:write_u8(0xe41c,0)
   p:write_u8(0xe408,0xff);p:write_u8(0xe404,0x80);p:write_u16(0x118,512)
  end
  for i=0,511 do p:write_u8(0x4000+i,(i*29+7)&255) end
  command(0x2a,3);transfer_count()
  p:write_u16(0x11a,0xffff);p:write_u8(0x11c,0x0f);p:write_u8(0x11d,0x78)
  assert(p:read_u16(0x118)==512 and p:read_u8(0xe41a)==2,'Invalid RAM source consumed output')
  p:write_u16(0x11a,0x4000);p:write_u8(0x11c,0);p:write_u8(0x11d,0x78)
  assert(p:read_u16(0x118)==0 and p:read_u8(0xe41a)==0,'RAM output DMA did not complete')
  assert(p:read_u16(0x11a)==0x4200 and p:read_u8(0xe408)&0x10~=0,'RAM address or SPC completion incorrect')
  command(0x28,3);transfer_count()
  for i=0,511 do assert(p:read_u8(0xe414)==((i*29+7)&255),'RAM WRITE/readback mismatch') end
  -- A reset of an incomplete command must preserve the previous sector.
  command(0x2a,3);p:write_u8(0xe414,0x11)
  command(0x28,3);transfer_count()
  for i=0,511 do assert(p:read_u8(0xe414)==((i*29+7)&255),'Interrupted WRITE committed partial sector') end
  -- Fill a wave source through its real register port, then direct output DMA.
  for i=0,255 do
   p:write_u16(0xc00e,i);p:write_u16(0xc00c,0);p:write_u16(0xc008,((i*2*13+5)&255)|((((i*2+1)*13+5)&255)<<8))
  end
  command(0x2a,4);transfer_count()
  p:write_u16(0xc00e,0);p:write_u16(0xc00c,0x100);p:write_u8(0x11d,0xa0)
  assert(p:read_u16(0x118)==512 and p:read_u8(0xe41a)==2,'Invalid wave source consumed output')
  p:write_u16(0xc00e,0);p:write_u16(0xc00c,0);p:write_u8(0x11d,0xa0)
  assert(p:read_u16(0x118)==0 and p:read_u8(0xe41a)==0,'Wave output DMA did not complete')
  assert(p:read_u16(0xc00e)==256,'Wave output address did not advance')
  command(0x28,4);transfer_count()
  for i=0,511 do assert(p:read_u8(0xe414)==((i*13+5)&255),'Wave WRITE/readback mismatch') end
 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),ram_dma=0x78,wave_dma=0xa0,bytes=1024,interrupted_command=true,firmware_save=false}));f:close();m:exit()
end)
'''
if __name__=='__main__':main(LUA,native_only=True,prepare_work=prepare)
