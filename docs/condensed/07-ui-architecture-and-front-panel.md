# UI Architecture & Front Panel

## Current status — 2026-10-11 review

Native MAME supplies real CRT/LCD frames and firmware controls to the standalone and concrete WebView2 plugin editor. SoundCheck qualifies firmware sample loading and audio during editor operation/reopening. Persistent plugin paths and startup diagnostics are available; in-plugin graphical recovery remains Milestone 4 work. Value and Output controls complete Milestone 2 playback/UI integration; Input Level remains explicitly deferred to Milestone 3 native recording. The current qualification does not establish analog pot taper or full IC20 quadrature behavior. Earlier scaffold descriptions below are historical architecture context.

See the [completion roadmap](../project/completion-roadmap.md) and [native runbook](11-native-boot-and-audio-runbook.md).

## Technical reference and dated milestone history

Milestone labels below apply to their cited finding, not to the present project status.


Input checkpoint: finding59. Native F008 now supplies the four-nibble
mouse movement packet and active-low buttons. A ROM-boot integration test
verifies firmware coordinate changes in both directions and left-button press/
release. The launcher enables host mouse input. Hardware cursor rendering,
encoder, RC-100 and complete IC20 behavior remain unfinished.


At that checkpoint: finding58. The experimental IC15 ROM boot now loads all112 OS tracks
and reaches interactive Perform Play. Correct OP-760 identification and live VDP
pointer readback remove the video blockers. New native EEPROM profiles default
to Mouse+CRT at the user's request; existing profiles retain their setting.
Native LCD writes and its screen surface are restored. Rendering, hardware cursor,
complete chip behavior and power-on bank defaults still need work.


At that checkpoint: finding56 connects the
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
routes the main interface to the CRT; the LCD still shows the firmware logo, version,
controller mode and "Please see your CRT" status (owner observation and native bus
replay, finding151). Blank LCD output was a controller emulation defect. The
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

[front-panel-button-mapping.md](../hardware/front-panel-button-mapping.md) remains the
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


## Native interface checkpoint (2026-10-11)

Native Studio now renders a rack with authentic LCD frames, native panel buttons
and acknowledgment-based drive status. Panel keyboard bindings match the driver;
text inputs/dialogs suppress shortcuts and held keys release on blur. Real MAME
browser acceptance includes keyboard Mode-menu navigation, load, reconnect and
session restore. Full historical demo-shell integration and native dial semantics
remain unfinished.

The optional Windows C++ WebView2 backend is now concrete: environment/controller,
resize, bounded text/frame channel, cancellation and reopen pass against the real
runtime. React supports that channel through its existing frame decoder. Native plugin/React controller lifetime is now qualified below; actual
DAW hosting and plugin configuration remain unqualified. See the
[checkpoint and limits](../testing/milestone-2-progress.md) and
[validation](validation/milestone-2-editor-2026-10-11.json).


The reusable runtime settings form is now connected to standalone startup,
including missing-firmware recovery, pre-shutdown validation, explicit memory
replacement confirmation, dirty/busy media protection and persisted settings.
Real MAME boot after GUI correction and relaunch using those settings pass.
The concrete embedded editor also schedules frames on a UI-thread timer and
cleans it up on close; automatic delivery/reopen pass with a diagnostic bridge.
Plugin configuration, actual DAW-host audio continuity and updated packaged acceptance
remain open. See [settings evidence](validation/milestone-2-settings-2026-10-11.json).


Native editor-controller close/reopen with built React and concurrent native PCM
passes at 44.1/48/96 kHz, using worker-delivered display snapshots to avoid UI
frame-request starvation. Sampled CRT canvas agreement, fresh cache timestamps
and an unchanged MAME child are asserted. C++ panel/pointer routing now applies
to the live host; unsupported legacy click/dial rejects. These are native harness
results, not SDK/DAW acceptance or complete demo-shell replacement. Concurrent
compilation still exposed an underrun; arbitrary system-load robustness remains
unqualified. See [evidence](validation/milestone-2-native-editor-2026-10-11.json).


SoundCheck 1.0.0 now discovers the Windows x64 native instrument and hosts the
concrete React/WebView2 editor: firmware Perform Play capture, close/reopen and
plugin removal pass. Independent Steinberg-SDK interface tests exposed and
verified corrections to local vtables, GUIDs and metadata. This advances actual
host editor acceptance. Loaded-sample SoundCheck audio and persistent configuration
with actionable diagnostics now also pass; in-plugin graphical recovery remains open. See [host evidence](../testing/milestone-2-progress.md).


### Verified embedded rack arrangement (2026-10-11)

The manual and owner's photograph confirm the navigation grid: S1/Dec, Up,
S2/Inc above Left, Down, Right. There are only two S buttons. F1–F6 appear
beneath the LCD; F4–F6 and Home/Mark/Jump each send their actual Shift chord.
See [the corrected manual mapping](../hardware/front-panel-button-mapping.md).
Input and output levels are separate knobs, and Value has a separate Menu
button. Value and Output are enabled and qualified; Input remains disabled pending native recording. Menu drives SC0/SP4 and opens the native
firmware menu. The OS 2.24 pointer adapter now accounts for firmware cursor
relocation and sensitivity using read-only feedback and normal MU-1 deltas;
Menu/Exit, reversal and paused-render tests close BUG-030.
The Gotek's own encoder and Up/Down buttons browse the host-owned inventory;
Select opens the image dialog, prefilled with the selected path, for confirmed native insertion. Confirmed insertion and browsing selection
are separate. The existing Select dialog configures recursive folders (up to1024 images,
with explicit scan bounds and transactional errors). Independent browse selection
and inserted identity survive editor recreation and native plugin-state recall.
Version2 metadata restores alongside checkpoint bytes, without remounting a source
file. Cold replay with relocated sources matches PCM exactly. See the
[media library contract and qualification](../emulator/guides/native-media-library.md).

