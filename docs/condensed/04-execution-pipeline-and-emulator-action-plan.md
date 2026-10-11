# Execution Status & Engineering Priorities

Latest functional milestone: finding64. Original-ROM boot plus a host floppy swap loads the TX81Z sample performance through Disk > Load. Perform Play shows populated patches;211,968 wave-memory bytes match the original sample disk. BMOV operand over-fetch and observed IC4 controlBC RAM-to-wave DMA were fixed. Native audio synthesis remains unverified.

Latest analysis and CPU fix: finding65. Native keyboard notes now have a verified write trace: wave slot selection, sample-address fields, pitch changes and note release. CMPL operand over-fetch and sticky-overflow handling are fixed and tested. The native path no longer starts the unrelated host audition. Boot and sample loading still pass; native audio output remains unfinished.

Latest implementation: finding66. Native Wave Custom selector/data writes now populate per-slot register state;1,080 updates pass independent replay. Pitch/rate tables are decoded with explicit inference limits. Native waveform output remains unfinished.

Latest audio milestone: finding67. The opt-in raw-wave monitor produces verified PCM from firmware notes and loaded wave RAM. CPU PORT1 selects the internal output clock. It bypasses TVF/MEQ/envelope and uses provisional loop/interpolation behavior; this is not full hardware audio emulation.

Current next step: decode downstream amplitude/filter and mixer commands, then validate loop and DI behavior. Separate pending work includes BMOVI applicability/implementation, SCSI, FDC save/errors, DMA timing, encoder/RC-100 and remaining display modes. Complete chip fidelity is not claimed.

Reproduction: run `docs/ic20-hle-findings/chatGPT-work/run-native-os.ps1`; after ROM/system-disk boot, F5 inserts the configured TX81Z sample disk, then use Disk > Load. The launcher defaults new EEPROM profiles to Mouse+CRT. Normal launch disables sound. Add `-RawWaveMonitor` for the diagnostic forward-loop PCM path; filtering, envelopes and mixing are not yet emulated there.

Latest display update: finding63, correcting finding62's text colours. Text RGB uses attribute bits4/5/6: the active Perform tab is red, B0/B1 labels yellow, E0 labels cyan. Native original-ROM boot now composes the guest graphics planes and uploaded text font. Perform hover reverses red/white text, keyboard hover turns its border pink, and Command/Exit remains functional. The colour/attribute model matches these observed transitions; exact output intensity, mask/alternate-font behavior, cursor pixels and other display modes remain provisional or unresolved.


Latest input update: finding59. Native F008 now supplies the four-nibble
mouse movement packet and active-low buttons. A ROM-boot integration test
verifies firmware coordinate changes in both directions and left-button press/
release. The launcher enables host mouse input. Hardware cursor rendering,
encoder, RC-100 and complete IC20 behavior remain unfinished.


Latest: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
and reaches interactive Perform Play. Correct OP-760 identification and live VDP
pointer readback remove the video blockers. New native EEPROM profiles default
to Mouse+CRT at the user's request; existing profiles retain their setting.
Native LCD writes and its screen surface are restored. Rendering, hardware cursor,
complete chip behavior and power-on bank defaults still need work.


Previous result: finding57. Original IC15 now reads the system disk through the
native FDC/observed IC4 DMA mode, loads all112 tracks (disk4800..1007FF to
RAM0..FBFFF), and enters the disk OS without payload preloading. The ROM path
services timer interrupts and scans the panel, but its CRT remains blank.
Reset bank defaults are experimental; DMA is synchronous and CPU/peripheral
emulation remains partial. The older direct handoff still reaches Perform Play.

Latest: finding56 connects the
13-switch native panel matrix. FixedF00A=80 incorrectly asserted all low scan
bits; native reads now return sequential active-low rows. Command/Mode open
firmware menus and Exit returns to Perform Play. Host keys: C/M/Backspace,
arrows, A/S/D for F1/F2/F3, Z/X for S1/S2, left Shift. Encoder/mouse and complete
IC20/CPU/display behavior remain unfinished.

Latest finding55 supersedes the SEEK stop below: documented KB extended interrupts
and real flag-stack operations let firmware service SEEK and reach its main loop.
A30-second native run writes the Perform Play screen to guest VRAM; MAME renders
it through a diagnostic ASCII raster. This is the reconstructed disk handoff,
not full ROM cold boot or complete CPU/peripheral emulation. See
finding55
for evidence and the complete-chip implementation gaps.

