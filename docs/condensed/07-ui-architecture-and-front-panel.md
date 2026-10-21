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

## Native popup reuse bounds in the private image browser

OS004B:62D4 refuses a popup backup when width*height exceeds0x026C (620 character cells), before saving or incrementing2144. A40x20 browser therefore has no saved parent surface. The private image browser fixes Exit by reading the parent screen from the native02DB stack and queueing native close/reopen/redraw; a separate mount flag suppresses parent reload during Disk Load handoff. Empty/loaded Perform restoration, stable repeated exits, preserved playback and a Disk Load before/after match of307200 RGB pixels qualify those parent cases, not arbitrary screens. Native field/highlight and CRT text/bitmap services remain reused; the keyboard is cleared within the browser. Footer/help, LCD and RC-100 browser behavior remain open.

On the tested selectable v9 X4/Y4 path at ordinary2x cursor sensitivity, relative trackball inputs reach an8-pixel grid. Private host targets between those positions can round into a one-row field's gap; targets on exact native text rows pass all15 pages and actual index99 selection for ISO and IMG. This diagnoses BUG-147 in the test coordinates, not a physical GB-6 defect or a sensitivity change. [Combined v9 native evidence](validation/bluescsi-im1-gb6-native-2026-10-19.json).

In the compact discovery/browser/SDS candidate, a genuine SDS receive header while the browser is open brings up the native Sample Dump Receiving modal. A collection click beneath it leaves the92-byte browser context,3400-byte listing and SCSI command stream unchanged while allocation cursor14/owner1 remain active. Receive cancellation cleans up to13/0; subsequent retry publishes14/0 with160 exact appended PCM bytes, preserving13 prior descriptors/119808 PCM bytes. This qualifies native receive-modal input exclusion only; the browser's direct2BBA guard is linked but its execution is not established by this case. Browser error presentation, general operation ownership and incoming MIDI during masked SCSI transfers remain open. BUG149 corrects the private test expectation that a browser callback would run beneath the modal. [Discovery/fit evidence](validation/bluescsi-im1-discovery-fit-2026-10-19.json).


The paced cancellation successor adds owned32-byte collection status text: Cancelled, SCSI error and Mount uncertain; select again. Native screenshots show these messages within the blue browser. A physical Exit press during D7 drains4000 wire bytes and returns to collections without D8. A held press after D8 starts is accepted14.84675ms later, queues no follow-on command/Load and shows uncertainty; fresh explicit selection then loads119808 exact bytes and plays. No rollback is claimed. BUG150 fixes disabled operation cancellation; BUG151 replaces an invalid0.821375ms test pulse with a held physical press. Four readiness probes have20ms timer/poll-bounded pacing; this does not establish physical readiness or IRQ latency. Full footer/help/identity and richer error policy remain open. [Evidence](validation/bluescsi-im1-cancel-recovery-2026-10-19.json).


The conditional-IRQ successor qualifies a real incoming SDS header during browser listing and during D8/readiness. Native receive claims cursor1/owner1 inside service. Listing now drains4000 bytes then returns to collections with Busy; native modal input blocks image clicks, and receive CANCEL rolls back to0/0. After D8, a late owner check records error11/uncertainty, leaves the native selected drive unchanged and queues no Load. Only cleanup plus explicit fresh selection permits native Load of13 samples/119808 exact bytes with playback. This fixes BUG153; BUG154 excludes native service time from the idle watchdog while retaining total deadlines. The messages/ownership are qualified on CRT/GB6, not the remaining LCD/RC100/full identity/footer matrix. [Results](../project/bluescsi-im1-irq-ownership-results-2026-10-19.md).

The next compact-catalog candidate retains the D7 mount index and all32 filename bytes in33 bytes, discarding the constant file-type byte on the directory-free stock CD picker. Wire input remains40 bytes/record. Moving3300-byte storage to physical4BE0 gives7776/8002 named bytes,226 free and98 contiguous after2814-byte code; mandatory v9 GB-6 and retained SDS helpers remain included. Six native workflows pass: exact0/1/100 records and101 rejection, cancellation/retry/exact Load/playback/SDS, failed mount recovery, incoming SDS during list/mount and128 MIDI clocks during D7. Exact rebuild and immutable originals pass. Full admission/UI/fit/stack/media/controller/hardware gates remain open;1FA4 is a Remote Mode session flag, not generic disk ownership. [Results](../project/bluescsi-im1-catalog33-results-2026-10-19.md), [validation](validation/bluescsi-im1-catalog33-2026-10-19.json).

