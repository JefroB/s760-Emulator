# UI Architecture & Front Panel

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


Latest: finding56 connects the
13-switch native panel matrix. FixedF00A=80 incorrectly asserted all low scan
bits; native reads now return sequential active-low rows. Command/Mode open
firmware menus and Exit returns to Perform Play. Host keys: C/M/Backspace,
arrows, A/S/D for F1/F2/F3, Z/X for S1/S2, left Shift. Encoder/mouse and complete
IC20/CPU/display behavior remain unfinished.

Condensed from the UI consolidation plan/review, front-panel mapping, and LCD
architecture, checked against current bridge, React tests, and driver code.

## Responsibility boundaries

`google-ui/` is the canonical physical shell: rack, monitor bezel, knobs,
buttons, meters, LCD/Gotek housings, and visual display effects. The emulation
backend supplies authentic CRT/LCD pixels, audio, and device state. Avoid
invented menus or fallback text inside MAME rasterizers; an enabled background
or fabricated UI does not prove firmware rendering.

The bridge and backend selector exist in `core/src/`; React's client is
`google-ui/src/bridge/S760BridgeClient.ts`. The canonical contract is
`core/include/s760/s760_bridge_protocol.hpp`, version 1. Browser/standalone uses
loopback WebSocket (default `ws://localhost:8760`); plugin editors support a
WebView binding or per-instance transport. Do not hard-code one plugin port.
Controls/telemetry are JSON; display frames are binary. Sampler audio remains
backend/host-owned; no audio framing is specified by this display wire contract.

Inbound categories: button press/release, dial delta, mouse movement/click,
disk mounting, note on/off. Mouse positions are normalized [0,1] CRT coordinates.
Outbound: CRT/LCD/Gotek frames and telemetry (dimensions, timestamp/FPS, peaks,
voices, mode). Each frame has a six-byte header: u8 surface, u16LE width,
u16LE height, u8 format. CRT uses RGBA8888; LCD/OLED use packed MSB-first MONO1.
Canonical sizes: 640×480, 160×64, 128×32. Reject malformed lengths.
Gotek OLED is an aftermarket drive display, not an original Roland controller.

## Migration order and acceptance

1. Remove duplicated MAME shell rendering and migrate affected pixel/chassis
   tests together. Preserve real CPU, peripheral, and display-controller behavior.
2. Correct coverage generators so React rows name actual React tests, and
   hardware rows name hardware/backend tests. Regenerate matrices.
3. Implement/verify the dual-backend bridge and composite incoming buffers into
   React. Confirm input reaches the selected backend and audio/video are live.
4. Exercise shell behavior with Vitest/component tests and Playwright/E2E;
   keep MAME assertions focused on authentic controller output.

The migration is partly implemented: invented MAME chassis/mode renderers are
removed; the bridge and React Vitest/Playwright suites exist. Tests include
ShellNavigationMigration, RackEars, SHIFT properties, bridge decode/input/pointer
math, shell navigation, and composed-shell E2E. Old claims that React has no test
tooling are obsolete. Existence is verified here; pass totals are not claimed
without a fresh run. The old ROM-undumpable dependency is also obsolete.

## Controller mode (finding 58)

The S-760 OS supports three controller/display modes (Owner's Manual Advanced
3-92): **Panel+LCD**, **Mouse+CRT**, and **RC100+CRT**. Selecting either CRT mode
routes display to the CRT and stops using the LCD ("Please see my CRT/LCD"). The
selection is a persisted preference in EEPROM **byte 8** (loaded by ROM532F..5346
into RAM 4CAA+, so byte 8 = RAM 4CB2): ROM5194 validates the range 0..2 and 51C4
clears it when no option board is present (byte8=1 = Mouse+CRT). Finding57's
"blank CRT" was NOT a boot failure — the OS had correctly selected Panel+LCD and
was displaying on the LCD. The native EEPROM default template now sets byte 8 = 1
(Mouse+CRT) per the user's request; `nvram_default()` applies the template only
when no saved EEPROM exists, so existing profiles keep their selection. Selecting
Mouse+CRT does NOT by itself implement mouse input.

**Mouse input is WIRED and verified (finding59).** The OP-760-1 mouse is an
MSX-protocol mouse (bus → IC20 MX0..MX6, Service Notes p14/p18), and MAME's
existing `MSX_MOUSE` device (`src/devices/bus/msx/ctrl/mouse.cpp`, Wilbert Pol)
edge/phase model is reused. The S-760 handshake runs at **F008 bit6**: OS file
18BB4..18C0D toggles F008 bit6 (40/BF/40/BF) and reads four nibbles, assembling X
then Y as negated signed bytes; a 3 ms gap restarts the four-nibble packet.
Buttons are active-low bits 4/5 (file 18C76..18CAA), with current/pressed/released
masks at RAM 2132..2135. The firmware applies a **2× multiplier** (file
18D1F..18D2C). Verified via post-boot MAME input injection: host +20,+10 → guest
40,20; left button sets mask 2132=0x10 on press, 0x00 on release; reverse motion
tracks. The resulting cursor position lands in the VDP cursor registers
E80C/E80E/E810 (see document 03). Right button is connected but was not
independently exercised; RC-100 and full IC20 port-direction behaviour remain
unimplemented.

