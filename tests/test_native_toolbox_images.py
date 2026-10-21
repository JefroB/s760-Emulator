"""Opt-in image-switch profile: synthetic SPC qualification, not firmware acceptance."""
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]

LUA = r'''
local m=manager.machine
local p=m.devices[':maincpu'].spaces['program']
local json=require('json')
emu.register_frame_done(function()
 emu.pause()
 local checked=0
 local ok,err=pcall(function()
  p:write_u16(0x10e,0x400)
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12);p:write_u8(0xe400,7)
  local function command(target,cdb,payload)
   p:write_u8(0xe408,0xff);p:write_u8(0xe416,0x80|(1<<target));p:write_u8(0xe404,0x24)
   assert(p:read_u8(0xe40a)==0x8a,'selection target '..target)
   for _,byte in ipairs(cdb) do
    assert(p:read_u8(0xe40a)==0x8a,'early CDB phase target '..target..' opcode '..cdb[1])
    p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   end
   if payload then
    for _,byte in ipairs(payload) do
     assert(p:read_u8(0xe40a)==0x88,'DATA OUT phase')
     p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
    end
   end
   local data={}
   while p:read_u8(0xe40a)==0x89 do
    assert(#data<4096,'unbounded response')
    data[#data+1]=p:read_u8(0xe416)
    p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   end
   assert(p:read_u8(0xe40a)==0x8b,'status phase')
   local status=p:read_u8(0xe416)
   p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   assert(p:read_u8(0xe40a)==0x8f and p:read_u8(0xe416)==0,'complete message')
   p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
   assert(p:read_u8(0xe40a)==0,'bus release')
   return status,data
  end
  local function sense(target)
   local status,data=command(target,{3,0,0,0,18,0})
   assert(status==0 and #data==18,'sense payload');return data
  end
  local function vendor(op,sub,length,payload)
   return command(2,{op,sub or 0,0,0,0,0,0,0,length or 0,0},payload)
  end
  local function path(value)
   local payload={};for i=1,#value do payload[#payload+1]=value:byte(i) end
   return vendor(0xd9,2,#payload,payload)
  end
  local function text(data) local s='';for _,v in ipairs(data) do if v==0 then break end;s=s..string.char(v) end;return s end

  local function be32(data,at) return (data[at]<<24)|(data[at+1]<<16)|(data[at+2]<<8)|data[at+3] end
  for _,id in ipairs({1,2,3,6}) do
   local status,data=command(id,{0xda,0,0,0,0,0,0,0,0,0});assert(status==0 and #data==1 and data[1]==100,'image count target '..id)
   status,data=command(id,{0xd7,0,0,0,0,0,0,0,0,0});assert(status==0 and #data==4000 and data[1]==0 and data[3961]==99,'image list target '..id)
   status,data=command(id,{0xd8,99,0,0,0,0,0,0,0,0});assert(status==0 and #data==0,'switch target '..id)
   status,data=command(id,{0,0,0,0,0,0});assert(status==2,'first readiness absent');data=sense(id);assert(data[3]==2 and data[13]==0x3a,'absent sense')
   status,data=command(id,{0,0,0,0,0,0});assert(status==2,'unit attention');data=sense(id);assert(data[3]==6 and data[13]==0x28,'media change sense')
   status,data=command(id,{0,0,0,0,0,0});assert(status==0,'ready')
   status,data=command(id,{0x25,0,0,0,0,0,0,0,0,0});assert(status==0 and be32(data,1)==1 and be32(data,5)==(id==2 and 512 or 2048),'new capacity')
   status,data=command(id,{0x28,0,0,0,0,0,0,0,1,0});assert(status==0 and data[1]==id+99,'exact switched read')
   status,data=command(id,{0x2a,0,0,0,0,0,0,0,1,0});assert(status==2,'read only library target');data=sense(id);assert(data[3]==7 and data[13]==0x27,'write protected sense')
  end
  local status,data=command(1,{0xd8,255,0,0,0,0,0,0,0,0});assert(status==0,'upstream invalid index status retained')
  status,data=command(1,{0,0,0,0,0,0});assert(status==2,'failed mount unavailable');data=sense(1);assert(data[3]==2,'failed mount not ready')
  status,data=command(1,{0xd8,0,0,0,0,0,0,0,0,0});assert(status==0,'recovery switch')
  for i=1,3 do status,data=command(1,{0,0,0,0,0,0});if status==2 then sense(1) end end
  assert(status==0,'recovered ready')
  status,data=command(1,{0x1b,0,0,0,2,0});assert(status==0,'eject and cycle')
  status,data=command(1,{0x1b,0,0,0,3,0});assert(status==0,'close tray')
  status,data=command(1,{0,0,0,0,0,0});if status==2 then sense(1) end
  status,data=command(1,{0x28,0,0,0,0,0,0,0,1,0});assert(status==0 and data[1]==2,'eject advanced image')
  status,data=command(0,{0xda,0,0,0,0,0});assert(status==2,'unconfigured target remains ordinary');data=sense(0);assert(data[3]==5 and data[13]==0x20,'unsupported sense')
  checked=4
 end)
 local f=assert(io.open('result.json','w'));f:write(json.stringify({passed=ok,error=ok and '' or tostring(err),target_profiles=checked,qualification='Synthetic native SPC register fixture; no firmware/hardware acceptance.'}));f:close();m:exit()
end)
'''