Seven native workflows on the unchanged7776/8002 compact candidate qualify remote/local sender cancellation, a local no-click control, complete116-packet sends with9216 exact allocation bytes each and96 zero encoded padding bytes, and outgoing requests during D7/mount-readiness. Remote owner7 blocks browser commands; local owner8 cancels on input while the control remains active. Requests trigger late Busy without drive/Load commit; explicit cleanup restores browsing. No new firmware bytes;226 free/98 code-adjacent remain. This qualifies scoped sender paths, not concurrent native Load/Save/Format, the manufacturer41 session caller, full ISR/stack or physical timing. [Results](../project/bluescsi-im1-sender-admission-results-2026-10-19.md), [validation](validation/bluescsi-im1-sender-admission-2026-10-19.json).

BUG155 is reproduced on the prior browser: manufacturer41 Remote Mode1FA4 becomes pending while SDS2BBA stays0, yet D8 readiness commits native drive1/handoff7601. A specific shared1FA4 check at entry/catalog/mount adds10 bytes and refuses publication/Load with Busy, retaining drive8 and handoff0; both paired race tests recover after session exit. Eleven primary native cases pass:2 races,5 Remote Mode cases and4 browser regressions. Complete116-packet/9216-byte send and160-byte receive publication are exact. Complete/cancel/timeout restore40 scratch words/selectors/WSR at the caller. Deferred exit first differs in3 scratch words at the later continuation; a twelfth native run confirms isolated helper restoration and a matching continuation. Original differing rows remain; broad ISR/caller proof stays open. Mandatory GB6-v9 remains at7786/8002,216 free/88 code-adjacent; exact rebuild passes. General disk/external-session safety, full fit/stack/UI/media/controller/hardware gates remain open. [Results](../project/bluescsi-im1-session-admission-results-2026-10-19.md), [validation](validation/bluescsi-im1-session-admission-2026-10-19.json).

Native Disk options preserves all9 stock actions via0196:94D9 instead of a second menu clone (BUG156). Eight native screens and corrected Volume Dump FD warning/cancel are observed; BUG157 fixes its initial OS-Load mislabel. Browser ISO index99 -> separate private10MiB HD0 initialization/Save/export -> fresh cold Load preserves13 allocations/119808 exact bytes and playback peak. New32-byte records validate every D7 index as its ordinal before implicit storage;25700 decoded cases and native0/1/100/101/index99/cancel/SDS/Remote Mode checks pass. Current7918/8002 has84 free/68 code-adjacent, mandatory GB6-v9 and exact rebuild retained. Full persistence uses the preceding label variant; final labels change only the text table and one immediate pointer, with warning/cancel and rebuild acceptance. Malformed-index native draining, concurrent operations, full UI/fit/controller/media/stack/hardware gates remain open. [Results](../project/bluescsi-im1-disk-operations-results-2026-10-19.md), [validation](validation/bluescsi-im1-disk-operations-2026-10-19.json).

Visible-page catalog storage reclaims2936 net bytes in the same candidate:3200 ->224 data bytes for40 added code bytes. The full D7 stream and all indices are still validated, retaining seven32-byte names; Next/Previous reread DA/D7. Current4982/8002 leaves3020 free,3004 directly after code. Nine native workflows on the same hash cover all100 names forward/back, shrink clamp, failed refresh/no stale mount, boundaries, exact Load/SDS/cancel/recovery, HDD Save/export/cold Load, Remote Mode and128-clock/SDS-during-Next IRQ service. Index/window models cover25700/10000 cases; exact rebuild and originals pass. Catalog rereads measure median349.998ms from DA-end to D7-end, not physical latency. Scoped extra stack reaches194, not a full bound. Remaining UI/policy/controllers/media/concurrency/stack/hardware and full feature fit remain open; another RAM region is deferred. [Results](../project/bluescsi-im1-page-window-results-2026-10-19.md), [validation](validation/bluescsi-im1-page-window-2026-10-19.json).


## IM1 browser footer ownership — 2026-10-19

The browser now clears inherited parent softkey labels and uses its existing Image Library string as native descriptor identity, with no allocation growth (4982/8002 bytes). Two exact-hash native workflows qualify catalog boundaries, failed-page recovery and explicit retry; Exit visually restores the native keyboard/footer. Dedicated help, other controllers/LCD and physical acceptance remain open. [Validation](validation/bluescsi-im1-owned-footer-2026-10-19.json) records the three-byte change and build identity. Finding280.


## IM1 contextual CRT help and identity — 2026-10-19