(Correction to an earlier note: the handshake is F008 bit6, NOT the VDP
D020-D023 "mouse X/Y" from the superseded flat model.)

## Native panel scan matrix (finding 56, Service Notes p18/21, visually checked)

The IC20 uPD65012GF drives scan columns SC0..3; the thirteen panel switches
return on SP0..3 (pulled up, active-low). Firmware (bank003B:4030/4320) writes
0 to F00A, reads four consecutive scan bytes, complements and masks each with
0x3F, and stores current/previous/pressed/released rows at 2065/206D/2075/207D
(the 4320 variant also caches the raw byte at 2085). Confirmed wiring:

| Scan column | SP0 | SP1 | SP2 | SP3 |
| --- | --- | --- | --- | --- |
| SC0 | Command | S1 | S2 | Right |
| SC1 | Mode | Exit | Up | (unused) |
| SC2 | F1 | F3 | Left | (unused) |
| SC3 | F2 | Shift | Down | (unused) |

Native mode reads four MAME input ports sequentially at F00A, restarting the
scan on the firmware's zero write; the scan index is save-state registered.
Returning a constant (old F00A=80) asserted every low scan bit and spuriously
opened the Command menu — fixed by returning released rows. Upper configuration
bits still use `S760_F00A` (default 0x80); native mode ignores that override's
low six bits. Host-key bindings (through the scan port, not RAM writes):
C=Command, M=Mode, Backspace=Exit, arrows=cursors, A/S/D=F1/F2/F3, Z/X=S1/S2,
left Shift=Shift. Confirmed interactive: Command and Mode open their firmware
menus and Exit returns to Perform Play. Still open: encoder (F012), remote/mouse,
SP4+ wiring (incl. the SC0/SP4 diode on p18), scan timing, and the high
configuration-bit source. F010 LED readback is still the old incorrect EEPROM
alias; this is NOT complete IC20 emulation.

## Front-panel mapping contract

[front-panel-button-mapping.md](../front-panel-button-mapping.md) remains the
human canonical enumeration; `google-ui/src/data/shiftButtonMap.ts` is its
machine-readable mirror. The source seeds **23 unverified controls**:
POWER; PERF/PATCH/PART/SAMPLE/SYSTEM/DISK; NAV_LEFT/RIGHT/UP/DOWN; DEC/INC;
ENTER/EXIT; F1–F6; VOLUME; VALUE_DATA. This is the mapping's seeded inventory,
not independent confirmation of the physical panel layout.

The seeded SHIFT functions, silkscreen labels, chord types/payloads, and manual
page references are empty. A SHIFT control may render only when its function is
`Verified`, it has a recorded chord, and it is not Gotek-owned. Verification
requires a specific manual page; unverified entries require a reason. Keep the
Markdown and TypeScript entries in lockstep by `buttonId`. Do not fill gaps
using guessed shortcuts or UI mockups. Gotek controls remain a separate owner.

## SED1335 LCD reference

The front LCD is 160×64 monochrome; a full bitmap is 20 bytes/line × 64 =
1,280 bytes. The LCD document describes 4 KB memory, a 20×8 text matrix at
SAD1 `0x0000`, and a graphic layer at SAD2 `0x0800`; these are documented model
defaults, while actual layer start/stride are programmable.

| Command | Purpose |
| --- | --- |
| `0x40` SYSTEM SET | Geometry/stride/controller configuration (8 parameter bytes) |
| `0x44` SCROLL | Layer starts and line allocations |
| `0x46/47` CSRW/CSRR | Write/read cursor address |
| `0x42/43` MWRITE/MREAD | Stream VRAM and advance cursor |
| `0x58/59` DISP OFF/ON | Blank/enable selected layers |
| `0x5A` HDOT SCR | Horizontal fine scroll |
| `0x5B` OVLAY | Layer composition |
| `0x5D` CSRFORM | Cursor shape |

The old LCD document's broad `0xE000–0xEFF7` window and `E000=data/E001=cmd`
mapping conflict with later driver findings. For the current S-760 integration,
use the narrow **`0xE000–0xE003`** window, **`E000=command/status`,
`E002=data`** (shared finding 13). Widening the window consumes resident code.
Consult controller documentation/implementation for exact parameter counts and
status semantics rather than treating this abbreviated table as a datasheet.
