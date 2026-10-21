"""Local sender cleanup must release the admission flag after UI cleanup."""
import hashlib
from pathlib import Path
import sys

import pytest
from conftest import require_system_image

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from patch_sds_local_cleanup import patches


def image():
    source=require_system_image()
    data=bytearray(source.read_bytes())
    for offset,_,before,after in patches():
        assert data[offset:offset+len(before)]==before
        assert len(before)==len(after)
        data[offset:offset+len(after)]=after
    return data


@pytest.mark.parametrize('entry',[0x9AA0,0x9B0B,0x9BA8])
@pytest.mark.parametrize('controller',[0,1,3])
def test_local_cleanup_releases_sender_after_display(entry,controller):
    data=image();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    regs={0:0,0xDA:0xA5};memory={0xB1AE:0,0x2BBA:0,0x2476:controller}
    pc=entry;equal=False;events=[];selector=0x2BE;stack=[];peak=0
    for _ in range(32):
        offset=0x56000+pc
        ins=ctx.disassemble(bytes(data[offset:offset+8]),base_address=pc,max_instructions=1).instructions[0]
        b=data[offset:offset+ins.length];pc+=len(b)
        if b[0]==0xB1:regs[b[2]]=b[1]
        elif b[0]==0xC7:
            address=int.from_bytes(b[2:4],'little')
            if address==0xB1AE:assert selector==0x2BE,'Sender release uses the wrong data bank'
            memory[address]=regs[b[4]]
            events.append((address,memory[address]))
        elif b[0]==0xCB:
            assert b==bytes.fromhex('CB 01 0C 01');stack.append(selector);peak=max(peak,len(stack))
        elif b[0]==0xCF:
            assert b==bytes.fromhex('CF 01 0C 01');selector=stack.pop()
        elif b[0]==0xC3:
            assert b[:4]==bytes.fromhex('C3 01 0C 01');selector=regs[b[4]]
        elif b[0]==0x9B:equal=regs[b[4]]==memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==0xDF:
            if equal:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif 0x20<=b[0]<=0x27:
            delta=((b[0]&7)<<8)|b[1];pc+=delta-2048 if delta&1024 else delta
        elif b[0]==0xA1:regs[b[3]]=int.from_bytes(b[1:3],'little')
        elif b[0]==0xEF:
            target=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
            assert target==0xCE62 and regs[0x1E]==0xF732
            assert memory[0xB1AE]==0,'Sender released before display cleanup'
            events.append(('display',target));regs[0xDA]=0x39;selector=0x27C
        elif b[0]==0xF0:break
        else:assert b==bytes([0xFD]),b.hex()
    else:pytest.fail('Cleanup did not terminate')
    assert memory[0xB1AE]==255,'Quiescent local sender still blocks admission'
    assert memory[0x2BBA]==0 and regs[0x72]==8
    assert events[-1]==(0xB1AE,255)
    assert sum(e[0]=='display' for e in events)==(controller!=0)
    assert selector==(0x27C if controller else 0x2BE) and not stack and peak<=1


def test_local_patch_uses_only_existing_cleanup_extents():
    data=image();spans=patches()[-3:]
    assert [(o,p,len(a)) for o,p,_,a in spans]==[(0x5FAA0,0x9AA0,28),(0x5FB0B,0x9B0B,28),(0x5FBA8,0x9BA8,28)]
    ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    for _,pc,_,after in spans:
        rows=ctx.disassemble(after,base_address=pc).instructions
        assert sum(i.length for i in rows)==len(after)
        assert not any(i.mnem=='SCALL' for i in rows)
    # The active local cancel path retains its busy flag until common cleanup.
    assert data[0x5FADE:0x5FAE3]==bytes.fromhex('C7 01 AE B1 00')
    assert hashlib.sha256(require_system_image().read_bytes()).hexdigest()=='3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'


def test_builder_rejects_invalid_inputs_without_firmware(tmp_path):
    from patch_sds_local_cleanup import patch_image,IMAGE_SIZE
    source=ROOT/'roms/System/S760224.IMG';output=tmp_path/'local.IMG'
    with pytest.raises(ValueError,match='differ'):patch_image(source,source)
    with pytest.raises(ValueError,match='.IMG'):patch_image(source,output.with_suffix('.bin'))
    bad=tmp_path/'bad.IMG';bad.write_bytes(bytes(IMAGE_SIZE))
    with pytest.raises(ValueError,match='unmodified'):patch_image(bad,output)
    assert not output.exists()


def test_build_is_exact_and_does_not_overwrite(tmp_path):
    from patch_sds_local_cleanup import patch_image
    source=require_system_image();output=tmp_path/'local.IMG'
    report=patch_image(source,output);expected=bytes(image())
    assert output.read_bytes()==expected
    assert report['output_sha256']==hashlib.sha256(expected).hexdigest()
    assert len(report['patches'])==11
    with pytest.raises(FileExistsError):patch_image(source,output)
    assert output.read_bytes()==expected
