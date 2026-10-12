"""Device-level SCSI checkpoint regression; not firmware workflow acceptance."""
import argparse, json, os, subprocess, shutil
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--state-dir',type=Path,required=True)
    args=parser.parse_args();work=args.state_dir.resolve()
    if work.exists() and any(work.iterdir()):
        parser.error('Use a fresh empty private state directory')
    work.mkdir(parents=True,exist_ok=True)
    rom=work/'roms/s760';rom.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(ROOT/'roms/System/S760224.IMG',rom/'s760224.img')
    media=work/'roms/SCSI';media.mkdir(parents=True,exist_ok=True)
    image=bytes((i*29+17)%256 for i in range(257*512));(media/'HD00_512.img').write_bytes(image)
    (media/'CD10_2048.iso').write_bytes(bytes([0x5a])*2048)
    lua=r'''local json=require('json')
local m=manager.machine
local p=m.devices[':maincpu'].spaces['program']
local function w(o,v) p:write_u8(0xf020+o,v) end
local function r(o) return p:read_u8(0xf020+o) end
local function command(bytes,target)
 w(1,1);w(11,2^(target or 0));w(2,1)
 for _,b in ipairs(bytes) do w(10,b) end
end
local function read(n) local t={} for i=1,n do t[i]=r(10) end return t end
local paused=0
emu.register_frame_done(function() if not m.paused then emu.pause() end end)
emu.register_periodic(function()
 if not m.paused then return end
 paused=paused+1;if paused<2 then return end
 local ok,err=pcall(function()
 if os.getenv('S760_CHECKPOINT_COLD')=='1' then
  local f=assert(io.open('device-state.bin','rb'));local saved=f:read('a');f:close()
  assert(m:buffer_load(saved))
  local tail=read(28)
  f=assert(io.open('expected.json','r'));local expected=json.parse(f:read('a'));f:close()
  assert(json.stringify(tail)==json.stringify(expected),'Cold response differs')
  command({8,0,0,0,1,0});local sector=read(512)
  for i=1,512 do assert(sector[i]==((i-1)*29+17)%256,'Cold disk contents differ') end
  f=assert(io.open('write-state.bin','rb'));local written=f:read('a');f:close()
  assert(m:buffer_load(written))
  command({8,0,0,255,1,0});local saved_sector=read(512)
  for i=1,512 do assert(saved_sector[i]==((255*512+i)%251),'Cold written disk differs') end
  f=assert(io.open('partial-write-state.bin','rb'));local partial=f:read('a');f:close()
  assert(m:buffer_load(partial))
  for i=174,512 do w(10,(i*7)%256) end
  command({8,0,0,1,1,0});local resumed=read(512)
  for i=1,512 do assert(resumed[i]==(i*7)%256,'Cold partial write offset/data differs') end
  f=assert(io.open('cold-result.json','w'));f:write(json.stringify({passed=true,response_bytes=28,media_bytes=512,written_media=true,partial_write10=true}));f:close()
  return
 end
 command({0x12,0,0,0,36,0});read(8)
 local state=m:buffer_save()
 local f=assert(io.open('device-state.bin','wb'));f:write(state);f:close()
 local expected=read(28)
 f=assert(io.open('expected.json','w'));f:write(json.stringify(expected));f:close()
 command({3,0,0,0,18,0});read(18)
 assert(m:buffer_load(state))
 local actual=read(28)
 assert(json.stringify(actual)==json.stringify(expected),'SCSI response bytes changed after restore')
 -- Partial command: resume the last three bytes of READ CAPACITY's CDB.
 w(1,1);w(11,1);w(2,1);for _,b in ipairs({0x25,0,0,0,0,0,0}) do w(10,b) end
 state=m:buffer_save();for i=1,3 do w(10,0) end;expected=read(8)
 command({3,0,0,0,18,0});read(18);assert(m:buffer_load(state))
 for i=1,3 do w(10,0) end
 assert(json.stringify(read(8))==json.stringify(expected),'Partial CDB differs')
 -- DATA_OUT storage: compare complete paused snapshots after identical completion.
 command({0x0a,0,0,0,1,0});for i=1,173 do w(10,i%256) end
 state=m:buffer_save();for i=174,512 do w(10,i%256) end
 local completed=m:buffer_save()
 command({3,0,0,0,18,0});read(18);assert(m:buffer_load(state))
 for i=174,512 do w(10,i%256) end
 assert(m:buffer_save()==completed,'Partial DATA_OUT differs')
 command({8,0,0,0,1,0});local after_write=read(512);local writeback=true
 for i=1,512 do if after_write[i]~=i%256 then writeback=false end end
 assert(writeback,'WRITE(6) acknowledged but discarded payload')
 local function status(expected)
  assert(r(5)==0x8b,'Expected STATUS phase')
  assert(r(10)==expected,'Wrong SCSI status');assert(r(10)==0,'Wrong message')
 end
 status(0)
 -- Nonzero WRITE(10) LBA and immediate readback; untouched neighbor remains intact.
 command({0x2a,0,0,0,0,1,0,0,1,0})
 for i=1,173 do w(10,(i*7)%256) end
 state=m:buffer_save()
 f=assert(io.open('partial-write-state.bin','wb'));f:write(state);f:close()
 for i=174,512 do w(10,(i*7)%256) end;status(0)
 -- Change the pending write offset, then recover the saved nonzero-LBA transfer.
 command({0x0a,0,0,2,1,0});assert(m:buffer_load(state))
 for i=174,512 do w(10,(i*7)%256) end;status(0)
 command({0x28,0,0,0,0,1,0,0,1,0});local block=read(512)
 for i=1,512 do assert(block[i]==(i*7)%256,'WRITE(10) offset/data mismatch') end;status(0)
 command({8,0,0,2,1,0});block=read(512)
 for i=1,512 do assert(block[i]==((1024+i-1)*29+17)%256,'Neighbor damaged') end
 -- Reset after partial payload must not modify the target.
 command({0x2a,0,0,0,0,1,0,0,1,0});for i=1,173 do w(10,0xee) end
 command({8,0,0,1,1,0});block=read(512)
 for i=1,512 do assert(block[i]==(i*7)%256,'Aborted write changed disk') end
 -- Zero READ/WRITE(10) succeeds without entering a data phase.
 for _,op in ipairs({0x28,0x2a}) do command({op,0,0,0,0,0,0,0,0,0});status(0) end
 -- Out-of-range read and write: CHECK CONDITION + ILLEGAL REQUEST / LBA range.
 for _,op in ipairs({0x28,0x2a}) do
  command({op,0,0xff,0xff,0xff,0xff,0,0,1,0});status(2)
  state=m:buffer_save()
  command({3,0,0,0,18,0});local sense=read(18)
  assert(sense[3]==5 and sense[13]==0x21,'Missing range sense')
  assert(m:buffer_load(state));command({3,0,0,0,18,0});sense=read(18)
  assert(sense[3]==5 and sense[13]==0x21,'Sense lost on checkpoint')
  command({3,0,0,0,18,0});sense=read(18);assert(sense[3]==0 and sense[13]==0,'Sense not cleared')
 end
 -- CD-ROM is protected; sense belongs to that target and the CD bytes stay intact.
 command({0x2a,0,0,0,0,0,0,0,1,0},1);status(2)
 command({3,0,0,0,18,0},0);local sense=read(18);assert(sense[3]==0,'Sense leaked across targets')
 command({3,0,0,0,18,0},1);sense=read(18);assert(sense[3]==7 and sense[13]==0x27,'Missing write-protect sense')
 command({8,0,0,0,1,0},1);block=read(2048)
 for i=1,2048 do assert(block[i]==0x5a,'CD-ROM changed') end
 -- WRITE(6) count zero means 256 sectors. Last sector and guard bound verified.
 command({0x0a,0,0,0,0,0})
 for i=1,256*512 do w(10,i%251) end;status(0)
 command({8,0,0,255,1,0});block=read(512)
 for i=1,512 do assert(block[i]==(255*512+i)%251,'WRITE(6) zero-count length mismatch') end
 command({8,0,1,0,1,0});block=read(512)
 for i=1,512 do assert(block[i]==((256*512+i-1)*29+17)%256,'WRITE(6) overrun') end
 f=assert(io.open('write-state.bin','wb'));f:write(m:buffer_save());f:close()

 f=assert(io.open('result.json','w'));f:write(json.stringify({passed=true,remaining_bytes=28,partial_cdb=true,partial_data_out=true,writeback_supported=writeback,write10=true,range_sense=true,cd_protection=true,aborted_write=true,zero_counts=true,sense_recall=true}));f:close()
 end)
 if not ok then local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=false,error=tostring(err)}));f:close() end
 m:exit()
end)
'''
    script=work/'probe.lua';script.write_text(lua)
    env={k:v for k,v in os.environ.items() if not k.startswith('S760_')}
    command=[str(ROOT/'mame-source/mames760.exe'),'s760','-rompath',str(work/'roms'),'-pluginspath',str(ROOT/'mame-source/plugins'),'-video','none','-sound','none','-nothrottle','-skip_gameinfo','-autoboot_delay','0','-autoboot_script',str(script),'-cfg_directory',str(work/'cfg'),'-nvram_directory',str(work/'nvram')]
    with (work/'mame.log').open('wb') as log:
        result=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert result.returncode==0,result.returncode
    result=json.loads((work/'result.json').read_text());print(json.dumps(result));assert result['passed'],result
    assert (media/'HD00_512.img').read_bytes()==image, 'Guest WRITE modified source file'
    # Change the same-sized host image before cold restart: checkpoint must restore saved bytes.
    (media/'HD00_512.img').write_bytes(bytes(len(image)));env['S760_CHECKPOINT_COLD']='1'
    with (work/'cold.log').open('wb') as log:
        cold=subprocess.run(command,cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    assert cold.returncode==0,cold.returncode
    result=json.loads((work/'cold-result.json').read_text());print(json.dumps(result));assert result['passed'],result
if __name__=='__main__':main()