**Latest independent progress: findings53/54.** Opt-in banked C000 handoff
executes native services, passes the sample-memory probe with a provisional
host-port model, and reaches FDC SEEK. The next blocker is196KB interrupt
mask/source/vector routing: bank005A:5DEB waits on flag[1D0E], while SFR12/13
writes are unmapped by N8097BH. Verify interrupt semantics and the firmware
handler before implementing them. Do not inject flags or guessed opcode behavior.
The older flat-run observations below remain historical comparison evidence.

**Current state (findings53/54/55/56): the banked native handoff boots the disk
OS to Perform Play and runs interactive front-panel menus** (Command/Mode open,
Exit returns; 13-switch SC/SP scan matrix in document 07). The
separate-instruction/data banking hypothesis
(ROM4F74 data selectors0108–010E; instruction selectors0100–0106) is confirmed
by coherent native execution: ROM4750 hands off at C000 with the disk payload at
physical0, native EEPROM/sample-RAM/FDC services run without the old HLE stubs,
FDC SEEK interrupts are serviced (vector203A→0120→handler CD5D), and the main
loop draws Perform Play to guest VRAM (rendered via a diagnostic ASCII raster).
This supersedes the flat-baseline "D010 never reached" framing below as the
leading path. It is opt-in (`S760_BANKED_OS=1`), a post-loader handoff rather than
a full ROM cold boot, and does NOT claim complete CPU/peripheral fidelity — the
flat baseline remains for comparison. The earlier flat-model lifecycle/overlap
and D010-enable notes below are retained as the superseded-baseline record.

**Interrupt servicing confirmed (native, `native-panel-fresh-60s.log`).** Over a
60 s run the guest services two real ISRs with vectors resolved from guest memory
and flags saved/restored on the real guest stack (SP bounded ~0x1100–0x111a):
- **HSO / software timer**, level 5, vector `200A` → `CAD1`: **2,604** times.
- **FDC EXTINT1**, level 13, vector `203A` → `0120` (`PUSHF; LJMP CD5D`): **3** times.
The main loop reaches ≥20,000,000 instructions with queue 0000/0000 and no derail
— a live executive, not a spin. These require real 196KB interrupt semantics
(INT_MASK1/INT_PEND1 at 13/12, EXTINT1 at 203A); the old stack-neutral
PUSHF/PUSHA/POPA workarounds apply only to the flat baseline.

**Reproduce the native OS boot** (opt-in; `chatGPT-work/run-native-os.ps1`):
`S760_BANKED_OS=1 S760_F00A=80` (PAGE_XLAT/QUEUE_INIT unset), then
`mames760.exe s760 -rompath <roms> -nvram_directory <scratch> -video gdi
-sound none -window -skip_gameinfo`. The `-nvram_directory` is required so the
93C46 EEPROM persists; `-video gdi` renders the diagnostic text raster. Headless
verification uses `-video none ... -str <sec>` + `verify_native_boot.py`, which
replays logged VDP commits into a VRAM buffer and asserts the literal guest bytes
`Perform Play 1` / `Patch Name` / `KbdOn` plus the FDC/HSO interrupt counts.

**Complete-chip scope (user requirement, finding55).** The opt-in KB interrupt
extension is a verified subset, not a complete S80C196KB. Remaining: a dedicated
KB device/full SFR+WSR windows; NMI and all extended interrupt sources with
priority/timing; Timer2 capture/overflow, serial TI/RI, HSI FIFO variants;
instruction audit (esp. IDLPD and block ops) with cycle validation; full CPU-gate
0110..011F control/IRQ/DMA; real ROM cold boot; encoder input (front-panel/mouse
input is now WIRED — MSX-protocol mouse via F008 bit6 handshake, verified in
finding59, see document 07); and VDP character-ROM/attributes/composition + LCD.
Do not claim full chip fidelity, usable front-panel input, working sample
load/audio, or hardware-exact graphics from this bounded boot.

Snapshot 2026-10-10: shared findings through 55, checked against current code.
Native results are ChatGPT findings 53–55 (opt-in `S760_BANKED_OS`); the flat
baseline results below are Kiro's finding 25.