The final browser candidate adds collection/target titles and bottom-row instructions without hiding any of the32 filename bytes. Init renders dynamic rows before drawing, fixing BUG-159 (invisible cold-entry Disk options). Two native workflows qualify all4 collection identities, paging, Disk options, Exit/reopen, exact119808-byte Load/playback and retained SDS cancellation/retry. Allocation5393/8002,2609 free/2121 code-adjacent; remaining LCD/controller/parent, Save System cold-state, concurrency/reset/stack and physical gates remain open. Earlier broad matrices retain their earlier-hash scope. [Validation](validation/bluescsi-im1-help-identity-2026-10-19.json). Finding282.


## IM1 fresh-entry and Save System cold-start update - 2026-10-19

BUG-160 is fixed by clearing76 operation bytes on every browser entry, preserving16 callback-save bytes. A native stale-catalog baseline fails as expected; fresh reentry and actual Save System export/new-process cold boot rebuild Collections before commands. Saved stale page/labels remain on disk but cannot be selected; explicit new catalog/index0 Load restores119808 exact bytes with playback/release. Final-hash cancellation/SDS and rebuild pass. Footprint5408/8002,2594 free/2106 code-adjacent supersedes earlier values above. External checkpoint/device reset reconciliation, live collection mutation, controller/LCD, full stack and physical gates remain open. [Validation](validation/bluescsi-im1-entry-state-2026-10-19.json). Finding283.


## IM1 Mouse+CRT qualification — 2026-10-19

Current firmware32143f10... passes all4 collection identities/paging/help/Disk options/Exit/fresh reopen and exact119808-byte Load/playback/cancellation/SDS in native mode1 with genuinely saved NVRAM. Firmware remains5408/8002,2594 free. Mode0 stock Mode->Disk LoadF7 and Command are separately observed; native LCD F5/F7 descriptor neighborhoods remain original. CRT browserF4 does not qualify the separate LCD layout; dedicated LCD UI and RC100 packet input remain open, along with other parent/concurrency/reset/stack/hardware gates. [Validation](validation/bluescsi-im1-controllers-2026-10-19.json). Finding284.


## IM1 LCD feasibility prototype — 2026-10-19

A separate LCD F5 resource/renderer shares the existing protocol/admission callbacks. Triale798c0bf... passes mode0 seven-row scrolling over a100-image ISO catalog, Next/reopen, index0 mount to nativeF7,119808 exact loaded bytes and playback/release. Same-hash GB-6 CRT cancellation/Load/SDS regression and rebuild pass. Trial6141/8002,1861 free/1611 code-adjacent; broader CRT baseline32143f10... remains separate. LCD shows21 name bytes: full32-byte identity/viewing, complete paging/IMG/Disk/error/cancellation/cold-state and RC100/stack/hardware gates remain open. BUG161 removes a trial-only diagnostic/scroll alias. [Validation](validation/bluescsi-im1-lcd-prototype-2026-10-19.json). Finding285.


## IM1 LCD full-name confirmation — 2026-10-19

Candidateefec015f... displays the32 returned ASCII filename bytes in two16-byte lines before explicit Mount + Load, with Back and a separate CD identity row. Native shared21-byte-prefix fixtures, Back/preview/held-key noD8, index1 exact119808-byte Load/playback and same-hash CRT cancellation/SDS pass.256 decoded byte-filter cases and rebuild pass; BUG162/163 are fixed. Trial6487/8002,1515 free/1297 code-adjacent. This does not expose names beyond D7's32-byte field or lock external directory changes; final-hash LCD paging/IMG/Disk/error/cancellation/cold state, broader controllers/reset/stack and hardware remain open. [Validation](validation/bluescsi-im1-lcd-names-2026-10-19.json). Finding286.


### BlueSCSI LCD paging boundary — 2026-10-20

Native candidate19448d85... verifies all100 full32-byte catalog names across15 pages forward/back and Collections without mounting. BUG164: disabled Next formerly reset scroll without redraw, making immediate Previous ineffective; moving reset into render fixes the native negative case without growth. Same-hash name confirmation/exact119808-byte Load/playback, CRT cancellation/SDS and exact rebuild pass. Footprint6487/8002,1515 free/1297 code-adjacent. Remaining LCD/RC100/ownership/reset/stack/hardware gates stay open; no full IM1 GO. [Validation](validation/bluescsi-im1-lcd-paging-2026-10-20.json).


### BlueSCSI LCD collections and IMG — 2026-10-20