SoundCheck screenshots show the whole rack at 1480x900, an active CRT without
unused bottom rows, and firmware LCD status in Mouse+CRT mode. Original LCD
bus replay and native pixels agree exactly for the boot status screen. These
results do not establish all-mode LCD hardware parity. Separate loaded-sample
SoundCheck acceptance now passes. BUG-026/027/028/029 are fixed for the delivered playback rack; recording Input Level is a separate Milestone 3 requirement.

SoundCheck audio qualification uses ROBOFULL through actual React Disk/Load,
MIDI 60/velocity 127, 44.1 kHz/512-frame callbacks and editor reopening while held.
The fixed-frequency fixture gives 20,004 Hz and 0.0445375 peak, with no silent
steady blocks and zero release tail. Settings-only startup and failure recovery
pass from an unrelated host working directory. See [configuration contract](../emulator/guides/native-plugin-configuration.md)
and [validation](validation/milestone-2-audio-config-2026-10-11.json).


The Value knob uses native IC20 F012, consumed and cleared by OS2.24
bank003B:452D–45A9 (image01392D). Flag1 qualifies direction bit0; native values2/3
produce increasing/decreasing edits. Conservative20ms detent pacing is a host
input policy, not measured ASIC timing. The runtime stores the relative position
and MAME stores the latch/pacing state; native recall and reversal are verified.
Output Level is analog VR1 attenuation according to Service Notes p20, outside
firmware parameter editing. The native stereo implementation supplies linear
software gain: exact half amplitude at50%, silence at0%, with UI readback and
same-build recall. Input Level precedes analog conversion and awaits native ADC.
See the [control contract](../emulator/guides/native-rack-controls.md) and
[validation](validation/milestone-2-rack-controls-2026-10-11.json) for scope and limits.


### OS2.24 callback slots and event ring (static)

[Resident UI event decoding](../firmware/os/os-ui-event-dispatch.md) connects000F:2080 to0000:F468 through a128-byte ring21B0..222F with modulo128 cursors21AC/21AE. Producer tag1 carries two bytes; tags3/0A/0E/0F/10 carry one. The consumer drains using a local cursor and resets both stored cursors on exhaustion; special exits and concurrency remain unvalidated.

The screen loader's ten four-byte callback pairs at2174..219B are target-first/page-second. DD1C/DD77/DDB2/DE00 consume slots0..3. The guardedEA42..EA60 path accepts events17..1C and invokes slots4..9 throughF0C1. Each selects fetch0104 from the pair and data010C=0299; return continuations restore data010C but do not locally restore fetch0104. Startup descriptor0130 initializes all ten to0171:8000, whose sole decoded instruction is RET; mutable descriptor targets remain open. [Byte evidence](validation/os-ui-event-ring-2026-10-16.json) preserves conditional wrapper sites and new anchors. No native or hardware UI parity is claimed.


### Fixed screen callbacks and transfer status rows

[Static selection analysis](../firmware/os/os-ui-selection-callbacks.md) follows initial screen011E/011F through five type2 fields and cached callbacks0196:9960/9AC7 and0171:8172/818F. Update handlers use mutable next-screen tables02DB:48AA/48B6; their bounds remain unresolved. Numeric metadata provides separate display/edit function pointers and two sign-extended words whose limit semantics remain provisional. [Byte evidence](validation/os-fixed-screen-callbacks-2026-10-16.json) preserves all newly decoded anchors and initial descriptors.

005A:747E/746E implement temporary CRT row2/LCD row7 status overlays with countdown4000/2000 (units unresolved), saving40/25 character-attribute pairs and restoring onindex0 when marker0D is present. Supervisor results2/3/4/5 select Illegal Sample #, Memory Full, Dump Adrs Error !, Dump Data Error !. Only four consumer-bounded messages are classified; no full table/runtime acceptance claim follows.


### Concrete numeric limits and object startup

[Numeric/device continuation](../firmware/os/os-device-probe-and-numeric-fields.md) follows initial011E index2 via02DB:48AA toscreen012F. Its first six type3 tuples resolve metadata5CE4/5CEC/5CF4/5D40/5BBC/5D48, with signed bounds-1..15,0..1,0..1,0..31,0..1,0..4.01EC:81BD compares signed32-bit upper thenlower limits and marks saturation; postprocesscallee preservation and ordinary editing acceptance remain open. Initialtarget annotations retain unknown edges for otherinvocations. [Byte evidence](validation/os-device-probe-and-numeric-2026-10-16.json) records the path and sixmetadatarecords.

004B:730A expands361E/3620 andcopies3618 intodata0299 fields8100..8115.7362/73D3/7423 copy128/256-byte objecttemplates todata0356 stagingrecords. These are runtimecopies,withoutnew immutable-resourceextents.0196:88B4 qualifies mode1 geometry/outside state22A8 andevent2 enqueueing on outside scroll events;nativepointerparity remainsopen.


[Full-field/postprocess decoding](../firmware/os/os-postprocess-and-full-fields.md) extends initial012F to40 records and238 tuple bytes. Dynamic editor81E2 overrides loaded bounds; metadata5D96 indexes a byte array through23A8.01D1 propagation switches source/destination data banks explicitly and preserves the numeric value under bounded object-offset assumptions. Native editing remains open. [Evidence](validation/os-postprocess-full-fields-2026-10-16.json) retains those limits.
