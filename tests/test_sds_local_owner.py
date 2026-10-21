"""Local ownership must outlive the final packet and all display cleanup."""
from pathlib import Path
import sys
import pytest
from conftest import require_system_image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import patch_sds_local_owner as patch


def image():
    data=bytearray(require_system_image().read_bytes())
    for offset,_,before,after in patch.patches():
        assert data[offset:offset+len(before)]==before
        data[offset:offset+len(after)]=after
    return data


@pytest.mark.parametrize('entry',[0x9AA0,0x9B0B,0x9BA8])
@pytest.mark.parametrize('controller',[0,1,3])
def test_cleanup_holds_owner_through_display(entry,controller):
    data=image();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    regs={0:0,0xDA:0xA5};memory={0xB1AE:255,0x2BBA:8,0x2476:controller}
    pc=entry;equal=False;events=[];selector=0x2BE;stack=[];enabled=True
    for _ in range(100):
        offset=(0x8400 if pc<0x4000 else 0x56000)+pc
        ins=ctx.disassemble(bytes(data[offset:offset+8]),base_address=pc,max_instructions=1).instructions[0]
        b=data[offset:offset+ins.length];pc+=len(b)
        if b[0]==0xB1:regs[b[2]]=b[1]
        elif b[0]==0xC7:
            address=int.from_bytes(b[2:4],'little')
            if address==0xB1AE:assert selector==0x2BE
            memory[address]=regs[b[4]];events.append((address,memory[address],enabled))
        elif b[0]==0xCB:assert b==bytes.fromhex('CB 01 0C 01');stack.append(selector)
        elif b[0]==0xCF:assert b==bytes.fromhex('CF 01 0C 01');selector=stack.pop()
        elif b[0]==0xC3:assert b[:4]==bytes.fromhex('C3 01 0C 01');selector=regs[b[4]]
        elif b[0]==0x9B:equal=regs[b[4]]==memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==0xDF:
            if equal:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif 0x20<=b[0]<=0x27:
            delta=((b[0]&7)<<8)|b[1];pc+=delta-2048 if delta&1024 else delta
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xA1:regs[b[3]]=int.from_bytes(b[1:3],'little')
        elif b[0]==0xEF:
            target=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
            assert target==0xCE62 and regs[0x1E]==0xF732
            assert memory[0x2BBA]!=0,'Completed local sender exposes idle admission during display cleanup'
            events.append(('display',target));regs[0xDA]=0x39;selector=0x27C
        elif b[0]==0xF4:stack.append(enabled);enabled=False
        elif b[0]==0xF5:enabled=stack.pop()
        elif b[0]==0xF0:break
        else:assert b==bytes([0xFD]),b.hex()
    else:pytest.fail('Cleanup did not terminate')
    assert memory[0xB1AE]==255 and memory[0x2BBA]==0 and regs[0x72]==8
    release=next(e for e in events if e[0]==0x2BBA)
    assert release==(0x2BBA,0,False),'Local owner release is not atomic'
    assert selector==(0x27C if controller else 0x2BE) and not stack and enabled