Unchanged19448d85... passes all4 configured LCD collection identities/preview Back/Collections/fresh reopen and target2 IMG index1 native Load13 allocations/119808 exact bytes/playback. Named10MiB Roland512-sector HD2 fixture only; no arbitrary IMG/hardware claim. Separate LCD Disk options verifies9 labels/scroll/Exit/reopen/native Load routing; other8 operations/writeback remain execution-unqualified.6487/8002,1515 free. LCD errors/cancellation/cold-state, RC100, ownership/reset/stack/hardware/full-fit gates stay open. [Validation](validation/bluescsi-im1-lcd-collections-img-2026-10-20.json).


### BlueSCSI LCD recovery — 2026-10-20

Unchanged19448d85... passes native LCD ordinary-target refusal/error9 and modeled D8 GOOD/open-failure bounded4 TUR/sense pairs, with no handoff/allocations. Physical Exit D7 drains4000 bytes then cancels; D8 interruption has no follow-on/native Load and explicitly reports uncertainty. Independent-target error recovery and fresh explicit cancellation retry each Load119808 exact sample bytes/13 allocations and pass playback/release. LCD renderer reads confirm status messages. No rollback or physical-failure parity claim.6487/8002,1515 free. LCD Save System/cold-state, native operations, RC100 and broader ownership/reset/stack/hardware/full-fit gates stay open. [Validation](validation/bluescsi-im1-lcd-recovery-2026-10-20.json).


### BlueSCSI LCD Save System cold boot — 2026-10-20

Unchanged19448d85... executes LCD native Save System/blank-floppy format/S2 Yes/export. Saved1474560-byte image74bbfa28... preserves3951 browser code bytes,212-byte LCD descriptor, SDS spans and mandatory GB-6 v9 checks. Fresh-process cold boot clears all76 operation-context bytes, issues no image command before collection choice, and explicitly loads ISO index1/13 allocations/119808 exact bytes with playback/release. Native emulator scope; no external checkpoint synchronization, interrupted save/format or physical media claim.6487/8002,1515 free. Remaining Disk operations, RC100, ownership/reset/stack/hardware/full-fit gates stay open. [Validation](validation/bluescsi-im1-lcd-cold-system-2026-10-20.json).


### BlueSCSI current-build HDD persistence and RC-100 scope — 2026-10-20

Unchanged19448d85... passes native GB6 browser ISO index99 Load, Disk options Utility/private HD0 quick initialization, Save/export and fresh-process HDD Load.13 sample allocations/119808 bytes match expectedB exactly before/after export; playback/release passes. All observed RAM snapshots retain browser/SDS code; original media unchanged. Named10MiB512-sector native profile only, no physical/arbitrary geometry/interruption/concurrency claim. User waived RC-100 input testing as an IM1 gate: its untouched implementation is assumed compatible, no controller available; this is not verified protocol compatibility and supersedes earlier RC100 release-blocking wording.6487/8002,1515 free. Remaining native operations/parent/ownership/reset/checkpoint/stack/hardware/full-fit gates stay open. [Validation](validation/bluescsi-im1-hdd-save-current-2026-10-20.json).


## IM1 multi-gate batch and nested-mode defect — 2026-10-20

Unchanged19448d85... candidate passes browser-mounted native Akai Convert Load with30 samples/13,568,196 exact converted PCM bytes,15 distinct L/R pairs and stereo playback/release; same-process checkpoint stale-load refusal and explicit119808-byte image reselection; and current Mouse+CRT D7/D8 cancellation/Load/SDS160-byte retry. A26-cycle/13-screen GB-6 matrix preserves screen IDs, browser/SDS code and loaded PCM with final playback, but full parent acceptance is OPEN: matched original/current Mouse evidence proves BUG-165. Native System mode ancestor8120 survives original depth3→4→3; browser Exit collapses it to depth2/page0121 and highlights Perform. Native Mode selection is a workaround. Private Volume Dump FD initialization/export reaches an empty4-slot directory; populated save/reload remains unqualified. No firmware growth:6487/8002,1515 free/1297 contiguous. Stack/resource lifetime, general concurrency, broader media/reset/cold recall and physical qualification remain open; RC100 stays assumed under the user waiver. [Results](../project/bluescsi-im1-multi-gates-results-2026-10-20.md), [validation](validation/bluescsi-im1-multi-gates-2026-10-20.json).


## IM1 native Exit ancestry repair (2026-10-20)