## Established bring-up path

Disk RAM preload → reset 2080 → stack/work init → resource HLE → B93A → 2237
→ EI 2185 → main entry 2831 → timer ISR 2B51 → executive 2887 → controller writes.
This is disk-reset HLE, not native IC15 cold boot.

Resolved blockers: AS_DATA register access; vector RAM (200A→2B51); narrow
E000–E003 LCD window; RET compatibility shims at 9B42/9B51/9B71 to prevent a
zero-byte sled into 9C80 blanking; high-byte handling at D019/D025/D035/D031.
The original runtime population of delay stubs remains unknown.

Current F00A default is **80**, overridable with `S760_F00A`; this is the tested
bring-up setting, not a complete board-strap specification.

## CPU workaround status

PUSHA/POPA are stack-neutral in `mcs96ops.lst`. PUSHF is stack-neutral but clears
PSW and checks IRQ; POPF leaves PSW/SP. These are **boot compatibility workarounds**,
not proved Intel architectural semantics. Do not change them in unrelated work.

**Block-op over-fetch corrections (findings 64/65, native mode).** `BMOV` (0xC1)
and `CMPL` (0xC5) each had duplicate operand fetches in the generated core: after
`direct_2w` fetched the operands, the opcode body fetched two more bytes,
consuming the following instruction and corrupting block copies / comparisons.
Both were corrected per the 80C196KB User's Guide (BMOV: 3-byte, 6 setup + 8/11/14
states per word, count exhausted; CMPL: 3-byte, 32-bit subtract, 7 states, sticky
VT on overflow). Each verified by isolated CPU fixtures. **BMOVI (0xCD) still has
the same duplicate-fetch pattern and is UNaudited** — its KB applicability/interrupt
semantics must not be assumed from later 196 variants; audit separately before use.

Finding 25 traced the derail to PUSHF E086 followed by RET E136 popping PSW as
an address. With the workaround Kiro reports six seconds, exit zero, no derail.
The 519F BR[RW3C] failure followed misaligned execution; task 24 identifies the
normal RW3C load at 5186. It does not justify forcing RW3C through HLE.

Gemini's `25-rw3c-dispatch-decode.md` confirms the consumed dispatch record:
RW38=2184+4*(RE0-17h), handler word at +0, selector word at +2. Its proposed
F121 continuation is not verified: aligned original-image code has a five-byte
load at F120 and the comparison at F125, so F121 is inside an instruction.
Live handler/loader behavior must explain the pushed F121 before adding RET
stubs or stack padding. Shared review 29 records the exact bytes and requests.

Gemini's response `30-gemini-response-to-chatgpt-dispatch-review.md` accepts
that correction and rejects the earlier artificial dispatch fixes. Original
bytes at 4AC2–4AE0 confirm this caller selects RE0=17h–1Ch before jumping to
5141, addressing six four-byte slots at 2184–2198. This establishes the
caller's accepted IDs, not exclusive entry points or valid live table contents.
The response commits to shadow/countdown watches but supplies no new live
write-watch results; initialization and the natural D010 trigger remain open.

## Latest reported result

```text
vram_active=1 sed_active=83 display_enabled_ever=0 ctrl0(D010)=00
addr=074ba matrix_base=0000 attr_base=0a00 tile_base=1400 bitmap_base=3400
```

Controller activity is established for this bounded run. A complete CRT UI,
native ROM boot, hardware DSP parity, and all-suite test success are not.
Finding 23's earlier blue-screen observation is a different run.

Later instrumented runs (findings 48/50/52, verified exe) report
`vram_active=1 display_enabled_ever=0 ctrl0(D010)=00 addr=074ba` and show the
executive doing a bounded IC20 selector-4B burst after a one-shot 00B1 dispatch
(see document 02). Finding 52's 30-second run proves the 4B burst is NOT a
permanent stall (4B count flat at 132,413 while 0166 keeps climbing; the OS
proceeds to DFxx/E09x relinking work). At 30 s: PC=DFC3, SP=111C, queue words
0102/EF1C (still invalid indices), word 2A8C=0601, only three nonzero VDP bytes
in 07400–077FF. `display_enabled_ever=0` / `D010=00` is unchanged: the natural
D010 enable is still never reached, and no OS display boot is achieved.

