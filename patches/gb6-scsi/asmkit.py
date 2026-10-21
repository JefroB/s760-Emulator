"""Private, ordinary-callback guest SCSI experiment; not release firmware."""
from pathlib import Path
import argparse, hashlib, json, struct
import pypcode

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
BASE=0x8480
BUFFER=0x4800
TABLE=0x5804
RECORDS=0x5a00
RECORD_SIZE=32
CONTROL=0x5ff0
SOURCE_SHA='3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd'
HOOK_PC=0x9040
HOOK=0x4800+(0x181<<10)+(HOOK_PC&0x3fff)
CASES=[{'name': 'count100', 'cdb': 'da 00 00 00 00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 1, 'status': 0, 'payload': '64'}, {'name': 'list100', 'cdb': 'd7 00 00 00 00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 4000, 'status': 0}, {'name': 'select99', 'cdb': 'd8 63 00 00 00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 0}, {'name': 'first-not-ready', 'cdb': '00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 2}, {'name': 'absent-sense', 'cdb': '03 00 00 00 12 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 18, 'status': 0, 'sense': [2, 58]}, {'name': 'attention', 'cdb': '00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 2}, {'name': 'attention-sense', 'cdb': '03 00 00 00 12 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 18, 'status': 0, 'sense': [6, 40]}, {'name': 'ready', 'cdb': '00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 0}, {'name': 'capacity', 'cdb': '25 00 00 00 00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 8, 'status': 0, 'payload': '0000000100000800'}, {'name': 'read99', 'cdb': '28 00 00 00 00 00 00 00 01 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 2048, 'status': 0, 'payload': '6464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464646464'}, {'name': 'select0', 'cdb': 'd8 00 00 00 00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 0}, {'name': 'first-not-ready', 'cdb': '00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 2}, {'name': 'absent-sense', 'cdb': '03 00 00 00 12 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 18, 'status': 0, 'sense': [2, 58]}, {'name': 'attention', 'cdb': '00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 2}, {'name': 'attention-sense', 'cdb': '03 00 00 00 12 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 18, 'status': 0, 'sense': [6, 40]}, {'name': 'ready', 'cdb': '00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 0, 'status': 0}, {'name': 'capacity', 'cdb': '25 00 00 00 00 00 00 00 00 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 8, 'status': 0, 'payload': '0000000100000800'}, {'name': 'read0', 'cdb': '28 00 00 00 00 00 00 00 01 00', 'target': 1, 'capacity': 4096, 'code': 0, 'length': 2048, 'status': 0, 'payload': '0101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101010101'}]

class Asm:
 def __init__(self): self.code=bytearray();self.labels={};self.fixups=[];self.rows=[]
 @property
 def pc(self):return BASE+len(self.code)
 def label(self,n):assert n not in self.labels;self.labels[n]=self.pc
 def emit(self,*b):self.code.extend(b)
 def word(self,n):self.code.extend(struct.pack('<H',n&65535))
 def imm(self,r,n):self.emit(0xa1);self.word(n);self.emit(r)
 def byte(self,r,n):self.emit(0xb1,n&255,r)
 def ld(self,r,a):self.emit(0xa3,1);self.word(a);self.emit(r)
 def ldb(self,r,a):self.emit(0xb3,1);self.word(a);self.emit(r)
 def st(self,r,a):self.emit(0xc3,1);self.word(a);self.emit(r)
 def stb(self,r,a):self.emit(0xc7,1);self.word(a);self.emit(r)
 def mov(self,r,s):self.emit(0xa0,s,r)
 def clr(self,r):self.emit(1,r)
 def cmp(self,r,n):self.emit(0x89);self.word(n);self.emit(r)
 def cmpb(self,r,n):self.emit(0x99,n&255,r)
 def jmp(self,label,op=0xe7):
  self.emit(op);self.fixups.append((len(self.code),label,self.pc+2));self.word(0)
 def call(self,label):self.jmp(label,0xef)
 def cond(self,op,label):
  # Inverse conditional skips a long jump, avoiding hidden short-branch limits.
  self.emit(op^8,3);self.jmp(label)
 def finish(self):
  for index,label,after in self.fixups:
   assert label in self.labels,label
   self.code[index:index+2]=struct.pack('<H',(self.labels[label]-after)&65535)
  ctx=pypcode.Context('MCS96:LE:16:default')
  ins=ctx.disassemble(bytes(self.code),base_address=BASE).instructions
  assert sum(i.length for i in ins)==len(self.code)
  starts={i.addr.offset for i in ins}
  assert all(v in starts for k,v in self.labels.items() if k!='code_end')
  for i in ins:
   if i.mnem in ('LJMP','LCALL','JE','JNE','JC','JNC','JH','JNH'):
    assert int(i.body,16) in starts,(i.mnem,i.body)
  self.rows=[dict(pc=i.addr.offset,bytes=bytes(self.code[i.addr.offset-BASE:i.addr.offset-BASE+i.length]).hex(),text=i.mnem+' '+i.body) for i in ins]
  from relax import relax
  return relax(self,BASE)

def build(output):
 original=(ROOT/'S760224.IMG').read_bytes()
 assert len(original)==0x168000 and hashlib.sha256(original).hexdigest()==SOURCE_SHA
 assert original[0x853e:0xa480]==bytes(8002)
 assert original[HOOK:HOOK+8]==bytes.fromhex('a1 71 01 1c a1 5e 9b 1e')
 a=Asm();a.label('entry');a.emit(0xf4) # Save PSW, WSR and MASK1; interrupts masked.
 a.label('entry_bank_read');a.emit(0xcb,1,0x0a,1)
 # WSR is zero at this qualified callback. Save all registers this probe uses.
 saved=list(range(0x1c,0x60,2))+[0xda]
 for r in saved:a.emit(0xc8,r)
 a.byte(0x14,0);a.imm(0x1c,15);a.st(0x1c,0x10a)
 # Capture the native bank and PUSHA frame through the guest's own stack.
 for offset,dest in [(70,6),(72,10),(74,8)]:
  a.emit(0xa3,0x19);a.word(offset);a.emit(0x44);a.st(0x44,CONTROL+dest)
 a.ldb(0x44,0x115);a.stb(0x44,CONTROL+14)
 # Own the PIO controller: mask native SCSI/DMA completion while preserving
 # the other IC4 sources; timer ISR ORs 0x44, leaving this bit clear.
 a.emit(0x71,0xef,0x44);a.stb(0x44,0x115)
 a.st(0,CONTROL+16);a.st(0,CONTROL+18);a.st(0,CONTROL+20);a.st(0,CONTROL+22);a.st(0,CONTROL+24)
 a.imm(0x44,0xb501);a.st(0x44,CONTROL)
 a.imm(0x20,TABLE);a.imm(0x22,RECORDS);a.imm(0x24,len(CASES));a.clr(0x26)
 a.label('case_loop');a.st(0x26,CONTROL+2)
 # Clear only the current diagnostic record. This is extension-owned test RAM.
 a.mov(0x48,0x22);a.imm(0x4a,RECORD_SIZE//2)
 a.label('clear_record');a.emit(0xc2,0x49,0);a.emit(5,0x4a);a.cond(0xd7,'clear_record')
 # Case layout: mask, CDB length, hold-ACK, reserved, capacity, poll limit,
 # unused word, CDB bytes at+10 (padded to14), total record24.
 a.emit(0xb2,0x21,0x50,0xb2,0x21,0x52,0xb2,0x21,0x54,0xb2,0x21,0x5c)
 a.emit(0xa2,0x21,0x2e,0xa2,0x21,0x3a,0xa2,0x21,0x56)
 a.mov(0x28,0x20);a.mov(0x2a,0x52);a.emit(0x61,0xff,0,0x2a)
 a.imm(0x2c,BUFFER)
 a.imm(0x48,BUFFER);a.imm(0x4a,2048);a.mov(0x4c,0x56)
 a.label('fill_buffer');a.emit(0xc2,0x49,0x4c);a.emit(0x65,1,1,0x4c)
 a.mov(0x44,0x4a);a.emit(0x61,63,0,0x44);a.cmp(0x44,0);a.cond(0xd7,'fill_continue');a.call('service')
 a.label('fill_continue');a.emit(5,0x4a);a.cond(0xd7,'fill_buffer')
 a.imm(0x44,0xa55a);a.st(0x44,BUFFER-2);a.st(0x44,BUFFER+4096)
 a.clr(0x30);a.clr(0x34);a.clr(0x36);a.clr(0x3e);a.clr(0x58)
 a.imm(0x40,0xffff);a.mov(0x32,0x0a);a.mov(0x38,0x32);a.mov(0x5a,0x32)
 a.byte(0x44,1);a.stb(0x44,CONTROL+18)
 a.call('transaction');a.stb(0,CONTROL+18)
 # Cancellation is an operation result after a successful command drain.
 # Transport failures and original CHECK CONDITION keep precedence.
 a.ld(0x44,CONTROL+16);a.cmp(0x44,0);a.cond(0xdf,'record_result')
 a.cmp(0x3e,0);a.cond(0xd7,'record_result');a.cmpb(0x40,0);a.cond(0xd7,'record_result')
 a.imm(0x3e,7)
 a.label('record_result')
 # Capture results without interpreting status as the transport outcome.
 for reg,offset in [(0x3e,0),(0x30,2),(0x40,4),(0x34,8),(0x36,10),(0x3a,12),(0x32,14),(0x2a,16),(0x5a,18),(0x26,20)]:
  a.emit(0xc3,0x23);a.word(offset);a.emit(reg)
 a.ldb(0x44,0xe40a);a.emit(0xc7,0x23,6,0,0x44)
 for address,offset in [(BUFFER-2,22),(BUFFER+4096,24)]:
  a.ld(0x44,address);a.emit(0xc3,0x23);a.word(offset);a.emit(0x44)
 for address,offset in [(CONTROL+16,26),(CONTROL+20,28),(CONTROL+22,30)]:
  a.ld(0x44,address);a.emit(0xc3,0x23);a.word(offset);a.emit(0x44)
 a.label('case_complete');a.st(0x26,CONTROL+4)
 a.ld(0x44,CONTROL+16);a.cmp(0x44,0);a.cond(0xd7,'finish_operation')
 a.emit(0x65,14,0,0x20,0x65,RECORD_SIZE,0,0x22,7,0x26,5,0x24);a.cond(0xd7,'case_loop')
 a.label('finish_operation');a.ldb(0x44,CONTROL+14);a.stb(0x44,0x115)
 a.imm(0x44,0xb502);a.st(0x44,CONTROL)
 for r in reversed(saved):a.emit(0xcc,r)
 a.label('exit_bank_write');a.emit(0xcf,1,0x0a,1);a.emit(0xf5)
 a.label('original_replay');a.emit(*original[HOOK:HOOK+8]);a.emit(0xf0)

 a.label('transaction')
 a.call('cancel_scan');a.ld(0x44,CONTROL+16);a.cmp(0x44,0);a.cond(0xdf,'acquire_bus')
 a.imm(0x3e,7);a.emit(0xf0)
 a.label('acquire_bus')
 a.ldb(0x44,0xe40a);a.emit(0x71,0x48,0x44);a.cmpb(0x44,0);a.cond(0xd7,'busy')
 a.byte(0x44,255);a.stb(0x44,0xe408)
 a.byte(0x44,1);a.ldb(0x46,0x3623);a.emit(0x19,0x46,0x44,0x90,0x50,0x44);a.stb(0x44,0xe416)
 a.byte(0x44,0x10);a.stb(0x44,0xe418);a.stb(0,0xe41a);a.byte(0x44,4);a.stb(0x44,0xe41c)
 a.stb(0,0xe410);a.byte(0x44,0x24);a.stb(0x44,0xe404);a.byte(0x58,1)
 a.label('selection');a.call('budget');a.cond(0xdb,'cleanup')
 a.ldb(0x44,0xe408);a.emit(0x71,4,0x44);a.cmpb(0x44,0);a.cond(0xd7,'absent')
 a.ldb(0x44,0xe408);a.emit(0x71,0x10,0x44);a.cmpb(0x44,0);a.cond(0xdf,'selection')
 a.label('cdb_loop');a.call('req');a.cond(0xdb,'cleanup')
 a.cmpb(0x43,2);a.cond(0xd7,'phase_error')
 a.emit(0xb2,0x29,0x44);a.stb(0x44,0xe416);a.call('ack');a.cond(0xdb,'cleanup')
 a.emit(5,0x2a);a.cond(0xd7,'cdb_loop')
 a.label('data_loop');a.call('req');a.cond(0xdb,'cleanup')
 a.cmpb(0x43,3);a.cond(0xdf,'status')
 a.cmpb(0x5c,0);a.cond(0xdf,'data_in')
 a.cmpb(0x43,0);a.cond(0xd7,'phase_error')
 a.emit(0x88,0x2e,0x30);a.cond(0xdb,'capacity')
 a.emit(0xb2,0x2d,0x44);a.stb(0x44,0xe416);a.jmp('data_ack')
 a.label('data_in')
 a.cmpb(0x43,1);a.cond(0xd7,'phase_error')
 a.emit(0x88,0x2e,0x30);a.cond(0xdb,'capacity')
 a.ldb(0x44,0xe416);a.emit(0xc6,0x2d,0x44)
 a.label('data_ack');a.call('ack');a.cond(0xdb,'cleanup');a.emit(7,0x30);a.jmp('data_loop')
 a.label('status');a.ldb(0x40,0xe416);a.call('ack');a.cond(0xdb,'cleanup')
 a.call('req');a.cond(0xdb,'cleanup');a.cmpb(0x43,7);a.cond(0xd7,'phase_error')
 a.ldb(0x41,0xe416);a.call('ack');a.cond(0xdb,'cleanup')
 a.label('completion');a.call('budget');a.cond(0xdb,'cleanup');a.ldb(0x44,0xe40a);a.emit(0x71,0x48,0x44);a.cmpb(0x44,0);a.cond(0xd7,'completion');a.jmp('cleanup')
 for name,code in [('busy',1),('absent',2),('phase_error',6),('capacity',5)]:
  a.label(name);a.imm(0x3e,code);a.jmp('cleanup')
 a.label('cleanup');a.cmpb(0x58,0);a.cond(0xdf,'return')
 # Experimental model cleanup: release ACK and bus; never invoke native init.
 a.byte(0x44,0xc4);a.stb(0x44,0xe404);a.stb(0,0xe404)
 for addr in [0xe418,0xe41a,0xe41c,0xe410]:a.stb(0,addr)
 a.byte(0x44,255);a.stb(0x44,0xe408);a.imm(0x48,64)
 a.label('cleanup_wait');a.ldb(0x44,0xe40a);a.emit(0x71,0x48,0x44);a.cmpb(0x44,0);a.cond(0xdf,'return')
 a.emit(5,0x48);a.cond(0xd7,'cleanup_wait');a.emit(0x81,0x80,0,0x3e)
 a.label('return');a.emit(0xf0)

 a.label('req');a.call('budget');a.cond(0xdb,'helper_return')
 a.ldb(0x42,0xe40a);a.emit(0xb0,0x42,0x43,0x71,7,0x43)
 a.mov(0x44,0x42);a.emit(0x71,0x80,0x44);a.cmpb(0x44,0);a.cond(0xdf,'req')
 a.emit(0xf8,0xf0)
 a.label('ack');a.byte(0x44,0xe4);a.stb(0x44,0xe404)
 a.label('ack_req_low');a.call('budget');a.cond(0xdb,'helper_return');a.ldb(0x44,0xe40a);a.emit(0x71,0x80,0x44);a.cmpb(0x44,0);a.cond(0xd7,'ack_req_low')
 a.cmpb(0x54,0);a.cond(0xdf,'ack_release')
 # Intentionally hold our ACK to exercise a real guest polling timeout.
 # This is not an emulated target fault or a physical stuck-device test.
 a.call('req');a.emit(0xf0)
 a.label('ack_release');a.byte(0x44,0xc4);a.stb(0x44,0xe404)
 a.label('ack_low');a.call('budget');a.cond(0xdb,'helper_return');a.ldb(0x44,0xe40a);a.emit(0x71,0x40,0x44);a.cmpb(0x44,0);a.cond(0xd7,'ack_low')
 a.mov(0x38,0x0a);a.emit(0xf8,0xf0)
 a.label('helper_return');a.emit(0xf0)

 a.label('budget')
 a.mov(0x44,0x3a);a.emit(0x61,63,0,0x44);a.cmp(0x44,0);a.cond(0xd7,'budget_sample');a.call('service')
 a.label('budget_sample');a.mov(0x46,0x0a);a.mov(0x44,0x46);a.emit(0x68,0x32,0x44);a.mov(0x32,0x46)
 a.emit(0x64,0x44,0x34,0xa4,0,0x36)
 # Experimental 32*65536 tick total budget permits full PIO blocks. This
 # explicitly does not qualify the masked interval for production use.
 a.cmp(0x36,32);a.cond(0xdb,'deadline')
 a.emit(0x68,0x38,0x46);a.cmp(0x46,5000);a.cond(0xdb,'deadline')
 a.emit(5,0x3a);a.cond(0xdf,'poll_limit');a.emit(0xf8,0xf0)
 a.label('deadline');a.imm(0x3e,3);a.emit(0xf9,0xf0)
 a.label('poll_limit');a.imm(0x3e,4);a.emit(0xf9,0xf0)
 # All service calls occur masked with WSR=0 and no live flags contract.
 # Preserve the transport scratch registers, but allow OS ISR-owned globals
 # (MIDI ring pointers, timer counters, etc.) to advance normally.
 a.label('service');a.emit(0x8b,1,(CONTROL+12)&255,(CONTROL+12)>>8,0)
 for r in saved:a.emit(0xc8,r)
 a.call('cancel_scan')
 a.ld(0x44,CONTROL+8);a.ld(0x46,CONTROL+10);a.ld(0x48,CONTROL+6)
 a.label('service_native_bank');a.st(0x48,0x10a)
 # No unconditional EI: the original caller must have its I bit set.
 a.emit(0x39,0x45,3);a.jmp('service_mask')
 a.emit(0xb0,0x44,8,0xb0,0x47,0x13)
 a.label('service_enable');a.emit(0xfb,*([0xfd]*8))
 a.label('service_mask');a.emit(0xfa);a.byte(8,0);a.byte(0x13,0)
 a.imm(0x48,15);a.label('service_probe_bank');a.st(0x48,0x10a)
 for r in reversed(saved):a.emit(0xcc,r)
 a.label('service_exit');a.emit(0x8b,1,(CONTROL+12)&255,(CONTROL+12)>>8,0);a.emit(0xf0)
 # Model-qualified raw scan follows the original 003B:4320 four-row access.
 # No native event queue, descriptor callback, or old button state is forced.
 # Scan only within an operation, while masked, with the MMIO bank unchanged.
 a.label('cancel_scan');a.ldb(0x44,CONTROL+18);a.cmpb(0x44,0);a.cond(0xdf,'cancel_scan_return')
 a.ld(0x44,CONTROL+16);a.cmp(0x44,0);a.cond(0xd7,'cancel_scan_return')
 a.stb(0,0xf00a);a.ldb(0x44,0xf00a);a.label('cancel_exit_row');a.ldb(0x46,0xf00a)
 a.ldb(0x44,0xf00a);a.ldb(0x44,0xf00a)
 a.emit(0x71,2,0x46);a.cmpb(0x46,0);a.cond(0xd7,'cancel_scan_return')
 a.st(0x30,CONTROL+20);a.mov(0x44,0x0a);a.st(0x44,CONTROL+22)
 a.ldb(0x44,0xe40a);a.stb(0x44,CONTROL+24)
 a.imm(0x44,1);a.label('cancel_latch');a.st(0x44,CONTROL+16)
 a.label('cancel_scan_return');a.emit(0xf0)
 a.label('code_end')
 code=a.finish();assert a.pc<=0x7fe
 result=bytearray(original);result[0x853e:0x853e+len(code)]=code
 table=bytearray()
 for case in CASES:
  cdb=bytes.fromhex(case['cdb']);assert len(cdb) in (6,10)
  table.extend(struct.pack('<BBBBHHH',1<<case['target'],len(cdb),case.get('hold_ack',0),case.get('direction',0),case['capacity'],case.get('poll_limit',65535),case.get('seed',0xdcba))+cdb+bytes(14-len(cdb)))
 table_offset=0x4800+(15<<10)+(TABLE&0x3fff)
 result[table_offset:table_offset+len(table)]=table
 hook=bytes([0xef])+struct.pack('<H',(BASE-(HOOK_PC+3))&65535)+bytes([0xfd])*5
 result[HOOK:HOOK+8]=hook
 decoded_hook=pypcode.Context('MCS96:LE:16:default').disassemble(hook,base_address=HOOK_PC).instructions
 assert decoded_hook[0].mnem=='LCALL' and int(decoded_hook[0].body,16)&65535==BASE
 diffs=[dict(offset=i,before=x,after=y) for i,(x,y) in enumerate(zip(original,result)) if x!=y]
 assert all(0x853e<=d['offset']<0xa480 or HOOK<=d['offset']<HOOK+8 for d in diffs)
 with output.open('xb') as f:f.write(result)
 report=dict(source_sha256=SOURCE_SHA,output_sha256=hashlib.sha256(result).hexdigest(),image_bytes=len(result),hook_file_offset=HOOK,hook_original=original[HOOK:HOOK+8].hex(),hook_new=hook.hex(),code_base=BASE,code_bytes=len(code),labels=a.labels,decoded=a.rows,cases=CASES,table_bytes=len(table),record_size=RECORD_SIZE,record_base=RECORDS,control=CONTROL,buffer=BUFFER,buffer_size=4096,saved_registers=saved,stack_local_bytes=4+2+2*len(saved),byte_diffs=diffs,qualifications=['Private research image; not released firmware.','Guest reads/commands through normal Save System entry; observer must not force guest state.','Interrupts permitted only at explicit service points; physical timing and worst-case IRQ latency remain unqualified.','Held-ACK cases deliberately stall the initiator handshake, not a simulated target fault.','Exit latches cancellation, drains the current bounded command, and stops subsequent operations. No physical abort/reset or write rollback claim.','Standard ten-byte command with byte-sensitive payload is not a BlueSCSI Toolbox command.'])
 output.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(dict(code_bytes=len(code),table_bytes=len(table),record_bytes=len(CASES)*RECORD_SIZE,stack_local_bytes=report['stack_local_bytes'],output_sha256=report['output_sha256'],decoded_instructions=len(a.rows))))

if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();build(args.output)
