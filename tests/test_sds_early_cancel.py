"""Cancellation must preserve unpublished receive ownership until rollback."""
from pathlib import Path
import sys
import pytest
from conftest import require_system_image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import patch_sds_early_cancel as patch

def image():
    data=bytearray(require_system_image().read_bytes())
    for offset,pc,before,after in patch.patches():
        assert data[offset:offset+len(before)]==before
        data[offset:offset+len(after)]=after
    return data

@pytest.mark.parametrize('state',[0,1,2,3,4,5,6,7,8,10,127,128,253,254,255])
def test_decoded_cancel_preserves_receive_class_and_sender_cleanup(state):
    data=image();ctx=pytest.importorskip('pypcode').Context('MCS96:LE:16:default')
    memory={0x2bba:state,0xb1ae:0};regs={0:0};pc=0x6d8f;equal=False;carry=False
    for _ in range(30):
        offset=(0x8400 if pc<0x4000 else 0x8400)+pc
        ins=ctx.disassemble(bytes(data[offset:offset+8]),base_address=pc,max_instructions=1).instructions[0]
        b=data[offset:offset+ins.length];pc+=len(b)
        if b[0]==0xe7:pc=(pc+int.from_bytes(b[1:3],'little',signed=True))&65535
        elif b[0]==0xb3:regs[b[4]]=memory[int.from_bytes(b[2:4],'little')]
        elif b[0]==0x99:equal=regs[b[2]]==b[1];carry=regs[b[2]]>=b[1]
        elif b[0] in (0xdf,0xd3):
            if equal if b[0]==0xdf else not carry:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xb1:regs[b[2]]=b[1]
        elif b[0]==0xc7:memory[int.from_bytes(b[2:4],'little')]=regs[b[4]]
        elif b[0]==0x20:pc+=int.from_bytes(b[1:2],'little',signed=True)
        elif b[0]==0xf0:break
        else:assert b==bytes([0xfd]),b.hex()
    else:pytest.fail('Cancel did not terminate')
    assert memory[0x2bba]==(254 if state in (1,254,255) else 10)
    assert memory[0xb1ae]==255 and regs[0x72]==8

def test_receive_loop_detects_cancel_marker_without_new_stack_or_ram():
    data=image()
    assert data[0x5e83d:0x5e840]==bytes.fromhex('99 FE DA')
    # Existing signed dispatcher routes FE and FF to receive processing.
    assert data[0x5e7e4:0x5e7e9]==bytes.fromhex('99 01 30 D2 04')

def test_builder_bounds_and_original_immutability(tmp_path):
    original=require_system_image();before=original.read_bytes();output=tmp_path/'early.img'
    report=patch.patch_image(original,output)
    assert original.read_bytes()==before and output.stat().st_size==len(before)
    assert report['output_sha256']!=report['source_sha256']
    with pytest.raises(FileExistsError):patch.patch_image(original,output)