Task 26 asks for the natural nonzero D010 writers and their root guards. Named
candidates: 92D0, 9326, 9F95, A012, A900; blank writers include 2999 and 9CAC.
Event pump 54E8 reads FIFO indices 21AC/21AE and storage 21B0. Finding 21 links
event 0C to 5714/drawing, but the natural boot producer and exact enable guard
still need proof. Do not inject a synthetic event or force the register.

The earlier assertion that `(cached_config & C0)==40` is satisfied by F00A=80
is arithmetically false. Some cited locations are disk offsets beyond resident
64 KB. Mapping/branch sense must be established before defining a controller
contract; the evidence request is in `shared/`.

Priorities: solve task 26; align streamed VRAM with renderer; verify authentic
UI output; correct HLE records/disk errors; replace workarounds only with proof.

Kiro's later finding `29-RESPONSE-root-cause-work-ram-not-zeroed-queue-ptrs-garbage.md`
reports no executed 2496/24A0, natural queue-post entry or candidate display
enable routine in the reset trace. Invalid queue indices retain startup-image
bytes. This supports an initialization/loading problem; the proposed zeroing
fix is unproved. The cited ROM clear range 4000–8000 excludes 21AC/21AE,
which overlap startup instructions in the preload. Establish the loader's
actual writes and transition from startup code to data before clearing them.
Shared review 30 provides exact overlapping instructions and evidence requests.

Finding 31 reports an opt-in queue-zero diagnostic reaching the empty-queue
exit and 3F1C, then faulting at B92B; it does not demonstrate D010 enable.
Original-image bytes put B92B inside the load at B928 (`A1 E6 54 1E`),
and B93A inside the byte load at B938 (`B1 05 F4`). These alternate entry
boundaries need live loader/service evidence before opcode changes. Review 32
records the decode. Current source enables this diagnostic whenever the
`S760_QUEUE_INIT` variable exists, even with value `0`; unset it for baseline.

## Verification gates

Retain the original independent-review meanings (older condensed renumbering
was inconsistent):

| Gate | Meaning |
| --- | --- |
| G1/G2 | EI 2185 / main entry 2831 |
| G3/G4 | Proven interrupt/vector acceptance / sane return |
| G5/G6/G7 | VDP register / VDP VRAM / SED command-data activity |
| G8 | Non-background rendered frame; assess actual UI separately |
| G9 | Automated verification passes |

Activity, enabled-ever, frame content, and UI legibility are different checks.
Prefer direct activity flags to intrusive auto-increment data-port reads.

Existing helpers: `.agents/scripts/regen_mcs96.ps1`, `temp/build_s760.ps1`
(driver lib `mame_s760.lib`), `temp/build_optional.ps1` (CPU core `optional.lib`
after editing `mcs96.cpp/.h`), `temp/link_s760.ps1` (relink exe), `temp/verify.py`,
`temp/run_trace.ps1`, `temp/trace_crash.ps1`. Inspect options before use. New
scratch belongs in the author's work folder; move finished findings to shared.
Full testing guidance is in document 08.

**Build procedure (confirmed; full runbook in `.kiro/steering/mame-build-and-trace.md`).**
The incremental build has reproducible silent-failure modes — verify every step,
never trust "exit 0":
- An "exit 0" compile can leave the `.obj` stale/older than source (symbol not in
  the lib). Delete the specific `.obj` to force recompile; confirm the lib
  contains a unique string you added.
- A link can print `-> mames760.exe` yet produce no exe (empty `@(Link)` /
  up-to-date skip). Delete `mames760.exe` + its `.tlog`, then relink.
- `/t:Build`/`/t:Rebuild` on the exe project regenerates the FULL MAME driver
  list → ~43k unresolved `driver_*` externals; the CustomBuild must keep the
  `-f src/mame/s760.flt` filter (correct `drivlist.cpp` has `s_driver_count=2`).
- Parallel MSBuild can lose outputs via a failing shared `mspdbsrv` (C1902).
  Building SERIALLY with `/p:UseMultiToolTask=false /p:CL_MPCount=1
  /p:DebugInformationFormat=OldStyle /m:1` is the confirmed fix.