def _run_image_fixture(tmp_path, program=LUA, image_count=100, image_setup=None, stall_after=None, expected_profiles=None):
    exe = Path(os.environ.get('S760_MAME_EXE', ROOT/'mame-source/mames760.exe'))
    source = ROOT/'S760224.IMG'
    if not exe.is_file() or not source.is_file():
        pytest.skip('Local native executable and user-provided OS required')
    rom = tmp_path/'roms/s760'
    rom.mkdir(parents=True)
    shutil.copyfile(source, rom/'s760224.img')
    media = tmp_path/'roms/SCSI'
    media.mkdir()
    for name in ('HD00_512.img', 'HD20_512.img','CD10_2048.iso','CD30_2048.iso','CD60_2048.iso'):
        (media/name).write_bytes(bytes(8192))
    lua = tmp_path/'probe.lua'
    lua.write_text(program, encoding='utf-8')
    env = {k:v for k,v in os.environ.items() if not k.startswith('S760_')}
    env['S760_BANKED_OS'] = '1'
    fixture=tmp_path/'images';fixture.mkdir()
    for target in (1,2,3,6):
        folder=fixture/f'CD{target}';folder.mkdir()
        for n in range(image_count if target==1 else 100):
            (folder/f'{n:03}.img').write_bytes(bytes([target+n])*(1024 if target==2 else 4096))
        (folder/'Sub').mkdir()
        (folder/'Sub/ignored.iso').write_bytes(bytes(4096))
    if image_setup is not None:
        image_setup(fixture)
    env['S760_TOOLBOX_IMAGE_ROOT']=str(fixture)
    if stall_after is not None:
        env['S760_TOOLBOX_IMAGE_STALL_AFTER']=str(stall_after)
    command = [str(exe), 's760', '-rompath', str(tmp_path/'roms'),
               '-pluginspath', str(ROOT/'mame-source/plugins'),
               '-video', 'none', '-sound', 'none', '-nothrottle', '-skip_gameinfo',
               '-autoboot_delay', '0', '-autoboot_script', str(lua),
               '-cfg_directory', str(tmp_path/'cfg'), '-nvram_directory', str(tmp_path/'nvram')]
    result = subprocess.run(command, cwd=tmp_path, env=env, capture_output=True,
                            text=True, timeout=30,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    (tmp_path/'console.log').write_text(result.stdout+result.stderr, encoding='utf-8')
    assert result.returncode == 0, (result.stdout+result.stderr)[-2000:]
    observation = json.loads((tmp_path/'result.json').read_text())
    assert observation['passed'], observation
    assert observation['target_profiles'] == (expected_profiles if expected_profiles is not None else (1 if image_count!=100 else 4))
    assert all((media/name).read_bytes() == bytes(8192) for name in ('HD00_512.img','HD20_512.img'))


def test_native_toolbox_image_fixture(tmp_path):
    # Explicitly protected IMG remains a useful negative profile.
    def protect(fixture):
        for path in (fixture/'CD2').glob('*.img'):
            path.chmod(0o444)
    try:
        _run_image_fixture(tmp_path, image_setup=protect)
    finally:
        for path in (tmp_path/'images/CD2').glob('*.img'):
            path.chmod(0o666)


@pytest.mark.parametrize('stall_after', [0, 1, 3999])
@pytest.mark.parametrize('release', ['bus', 'controller', 'reset'])
def test_native_image_fixture_one_shot_listing_stall(tmp_path, stall_after, release):
    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    program = r'''
  p:write_u8(0xe416,0x82);p:write_u8(0xe404,0x24)
  for _,v in ipairs({0xd7,0,0,0,0,0,0,0,0,0}) do
   assert(p:read_u8(0xe40a)==0x8a)
   p:write_u8(0xe416,v);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  for i=1,STALL_AFTER do
   assert(p:read_u8(0xe40a)==0x89,'data before fault')
   p:read_u8(0xe416);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  for i=1,4096 do assert(p:read_u8(0xe40a)==0x09,'target must hold BSY without REQ') end
  RELEASE
  assert(p:read_u8(0xe40a)==0,'released bus')
  local status,data=command(1,{0xd7,0,0,0,0,0,0,0,0,0})
  assert(status==0 and #data==4000,'explicit fresh retry succeeds after one-shot fault')
'''.replace('STALL_AFTER', str(stall_after)).replace('RELEASE', {
        'bus': "p:write_u8(0xe404,0)",
        'controller': "p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12)",
        'reset': "p:write_u8(0xe404,0x10)",
    }[release])
    _run_image_fixture(tmp_path, prefix+program+suffix, stall_after=stall_after, expected_profiles=1)


def test_native_toolbox_writable_img_persists_across_switch(tmp_path):
    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    program = r'''
  local function mount(index)
   local status=command(2,{0xd8,index,0,0,0,0,0,0,0,0});assert(status==0)
   for i=1,3 do status=command(2,{0,0,0,0,0,0});if status==2 then sense(2) end end
   assert(status==0,'mounted IMG ready')
  end
  mount(0)
  local payload={};for i=1,512 do payload[i]=i%251 end
  local status,data=command(2,{0x2a,0,0,0,0,1,0,0,1,0},payload)
  assert(status==0,'writable IMG WRITE(10)')
  mount(1)
  status,data=command(2,{0x28,0,0,0,0,1,0,0,1,0});assert(status==0 and data[1]==3,'other image unchanged')
  mount(0)
  status,data=command(2,{0x28,0,0,0,0,1,0,0,1,0})
  assert(status==0 and #data==512,'reselected read')
  for i=1,512 do assert(data[i]==payload[i],'persisted payload') end
  status=command(2,{0x2a,0,0,0,0,2,0,0,1,0});assert(status==2,'out of range')
  data=sense(2);assert(data[3]==5 and data[13]==0x21,'range sense')
'''
    _run_image_fixture(tmp_path, prefix+program+suffix, image_count=0)
    assert (tmp_path/'images/CD2/000.img').read_bytes()==bytes([2])*512+bytes(i%251 for i in range(1,513))
    assert (tmp_path/'images/CD2/001.img').read_bytes()==bytes([3])*1024


def test_native_toolbox_native_format_unit_is_non_erasing(tmp_path):
    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    program = r'''
  for _,id in ipairs({1,2}) do
   local status=command(id,{0xd8,0,0,0,0,0,0,0,0,0})
   for i=1,3 do status=command(id,{0,0,0,0,0,0});if status==2 then sense(id) end end
   assert(status==0,'mounted')
  end
  for i=1,2 do
   local status=command(2,{4,0,0,0,0,0});assert(status==0,'native FORMAT UNIT no-data form')
   local _,data=command(2,{0x28,0,0,0,0,0,0,0,2,0})
   assert(#data==1024,'capacity unchanged');for _,byte in ipairs(data) do assert(byte==2,'FORMAT must not erase') end
  end
  for field=2,6 do
   local cdb={4,0,0,0,0,0};cdb[field]=field==2 and 0x10 or 1
   assert(command(2,cdb)==2,'unsupported FORMAT form')
   local data=sense(2);assert(data[3]==5 and data[13]==0x24,'invalid form sense')
  end
  assert(command(1,{4,0,0,0,0,0})==2,'ISO remains protected')
  local data=sense(1);assert(data[3]==7 and data[13]==0x27,'ISO protection sense')
  assert(command(0,{4,0,0,0,0,0})==2,'ordinary target retains unsupported command')
  data=sense(0);assert(data[3]==5 and data[13]==0x20,'ordinary unsupported sense')
'''
    _run_image_fixture(tmp_path, prefix+program+suffix, image_count=1)
    assert (tmp_path/'images/CD2/000.img').read_bytes()==bytes([2])*1024


def test_native_toolbox_interrupted_img_write_leaves_backing_unchanged(tmp_path):
    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    program = r'''
  local status=command(2,{0xd8,0,0,0,0,0,0,0,0,0})
  for i=1,3 do status=command(2,{0,0,0,0,0,0});if status==2 then sense(2) end end
  assert(status==0)
  p:write_u8(0xe416,0x84);p:write_u8(0xe404,0x24)
  for _,v in ipairs({0x2a,0,0,0,0,0,0,0,1,0}) do
   p:write_u8(0xe416,v);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  for i=1,127 do
   assert(p:read_u8(0xe40a)==0x88)
   p:write_u8(0xe416,0x55);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)
  end
  p:write_u8(0xe402,0x40);p:write_u8(0xe402,0x12)
  local data;status,data=command(2,{0x28,0,0,0,0,0,0,0,1,0})
  assert(status==0 and #data==512)
  for _,v in ipairs(data) do assert(v==2,'partial write escaped buffer') end
'''
    _run_image_fixture(tmp_path, prefix+program+suffix, image_count=0)
    assert (tmp_path/'images/CD2/000.img').read_bytes()==bytes([2])*1024


@pytest.mark.parametrize('target', [0, 1, 2])
@pytest.mark.parametrize('cdb_bytes', [0, 1, 5, 9])
def test_native_toolbox_recalled_partial_command_requires_fresh_selection(tmp_path, target, cdb_bytes):
    """Synthetic SPC replay; changed external catalogs must not reinterpret saved indices."""
    prefix = LUA[:LUA.index('  local function be32')]
    prefix = prefix.replace('  local function command', '  local recall=true\n  local function command', 1)
    checkpoint = f'''
   if recall and target=={target} and cdb[1]=={0x12 if target == 0 else 0xd8} then
    recall=false
    local saved=m:buffer_save()
    local path=os.getenv('S760_TOOLBOX_IMAGE_ROOT')..'/CD{target}/001.img'
    if target~=0 then
     local out=assert(io.open(path,'wb'));out:write(string.rep(string.char(0x55),{1024 if target == 2 else 4096}));out:close()
    end
    assert(m:buffer_load(saved),'checkpoint recall')
   end
'''
    if cdb_bytes == 0:
        prefix = prefix.replace('   for _,byte in ipairs(cdb) do', checkpoint+'   for _,byte in ipairs(cdb) do', 1)
    else:
        prefix = prefix.replace('   for _,byte in ipairs(cdb) do', '   for position,byte in ipairs(cdb) do', 1)
        marker = '    p:write_u8(0xe416,byte);p:write_u8(0xe404,0xe4);p:write_u8(0xe404,0xc4)'
        prefix = prefix.replace(marker, marker+f'\n    if position=={cdb_bytes} then\n'+checkpoint+'    end', 1)
    if target == 0:
        # Ordinary INQUIRY is six bytes; use READ(10) for the later boundary.
        opcode = 0x12 if cdb_bytes < 6 else 0x28
        prefix = prefix.replace('cdb[1]==18 then', f'cdb[1]=={opcode} then')
        cdb = '{0x12,0,0,0,36,0}' if opcode == 0x12 else '{0x28,0,0,0,0,0,0,0,1,0}'
        program = f'''
  local status,data=command(0,{cdb})
  assert(not recall,'recall boundary reached')
  assert(status==0 and #data=={36 if opcode == 0x12 else 512},'ordinary target unchanged by fixture recall guard')
'''
    else:
        program = f'''
  local status=command({target},{{0xd8,1,0,0,0,0,0,0,0,0}})
  assert(not recall and status==2,'restored partial switch must fail')
  local data=sense({target});assert(data[3]==6 and data[13]==0x28,'recall media-change sense')
  status=command({target},{{0,0,0,0,0,0}});assert(status==2,'no automatic mount after recall')
  data=sense({target});assert(data[3]==2 and data[13]==4,'invalidated media remains unavailable')
  status=command({target},{{0xd8,1,0,0,0,0,0,0,0,0}});assert(status==0,'fresh selection admitted')
  for i=1,3 do status=command({target},{{0,0,0,0,0,0}});if status==2 then sense({target}) end end
  assert(status==0,'freshly selected replacement ready')
  status,data=command({target},{{0x28,0,0,0,0,0,0,0,1,0}})
  assert(status==0 and data[1]==0x55,'fresh selection reads exact new backing')
'''
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    _run_image_fixture(tmp_path, prefix+program+suffix, image_count=2)


@pytest.mark.parametrize('changed_backing', ['missing', 'resized'])
def test_native_toolbox_changed_img_backing_reports_write_error(tmp_path, changed_backing):
    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    change = ("assert(os.remove(file))" if changed_backing == 'missing' else
              "local out=assert(io.open(file,'wb'));out:write('changed');out:close()")
    program = r'''
  local status=command(2,{0xd8,0,0,0,0,0,0,0,0,0})
  for i=1,3 do status=command(2,{0,0,0,0,0,0});if status==2 then sense(2) end end
  assert(status==0)
  local file=os.getenv('S760_TOOLBOX_IMAGE_ROOT')..'/CD2/000.img'
''' + change + r'''
  local payload={};for i=1,512 do payload[i]=0x55 end
  status=command(2,{0x2a,0,0,0,0,0,0,0,1,0},payload)
  assert(status==2,'failed host write must not report GOOD')
  local data=sense(2);assert(data[3]==3 and data[13]==0x0c,'WRITE ERROR sense')
  status=command(2,{0x28,0,0,0,0,0,0,0,1,0})
  assert(status==2,'changed backing invalidates cached media')
  data=sense(2);assert(data[3]==2 and data[13]==4,'NOT READY sense')
'''
    _run_image_fixture(tmp_path, prefix+program+suffix, image_count=0)
    backing=tmp_path/'images/CD2/000.img'
    if changed_backing == 'missing':
        assert not backing.exists()
    else:
        assert backing.read_bytes()==b'changed'
    assert (tmp_path/'images/CD2/001.img').read_bytes()==bytes([3])*1024


@pytest.mark.parametrize('image_count', [0, 101])
def test_native_toolbox_image_count_boundaries(tmp_path, image_count):
    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    if image_count == 101:
        program = r"""
  local status,data=command(1,{0xda,0,0,0,0,0,0,0,0,0})
  assert(status==2 and #data==0,'count overflow must error')
  data=sense(1);assert(data[3]==5 and data[13]==0 and data[14]==1,'upstream overflow ASC/ASCQ0001')
  status,data=command(1,{0xd7,0,0,0,0,0,0,0,0,0})
  assert(status==0 and #data==4000,'list alone truncates; caller must count')
"""
    else:
        program = r"""
  local status,data=command(1,{0xda,0,0,0,0,0,0,0,0,0})
  assert(status==0 and #data==1 and data[1]==0,'empty count')
  status,data=command(1,{0xd7,0,0,0,0,0,0,0,0,0})
  assert(status==0 and #data==0,'empty list must finish without data')
  status,data=command(1,{0xd8,0,0,0,0,0,0,0,0,0})
  assert(status==0,'upstream failed selection handler drops return')
  status,data=command(1,{0,0,0,0,0,0});assert(status==2,'empty mount not ready')
  data=sense(1);assert(data[3]==2 and data[13]==4,'failed mount initializing sense')
"""
    _run_image_fixture(tmp_path, prefix + program + suffix, image_count)


@pytest.mark.parametrize('image_bytes,accepted', [
    (64 * 1024 * 1024 + 2048, True),
    (1024 * 1024 * 1024 + 2048, False),
    (4097, False),
])
def test_native_toolbox_image_geometry_and_large_media(tmp_path, image_bytes, accepted):
    def prepare(fixture):
        # Seek avoids constructing a >1GiB Python buffer for the rejected input.
        with (fixture/'CD1/000.iso').open('xb') as stream:
            stream.write(b'FIRST')
            stream.seek(image_bytes - 4)
            stream.write(b'LAST')

    prefix = LUA[:LUA.index('  local function be32')]
    suffix = LUA[LUA.index('  checked=4'):].replace('checked=4', 'checked=1')
    program = r'''
  local status,data=command(1,{0xd8,0,0,0,0,0,0,0,0,0})
  assert(status==0,'upstream switch status')
  for i=1,3 do status,data=command(1,{0,0,0,0,0,0});if status==2 then sense(1) end end
'''
    if accepted:
        last = image_bytes // 2048 - 1
        program += f'''
  assert(status==0,'large image must become ready')
  status,data=command(1,{{0x25,0,0,0,0,0,0,0,0,0}})
  local last=(data[1]<<24)|(data[2]<<16)|(data[3]<<8)|data[4]
  assert(status==0 and last=={last} and data[7]==8,'full capacity')
  status,data=command(1,{{0x28,0,0,0,0,0,0,0,1,0}})
  assert(status==0 and #data==2048 and data[1]==70 and data[5]==84,'first sector')
  status,data=command(1,{{0x28,0,{last >> 24},{(last >> 16) & 255},{(last >> 8) & 255},{last & 255},0,0,1,0}})
  assert(status==0 and #data==2048 and data[2045]==76 and data[2048]==84,'last sector')
'''
    else:
        program += "  assert(status==2,'oversize or unaligned image must remain unavailable')\n"
    _run_image_fixture(tmp_path, prefix + program + suffix, 0, prepare)
