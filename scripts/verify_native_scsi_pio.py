"""Native TEMP/ACK/REQ command and input-FIFO INQUIRY fixture.

Synthetic register setup, private target6; not firmware Load or physical timing.
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
    for _,byte in ipairs({0x12,0,0,0,36,0}) do
     assert(p:read_u8(0xe40a)&0x80~=0,'Command byte REQ missing')
     p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4)
     assert(p:read_u8(0xe40a)&0x80==0,'Target must drop REQ after ACK')
     assert(p:read_u8(0xe40a)&0x40~=0,'ACK sense missing')
     p:write_u8(0xe404,0xc4)
    end
    assert(p:read_u8(0xe40a)&7==1,'INQUIRY did not enter DATA IN')
    p:write_u8(0xe418,0);p:write_u8(0xe41a,0);p:write_u8(0xe41c,36)
    p:write_u8(0xe408,0xff);p:write_u8(0xe404,0x84)
    local response={}
    for i=1,36 do
     assert(p:read_u8(0xe40c)&3~=1,'Data FIFO reported empty during INQUIRY')
     response[i]=p:read_u8(0xe414)
     assert(p:read_u8(0xe41c)==36-i,'PIO counter did not decrement')
    end
    assert(p:read_u8(0xe408)&0x10~=0,'PIO transfer completion missing')
    assert(response[1]==5,'Wrong target type returned')
    assert(response[9]==string.byte('S') and response[10]==string.byte('O'),'Wrong target inquiry identity')
    assert(p:read_u8(0xe416)==0,'INQUIRY status must be good')
    p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
    assert(p:read_u8(0xe40a)&7==7,'MESSAGE IN phase missing')
    assert(p:read_u8(0xe416)==0,'Command-complete message missing')
    p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
    assert(p:read_u8(0xe40a)==0,'Command completion did not free bus')
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
  firmware_load=false,native_pio_inquiry=true}));f:close();m:exit()
end)
'''


def prepare(work):
    media = work / 'roms/SCSI'
    media.mkdir(parents=True)
    (media / 'CD60_2048.iso').write_bytes(bytes(4096))


if __name__ == '__main__':
    main(LUA, native_only=True, prepare_work=prepare)
