"""Browser-service-only bounded native MIDI queue admission; original outside it."""
import struct,pypcode
BASE=0x1500;FILE=0x9900;CONTROL=0x5fc0
def patch_parser(image):
    assert image[0xa53a:0xa53d]==bytes.fromhex('3a7b08')
    code=bytearray();labels={};fix=[]
    def emit(*values):code.extend(values)
    def label(name):labels[name]=BASE+len(code)
    def branch(op,name):emit(op,0);fix.append((len(code)-1,name,1))
    def jump(name):emit(0xe7,0,0);fix.append((len(code)-2,name,2))
    def restore():emit(0xcf,1,0x0a,1,0xcc,0x44,0xf5)
    # PUSHA saves/restores masks/window/flags; explicit DI documents atomic mapping.
    label('entry');emit(0xf4,0xfa,0xb1,0,0x14,0xc8,0x44,0xcb,1,0x0a,1)
    emit(0xa1,15,0,0x44,0xc3,1,0x0a,1,0x44)
    emit(0xa3,1,0xda,0x5f,0x44,0x89,0,0x80,0x44)
    branch(0xd3,'native');branch(0xdf,'yield')
    emit(5,0x44,0xc3,1,0xda,0x5f,0x44)
    emit(0xa0,0x0a,0x44,0x6b,1,0xdc,0x5f,0x44,0x89,0x80,0x3e,0x44)
    branch(0xdb,'yield')
    label('native');restore()
    emit(0x3a,0x7b,3);jump('native_empty_check');jump('native_byte')
    label('yield')
    # Keep ring/parser state and arrange a later native MIDI service if work remains.
    emit(0x3a,0x7b,5,0x88,0x70,0x6e);branch(0xdf,'return')
    emit(0x91,0x10,0x7b)
    label('return');restore();emit(0xf0)
    labels.update(native_empty_check=0x213d,native_byte=0x2145)
    for pos,name,width in fix:
        displacement=labels[name]-(BASE+pos+width)
        if width==1:assert -128<=displacement<128;code[pos]=displacement&255
        else:struct.pack_into('<H',code,pos,displacement&65535)
    ctx=pypcode.Context('MCS96:LE:16:default');ins=ctx.disassemble(bytes(code),base_address=BASE).instructions
    assert sum(i.length for i in ins)==len(code)
    starts={i.addr.offset for i in ins}|{0x213d,0x2145}
    for i in ins:
        if i.mnem.startswith('J') or i.mnem in ('LJMP','SJMP'):
            assert int(i.body.split()[-1],16)&65535 in starts,(i.mnem,i.body)
    assert FILE+len(code)<=0x9d00
    image[FILE:FILE+len(code)]=code
    image[0xa53a:0xa53d]=b'\xe7'+struct.pack('<H',(BASE-0x213d)&65535)
    image[0xa3da:0xa3dc]=bytes(2)
    return dict(file=FILE,physical=FILE-0x4800,logical=BASE,bytes=len(code),labels=labels,
        hook=dict(file=0xa53a,logical=0x213a,before='3a7b08',after=image[0xa53a:0xa53d].hex()),
        quota_word_physical=0x5bda,quota=32,service_time_threshold_ticks=16000,
        decoded=[dict(pc=i.addr.offset,bytes=bytes(code[i.addr.offset-BASE:i.addr.offset-BASE+i.length]).hex(),text=i.mnem+' '+i.body) for i in ins],
        limitation='Parser admission bounded per browser service; single-byte processing and control ISR still require time bounds.')
