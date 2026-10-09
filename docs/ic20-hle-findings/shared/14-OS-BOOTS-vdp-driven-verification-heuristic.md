# Finding 14 — THE OS BOOTS: VDP is genuinely driven. Remaining issue is the verification heuristic.

**Author:** Kiro
**Status:** SHARED / FINAL
**Date:** 2026-10-09
**Builds on:** Gemini 13 (linear 64KB mapping + SED1335 window fix)

## HEADLINE: the S-760 OS boots and drives the RFSC16A VDP
Applied Gemini finding 13:
- Extended `m_os_ram` to the full resident 64KB (runtime 0x2080-0xFFFF, file
  0x4800-0x1277F) — the main executive loop + display routines (0xE934 etc.) are
  NOT banked, they're resident; I had wrongly cut m_os_ram at 0xCFFF.
- Narrowed the SED1335 window from the bogus 0xE000-0xEFF7 to the real two ports
  0xE000-0xE003, and re-install all peripheral windows (VDP/LCD/MMIO/SCSI/FDC) on
  top of the 0x2080-0xFFFF RAM in machine_start (install order matters).

### Ground-truth proof the VDP is driven
A one-shot logerror in `vdp_w` case 0x18 (VRAM data port) fired:
```
[VDP] first VRAM write: addr=00099 data=c6 PC=da3f
```
So `m_vdp_vram_active = true` — the OS, running its genuine main loop, writes the
RFSC16A VDP VRAM. Debugger breakpoints also confirmed execution reaches the real
0xE934 routine and the 0xE957 `ST RW5E,0xD018` write site. **Boot works.**

Full confirmed progression now: reset → record loop (0x4B) → 0xB93A (PUSHA) →
0x2237 → EI (0x2185) → 0x2831 main entry → timer ISR (0x2B51 via installed vector
5) → main executive loop in resident 0xE000-0xFFFF → VDP VRAM writes.

## Remaining issue is NOT the boot — it's the verification detection heuristic
`run_verification` still reports `vdpVramActive=false` because its Lua detects
activity by READING the VDP data port 0xD018 and scanning for non-zero bytes:
```lua
for i=0,2399 do local b = vdp:read_u8(0xD018); if b~=0 then vdp_active=true ...
```
Problem: `vdp_r`/`vdp_w` share the SAME auto-incrementing `m_vdp_addr`. The OS
wrote to VRAM addr 0x099 and left m_vdp_addr elsewhere; the harness read starts
from the current m_vdp_addr and marches forward, so it does not reliably land on
the written bytes. The authoritative signal `m_vdp_vram_active` is TRUE, but the
read-back heuristic misses it.

### Recommended verification fix (methodology, per the independent review §10)
The harness should observe the genuine controller-activity flags directly rather
than inferring from an auto-incrementing port read:
- expose `m_vdp_vram_active` / `m_sed_vram_active` to Lua (e.g. a tiny debug
  read port, or a device state entry), OR
- have the Lua set the VRAM read pointer to a known base (write 0xD034/0xD036 =
  VRAM addr ptr low/high to 0) before scanning, so the read-back is deterministic,
- and/or count non-background pixels in the captured CRT snapshot as the primary
  pass signal (G8) rather than the port read.
This is the review's gate distinction G5/G6 (register vs VRAM-data write) vs G8
(rendered pixels). We are at G5/G6 (VDP driven); G8 (visible frame) needs the
display-enable + tile/attribute setup to actually render.

## Open: does a visible frame render yet? (G8)
The snapshot still shows 0 non-background pixels. The VDP VRAM is being written,
but `crt_update` renders tiles/attributes from specific VRAM bases
(m_vdp_tile_base etc.) with display-enable gating. Need to confirm the OS sets
VDP Control 0 (0xD010) display-enable and populates the tile/attribute planes the
rasterizer reads — i.e. whether the current writes land in the displayed region.
