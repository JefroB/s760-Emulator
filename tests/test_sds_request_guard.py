"""Incoming sample requests must not replace a receive transaction's metadata."""
import hashlib
from functools import lru_cache
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from patch_sds_header_lifecycle import IMAGE_SIZE, SOURCE_SHA256
from patch_sds_request_guard import patch_image, patches


@lru_cache(maxsize=1)
def decoded_request():
    pypcode = pytest.importorskip('pypcode')
    spans = patches()[-2:]
    code, rows = {}, {}
    ctx = pypcode.Context('MCS96:LE:16:default')
    for _, base, _, data in spans:
        for i in ctx.disassemble(data, base_address=base).instructions:
            rows[i.addr.offset] = i
            code[i.addr.offset] = data[i.addr.offset-base:i.addr.offset-base+i.length]
    return code, rows


def run(state, low, high):
    """Decode both patched spans; stop at the existing sender/CANCEL handlers."""
    code, rows = decoded_request()
    regs = bytearray(256); memory = {0x2BBA:state,0xB04F:low,0xB050:high}
    pc, stack, equal, carry, writes = 0x6D81, [], False, False, []
    def word(a):return int.from_bytes(regs[a:a+2],'little')
    def put(a,v):regs[a:a+2]=(v&65535).to_bytes(2,'little')
    for _ in range(40):
        if pc in (0x6D30,0x695A):return pc,word(0x5E),writes,len(stack)
        i=rows[pc];b=code[pc];pc+=i.length
        if b[0]==0x9B:equal=regs[b[4]]==memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==0xD7:
            if not equal:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xEF:
            stack.append(pc);pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xA1:put(b[3],int.from_bytes(b[1:3],'little'))
        elif b[0]==0xB2:
            ptr=b[1]&254;regs[b[2]]=memory[word(ptr)]
            if b[1]&1:put(ptr,word(ptr)+1)
        elif b[0]==0x19:regs[b[2]]=(regs[b[2]]<<b[1])&255
        elif b[0]==0x08:put(b[2],word(b[2])>>b[1])
        elif b[0]==0xC3:writes.append((int.from_bytes(b[2:4],'little'),word(b[4])))
        elif b[0]==0x89:
            immediate=int.from_bytes(b[1:3],'little')
            carry=word(b[3])>=immediate;equal=word(b[3])==immediate
        elif b[0]==0xDB:
            if carry:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xD9:
            if carry and not equal:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0] in (0xF8,0xF9):carry=b[0]==0xF9
        elif b[0]==0xF0:
            if not stack:return 'return-error' if carry else 'return-ok',word(0x5E),writes,0
            pc=stack.pop()
        else:assert i.mnem=='NOP'
    raise AssertionError('Request did not terminate')


def test_busy_request_never_decodes_or_calls_sender():
    for state in range(1,256):
        for low,high in ((0,0),(1,0),(127,3),(0,4),(127,127)):
            target,_,writes,depth=run(state,low,high)
            assert target==0x6D30 and writes==[] and depth==0


def test_idle_request_slot_bounds_and_tail_call():
    for slot in range(16384):
        target,decoded,writes,depth=run(0,slot&127,slot>>7)
        assert decoded==slot and writes==[(0xB180,slot)]
        assert target==(0x695A if slot<512 else 'return-error')
        assert depth==(1 if slot<512 else 0)


def test_source_safety_and_exact_extent(tmp_path):
    source=ROOT/'roms/System/S760224.IMG'; output=tmp_path/'request.IMG'
    with pytest.raises(ValueError,match='differ'):patch_image(source,source)
    with pytest.raises(ValueError,match='.IMG'):patch_image(source,output.with_suffix('.bin'))
    invalid=tmp_path/'invalid.IMG';invalid.write_bytes(bytes(IMAGE_SIZE))
    with pytest.raises(ValueError,match='unmodified'):patch_image(invalid,output)
    assert not output.exists()
    if not source.exists():pytest.skip('Requires the user-owned original OS2.24 image')
    pytest.importorskip('pypcode')
    before=source.read_bytes();report=patch_image(source,output);after=output.read_bytes()
    allowed={i for offset,_,old,_ in patches() for i in range(offset,offset+len(old))}
    assert len(after)==IMAGE_SIZE
    assert {i for i,(a,b) in enumerate(zip(before,after)) if a!=b}<=allowed
    assert report['source_sha256']==hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256
    with pytest.raises(FileExistsError):patch_image(source,output)
    assert output.read_bytes()==after
