"""Decode transfer admission and header setup without changing original firmware."""
from functools import lru_cache
import hashlib
from pathlib import Path
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from patch_sds_sender_guard import IMAGE_SIZE,SOURCE_SHA256,patch_image,patches


@lru_cache(maxsize=1)
def instructions():
    ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    code={}
    for _,base,_,span in patches():
        rows=ctx.disassemble(span,base_address=base).instructions
        assert sum(i.length for i in rows)==len(span)
        for i in rows:code[i.addr.offset]=span[i.addr.offset-base:i.addr.offset-base+i.length]
    return code


def admission(entry,receive,sender):
    code=instructions();pc=entry;regs={0:0};equal=False;stack=[];peak=0
    memory={0x2BBA:receive,0xB1AE:sender}
    for _ in range(24):
        if pc in (0x6E05,0x7370,0x6D10,0x6D30):return pc,peak
        b=code[pc];pc+=len(b)
        if b[0]==0xB3:regs[b[4]]=memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==0x17:
            regs[b[1]]=(regs[b[1]]+1)&255;equal=regs[b[1]]==0
        elif b[0]==0x93:
            regs[b[4]]|=memory[int.from_bytes(b[2:4],'little')];equal=regs[b[4]]==0
        elif b[0]==0x9B:equal=regs[b[4]]==memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==0xD7:
            if not equal:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif 0x28<=b[0]<=0x2F:
            relative=((b[0]&7)<<8)|b[1];stack.append(pc);peak=max(peak,len(stack))
            pc=(pc+(relative-2048 if relative&1024 else relative))&65535
        elif b[0]==0xEF:
            stack.append(pc);peak=max(peak,len(stack));pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xF0:pc=stack.pop()
        else:assert b==bytes([0xFD]),b.hex()
    raise AssertionError('Admission did not terminate')


def test_both_directions_reject_every_busy_state_pair():
    for entry in (0x6D08,0x6D81):
        for receive in range(256):
            for sender in range(256):
                destination,peak=admission(entry,receive,sender)
                idle=receive==0 and sender==255
                assert destination==((0x6E05 if entry==0x6D08 else 0x7370) if idle else 0x6D30)
                assert peak<=1  # Temporary 2-byte call frame, no nested gate call.


def test_header_setup_callee_order_and_error_exits():
    code=instructions()
    for failing in (None,0x6E64,0x6FBF):
        pc=0x6D08;calls=[];carry=False
        for _ in range(30):
            if pc==0x6D30:break
            b=code[pc];pc+=len(b)
            if 0x28<=b[0]<=0x2F:
                rel=((b[0]&7)<<8)|b[1];target=(pc+(rel-2048 if rel&1024 else rel))&65535
                calls.append(target);carry=target==failing
            elif b[0]==0xEF:
                calls.append((pc+int.from_bytes(b[1:3],'little',signed=True))&65535)
            elif b[0]==0xDB:
                if carry:pc+=int.from_bytes(b[1:2],'little',signed=True)
            elif b[0]==0xD7:pass  # Gate is idle for this callee-order test.
            elif b[0]==0xF8:carry=False
            elif b[0]==0xF0:break
            else:assert b==bytes([0xFD]),b.hex()
        expected=[0x6D20,0x6E05,0x6E64,0x6FBF,0x4F05,0x6AA5,0x7495]
        assert calls==(expected if failing is None else expected[:expected.index(failing)+1])
        assert (pc==0x6D30)==(failing is not None)


def test_image_safety_extent_and_counter_helper(tmp_path):
    source=ROOT/'roms/System/S760224.IMG';output=tmp_path/'sender.IMG'
    with pytest.raises(ValueError,match='differ'):patch_image(source,source)
    with pytest.raises(ValueError,match='.IMG'):patch_image(source,output.with_suffix('.bin'))
    bad=tmp_path/'bad.IMG';bad.write_bytes(bytes(IMAGE_SIZE))
    with pytest.raises(ValueError,match='unmodified'):patch_image(bad,output)
    assert not output.exists()
    if not source.exists():pytest.skip('Requires the user-owned OS2.24 image')
    pytest.importorskip('pypcode')
    before=source.read_bytes();report=patch_image(source,output);after=output.read_bytes()
    allowed={i for offset,_,old,_ in patches() for i in range(offset,offset+len(old))}
    assert len(after)==IMAGE_SIZE
    assert {i for i,(a,b) in enumerate(zip(before,after)) if a!=b}<=allowed
    assert after[0xEEA5:0xEEB5]==bytes.fromhex('A1 FF FF 5C C3 01 A0 B1 5C C3 01 A2 B1 5C F8 F0')
    assert report['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
    with pytest.raises(FileExistsError):patch_image(source,output)
    assert output.read_bytes()==after
