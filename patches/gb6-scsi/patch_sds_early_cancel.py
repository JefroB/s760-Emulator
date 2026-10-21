"""Experimental receive cancellation ownership repair for BUG-125.

Keep FE as pending receive rollback; preserve generic 0A sender cancellation.
Includes all earlier local/remote SDS owner repairs. No new RAM or stack frame.
"""
import argparse
import hashlib
import json
from pathlib import Path
from patch_sds_local_owner import (COMMANDS,IMAGE_SIZE,SOURCE_SHA256,TABLE_OFFSET,
                                    patches as local_patches)

BASE=0x0AA0

def jump(pc,target):return bytes([0xE7])+((target-pc-3)&65535).to_bytes(2,'little')

def helper():
    # Receive active, complete-unpublished and already-cancelled retain the
    # receive class. In particular, repeated CANCEL must not lose rollback.
    code=bytes.fromhex('B3 01 BA 2B 6A 99 01 6A DF 05 99 FE 6A D3 05 '
                       'B1 FE 6A 20 03 B1 0A 6A C7 01 BA 2B 6A')
    return code+jump(BASE+len(code),0x6D97)

def patches():
    code=helper()
    return local_patches()+[
        (0xF18F,0x6D8F,bytes.fromhex('B1 0A 6A C7 01 BA 2B 6A'),jump(0x6D8F,BASE)+bytes([0xFD])*5),
        (0x5E83D,0x883D,bytes.fromhex('99 0A DA'),bytes.fromhex('99 FE DA')),
        (0x8400+BASE,BASE,bytes(len(code)),code),
    ]

def patch_image(source,output):
    source,output=Path(source).resolve(),Path(output).resolve()
    if source==output or output.suffix.lower()!='.img':raise ValueError('Use a distinct .IMG output')
    original=source.read_bytes()
    if len(original)!=IMAGE_SIZE or hashlib.sha256(original).hexdigest()!=SOURCE_SHA256:raise ValueError('Expected original OS2.24')
    if original[TABLE_OFFSET:TABLE_OFFSET+8]!=COMMANDS:raise ValueError('Unexpected command table')
    import pypcode
    ctx=pypcode.Context('MCS96:LE:16:default');patched=bytearray(original);decoded=[]
    for offset,pc,before,after in patches():
        if len(before)!=len(after) or original[offset:offset+len(before)]!=before:raise ValueError(f'Hook mismatch {offset:06X}')
        rows=ctx.disassemble(after,base_address=pc).instructions
        if sum(i.length for i in rows)!=len(after):raise ValueError('Instruction boundary mismatch')
        patched[offset:offset+len(after)]=after
        decoded.append(dict(offset=offset,pc=pc,before=before.hex(),after=after.hex(),instructions=[dict(pc=i.addr.offset,length=i.length,mnemonic=i.mnem,operands=i.body) for i in rows]))
    with output.open('xb') as f:f.write(patched)
    return dict(source_sha256=SOURCE_SHA256,output_sha256=hashlib.sha256(patched).hexdigest(),output=str(output),bytes=len(patched),patches=decoded,
                diff=[dict(offset=i,before=a,after=b) for i,(a,b) in enumerate(zip(original,patched)) if a!=b],
                limitation='Experimental SDS receive rollback ownership; full stack/ISR, stereo importer and hardware qualification remain open')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--input',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args()
    print(json.dumps(patch_image(a.input,a.output),indent=2))
