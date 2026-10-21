"""Experimental foreground ownership and bounded remote SDS recovery (BUG-123).

Five seconds without packet-counter progress, or panel Exit, cancels a remote
dump. A separate poll limit bounds the owner's loop if TIMER1 stops. Native
callee/interrupt timing and physical behavior still require qualification.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from patch_sds_local_cleanup import (COMMANDS, IMAGE_SIZE, SOURCE_SHA256,
                                     TABLE_OFFSET, long_call,
                                     patches as local_patches)

BASE=0x0780
DEADLINE_US=5_000_000
POLL_LIMIT=0x100000
SAVED=tuple(range(0x1C,0x6C,2))


class Asm:
    def __init__(self):self.code=bytearray();self.labels={};self.fixups=[]
    @property
    def pc(self):return BASE+len(self.code)
    def label(self,name):self.labels[name]=self.pc
    def emit(self,*b):self.code.extend(b)
    def word(self,n):self.code.extend(struct.pack('<H',n&65535))
    def imm(self,r,n):self.emit(0xA1);self.word(n);self.emit(r)
    def byte(self,r,n):self.emit(0xB1,n&255,r)
    def ld(self,r,a):self.emit(0xA3,1);self.word(a);self.emit(r)
    def ldb(self,r,a):self.emit(0xB3,1);self.word(a);self.emit(r)
    def st(self,r,a):self.emit(0xC3,1);self.word(a);self.emit(r)
    def stb(self,r,a):self.emit(0xC7,1);self.word(a);self.emit(r)
    def mov(self,r,s):self.emit(0xA0,s,r)
    def clr(self,r):self.emit(1,r)
    def cmpb(self,r,n):self.emit(0x99,n&255,r)
    def jump(self,name,opcode=0xE7):
        self.emit(opcode);self.fixups.append((len(self.code),name,self.pc+2));self.word(0)
    def call(self,name):self.jump(name,0xEF)
    def native(self,target):self.code.extend(long_call(self.pc,target))
    def cond(self,opcode,name):self.emit(opcode^8,3);self.jump(name)
    def finish(self):
        for offset,name,end in self.fixups:
            self.code[offset:offset+2]=struct.pack('<H',(self.labels[name]-end)&65535)
        return bytes(self.code)


def helper():
    a=Asm();a.label('request')
    a.native(0x7370);a.cond(0xDB,'request_return')
    a.byte(0x6A,7);a.stb(0x6A,0x2BBA);a.emit(0xF8)
    a.label('request_return');a.emit(0xF0)
    a.label('owner_dispatch');a.ldb(0x30,0x2BBA);a.cmpb(0x30,7)
    a.cond(0xDF,'owner');a.emit(0xF0)
    a.label('owner');a.emit(0xF4);a.byte(0x14,0)
    for selector in (0x102,0x10A,0x10C):a.emit(0xCB,1,selector&255,selector>>8)
    for r in SAVED:a.emit(0xC8,r)
    # PUSHA frame: after 80 register bytes and 6 selector bytes, WSR/MASK1
    # is at SP+86 and saved PSW/MASK0 at SP+88 (the qualified native layout).
    for displacement,r in ((88,0x44),(86,0x46)):
        a.emit(0xA3,0x19);a.word(displacement);a.emit(r)
    a.imm(0x1C,0x2BE);a.st(0x1C,0x10C)
    a.imm(0x1C,0x1F);a.st(0x1C,0x102)
    a.mov(0x24,0x0A);a.ld(0x28,0xB1A0);a.ld(0x2A,0xB1A2)
    a.clr(0x20);a.clr(0x22);a.imm(0x30,POLL_LIMIT&65535);a.imm(0x32,POLL_LIMIT>>16)
    a.label('poll');a.ldb(0x40,0xB1AE);a.cmpb(0x40,255);a.cond(0xDF,'cleanup')
    a.label('clock_read');a.mov(0x38,0x0A);a.mov(0x26,0x38)
    a.emit(0x68,0x24,0x26);a.mov(0x24,0x38)
    a.emit(0x64,0x26,0x20,0xA4,0,0x22)
    a.ld(0x2C,0xB1A0);a.ld(0x2E,0xB1A2);a.emit(0xC5,0x28,0x2C)
    a.cond(0xDF,'no_progress')
    a.label('progress');a.mov(0x28,0x2C);a.mov(0x2A,0x2E)
    a.clr(0x20);a.clr(0x22);a.imm(0x30,POLL_LIMIT&65535);a.imm(0x32,POLL_LIMIT>>16)
    a.label('no_progress');a.imm(0x34,DEADLINE_US&65535);a.imm(0x36,DEADLINE_US>>16)
    a.emit(0xC5,0x34,0x20);a.cond(0xDB,'timeout')
    a.emit(0x69,1,0,0x30,0xA8,0,0x32);a.mov(0x40,0x30);a.emit(0x80,0x32,0x40)
    a.cond(0xDF,'poll_exhausted')
    # Read the four native panel rows; do not synthesize UI queue events.
    a.stb(0,0xF00A);a.ldb(0x40,0xF00A);a.ldb(0x42,0xF00A)
    a.ldb(0x40,0xF00A);a.ldb(0x40,0xF00A);a.emit(0x71,2,0x42)
    a.cond(0xDF,'exit_pressed');a.call('service');a.jump('poll')
    a.label('timeout');a.byte(0x3A,1);a.jump('abort')
    a.label('poll_exhausted');a.byte(0x3A,3);a.jump('abort')
    a.label('exit_pressed');a.byte(0x3A,2)
    a.label('abort');a.byte(0x40,255);a.stb(0x40,0xB1AE);a.native(0x7481)
    a.label('cleanup');a.byte(0x72,8);a.stb(0,0x2BBA)
    for r in reversed(SAVED):a.emit(0xCC,r)
    for selector in (0x10C,0x10A,0x102):a.emit(0xCF,1,selector&255,selector>>8)
    a.emit(0xF5,0x11,0x30,0xF0)
    a.label('service')
    # MIDI/timer ISR scratch is not the owner's scratch. Preserve it across
    # each service window while leaving ISR-owned registers >=70 live.
    for r in SAVED:a.emit(0xC8,r)
    a.emit(0x39,0x45,3);a.jump('service_mask')  # Original caller must allow IRQs.
    a.emit(0xB0,0x44,8,0xB0,0x47,0x13)
    a.label('service_enable');a.emit(0xFB,*([0xFD]*8))
    a.label('service_mask');a.emit(0xFA);a.byte(8,0);a.byte(0x13,0)
    for r in reversed(SAVED):a.emit(0xCC,r)
    a.emit(0xF0)
    code=a.finish()
    assert BASE+len(code)<=0x0D40,'Exceeds proposed code/UI ceiling'
    return code,a.labels


def patches():
    spans=local_patches();code,labels=helper()
    for index,(offset,pc,before,after) in enumerate(spans):
        if pc==0x6D81:
            spans[index]=(offset,pc,before,after[:4]+long_call(0x6D85,labels['request'])+after[7:])
    spans.extend([(0x5E7B5,0x87B5,bytes.fromhex('B3 01 BA 2B 30'),
                   long_call(0x87B5,labels['owner_dispatch'])+bytes([0xFD])*2),
                  (0x8400+BASE,BASE,bytes(len(code)),code)])
    return spans

def patch_image(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output:
        raise ValueError('Output must differ from the original image')
    if output.suffix.lower() != '.img':
        raise ValueError('Use an .IMG output filename')
    original = source.read_bytes()
    if len(original) != IMAGE_SIZE or hashlib.sha256(original).hexdigest() != SOURCE_SHA256:
        raise ValueError('Input must be the original unmodified OS2.24 baseline')
    if original[TABLE_OFFSET:TABLE_OFFSET+8] != COMMANDS:
        raise ValueError('Unexpected SDS command table')
    import pypcode
    ctx = pypcode.Context('MCS96:LE:16:default')
    patched = bytearray(original); decoded = []
    for offset, pc, before, after in patches():
        if len(before) != len(after) or original[offset:offset+len(before)] != before:
            raise ValueError(f'Hook byte/length mismatch at {offset:06X}')
        instructions = ctx.disassemble(after, base_address=pc).instructions
        if sum(i.length for i in instructions) != len(after):
            raise ValueError(f'Instruction boundary mismatch at {pc:04X}')
        patched[offset:offset+len(after)] = after
        decoded.append(dict(offset=offset, pc=pc, before=before.hex(), after=after.hex(),
                            instructions=[dict(pc=i.addr.offset, length=i.length, mnemonic=i.mnem, operands=i.body)
                                          for i in instructions]))
    with output.open('xb') as target:
        target.write(patched)
    return dict(source_sha256=SOURCE_SHA256, output_sha256=hashlib.sha256(patched).hexdigest(),
                output=str(output), bytes=len(patched), patches=decoded,
                diff=[dict(offset=i, before=a, after=b) for i,(a,b) in enumerate(zip(original,patched)) if a!=b],
                limitation='Experimental foreground remote recovery; physical timing, full local UI/disk exclusion, memory/stack ownership and stereo remain unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(patch_image(args.input, args.output), indent=2))
