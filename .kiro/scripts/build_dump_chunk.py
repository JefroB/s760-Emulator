"""
build_dump_chunk.py - build an IC20 dump-chunk image (attempt 3, safe/chunked).

Injects a boot-time stub that copies a BOUNDED chunk of low memory (IC20 region)
into a PROVEN-SAFE gap (rt 0x5DBE), then continues boot. A normal SaveSys then
writes that chunk to disk, where we read it back. Chunks are kept WELL WITHIN the
gap (no overrun -> the attempt-1 hang cause, F144).

Usage:
  python build_dump_chunk.py <src_hex> <len_hex> <out.img>
  e.g. python build_dump_chunk.py 0x0000 0x800 temp/work/S760_DUMP_c0.IMG

Layout:
  hook @ file 0x490B (rt 0x218B): E7 -> LJMP 0x5DBE   (proven in B0/B1)
  stub @ rt 0x5DBE / file 0x853E: copy [src..src+len) -> DST, then LJMP 0x2831
  DST  = 0x5E00 (rt), inside the 8KB gap 0x5DBE..0x7D00, leaving margin.
        max len so DST+len < 0x7C00 (stop >=0x100 before gap end): len<=0x1E00.
On disk the chunk lands at file (DST-0x2080+0x4800)=0x8580 .. +len.
Every stub byte is verified by re-disassembling via pypcode.
"""
import sys, pypcode
ctx=pypcode.Context("MCS96:LE:16:default")
FILE_OFF=0x4800; BASE=0x2080
STUB_RT=0x5DBE; CONT=0x2831
DST_RT=0x5E00
GAP_END=0x7D00
def file_of(rt): return FILE_OFF+(rt-BASE)

def dis(bts, base):
    out=[]; a=0
    while a<len(bts):
        tx=ctx.disassemble(bytes(bts[a:a+8]),base_address=base+a,offset=0)
        ins=tx.instructions[0]
        if not ins.length: out.append((base+a,"??","len0")); break
        out.append((base+a, ins.mnem, ins.body)); a+=ins.length
    return out

def build_stub(src, length):
    assert DST_RT+length < GAP_END-0x100, "chunk too big for gap margin"
    b=[]
    # LD RW40,#src
    b+=[0xA1, src&0xFF,(src>>8)&0xFF,0x40]
    # LD RW42,#DST
    b+=[0xA1, DST_RT&0xFF,(DST_RT>>8)&0xFF,0x42]
    # LD RW44,#length
    b+=[0xA1, length&0xFF,(length>>8)&0xFF,0x44]
    loop=len(b)
    b+=[0xB2,0x41,0xB0]      # LDB RB0,[RW40]+
    b+=[0xC6,0x43,0xB0]      # STB RB0,[RW42]+
    dj=len(b); b+=[0xE1,0x44,0]   # DJNZW RW44, loop
    b[dj+2]=(loop-(dj+3))&0xFF
    lj=len(b); b+=[0xE7,0,0]      # LJMP CONT
    d16=(CONT-(STUB_RT+lj+3))&0xFFFF
    b[lj+1]=d16&0xFF; b[lj+2]=(d16>>8)&0xFF
    return b

def main():
    src=int(sys.argv[1],16); length=int(sys.argv[2],16); out=sys.argv[3]
    stub=build_stub(src,length)
    print("stub @0x%04X:"%STUB_RT)
    for a,m,bd in dis(stub,STUB_RT): print(f"  {a:04X}: {m} {bd}")
    # hook bytes: LJMP 0x5DBE at rt 0x218B
    d=(STUB_RT-(0x218B+3))&0xFFFF
    hook=[0xE7,d&0xFF,(d>>8)&0xFF]
    # apply to a copy of the original
    data=bytearray(open("S760224.IMG","rb").read())
    # verify hook site is the expected LJMP 0x2831 (E7 A3 06)
    assert bytes(data[0x490B:0x490E])==bytes([0xE7,0xA3,0x06]), "hook site changed!"
    data[0x490B:0x490E]=bytes(hook)
    data[0x853E:0x853E+len(stub)]=bytes(stub)
    assert len(data)==0x168000
    open(out,"wb").write(bytes(data))
    chunk_file=file_of(DST_RT)
    print(f"\nwrote {out}")
    print(f"IC20 chunk src=0x{src:04X} len=0x{length:04X} -> DST rt 0x{DST_RT:04X}")
    print(f"After SaveSys, chunk appears at file 0x{chunk_file:06X}..0x{chunk_file+length:06X}")

if __name__=="__main__":
    main()
