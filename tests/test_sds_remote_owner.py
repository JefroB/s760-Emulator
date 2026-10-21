"""Decode admission and exercise the emitted remote sender owner."""
from pathlib import Path
import sys
import pytest
from conftest import require_system_image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import patch_sds_remote_owner as patch


def image():
    data=bytearray(require_system_image().read_bytes())
    for offset,_,before,after in patch.patches():
        assert data[offset:offset+len(before)]==before
        data[offset:offset+len(after)]=after
    return data


@pytest.mark.parametrize('failed',[False,True])
def test_successful_request_claims_foreground_owner(failed):
    data=image();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    pc=0x6D85;stack=[];regs={0:0};state=0;carry=False
    for _ in range(24):
        offset=0x8400+pc
        b=data[offset:offset+8];i=ctx.disassemble(bytes(b),base_address=pc,max_instructions=1).instructions[0];b=b[:i.length];pc+=len(b)
        if b[0]==0xEF:
            target=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
            if target==0x7370:carry=failed
            else:stack.append(pc);pc=target
        elif b[0] in (0xDB,0xD3):
            if carry==(b[0]==0xDB):pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xB1:regs[b[2]]=b[1]
        elif b[0]==0xC7:
            assert b[1:4]==bytes.fromhex('01 BA 2B');state=regs[b[4]]
        elif b[0]==0xF8:carry=False
        elif b[0]==0xF0:
            if not stack:break
            pc=stack.pop()
        else:assert b==bytes([0xFD]),b.hex()
    assert state==(0 if failed else 7),'Request result has the wrong foreground owner'
    assert carry==failed


def poll_slice(elapsed,last_tick,tick,previous,current,budget):
    code,labels=patch.helper();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    instructions={i.addr.offset:code[i.addr.offset-patch.BASE:i.addr.offset-patch.BASE+i.length]
                  for i in ctx.disassemble(code,base_address=patch.BASE).instructions}
    regs={r:0 for r in range(0,256,2)}
    def pair(r,n):regs[r]=n&65535;regs[r+2]=(n>>16)&65535
    def long(r):return regs[r]+(regs[r+2]<<16)
    pair(0x20,elapsed);pair(0x28,previous);pair(0x30,budget);regs[0x24]=last_tick;regs[0x0A]=tick
    memory={0xB1A0:current&65535,0xB1A2:current>>16};pc=labels['clock_read'];carry=False;equal=False
    for _ in range(64):
        if pc in (labels['timeout'],labels['poll_exhausted']):return pc,long(0x20),long(0x30)
        b=instructions[pc];pc+=len(b)
        if b[0]==0xC7:return 'continue',long(0x20),long(0x30)  # First raw panel scan.
        if b[0]==0xA0:regs[b[2]]=regs[b[1]]
        elif b[0]==0xA1:regs[b[3]]=int.from_bytes(b[1:3],'little')
        elif b[0]==0xA3:regs[b[4]]=memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==1:regs[b[1]]=0;equal=True
        elif b[0] in (0x64,0xA4):
            total=regs[b[2]]+regs[b[1]]+(carry if b[0]==0xA4 else 0)
            regs[b[2]]=total&65535;carry=total>65535;equal=regs[b[2]]==0
        elif b[0] in (0x68,0x69,0xA8):
            dest=b[3] if b[0]==0x69 else b[2]
            sub=int.from_bytes(b[1:3],'little') if b[0]==0x69 else regs[b[1]]
            sub+=int(not carry) if b[0]==0xA8 else 0
            value=regs[dest]-sub;regs[dest]=value&65535;carry=value>=0;equal=regs[dest]==0
        elif b[0]==0xC5:carry=long(b[2])>=long(b[1]);equal=long(b[2])==long(b[1])
        elif b[0]==0x80:regs[b[2]]|=regs[b[1]];equal=regs[b[2]]==0
        elif b[0] in (0xDF,0xD7,0xDB,0xD3):
            take={0xDF:equal,0xD7:not equal,0xDB:carry,0xD3:not carry}[b[0]]
            if take:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        else:pytest.fail(b.hex())
    pytest.fail('Poll slice did not terminate')


