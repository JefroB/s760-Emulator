# Milestone 2 interface checkpoint — 2026-10-11

Milestone 2 is complete for the qualified Windows development profile. Value/Output controls now pass the native and SoundCheck checks below. The recording-dependent Input Level requirement is retained explicitly in Milestone 3 alongside native ADC/input; it is disabled and not claimed implemented. Older sections record the earlier checkpoints and their then-open work.

## Native rack and keyboard

Native Studio now uses a rack chassis with the existing rack ears, the actual
MAME LCD canvas, thirteen firmware panel buttons and acknowledged sample-drive
status. Selecting a disk does not claim it is inserted. After reconnect/restore,
the drive label remains unknown until another insertion acknowledgment; it does
not infer mounted media from the selection box.

Keyboard bindings match the native driver: arrows, C Command, M Mode, Backspace
Exit, A/S/D F1/F2/F3, Z/X S1/S2 and left Shift. Repeats are suppressed; inputs,
selectors, focused buttons and confirmation dialogs retain their normal keyboard
behavior. Held keys release on blur/hidden document/unmount, even if focus changed.
The real native browser test opens the firmware Mode menu via the keyboard.

This is a live Native Studio rack. The historical App still has demonstration
state and requires further integration. The native alpha dial is not implemented:
the legacy Gotek encoder path is insufficient evidence for its hardware behavior.

## Concrete embedded editor backend

`core/src/s760_webview2_host.cpp` now creates a real WebView2 environment and child
controller. UI-thread callbacks use weak lifetime state; closing during creation
and repeated close/reopen are supported. Bounds follow editor resize. Packaged
file pages are mapped to a local HTTPS origin for ES modules and root-relative
assets. Top-level navigation is restricted to the initial document; new windows
are suppressed and incoming messages must originate from that document.

Creation returns acceptance of the asynchronous request. `is_created()` becomes
true only after successful navigation. Product-facing asynchronous error reporting
remains to be integrated with the plugin configuration UI.

Text/control messages use JSON strings. Frames use
`{type:"S760_FRAME",base64:"..."}` containing the unchanged six-byte header plus
pixel payload. The largest frame is bounded to the 640×480 RGBA surface. Frames
before page readiness are dropped; the normal UI frame pump supplies subsequent
frames. No unbounded startup queue is introduced. These operations belong on the
UI thread, never the audio callback.

The React provider detects `window.chrome.webview`, attaches exactly one listener,
uses the existing frame decoder, and removes the listener on disconnect/dispose.
Ordinary standalone mode retains its loopback WebSocket. The real backend harness
and React mock-channel tests establish matching contracts, not an end-to-end
native plugin/React/DAW acceptance result.

Build the optional backend with an extracted Microsoft.Web.WebView2 SDK:

```powershell
cmake -S core -B <build> -DS760_HAVE_WEBVIEW2=ON -DS760_WEBVIEW2_SDK=<sdk>
cmake --build <build> --config Release --target s760_webview2_tests -- /m:1
<build>/Release/s760_webview2_tests.exe <existing-scratch-directory>
```

The tested SDK is 1.0.3856.49, Windows x64, installed Evergreen runtime. The SDK
and generated binaries stay local. The default build still uses the explicitly
named portable stub; changing that default requires plugin acceptance.

## Validation

[Machine-readable evidence](condensed/validation/milestone-2-editor-2026-10-11.json)
records source and harness identities.

- 96 React tests in 18 files; TypeScript and production Vite build pass.
- 241 Python regressions pass.
- Core, plugin and portable editor C++ suites pass.
- Real MAME browser: boot, load ROBOFULL, save, reconnect, export, restart,
  restore and keyboard Mode-menu navigation pass.
- Real C++ WebView2: text/frame round trips, resize, canceled initialization and
  two close/reopen cycles pass. This uses a small diagnostic HTML page.
- BUG-019 (uncaught malformed session JSON) and BUG-020 (success-reporting empty
  WebView2 outline) are fixed, with their scope recorded in the backlog.

Remaining Milestone 2 work: verified dial behavior, full demo-shell replacement,
shared graphical configuration/startup recovery, and native plugin/React editor
lifetime with audio continuing in an actual host. No firmware behavior changed.
The sealed Milestone 1 distribution artifact was not modified; changed builds
need fresh distribution qualification.


