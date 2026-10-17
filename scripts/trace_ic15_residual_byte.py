"""Observe original-ROM byte 6903 reads with debugger instruction history.

Runs use private media/state and ordinary panel inputs. No firmware mutation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OBSERVER = r'''
local cpu=manager.machine.devices[':maincpu']
local s=cpu.spaces['program']
local dbg=assert(manager.machine.debugger,'debugger must be enabled')
local active=true local inspecting=false local hits=0 local control=false
local taps={}
local function context(tag,a,d,m,page,physical)
 inspecting=true
 print(string.format('[CONTEXT-BEGIN] tag=%s addr=%04x data=%04x mask=%04x page=%04x physical=%06x',tag,a,d,m,page,physical))
 for name,state in pairs(cpu.state) do
  print(string.format('[REGISTER] %s=%x',name,state.value))
 end
 for selector=0x100,0x10e,2 do print(string.format('[SELECTOR] %04x=%04x',selector,s:read_u16(selector))) end
 local before=#dbg.consolelog
 dbg:command('history :maincpu,20')
 for line=before+1,#dbg.consolelog do print('[HISTORY] '..tostring(dbg.consolelog[line])) end
 print('[CONTEXT-END] '..tag)
 inspecting=false
end
-- Page base granularity is 400h, so all aliases retain low ten bits 103h.
for addr=0x0102,0xfd02,0x400 do
 local a0=addr
 taps[#taps+1]=s:install_read_tap(a0,a0+1,'residual-byte-'..a0,function(a,d,m)
  if not active or inspecting or (m & 0xff00)==0 then return end
  local logical=a+1 local page=s:read_u16(0x108+2*(logical >> 14))
  local physical=(page << 10)+(logical & 0x3fff)
  if physical>=0x1e0000 and physical<=0x1fffff and (physical & 0x7fff)==0x6903 then
   hits=hits+1 context('TARGET',logical,d,m,page,physical)
  end
 end)
end
positive=s:install_read_tap(0x8904,0x8905,'history-positive-control',function(a,d,m)
 if active and not inspecting and not control and (m & 255)~=0 and s:read_u16(0x10c)==0x798 then
  control=true context('KNOWN-FDC-TEMPLATE',a,d,m,0x798,0x1e6904)
 end
end)
finish=s:install_write_tap(0x106,0x107,'residual-handoff',function(a,d,m)
 if active and cpu.state['PC'].value==0x4755 then
  print(string.format('[ROM-HANDOFF] target_reads=%d positive_control=%s',hits,tostring(control))) active=false
 end
end)
local frames=0
emu.register_frame_done(function()
 frames=frames+1
 if frames%300==0 then print(string.format('[WATCH-STATE] frame=%d pc=%04x target_reads=%d positive_control=%s',frames,cpu.state['PC'].value,hits,tostring(control))) end
end)
'''


def run(case, output):
    output.mkdir(parents=True, exist_ok=False)
    media = output / 'roms/s760'
    media.mkdir(parents=True)
    original = ROOT / 'S760224.IMG'
    shutil.copyfile(original, media / 's760224.img')
    selected = media / 'selected.img'
    content = original.read_bytes()
    if case == 'invalid':
        content = bytes(len(content))
    elif case == 'short':
        content = content[:720 * 1024]
    selected.write_bytes(content)
    code = OBSERVER
    if case == 'setup':
        code += """
local mode=nil for _,f in pairs(manager.machine.ioport.ports[':PANEL1'].fields) do if f.name=='Mode' then mode=f end end
assert(mode) mode:set_value(1) local entered=false
emu.register_frame_done(function() if not entered then mode:set_value(1) local pc=cpu.state['PC'].value
 if pc>=0x5741 and pc<=0x5809 then entered=true mode:set_value(0) print('[SETUP-ENTERED]') end end end)
