"""Relax only emitted inverse-Jcc/LJMP pairs; preserve all control-flow targets."""
import struct,re,pypcode
def relax(a,base):
 old=bytes(a.code); oldlabels=dict(a.labels)
 ctx=pypcode.Context('MCS96:LE:16:default')
 before=ctx.disassemble(old,base_address=base).instructions
 candidates={index-3:(old[index-3]^8,label) for index,label,after in a.fixups if index>=3 and 0xd0<=old[index-3]<=0xdf and old[index-2:index]==bytes([3,0xe7])}
 selected=set()
 def mapped(offset):return offset-3*sum(start<offset for start in selected)
 while True:
  changed=False
  for start,(op,label) in candidates.items():
   if start in selected:continue
   target=oldlabels[label]-base
   distance=mapped(target)-(3 if target>start else 0)-(mapped(start)+2)
   if -128<=distance<=127:selected.add(start);changed=True
  if not changed:break
 result=bytearray();i=0
 while i<len(old):
  if i in selected:
   op,label=candidates[i];disp=mapped(oldlabels[label]-base)-(len(result)+2)
   assert -128<=disp<=127
   result.extend([op,disp&255]);i+=5
  else:result.append(old[i]);i+=1
 for index,label,after in a.fixups:
  if index-3 in selected:continue
  newindex=mapped(index);target=mapped(oldlabels[label]-base)
  struct.pack_into('<H',result,newindex,(target-(newindex+2))&65535)
 a.labels={k:base+mapped(v-base) for k,v in oldlabels.items()}
 after=ctx.disassemble(bytes(result),base_address=base).instructions
 assert sum(i.length for i in after)==len(result)
 starts={i.addr.offset for i in after}
 # Verify decoded branch/call destinations against old control-flow edges.
 afterby={i.addr.offset:i for i in after}
 for ins in before:
  offset=ins.addr.offset-base
  if offset in selected:
   new=afterby[base+mapped(offset)]
   assert new.mnem.startswith('J')
   assert int(new.body,16)==a.labels[candidates[offset][1]]
  elif offset-2 in selected:continue
  elif ins.mnem in ('LJMP','LCALL','JE','JNE','JC','JNC','JH','JNH','JBS','JBC'):
   targets=re.findall(r'0x[0-9a-fA-F]+',ins.body)
   assert targets,(ins.mnem,ins.body)
   target=int(targets[-1],16)
   new=afterby[base+mapped(offset)]
   expected=base+mapped(target-base)
   actual=int(re.findall(r'0x[0-9a-fA-F]+',new.body)[-1],16)
   assert actual==expected,(ins.mnem,ins.body,new.body,expected)
   assert actual in starts
 a.code=result
 a.rows=[dict(pc=i.addr.offset,bytes=bytes(result[i.addr.offset-base:i.addr.offset-base+i.length]).hex(),text=i.mnem+' '+i.body) for i in after]
 a.relaxation=dict(before=len(old),after=len(result),saved=len(old)-len(result),branches=len(selected))
 return bytes(result)