## Configuration and automatic frame delivery follow-up

The reusable `RuntimeSettings` React component now has a standalone adapter.
Startup errors leave the local UI service running; the user can correct missing
firmware/media paths and start from the form. Validation precedes shutdown of a
live machine, dirty/busy media rejects replacement, and configuration requires an
explicit unsaved-memory confirmation. Version-1 settings are atomically saved
only after native startup and reused on subsequent launches. The existing saved
configuration survives failed startup. No firmware bytes are distributed.

Real browser acceptance starts with a missing ROM, recovers to Perform Play,
rejects an invalid replacement while the machine remains running, then relaunches
without firmware arguments and passes load/save/reconnect/restart/restore. The
standalone setup objective is complete for this source profile. Plugin adapter,
actual host startup-error UX and updated package qualification remain pending.

The concrete editor controller now schedules a roughly 15Hz UI-thread timer,
waits for page readiness and removes the timer before close. The real WebView2
harness observes multiple automatic CRT frames, no deliveries after close, and
successful resumption after reopen. BUG-021 is fixed. This diagnostic uses a
bridge without an engine; native-plugin audio continuity and UI/audio transport
contention were still unqualified at that checkpoint; see the native test below.

See [follow-up evidence](condensed/validation/milestone-2-settings-2026-10-11.json).


## Native editor and concurrent audio checkpoint (2026-10-11)

The real Windows WebView2 editor controller now closes and reopens built React
while the native plugin engine continues playing. Twelve-second paced runs with
varying block sizes at 44.1, 48 and 96 kHz retain the same MAME child, advancing
display timestamps, exact offline-reference PCM, silent note-off tails and zero
dropped frames or missed callback deadlines. Sampled React canvas pixels agree
with native CRT wire pixels before and after reopening.

Separate UI frame requests originally caused an audio underrun (BUG-022). The
audio worker now includes requested display snapshots with render replies; UI
reads use a separate cache during processing. No audio delay was added. Supported
C++ panel/pointer input now reaches the native host (BUG-023); a firmware Mode-menu
change is verified. Unsupported legacy click/dial and invalid controls reject.

This is the common concrete editor controller plus the direct native plugin
class, not exported SDK IPlugView hosting or DAW acceptance. The existing App
display is exercised; demonstration chrome and complete embedded control/error
UX remain unfinished. A 44.1 kHz run concurrent with a full C++ rebuild underruns;
the three passing qualifications ran after compilation finished. Sustained load
robustness, plugin configuration and actual host acceptance remain open.

[Commands, identities and results](condensed/validation/milestone-2-native-editor-2026-10-11.json).
The sealed Milestone 1 distribution has not been changed or requalified.


## SoundCheck SDK host checkpoint (2026-10-11)

The Windows x64 plugin now uses SDK-compatible interface vtable layout, GUID
encoding and component/processor IDs. Factory metadata, audio class category and
stereo/MIDI bus metadata are initialized, unsupported factory interfaces reject,
and stereo bus negotiation validates the requested layout. BUG-024 records why
previous tests compiled against the same local definitions missed this defect.
An independently SDK-compiled test failed on the original module's factory
metadata and now passes factory/component/audio/controller and bus queries.
Configure `S760_VST3_SDK_PATH` to a local SDK to build `s760_vst3_sdk_tests`; it
loads the module supplied as its sole argument and requires the native factory
environment variables documented in the existing plugin runbook.

SoundCheck 1.0.0's native backend loads the instrument, opens the concrete
WebView2 React editor on firmware Perform Play, captures its client image, closes
and reopens it, captures again and acknowledges removal. The test drives 3,500
individual 512-frame process requests, paced through WebSocket at 44.1 kHz.
The native machine has no loaded sample; silence and SoundCheck's silence-based
'dropout' flag are not audio acceptance. Its process-test handler also does not
check the processor return code, so metrics alone cannot prove successful
processing. Loaded-sample playback, host configuration/errors, multiple instances
and host project recall remain open.

The host was rebuilt in private scratch from the local SoundCheck source with
only its listen address changed to 127.0.0.1; the independent checkout is untouched.
It uses the locally available Steinberg SDK and BreakJob headers required by
that host version. No SDK or firmware files were copied into the project.
The corrected plugin class ID differs from the malformed historical encoding;
old experimental host project IDs are not migrated. Windows x64 is the tested ABI.
[Validation](condensed/validation/milestone-2-soundcheck-2026-10-11.json).


