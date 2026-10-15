"""Isolated native MB89352 register-window regression, not firmware Load.

Synthetic bank-register setup is confined to this device fixture. Tests native
two-byte spacing and all transfer-counter ports; no media writes or guest patches.
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
   p:write_u8(0xe400,id)
   assert(p:read_u8(0xe400)==(1<<id),'BDID must read as a one-bit bus mask, id='..id)
   p:write_u8(0xe400,0xf8|id)
   assert(p:read_u8(0xe400)==(1<<id),'BDID upper write bits must be ignored, id='..id)
  end
  p:write_u8(0xe400,7)
  p:write_u8(0xe402,0x12)
  assert(p:read_u8(0xe402)==0x12,'SCTL readback')
  p:write_u8(0xe416,0x81)
  assert(p:read_u8(0xe416)==0x81,'TEMP port missing or misaddressed')
  p:write_u8(0xe418,1);p:write_u8(0xe41a,0x23);p:write_u8(0xe41c,0x45)
  assert(p:read_u8(0xe418)==1 and p:read_u8(0xe41a)==0x23 and p:read_u8(0xe41c)==0x45,'Transfer counter ports missing')
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12)
  assert(p:read_u8(0xe40c)==5,'Idle SSTS must report empty FIFO and zero counter, without busy/reset')
  p:write_u8(0xe41c,1)
  assert(p:read_u8(0xe40c)==1,'SSTS TC-zero must clear for a nonzero counter')
  p:write_u8(0xe41c,0)
  p:write_u8(0xe404,0x10)
  assert(p:read_u8(0xe40c)==13,'SSTS must expose asserted bus reset')
  p:write_u8(0xe404,0)
  assert(p:read_u8(0xe40c)==5,'SSTS reset must clear after deassertion')
  p:write_u8(0xe408,0xff)
  p:write_u8(0xe416,1);p:write_u8(0xe404,0x20)
  assert(p:read_u8(0xe408)==4,'Absent target SELECT must report timeout')
  assert(p:read_u8(0xe408)==4,'INTS must not clear on read')
  assert(p:read_u8(0xe40c)==5,'Absent selection must return to idle status')
  p:write_u8(0xe408,4);assert(p:read_u8(0xe408)==0,'INTS write acknowledgement')
 end)
 local f=assert(io.open('result.json','w'))
 f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),cpu='I80C196KB',native_scsi_stride=2,firmware_load=false}))
 f:close();m:exit()
end)
'''

if __name__ == '__main__':
    main(LUA, native_only=True)