@pytest.mark.parametrize('state,sender',[(0,255),(0,0),(0,1),(1,255),(6,255),(7,255),(8,255),(10,255),(255,255)])
@pytest.mark.parametrize('name,blocks',[(32,1),(127,1),(32,0)])
@pytest.mark.parametrize('interrupts',[False,True])
def test_decoded_entry_admits_only_idle_nonempty_sample(state,sender,name,blocks,interrupts):
    data=image();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    regs={0:0,0x6A:0xA55A};banks={0x102:0x123,0x10C:0x299}
    original_banks=dict(banks);memory={0x2BBA:state,0xB1AE:sender}
    pc=0x998E;stack=[];enabled=interrupts;equal=False;carry=False;lookups=0;claims=[]
    for _ in range(130):
        if pc==0x99AC:break
        offset=(0x8400 if pc<0x4000 else 0x56000)+pc
        ins=ctx.disassemble(bytes(data[offset:offset+8]),base_address=pc,max_instructions=1).instructions[0]
        b=data[offset:offset+ins.length];pc+=len(b)
        if b[0]==0xEF:
            target=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
            if target==0x6D20:
                assert not enabled and banks=={0x102:0x1F,0x10C:0x2BE}
                equal=(state==0 and sender==255);regs[0x6A]=0 if equal else 1
            elif target==0x6B2E:
                assert not enabled and banks[0x102]==0x4B and regs[0x4A]==5
                lookups+=1;regs[0x4E]=0x4000
            else:stack.append(pc);pc=target
        elif b[0]==0xF0:
            if not stack:break
            pc=stack.pop()
        elif b[0]==0xF4:stack.append(enabled);enabled=False
        elif b[0]==0xF5:enabled=stack.pop()
        elif b[0]==0xCB:stack.append(banks[int.from_bytes(b[2:4],'little')])
        elif b[0]==0xCF:banks[int.from_bytes(b[2:4],'little')]=stack.pop()
        elif b[0]==0xC8:stack.append(regs[b[1]])
        elif b[0]==0xCC:regs[b[1]]=stack.pop()
        elif b[0]==0xA1:regs[b[3]]=int.from_bytes(b[1:3],'little')
        elif b[0]==0xB1:regs[b[2]]=b[1]
        elif b[0]==0xC3:banks[int.from_bytes(b[2:4],'little')]=regs[b[4]]
        elif b[0]==0xC7:
            address=int.from_bytes(b[2:4],'little');assert address==0x2BBA
            memory[address]=regs[b[4]];claims.append((memory[address],enabled))
        elif b[0]==0xB2:assert b==bytes.fromhex('B2 4E DA');regs[0xDA]=name
        elif b[0]==0x99:equal=regs[b[2]]==b[1]
        elif b[0]==0x8B:assert b==bytes.fromhex('8B 4E 2A 00');equal=blocks==0
        elif b[0]==0xF8:carry=False
        elif b[0]==0xF9:carry=True
        elif b[0] in (0xDF,0xD7,0xD3):
            if {0xDF:equal,0xD7:not equal,0xD3:not carry}[b[0]]:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        else:assert b==bytes([0xFD]),b.hex()
    else:pytest.fail('Local entry did not terminate')
    idle=state==0 and sender==255;admitted=idle and name!=127 and blocks!=0
    assert (pc==0x99AC)==admitted and carry==(not admitted)
    assert claims==([(8,False)] if admitted else [])
    assert memory=={0x2BBA:8 if admitted else state,0xB1AE:sender}
    assert lookups==int(idle) and banks==original_banks and regs[0x6A]==0xA55A
    assert not stack and enabled==interrupts


@pytest.mark.parametrize('failed',[False,True])
def test_setup_preserves_failure_or_reclaims_local_owner(failed):
    data=image();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    pc=0x9A3F;stack=[];carry=False;state=8;regs={}
    for _ in range(24):
        if pc==0x9A42:break
        offset=(0x8400 if pc<0x4000 else 0x56000)+pc
        i=ctx.disassemble(bytes(data[offset:offset+8]),base_address=pc,max_instructions=1).instructions[0]
        b=data[offset:offset+i.length];pc+=len(b)
        if b[0]==0xEF:
            target=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
            if target==0x695A:state=6 if failed else 0;carry=failed
            else:stack.append(pc);pc=target
        elif b[0]==0xD3:
            if not carry:pc+=b[1]
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xB1:regs[b[2]]=b[1]
        elif b[0]==0xC7:assert b[:4]==bytes.fromhex('C7 01 BA 2B');state=regs[b[4]]
        elif b[0]==0xF8:carry=False
        elif b[0]==0xF0:pc=stack.pop()
        else:pytest.fail(b.hex())
    assert pc==0x9A42 and not stack and carry==failed and state==(6 if failed else 8)
    assert data[0x5FB85:0x5FB8A]==bytes([0xFD])*5  # Failure remains owned through its message.


def test_builder_rejects_invalid_inputs_without_firmware(tmp_path):
    source=ROOT/'roms/System/S760224.IMG';output=tmp_path/'local-owner.IMG'
    with pytest.raises(ValueError,match='differ'):patch.patch_image(source,source)
    with pytest.raises(ValueError,match='.IMG'):patch.patch_image(source,output.with_suffix('.bin'))
    bad=tmp_path/'bad.IMG';bad.write_bytes(bytes(patch.IMAGE_SIZE))
    with pytest.raises(ValueError,match='unmodified'):patch.patch_image(bad,output)
    assert not output.exists()


def test_image_is_exact_and_protects_original(tmp_path):
    import hashlib
    source=require_system_image();output=tmp_path/'local-owner.IMG'
    report=patch.patch_image(source,output);assert output.read_bytes()==image()
    assert report['output_sha256']==hashlib.sha256(output.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):patch.patch_image(source,output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==patch.SOURCE_SHA256
    code,labels=patch.helper();assert patch.BASE==0xA00 and patch.BASE+len(code)<=0xD40
    ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default');rows=ctx.disassemble(code,base_address=patch.BASE).instructions
    starts={i.addr.offset for i in rows};assert set(labels.values())<=starts
    for i in rows:
        if i.mnem in ('LCALL','LJMP','JE','JNE','JC','JNC'):assert int(i.body,16) in starts|{0x6D20,0x6B2E,0x695A}
