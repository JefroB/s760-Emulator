"""Isolated native initiator/target identity fixture; no firmware Load claim.

Only controller registers are exercised. A private zero-filled target6 image
establishes presence, not a supported Roland filesystem or PIO/DMA handshake.
"""
from verify_bmovi_fetch import main

LUA = r'''
local m=manager.machine
local p=m.devices[':maincpu'].spaces['program']
local json=require('json')
emu.register_frame_done(function()
 emu.pause()
 local ok,err=pcall(function()
  p:write_u16(0x10e,0x0400)
  for id=0,7 do
   p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12)
   p:write_u8(0xe400,0xf8|id)
   assert(p:read_u8(0xe400)==(1<<id),'BDID mask id='..id)
   if id~=6 then
    p:write_u8(0xe416,(1<<id)|0x40)
    p:write_u8(0xe404,0x20)
    assert(p:read_u8(0xe408)==0x10,'SELECT must exclude initiator bit, id='..id)
    assert(p:read_u8(0xe40a)==0x8a,'Selected target must enter command phase')
    assert(p:read_u8(0xe40c)&0x80~=0,'Initiator connected status missing')
    -- Direct-data fixture only; native transfer handshakes remain unqualified.
    for _,byte in ipairs({0x12,0,0,0,36,0}) do p:write_u8(0xe414,byte) end
    local response={}
    for i=1,36 do response[i]=p:read_u8(0xe414) end
    assert(response[1]==5,'Wrong target type returned')
    assert(response[9]==string.byte('S') and response[10]==string.byte('O'),'Wrong target inquiry identity')
    assert(p:read_u8(0xe414)==0,'INQUIRY status must be good')
    assert(p:read_u8(0xe414)==0,'Command-complete message missing')
   end
   p:write_u8(0xe408,0xff)
   p:write_u8(0xe416,1<<id);p:write_u8(0xe404,0x20)
   assert(p:read_u8(0xe408)==4,'Initiator-only mask must time out, id='..id)
   assert(p:read_u8(0xe40a)==0,'Initiator-only selection must leave bus free')
   p:write_u8(0xe408,0xff)
   p:write_u8(0xe414,0x40);p:write_u8(0xe416,0);p:write_u8(0xe404,0x20)
   assert(p:read_u8(0xe408)==4,'Empty mask must not reuse previous target')
  end
 end)
 local f=assert(io.open('result.json','w'))
 f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),initiator_ids=8,
  present_target_selections=7,target=6,target_type='CD-ROM',inquiry_bytes=36,
  firmware_load=false,native_transfer_handshake=false}));f:close();m:exit()
end)
'''


def prepare(work):
    media = work / 'roms/SCSI'
    media.mkdir(parents=True)
    (media / 'CD60_2048.iso').write_bytes(bytes(4096))


if __name__ == '__main__':
    main(LUA, native_only=True, prepare_work=prepare)
