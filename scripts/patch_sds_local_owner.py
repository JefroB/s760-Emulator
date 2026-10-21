"""Experimental atomic local Sample Dump ownership (BUG-124).

Includes the remote owner and prior SDS repairs. Claim state8 before shared
local setup, keep it after sender completion, and release after UI cleanup.
"""
import argparse
import hashlib
import json
from pathlib import Path
from patch_sds_remote_owner import (Asm,COMMANDS,IMAGE_SIZE,SOURCE_SHA256,
                                    TABLE_OFFSET,long_call,patches as remote_patches)

BASE=0x0A00


class LocalAsm(Asm):
    @property
    def pc(self):return BASE+len(self.code)


def helper():
    a=LocalAsm();a.label('entry');a.emit(0xF4)
    for selector in (0x102,0x10C):a.emit(0xCB,1,selector&255,selector>>8)
    a.emit(0xC8,0x6A)
    a.imm(0x1C,0x2BE);a.st(0x1C,0x10C)
    a.imm(0x1C,0x1F);a.st(0x1C,0x102);a.native(0x6D20)
    a.cond(0xD7,'refuse')
    # Original selected-slot lookup and empty/zero-allocation checks.
    a.byte(0x4A,5);a.imm(0x1C,0x4B);a.st(0x1C,0x102);a.native(0x6B2E)
    a.emit(0xB2,0x4E,0xDA);a.cmpb(0xDA,127);a.cond(0xDF,'refuse')
    a.emit(0x8B,0x4E,0x2A,0);a.cond(0xDF,'refuse')
    a.byte(0x6A,8);a.stb(0x6A,0x2BBA)
    for success in (True,False):
        if not success:a.label('refuse')
        a.emit(0xCC,0x6A)
        for selector in (0x10C,0x102):a.emit(0xCF,1,selector&255,selector>>8)
        a.emit(0xF5,0xF8 if success else 0xF9,0xF0)
    a.label('setup');a.native(0x695A);a.cond(0xDB,'setup_return')
    a.byte(0x6A,8);a.stb(0x6A,0x2BBA);a.emit(0xF8)
    a.label('setup_return');a.emit(0xF0)
    a.label('release');a.emit(0xF4,0xCB,1,0x0C,1)
    a.imm(0x1C,0x2BE);a.st(0x1C,0x10C)
    a.byte(0xDA,255);a.stb(0xDA,0xB1AE);a.byte(0x72,8);a.stb(0,0x2BBA)
    a.emit(0xCF,1,0x0C,1,0xF5,0xF0)
    code=a.finish();assert BASE+len(code)<=0x0D40
    return code,a.labels


def patches():
    spans=remote_patches();code,labels=helper()
    for i,(offset,pc,before,after) in enumerate(spans):
        if pc==0x9AA0:after=bytes([0xFD])*5+after[5:]
        elif pc==0x9BA8:after=after[:2]+bytes([0xE7])+((labels['release']-0x9BAD)&65535).to_bytes(2,'little')+bytes([0xFD])*23
        spans[i]=(offset,pc,before,after)
    original_entry=bytes.fromhex('B1 05 4A A1 4B 00 1C C3 01 02 01 1C EF 91 D1 B2 4E DA 99 7F DA DF 06 8B 4E 2A 00 D7 01 F0')
    entry=long_call(0x998E,labels['entry'])+bytes.fromhex('D3 01 F0')+bytes([0xFD])*24
    spans.extend([(0x5F98E,0x998E,original_entry,entry),
                  (0x5FA3F,0x9A3F,long_call(0x9A3F,0x695A),long_call(0x9A3F,labels['setup'])),
                  (0x5FB85,0x9B85,bytes.fromhex('C7 01 BA 2B 00'),bytes([0xFD])*5),
                  (0x8400+BASE,BASE,bytes(len(code)),code)])
    return spans


def patch_image(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if source==output:raise ValueError('Output must differ from the original image')
    if output.suffix.lower()!='.img':raise ValueError('Use an .IMG output filename')
    original=source.read_bytes()
    if len(original)!=IMAGE_SIZE or hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:
        raise ValueError('Input must be the original unmodified OS2.24 baseline')
    if original[TABLE_OFFSET:TABLE_OFFSET+8]!=COMMANDS:raise ValueError('Unexpected SDS command table')
    import pypcode
    ctx=pypcode.Context('MCS96:LE:16:default');patched=bytearray(original);decoded=[]
    for offset,pc,before,after in patches():
        if len(before)!=len(after) or original[offset:offset+len(before)]!=before:
            raise ValueError(f'Hook byte/length mismatch at {offset:06X}')
        rows=ctx.disassemble(after,base_address=pc).instructions
        if sum(i.length for i in rows)!=len(after):raise ValueError(f'Instruction boundary mismatch at {pc:04X}')
        patched[offset:offset+len(after)]=after
        decoded.append(dict(offset=offset,pc=pc,before=before.hex(),after=after.hex(),instructions=[dict(pc=i.addr.offset,length=i.length,mnemonic=i.mnem,operands=i.body) for i in rows]))
    with output.open('xb') as f:f.write(patched)
    return dict(source_sha256=SOURCE_SHA256,output_sha256=hashlib.sha256(patched).hexdigest(),output=str(output),bytes=len(patched),patches=decoded,
                diff=[dict(offset=i,before=a,after=b) for i,(a,b) in enumerate(zip(original,patched)) if a!=b],
                limitation='Experimental local and remote SDS owners; native Disk exclusion, full stack/ISR bounds, physical acceptance and stereo remain unqualified')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    print(json.dumps(patch_image(a.input,a.output),indent=2))
