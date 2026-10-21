"""Private linked IM1 candidate: mandatory GB6-v9, compact browser, retained SDS fixes."""
from pathlib import Path
import sys,json,hashlib,pypcode
from build_config import ROOT as R, OUTPUT as P, OS_SOURCE, BOOT_SOURCE
sys.path.insert(0,str(R/"patches"/"gb6"))
import build_gb6_combo as g
import patch_sds_remote_owner as remote
import patch_sds_local_owner as local
import patch_sds_early_cancel as early
build=json.loads((P/'build-linked.json').read_text());named=831+build['code_bytes']+224+build['resource_bytes']+192+build['extra_bytes']+build['lcd_bytes']+build['parser_quota']['bytes']
base=OS_SOURCE.read_bytes();assert hashlib.sha256(base).hexdigest()==g.OS_SOURCE_SHA256
browser=(P/'browser-linked.img').read_bytes();gb6=bytes(g.patch_os_disk_bytes(base,'v9'));boot=bytes(g.patch_boot_rom_bytes(BOOT_SOURCE.read_bytes()))
remote.BASE=0x013e;local.BASE=0x03be;early.BASE=0x045e
spans=early.patches();patched=bytearray(base);code_records=[];ctx=pypcode.Context('MCS96:LE:16:default')
for off,pc,before,after in spans:
 assert len(before)==len(after) and base[off:off+len(before)]==before,(hex(off),len(before))
 ins=ctx.disassemble(after,base_address=pc).instructions;assert sum(i.length for i in ins)==len(after)
 patched[off:off+len(after)]=after
 code_records.append(dict(file=off,pc=pc,bytes=len(after),data=after.hex(),instructions=[dict(pc=i.addr.offset,length=i.length,text=i.mnem+' '+i.body) for i in ins]))
sets=[{i for i,(a,b) in enumerate(zip(base,image)) if a!=b} for image in [browser,gb6,patched]]
assert not(sets[0]&sets[1] or sets[0]&sets[2] or sets[1]&sets[2]),'Patch collision'
combined=bytearray(base)
for image,offsets in zip([browser,gb6,patched],sets):
 for i in offsets:combined[i]=image[i]
for image,offsets in zip([browser,gb6,patched],sets):assert all(combined[i]==image[i] for i in offsets)
import patch_disk_warning_text as warning
combined=bytearray(warning.patch_bytes(bytes(combined)))
import patch_disk_verify_extent as extent
combined=bytearray(extent.patch_bytes(bytes(combined)))
for name,data in [('full.img',combined),('gb6.bin',boot)]:
 with (P/name).open('xb') as f:f.write(data)
report=dict(scope='private linked GB6-v9 + compact relocated browser + all early-cancel SDS predecessors; no full-fit/ownership/hardware claim',verify_extent_fixed=True,warning_text_fixed=True,gb6_mandatory=True,sha256=hashlib.sha256(combined).hexdigest(),rom_sha256=hashlib.sha256(boot).hexdigest(),no_patch_byte_overlap=True,gb6_checks=g.verify_disassembly(boot,combined),sds=code_records,layout=dict(sds_helpers=[dict(cpu=remote.BASE,file=0x8400+remote.BASE,bytes=640),dict(cpu=local.BASE,file=0x8400+local.BASE,bytes=160),dict(cpu=early.BASE,file=0x8400+early.BASE,bytes=31)],browser_code=dict(cpu=0x8480,file=0x8880,bytes=build['code_bytes']),listing=dict(logical=0x5bf0,physical=0x57f0,bytes=224),resources=dict(logical=0x5cd0,ui=0x9cd0,physical=0x58d0,bytes=build['resource_bytes']),control=dict(logical=0x5fc0,physical=0x5bc0,bytes=92),named_bytes=named,candidate_bytes=8002,residual_bytes=8002-named,full_stack_qualified=False,common_callback_local_stack=80),limitations=['Configured-target discovery, scoped drain cancellation, interruption/retry messages and SDS idle guard linked; native Disk ownership, full recovery and IRQ timing incomplete','No retained SDS execution claim until native lifecycle tests run','Common callback prologue adds2-byte saved RW1E and2-byte dispatcher return; interrupts/native callers add more stack','Runtime controller/input, browser media and SDS must be qualified on this exact hash'])
(P/'full.json').write_text(json.dumps(report,indent=2)+'\n');print('named',named,'residual',8002-named,'SHA',report['sha256'])