## Configurable media library and session recall complete

The approved rack layout is retained. Its Select dialog now configures recursive
media folders; selected and inserted paths are separate host-owned state.
SoundCheck verifies scanning, errors and uncommitted selection across reopening.
Native VST checkpoint version2 retains this metadata and restores into fresh
instances with relocated source files and exact PCM. Older states remain readable.
[Contract, limits and evidence](NATIVE_MEDIA_LIBRARY.md).

The media work left two objectives; the subsequent audio/configuration qualification below closes one. Verified native dial/rack input integration remains open.


## Loaded-sample SoundCheck audio and persistent configuration qualified

The actual native SDK host loads the concrete WebView2 instrument, boots original
OS 2.24, inserts ROBOFULL using Gotek Select, and executes Disk/Load through real
CRT pointer input. After Menu/Exit, absolute cursor translation now follows the
firmware's current position, bounds and 1x/2x sensitivity using read-only
observations and normal MU-1 input. No firmware bytes or state are forced.
BUG-025 and BUG-030 are closed for this tested input profile.

At 44.1 kHz with 512-frame callbacks, MIDI 60/velocity 127 plays the fixture at 20,004 Hz,
peak 0.0445375182 (native WAV reference peak 1459 PCM16). The editor closes and
reopens during the held note; all steady blocks remain audible and the release
tail is exactly zero. The approved rack arrangement is unchanged. This is
SoundCheck host acceptance for the fixture, not complete DSP hardware parity or
all-rate/all-workload host qualification.

[Persistent configuration](NATIVE_PLUGIN_CONFIGURATION.md) replaces mandatory
runtime environment variables with validated JSON paths and setup/check/diagnose
commands. The final host test uses a settings file, an unrelated CWD and no
runtime/UI environment overrides. Per-instance editor URLs follow that root
(BUG-032). Invalid JSON and missing firmware produce an actionable diagnostic;
repair and an independent SDK factory load succeed. Graphical in-plugin setup
remains the existing Milestone 4 objective; this is a command-line development
configuration workflow, not a packaged first-run UI.

At that checkpoint, native knob routing remained open; the qualification below supersedes that status.
[Qualification record](condensed/validation/milestone-2-audio-config-2026-10-11.json).

Separate reliability finding: two final native state-test runs failed cold
restoration, one reporting a disconnected/timed-out native connection. Four
subsequent diagnostic runs replayed 240000 stereo frames exactly at 48 kHz, including
pending/active notes, repeated recall, corrupt rejection and failed-write recovery.
BUG-033 remains open; these passes do not explain or erase the intermittent failure.


## Rack controls and Milestone 2 closure

The unchanged OS now consumes a native Value latch at F012. The React knob
changes Master Level127→124→127 in SoundCheck; independent native testing also
checks single steps, multi-step reversal and checkpoint recall of the edited
value and relative input position. Menu remains a separate physical switch.

Output Level reaches the native stereo signal. SoundCheck measured peaks
0.04453751817345619 at100%, 0.022268759086728096 at50%, and exactly0 at minimum.
The50% indicator survives actual editor close/reopen. Restoring full volume
recovers the expected20,004Hz fixture; note release is silent. Native checkpoint
replay at50% is byte-identical, and half-gain comparison has zero float error.
The approved layout remains unchanged apart from enabled controls/indicators.

The Input knob is an analog recording control, not another firmware encoder.
Its requirement is now grouped with the existing Milestone3 ADC/input dependency,
with an explicit unchecked objective. Nothing in this closure claims recording
support, measured physical potentiometer taper or complete IC20 equivalence.
BUG-033's intermittent cold restore remains open independently.

Regression totals:261 Python,111 React, six C++ suites, plus the actual native
runtime/bridge and SoundCheck acceptance. BUG-034/035/036/037 document the test
and implementation defects found during this work. The initial restricted Python
run failed/stalled on integration I/O and was stopped; the permitted full run
passed. Initial gain/readback and checkpoint/WAV assertion failures are retained.

See [rack controls](NATIVE_RACK_CONTROLS.md) and
[qualification record](condensed/validation/milestone-2-rack-controls-2026-10-11.json).