def test_decoded_deadline_wrap_progress_and_poll_exhaustion():
    _,labels=patch.helper()
    for last in (0,1,65534,65535):
        for delta in (0,1,65535):
            for elapsed in (0,patch.DEADLINE_US-65536,patch.DEADLINE_US-1,patch.DEADLINE_US):
                for previous,current in ((0xFFFFFFFF,0xFFFFFFFF),(0xFFFFFFFF,0),(127,128)):
                    for budget in (1,2,65536,patch.POLL_LIMIT):
                        destination,value,left=poll_slice(elapsed,last,(last+delta)&65535,previous,current,budget)
                        progress=previous!=current
                        wanted=0 if progress else elapsed+delta
                        remaining=patch.POLL_LIMIT if progress else budget
                        expected=labels['timeout'] if wanted>=patch.DEADLINE_US else labels['poll_exhausted'] if remaining==1 else 'continue'
                        assert (destination,value,left)==(expected,wanted,remaining if wanted>=patch.DEADLINE_US else remaining-1)


@pytest.mark.parametrize('interrupts',[False,True])
def test_service_window_preserves_scratch_and_leaves_midi_state_live(interrupts):
    code,labels=patch.helper();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    ins={i.addr.offset:code[i.addr.offset-patch.BASE:i.addr.offset-patch.BASE+i.length]
         for i in ctx.disassemble(code,base_address=patch.BASE).instructions}
    regs=bytearray(range(256));regs[0x45]=2 if interrupts else 0
    before=bytes(regs);stack=[];pc=labels['service'];enabled=0
    for _ in range(140):
        b=ins[pc];pc+=len(b)
        if b[0]==0xC8:stack.append(bytes(regs[b[1]:b[1]+2]))
        elif b[0]==0xCC:regs[b[1]:b[1]+2]=stack.pop()
        elif b[0]==0x39:
            if regs[b[1]]&2:pc+=b[2]
        elif b[0]==0xE7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xB0:regs[b[2]]=regs[b[1]]
        elif b[0]==0xB1:regs[b[2]]=b[1]
        elif b[0]==0xFB:
            enabled+=1
            for r in patch.SAVED:regs[r:r+2]=b'\xa5\x5a'
            regs[0x72]=7  # ISR parser state must not be rolled back by service.
        elif b[0]==0xF0:break
        else:assert b[0] in (0xFD,0xFA)
    assert not stack and enabled==int(interrupts)
    assert all(regs[r:r+2]==before[r:r+2] for r in patch.SAVED)
    assert regs[0x72]==(7 if interrupts else before[0x72])
    assert regs[8]==regs[0x13]==0


def test_image_extent_and_branch_targets():
    code,labels=patch.helper();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    rows=ctx.disassemble(code,base_address=patch.BASE).instructions
    starts={i.addr.offset for i in rows}
    assert sum(i.length for i in rows)==len(code) and set(labels.values())<=starts
    for i in rows:
        if i.mnem in ('LJMP','LCALL','JE','JNE','JC','JNC'):
            assert int(i.body,16) in starts|{0x7370,0x7481}
    assert patch.BASE>=0x779 and patch.BASE+len(code)<=0xD40


def test_builder_rejects_invalid_inputs_without_firmware(tmp_path):
    source=ROOT/'roms/System/S760224.IMG';output=tmp_path/'remote.IMG'
    with pytest.raises(ValueError,match='differ'):patch.patch_image(source,source)
    with pytest.raises(ValueError,match='.IMG'):patch.patch_image(source,output.with_suffix('.bin'))
    bad=tmp_path/'bad.IMG';bad.write_bytes(bytes(patch.IMAGE_SIZE))
    with pytest.raises(ValueError,match='unmodified'):patch.patch_image(bad,output)
    assert not output.exists()


def test_image_is_exact_and_protects_original(tmp_path):
    import hashlib
    source=require_system_image();output=tmp_path/'remote.IMG'
    report=patch.patch_image(source,output);assert output.read_bytes()==image()
    assert report['output_sha256']==hashlib.sha256(output.read_bytes()).hexdigest()
    with pytest.raises(FileExistsError):patch.patch_image(source,output)
    assert hashlib.sha256(source.read_bytes()).hexdigest()==patch.SOURCE_SHA256