"""
    if case.startswith('scsi-'):
        prior = json.loads((ROOT / 'docs/condensed/validation/ic15-native-scsi-absent-fallback-2026-10-16.json').read_text())
        code += '\n' + prior['observer_and_input_source']
        target_dir = output / 'roms/SCSI'
        target_dir.mkdir()
        if case != 'scsi-absent':
            source = ROOT / 'roms/SCSI/HD00_512.img'
            if case == 'scsi-valid':
                source = ROOT / 'docs/ic20-hle-findings/chatGPT-work/rom-scsi-contract-2026-10-16/native-scsi-valid-header/roms/SCSI/HD00_512.img'
            shutil.copyfile(source, target_dir / 'HD00_512.img')
    lua = output / 'observer.lua'
    lua.write_text(code, encoding='utf-8')
    env = {k: v for k, v in os.environ.items() if not k.startswith('S760_')}
    env.update(S760_ROM_BOOT=str(ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN'),
               S760_FLOPPY=str(selected), S760_NATIVE_VALUE_ENCODER='1')
    command = [str(ROOT / 'mame-source/mames760.exe'), 's760', '-rompath', str(output / 'roms'),
               '-nvram_directory', str(output / 'nvram'), '-cfg_directory', str(output / 'cfg'),
               '-video', 'none', '-sound', 'none', '-skip_gameinfo', '-nothrottle',
               '-seconds_to_run', '30', '-autoboot_delay', '0', '-autoboot_script', str(lua),
               '-log', '-debug', '-debugger', 'none']
    result = subprocess.run(command, cwd=output, env=env, capture_output=True, text=True,
                            timeout=60, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    log = result.stdout + result.stderr
    (output / 'console.log').write_text(log, encoding='utf-8')
    error_log = (output / 'error.log').read_text(errors='replace') if (output / 'error.log').exists() else ''
    evidence = dict(case=case, command=command, returncode=result.returncode, observer_source=code,
                    observations=[l for l in log.splitlines() if l.startswith(('[CONTEXT-', '[REGISTER]', '[SELECTOR]', '[ROM-HANDOFF]', '[WATCH-STATE]', '[SETUP-ENTERED]', '[TIMEOUT]', '[ENTERED]', '[INPUT]'))],
                    history_console=log, dma_rows=[l for l in error_log.splitlines() if '[NATIVEDMA]' in l],
                    lua_errors=[l for l in log.splitlines() if 'LUA ERROR' in l.upper()],
                    identities={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                for p in [ROOT / 'roms/BOOT/Roland_S-760_v1.11.BIN', original, ROOT / 'mame-source/mames760.exe', Path(__file__)]},
                    selected_media_sha256=hashlib.sha256(selected.read_bytes()).hexdigest(),
                    qualification='Passthrough data-read observers and debugger history; original ROM unchanged. Fresh private state; ordinary panel inputs. Native model, not physical parity. Stops target observation at first original-ROM OS handoff. History displays under current mapping; selector snapshots retain context.')
    # Retain an independent original-ROM reconstruction alongside raw history.
    # Debugger history uses current fetch selectors, not saved per-entry banks.
    import re
    analysis = json.loads((ROOT / 'docs/ic20-hle-findings/chatGPT-work/rom-residual-text-2026-10-16/analysis.json').read_text())
    instructions = {(r['page'], i['pc']): i for r in analysis['regions'] for i in r['instructions']}
    contexts = []
    for block in log.split('[CONTEXT-BEGIN] ')[1:]:
        head, body = block.split('\n', 1)
        body = body.split('[CONTEXT-END]', 1)[0]
        selectors = {int(k, 16): int(v, 16) for k, v in re.findall(r'\[SELECTOR\] ([0-9a-f]+)=([0-9a-f]+)', body)}
        history = []
        for pc_text, raw in re.findall(r'\[HISTORY\] ([0-9a-fA-F]+): ([^\n]+)', body):
            pc = int(pc_text, 16)
            page = selectors.get(0x100 + 2 * (pc >> 14))
            decoded = instructions.get((page, pc))
            history.append(dict(pc=pc, snapshot_fetch_page=page, raw_debugger_display=raw,
                                original_rom_instruction=decoded,
                                context_qualification='Snapshot fetch context; historical selector changes require separate review.'))
        contexts.append(dict(event=head, history=history))
    evidence['event_contexts'] = contexts
    evidence['history_qualification'] = 'Debugger history uses current fetch mapping after BUG-085. Retained PCs are also matched to independent original-ROM analysis using event fetch selectors; neither view proves historical selector preservation.'
    (output / 'evidence.json').write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(case=case, returncode=result.returncode, errors=evidence['lua_errors'],
                         contexts=[l for l in evidence['observations'] if l.startswith('[CONTEXT-BEGIN]')],
                         milestones=[l for l in evidence['observations'] if l.startswith(('[ROM-HANDOFF]', '[WATCH-STATE]', '[SETUP-ENTERED]'))][-6:])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['boot', 'setup', 'invalid', 'short', 'scsi-absent', 'scsi-bad-header', 'scsi-valid'], required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.case, args.output.resolve())