BUG-165 supersedes the earlier extra-close/reopen Exit repair. Native event02 reaches recursive0000:D383, which can consume a mode2 ancestor. The browser now queues event0B after ordinary popup close:0000:D297/DA9A refreshes the restored mode0 screen using a single pop/reopen. Mouse System retains depth3 and ancestor8120 with the correct System highlight;26 GB-6 cycles across13 screens preserve every active stack entry, code, PCM and playback. Native handoff still suppresses parent redraw. The change saves35 bytes; current6297274d... totals6452/8002. Full32-byte LCD identity/shared-prefix confirmation, Back/held-key no-mount, all4 collections/IMG and bounded error recovery also pass. RC100 remains assumed under the user waiver. The unused full-screen descriptor alternative is not required by this popup design. [Results](../project/bluescsi-im1-closeout-results-2026-10-20.md), [validation](validation/bluescsi-im1-closeout-2026-10-20.json).

The same OS now qualifies native Save on browser-selected writable HD2 IMG, verified CD2 reselection and cold Load/playback. Existing Disk menus also complete Copy overwrite Yes/No and Optimize with both native options; no menu or ROM growth was required. Optimize's options are alphabetical sorting and time-indication correction. Volume Dump FD uses F1 Save and F3 Load; the later matching-source case completes cold restoration as recorded below. These passes use physical panel/pointer input with observed cursor placement; an earlier missed-row reselect attempt is excluded. [Current compatibility evidence](../project/bluescsi-im1-final-gates-results-2026-10-20.md).


### Current IM1 LCD persistence and operation exclusion (2026-10-20)

Unchanged6297274d... on7c994e86... independently passes all100 full32-byte LCD filenames over15 pages forward/back, disabled Next/immediate Previous and Collections with no mount. Native LCD Save System export9a895c66... preserves browser/LCD/SDS/GB-6 v9; fresh boot clears76 operation bytes, issues no Toolbox command before explicit collection selection and loads119808 exact bytes with playback. This supersedes predecessor-only evidence for those named LCD cases.

During native mounted-IMG Save, a verified Mouse+CRT Disk-header click plus Mode overlaps WRITE(10) commands and issues no Toolbox command; saved PCM remains exact. The owner word083BBA is zero, so the observed protection is native UI serialization rather than a universal busy-word interlock. Native Volume Dump matching-source restore and current mounted-IMG Delete also pass. Other operation/interrupt ownership classes remain open. [Results](../project/bluescsi-im1-safety-batch-results-2026-10-20.md), [validation](validation/bluescsi-im1-safety-batch-2026-10-20.json).


### IM1 timing and partial-command recovery

Established6297274d... blocks the tested browser/Mode attempts during native Load and Mode during quick Initialize, Copy and Delete; each overlaps native I/O, admits no Toolbox command and preserves the expected media result. This extends the earlier Save exclusion; it does not cover every FDC/conversion/full-format state.

Experimental367f067d... retains GB-6 v9 and passes CRT cancellation/retry/SDS, incoming SDS during listing/mounting, LCD cancellation/error recovery and Remote Mode during listing/mounting. The dense-MIDI case parses775 bytes exactly and releases to silence with maximum28.006625ms observed service; no whole timer wraps are lost in that run. Trial remains unpromoted pending full timing/native stack and remaining compatibility evidence. Boot ROM is unchanged; RC100 input compatibility remains assumed under the user's waiver. [Results](../project/bluescsi-im1-timing-recovery-results-2026-10-20.md), [validation](validation/bluescsi-im1-timing-recovery-2026-10-20.json).


### Native disk warning resource correction (2026-10-20)

BUG172 repairs the inherited incomplete warning in both CRT and LCD variants:
"All existing data on this Disk will be lost." Dynamic disk-label token01 85
is retained. Sound Data and generic disk warning resources begin at OS file
0xC162C/0xC168F and0xC196C/0xC19CA (CRT/LCD pairs). Reflow preserves each original
extent, changes170 bytes per OS and requires no relocation or extra space.
The guarded scripts/patch_disk_warning_text.py is incorporated into both combined
builders, producing ecdbd721... (established) and79124692... (timing trial).
GB-6 v9, SDS and browser code remain byte-identical to their predecessors.

Native CRT Save and LCD Format display/No cases pass on both successors. LCD
No is front-panel F3 and returns to Utility; exported media remains unchanged.
CRT No also preserves media. Loaded resource bytes and both rendered displays
are checked. No additional boot-ROM change is needed. The timing trial remains
unpromoted; this cosmetic repair does not close its timing/ownership gates.
[Results](../project/bluescsi-im1-format-fdc-stack-results-2026-10-20.md) and
[validation](validation/bluescsi-im1-format-fdc-stack-2026-10-20.json).
