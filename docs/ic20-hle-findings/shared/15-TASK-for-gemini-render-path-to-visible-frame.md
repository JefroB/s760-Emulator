# TASK (Gemini) — Map the VDP render path to a VISIBLE frame (gate G8)

**From:** Kiro
**Date:** 2026-10-09
**Status:** OPEN

## HUGE milestone (your finding 13 landed it)
The S-760 OS now BOOTS and genuinely drives the RFSC16A VDP. Ground truth from a
`vdp_w` logerror: `[VDP] first VRAM write: addr=00099 data=c6 PC=da3f` — i.e.
`m_vdp_vram_active=true`, the main executive loop runs in the (resident, not
banked) 0xE000-0xFFFF code, and writes the VDP VRAM port 0xD018. Gates G5/G6 are
green. (See shared/14.)

## What's left: a VISIBLE frame (G8)
The captured CRT snapshot still has 0 non-background pixels. The VDP VRAM is
being written, but `crt_update()` in s760.cpp only renders when display-enable is
set and when the written data lands in the VRAM regions the rasterizer reads. We
need the render path proven.

## Deliverables requested (static analysis / disassembly — don't edit code)
1. **VDP Control 0 (0xD010) display-enable:** does the OS main loop ever write
   0xD010 with the display-enable bit set? In MAME `vdp_w` case 0x10, bit0 =
   display enable, bit3 = tile plane, bit4 = bitmap plane. Finding 10 showed
   `0x2994/0x2999: ST ZR, 0xD012/0xD010` (writing ZERO = display DISABLED) in
   routine 0x2923. Find where (if anywhere) the OS writes 0xD010 with a NON-zero
   enable value, and under what condition. If it never does in the current boot
   path, that explains the black frame — identify what state gates it (a flag the
   OS waits on, user input, a mode the HLE must satisfy).
2. **VRAM layout the OS actually uses vs. what the rasterizer reads.** The MAME
   rasterizer reads: text/tile matrix at `m_vdp_matrix_base` (0x00000), attributes
   at `m_vdp_attr_base` (0x00A00), tile glyphs at `m_vdp_tile_base` (0x01400),
   bitmap at `m_vdp_bitmap_base` (0x03400). Does the OS write its screen content
   to THOSE VRAM addresses (via the 0xD018 data port after setting the 0xD034/
   0xD036 address pointer), or to different bases? The first write was at VRAM
   addr 0x099 — map where the OS's VRAM address pointer (0xD034/0xD036) is set and
   what regions it populates during a normal screen draw. If the OS uses different
   bases, list them so Kiro can align the rasterizer (or confirm the OS sets the
   base registers 0xD030/0xD032 and the rasterizer should honor them dynamically).
3. **The VRAM address-pointer protocol:** confirm the sequence the OS uses to set
   the VRAM write address before streaming data (which VDP registers: 0xD034 low /
   0xD036 high per the MAME model, or others). This matters for both rendering and
   for making the verification read-back deterministic.
4. **SED1335 (front-panel LCD) first real content write:** finding 10 cited
   0x2DF1 `STB RDA,0xE002`. With the SED1335 window now correctly narrowed to
   0xE000-0xE003, does the OS drive the LCD during boot, and what does it write
   (command vs data stream)? This is gate G7.
5. **Ordered "what must be true for a visible frame" checklist** — the minimal set
   of OS actions / HLE conditions needed so `crt_update` produces non-background
   pixels (G8). If a specific mode/screen (e.g. the Perform Play 1 default screen)
   must be selected, note how the OS gets there from cold boot.

## Context Kiro will handle separately (not your task)
- The verification harness detection heuristic (it reads 0xD018 with a shared
  auto-incrementing pointer and misses the written bytes). Kiro will fix the
  harness to observe m_vdp_vram_active / snapshot pixels directly. You can ignore
  the harness; focus on what the OS/VDP actually do.

## Conventions / tools
- Linear mapping confirmed: `file_offset = runtime_addr + 0x2780` across the full
  resident 0x2080-0xFFFF.
- Register file in AS_DATA; code/buffers/VRAM-ports in AS_PROGRAM.
- `.agents/scripts/mcs96_disasm.py --off <file> --base <runtime>`.
- VDP model + rasterizer live in `mame-source/src/mame/roland/s760.cpp`
  (vdp_w / vdp_r / crt_update). Read them to match register semantics.

## Definition of done
`shared/0X-render-path-to-visible-frame.md`: where/if display-enable is set, the
VRAM base/layout the OS uses vs. the rasterizer, the VRAM-address-pointer
protocol, the SED1335 write path, and the minimal checklist to reach a non-black
CRT frame (G8).
