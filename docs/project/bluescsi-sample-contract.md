# BlueSCSI native sample contract

**2026-10-18 — BS1 metadata, permanent assignment, SDS bounds and proposed stereo transaction; gate open.**

The stock OS now has qualified rate/loop/address references and an ordinary
workflow for permanent stereo assignment, naming, Save and cold Load. These
establish the importer's required native result; WAV import and programmatic
object construction remain unimplemented.
[Roadmap](bluescsi-files-roadmap.md),
[native and byte evidence](../condensed/validation/bluescsi-sample-contract-2026-10-18.json).

## Permanent playable hierarchy and persistence

Two fresh stock-OS processes qualify one 44.1 kHz OneShot stereo pair through
Partial SMT, Patch Split, Perform Play, naming, Performance Save and cold
Performance Load. The original operating manual agrees with stereo search,
automatic L32/R32 pan, the 88-key map and the requirement to name sounds before
Disk operations (PDF pages 48/50/40/141; identity retained in the validation).
[Assignment and persistence evidence](../condensed/validation/bluescsi-permanent-assignment-2026-10-18.json).

| Native record in this run | Observed permanent relationship |
| --- | --- |
| Partial 0, physical `CA800`, 128 bytes | Words `+10/+20` reference public samples 0/1; bytes `+14/+24` are `E0/20` (L32/R32). Components 3/4 retain `FFFF` sample references. |
| Patch 0, physical `C2800`, 256 bytes | `+20..+77` contains 88 zero bytes, assigning MIDI keys 21..108 to partial 0. Native Set also writes zero to `+80..+D7`; those bytes' semantics remain unqualified. |
| Performance 0, physical `BE800`, 256 bytes | Byte `+10` selects patch 0 for the first part. The other 31 patch-reference bytes retain `FF`. |
| Each object's 16-byte name | Naming changes the initial `7F` marker to space (`20`) and commits `   :bs1perf` padded with spaces. All other native defaults are retained. |

These are observed locations for the loaded slots, not addresses for an
importer to hardcode. The manual workflow edits already initialized native
records. The field list is not a complete initializer for unused memory.
Unassigned defaults, current selections, derived state and native services
still require a construction contract.

The unnamed hierarchy can audition, but that alone does not make it eligible
for Save. Naming all three objects produces a disk containing one performance,
one patch, one partial and two samples. In this disk, patch/partial records
equal their RAM records exactly; performance byte `+03` changes from `3A` in
RAM to `80` on disk, and sample addresses/allocation bases are serialized.
Cold Load reconstructs all **736 bytes** of the five records exactly. The
239,616 combined PCM allocation bytes also match the original sample fixture
and both native wave dumps. This compares sample allocations, not whole wave RAM.

The first cold Perform Play audition succeeds while reserved preview partial
255 still has four `FFFF` references. Permanent playback therefore does not
depend on entering Loop/Smoothing or constructing preview slots 512/513.
Seven audio cases preserve distinct channels at a common source-frame position,
with maximum relative RMS fit error `4.016e-8` and silent final release seconds.
Only this 56,719-frame-per-channel pair, at root key 60, is qualified here.

Read-only taps retain 238 CPU stores with no dropped rows; replaying their
masked writes reconstructs each captured record exactly across 20 snapshots.
Five cold snapshots preserve the resulting hierarchy. Eleven byte-checked
store instructions identify construction points:

- `01EC:9B2F`: selected sample reference.
- `01D1:9A2D/9A33/9A3C/9A45/9A4B/9A54`: paired component references,
  routing and copied component bytes.
- `01D1:86B1/86B4`: 88 key-map entries and 88 associated zero writes.
- `01FA:97E4`: performance part's patch reference.
- `0196:8459`: the 16-byte name copy for each object.

These are observed stores inside routines, **not callable entry points or
complete ABI contracts**. They support tracing the eventual construction path;
they do not qualify a direct-call importer or transactional publication.

## Descriptor fields and rate codes

An ordinary sample descriptor is 48 bytes. The five little-endian 32-bit values
are fixed-point wave addresses with eight fractional bits. Their native screen
labels, established by a fixture with distinct values, are:

| Offset | Native meaning | Explicit fixture value, words |
| --- | --- | ---: |
| `+10` | Start | 5 |
| `+14` | Loop start | 17 |
| `+18` | Loop end | 3000 |
| `+1C` | Release-loop start (`R.Loop`) | 3500 |
| `+20` | Release-loop end | 4000 |
| `+24` | Loop mode | 0 Forward; 2 OneShot |
| `+28/+2A` | Allocation start/count, 16-bit words | Blocks of `0x1200` wave words |
| `+2C` | Sample-rate code | Table below |
| `+2D` | Root key | 60 in this fixture, displayed C-4 |

The on-disk points in this one-block fixture become native wave addresses by
adding `8 + 4608 * loaded_block` words. The observed base of eight words belongs
to this load; use the native allocation base rather than hardcoding it.

| Rate, Hz | Code | Measured preview tone, Hz | Expected tone, Hz |
| ---: | ---: | ---: | ---: |
| 48000 | 0 | 468.7801 | 468.7500 |
| 44100 | 1 | 430.7772 | 430.6641 |
| 24000 | 2 | 234.4942 | 234.3750 |
| 22050 | 3 | 215.3889 | 215.3320 |
| 30000 | 4 | 292.9415 | 292.9688 |
| 15000 | 5 | 146.4775 | 146.4844 |
| 32000 | 6 | 312.5435 | 312.5000 |
| 16000 | 7 | 156.2637 | 156.2500 |

Each tone uses the same 4,096-word, 40-cycle sine and root key 60. Maximum
frequency error is 0.050861%; this verifies native metadata behavior, not
physical DSP accuracy. All eight screen rate labels match. Forward cases
sustain and end with a silent final release second. OneShot at 44.1 kHz has
its last nonzero frame at 4,384 of 65,536 captured frames, before note release;
its release capture is entirely silent. Output channels are identical for
these mono controls. Stereo at every rate is still unqualified.

Ten sample allocations, including the asymmetric-point control, load exactly:
92,160 bytes including each fixture's 512-word wrap padding. Twelve read-only
RAM snapshots preserve all ten public descriptors through selection/playback.
This fixed-size experiment does not establish arbitrary import padding,
inclusive/exclusive endpoint policy, or final partial-block behavior.

## Original-OS construction evidence

With `file = 4800 + (page << 10) + (logical & 3FFF)`, the bounded original
`001F:6FBF..71F7` decode follows descriptor search and construction. At `6FFF`
RW5C becomes `1F6E`, a temporary 48-byte descriptor. Stores at `7071..70D8`
populate its five address fields; `714C` writes mode at `+24`, and `71E8`
writes the period-derived rate code at `+2C`. `71EF` writes root key 60.
The eight six-byte rate strings at file `0C0A1A..0C0A4A` agree with the native
fixture. No additional firmware-coverage percentage is inferred.

The SDS routine derives release points ten and fourteen words after the
incoming loop end, then writes `0x1200` zero words starting at the latter
point. Its fixed packet writer and hardware polls are not a qualified bounded
WAV writer. Allocation slack and endpoint conventions must be reconciled
before reusing this routine or applying its padding to arbitrary WAV lengths.

## SDS length boundaries and cancellation

The [length validation](../condensed/validation/bluescsi-length-contract-2026-10-18.json)
uses ordinary System MIDI controls to enable Exclusive RX, then sends external
SDS messages into stock firmware. Eighteen length cases and one settled
cancel/retry retain 54 snapshots, 249,760 exact transmitted PCM bytes and 3,143
exact acknowledgment messages. The lengths include 2/3, 39/40/41,
4594/4595/4596, 4607/4608/4609, 9202/9203/9204/9216, 13811, 18419 and 23027.

For these **16-bit, 44.1 kHz, OneShot headers with loop start 0 and incoming
loop end N-1**, the native path has the following observed contract. B is the
native wave-word allocation base, not a fixed address:

| Quantity | Observed result |
| --- | --- |
| Reservation | `ceil((N + 13) / 4608)` blocks |
| Descriptor points relative to B | `0, 0, N-2, N+8, N+12` |
| Initialization writes | 4,608 zero words starting at `B + N + 12` |
| Packet writes | `40 * ceil(N / 40)` words starting at B |
| Public descriptor | Remains unused during receive; publishes after completion |

The `N-2` endpoint is the header's native clamping behavior. It is **not a WAV
endpoint recommendation**. The matrix deliberately fills final packet padding
with nonzero witness words to expose the writer's extent; those extra words
really reach wave memory. For N=9,203, two blocks reserve 9,216 words while the
packet writer stores 9,240, exceeding that reservation by 24 words. Zero-fill
exceeds its reservation by up to 4,607 words in this matrix; for N=4,596 it fits
exactly. Earlier allocated samples remain unchanged because these runs append
into unused space. Full-capacity safety and physical behavior are unqualified.

**Do not reuse the SDS packet/zero-fill loops as the bounded WAV writer.** The
importer needs an explicit writer limited to its own reservation, with exact
frame count and a separately qualified endpoint/guard policy. Copying the
SDS reservation formula alone does not bound its actual writes. The 399
byte-checked original-OS decodes and per-snapshot write extents are retained.

A 4,609-word receive cancelled after its first packet restores cursor 2 to 0
without publishing any of the 512 public descriptors. Its already-written PCM
remains as free-space contents. After native cancellation UI/state cleanup
finishes, retry uses the same two blocks and publishes exact data. The native
state is briefly `0A` even after the cursor has returned to 0; rollback of the
cursor is therefore not proof that the owner has finished cleanup.

An early-retry control starts a new header during that interval, ending with
cursor 2 and no public sample. **BUG-118 is fixed in an opt-in experimental OS
patch:** the original supervisor's `0166:8905` state clear is observed erasing
the newly accepted transfer; a guard now rejects headers while `2BBA` is
nonzero, before decoding/allocation. Three fresh native timing cases preserve
existing samples, return exact CANCEL responses, and publish successful
settled retries plus follow-on samples without a leak. All nine published
samples match 28,800 transmitted PCM bytes. Original firmware is unchanged.
See the [repair and reproduction](../firmware/os/os-transfer-lifecycle.md#native-cancellation-overlap-and-private-os-guard)
and [validation](../condensed/validation/bluescsi-cancel-ownership-2026-10-18.json).

The later **BUG-119 header lifecycle repair** retains state FF through successful
publication and states 2–5 through error cleanup. Two negative controls prove
that the cancellation-only patch admits headers too early; four final native
runs preserve the completed descriptor and prevent unpublished reservations.
The short-transfer control also completes before supervisor entry and still
publishes correctly. Eleven samples match 10,800 PCM bytes, with exact ACK/CANCEL
responses and existing allocations preserved. See the
[extended header contract](../firmware/os/os-transfer-lifecycle.md#header-admission-through-publication-and-error-cleanup)
and [evidence](../condensed/validation/bluescsi-header-lifecycle-2026-10-18.json).

**BUG-120** now rejects outgoing sample requests before they decode a slot or
enter shared sender setup while a receive owns state. Seven final native runs
cover receive/publication/error/cancel overlap, ordinary ACK/NAK controls and
idle sending. Eighteen received samples match 2,880 PCM bytes; a complete idle
dump preserves 9,216 sample bytes and exact NAK retransmission. Ten focused
tests and ordinary runtime/audio checks pass.
[Request guard and limits](../firmware/os/os-transfer-lifecycle.md#receive-owner-exclusion-for-outgoing-requests),
[evidence](../condensed/validation/bluescsi-command-exclusion-2026-10-18.json).

**BUG-121** adds the shared admission condition `2BBA=0` and `B1AE=FF`.
Overlapping receive headers and dump requests preserve the active sender;
completion or explicit cancellation permits a later receive. Stale ACK/NAK
then leave its counters and PCM unchanged. Ten final native runs preserve 28
received samples/4,480 PCM bytes and four complete dumps/36,864 bytes; exact
responses and retransmission pass. Thirteen focused tests cover all state-byte
pairs at both admission entries, and ordinary playback/MIDI/audio still pass.
[Shared admission contract](../firmware/os/os-transfer-lifecycle.md#shared-admission-for-active-senders-and-receivers),
[evidence](../condensed/validation/bluescsi-sender-ownership-2026-10-18.json).

**BUG-122** reconciles native local Sample Dump cleanup with the FF idle
convention. Unacknowledged/acknowledged completion and ordinary Exit now allow
a subsequent exact receive. The final helper preserves the data bank changed
by display cleanup and temporarily saves one two-byte selector word. Five
native scenarios publish 15 samples/2,400 exact PCM bytes and preserve two
complete dumps/18,432 bytes; 24 focused tests and runtime/audio checks pass.
[Contract](../firmware/os/os-transfer-lifecycle.md#local-sample-dump-cleanup-and-remote-stalls), [evidence](../condensed/validation/bluescsi-local-sender-lifecycle-2026-10-18.json).

**BUG-123** adds a foreground remote sender owner (state 7). Header/data stalls
cancel after five seconds without packet-counter progress; ordinary panel Exit
also releases ownership. Completion, peer CANCEL and progress resumption pass,
including exact retransmission and stale-handshake rejection during the next
receive. Seven remote and four local compatibility runs retain 33 exact samples
and three complete dumps;30 focused tests and runtime/audio checks pass.
[Recovery contract](../firmware/os/os-transfer-lifecycle.md#foreground-remote-sender-recovery),
[evidence](../condensed/validation/bluescsi-remote-recovery-2026-10-18.json).

**BUG-124** now guards local Sample Dump entry and retains state 8 through
display cleanup, releasing it atomically. The final-packet/header race previously
leaked an allocation, and a queued request was discarded; both now reject
without mutation and permit settled retries. Nine accepted native cases preserve
27 samples/4,320 received PCM bytes and five dumps/46,080 bytes. All 96 focused
tests and ordinary runtime/audio pass. Busy local entry and setup-error retention
have decoded/model coverage. [Local owner contract](../firmware/os/os-transfer-lifecycle.md#local-ownership-through-setup-and-cleanup),
[evidence](../condensed/validation/bluescsi-local-owner-2026-10-18.json).

This remains narrower than the importer's required owner. Remaining local
preparation/cancel timing, native Disk exclusion, pre-supervisor cancellation,
resource exhaustion and atomic stereo publication still require separate tests. Native
callee waits and full ISR/stack bounds remain unqualified; the observed 182-byte
stack depth is not a worst-case bound. No physical timing guarantee or bounded
WAV writer is established. Local unacknowledged dumps retain their stock UI
fallback, distinct from remote requests.

Two native emulator prerequisites were fixed before accepting these results:
BUG-116 adds real serialized MIDI output and transmit-ready status; BUG-117
implements sequential C00A wave writes while preserving fixed-address C008.
Both regressions first failed. The final driver/executable builds pass all
590 backend tests with zero skips, plus ordinary boot/media/audio, scheduled
MIDI and variable-block runtime checks. The final executable SHA-256 is
`ccb370a3f37c5fd7a9b2aa761ef339b9b5965d6211b64751dd7520557efb4dda`.
Original ROM and OS files remain byte-exact. This does not qualify physical
MIDI output, wave-bus timing or a complete SDS protocol implementation.

## Stereo transaction requirements

The [original transfer lifecycle](../firmware/os/os-transfer-lifecycle.md)
has **one saved allocation cursor**, `1FA0`, captured from `3616` at
`001F:6E69`. It reserves wave blocks before searching for an empty descriptor
(`+2A == 0`) among 512 slots. Success copies the staged 48 bytes to the public
slot; higher-level failure restores the cursor and page `0299` mirrors.
This is static SDS evidence, not an importer ABI or observed stereo rollback.

Calling that allocator independently for left and right would overwrite its
single backup cursor. It therefore cannot, by itself, roll both allocations
back to the pre-stereo state. The importer needs one transaction owner:

1. Validate format, frame counts, arithmetic and required padding; locate one
   free slot for mono or two distinct free slots for stereo. Do not overwrite
   an existing sample or its name to make space.
2. Preserve the original allocation cursor once, check total block capacity
   for both channels, and acquire exclusive allocation ownership before any
   reservation. The exact exclusion mechanism remains to be qualified. Keep
   the transaction owned through cancellation UI/state cleanup, not just until
   cursor restoration; the early-retry counterexample above makes this required.
3. Keep both descriptors private in the proposed 96-byte staging area. Stream
   both channels into their reserved storage, retaining frame alignment and
   channel identity; publication requires both channels to be complete.
4. Publish the pair and dependent references under a qualified exclusion
   boundary. Two sequential descriptor copies are not inherently atomic to
   readers. Naming/partner rules must agree with the
   [observed stereo preview](bluescsi-feasibility.md#cold-load-selection-and-playback-follow-up)
   and the permanent hierarchy above. Dependent objects must be initialized
   and named before treating them as saveable; editing reference fields alone
   is insufficient. Existing objects and names need a non-destructive policy.
5. Before publication, failure/cancellation releases the entire reservation
   from the original saved cursor, restores allocation mirrors and invalidates
   staging. Do not rewind over another owner's allocations. After publication,
   cleanup needs a separate defined policy; a cursor rewind alone is unsafe.

These are design requirements, **not implemented or fault-tested behavior**.
Importer-driven partial/patch creation, two-slot exhaustion, nearly full wave
RAM, failure during the right channel and retry without leaks remain open. The
96-byte staging allowance is already included in the
[memory budget](bluescsi-memory-contract.md#corrected-budget-and-proposed-placement).

## Builder corrections and reproduction

BUG-114 corrects the builder's misnamed rate/loop controls: use `sample_rate`
in integer Hz and `loop_mode` as `forward` or `one_shot`. Historical
`loop_enable` is a deprecated raw rate-code alias, retained only for byte
compatibility; mixing it with `sample_rate` fails.

BUG-115 adds `sample_points`, requiring all five keys `start`, `loop_start`,
`loop_end`, `release_start`, `release_end`, each an integer offset within the
builder's 4,608-word slot. Legacy top-level address names retain their old
shifted layout and cannot be mixed with the explicit schema. The builder
does not infer loop ordering or resample WAV input. Existing demo-synth and
filter-sweep images remain byte-identical; manifests now express rate/loop
settings accurately. New fixture specs should use the explicit schema.

The durable validation embeds the fixture JSON, final native harness, read-only
observer, analyzer, source identities, test results and raw descriptor rows.
Build the fixture with `scripts/build_sample_disk.py --spec <fixture.json>
--out <private-image>` using the unchanged `waves760.sdk` template. Replay the
embedded harness from its original four-level private directory depth with a
fresh `--output`; it uses stock firmware and ordinary mouse/MIDI input. The
analyzer checks exact PCM, descriptor rebasing, frequency and release, and all
source hashes. The final backend suite passes **588 tests, zero skips**;
28 focused builder tests pass. Earlier failed exploration harnesses are
excluded and documented in the validation.

The separate permanent-assignment validation embeds its input harness,
passthrough observer, analyzer, complete object-write rows and snapshot record
bytes. Replay `native_assignment.py --output <fresh-save-run>` from the retained
four-level private directory depth. It prewrites the full ordinary-input
schedule and saves to a private copy of the blank formatted floppy. Then run
`--source <saved-performance.img> --cold-performance --output <fresh-cold-run>`
and atomically publish the retained cold `command-000.json` schedule. The first
cold audio capture precedes entry to Patch or Partial modes. The analyzer
verifies input immutability, record/store replay, disk serialization, exact PCM
and channel alignment. No emulator or production code changed in this
checkpoint; the previous 588-test suite result was not rerun.


### Early CANCEL reservation ownership

BUG-125 now preserves receive rollback through immediate, duplicate and completion-boundary cancellation using stateFE. The private image reuses the released allocation on retry and leaves existing samples intact. This fixes single-receive cleanup, not pair-wide stereo atomicity. [Current lifecycle](../firmware/os/os-transfer-lifecycle.md#early-receive-cancellation-ownership-bug-125), [evidence](../condensed/validation/bluescsi-early-cancel-2026-10-18.json).


### WAV reference and native-loader reuse (checkpoint27, 2026-10-18)

Checkpoint27 adds an executable host reference for the WAV-specific contract, with39 passing tests. It validates little-endian RIFF/WAVE, one fmt and one nonempty data chunk in either order, PCM16 mono/stereo, rate codes, block alignment, byte rate, chunk extents and odd-byte padding. Unknown chunks are skipped without reading their payloads; optional root/loop metadata is not interpreted. Duplicate fmt/data chunks, partial frames, unsupported encodings and truncation reject. Bytes outside the RIFF extent are ignored; extra PCM fmt bytes are ignored after validating the first16. The candidate rate list follows all eight decoded native codes; this does not qualify stereo playback at every rate. Metadata reads are at most16 bytes and streamed PCM reads at most4096, always complete frames. Short reads, cancellation and transport exceptions stop processing. Sparse near-4GiB arithmetic and a failure between PCM blocks pass without allocating large files. This is a host specification, not firmware implementation, native allocation or a measured code fit. The existing672-byte residual budget remains unproved.

The next reuse investigation must follow the ordinary SCSI disk Load path: identify callable allocation/descriptor and wave-transfer services, their register/bank inputs, write bounds and error cleanup. Reuse qualified native services where possible rather than duplicating them. The separate remote SCSI sample-transfer handler is not evidence for an ordinary disk-loader ABI. The SDS fixed-packet/zero-fill writer remains excluded because its writes can exceed reservation. WAV parsing and interleaved stereo conversion remain format-specific; publication still requires a pair-wide ownership contract.

[Reference](../../scripts/bluescsi_wav_contract.py), [tests](../../tests/test_bluescsi_wav_contract.py), [evidence](../condensed/validation/bluescsi-wav-contract-2026-10-18.json).


### Ordinary SCSI loader reuse (checkpoint28, 2026-10-18)

Stock HDD loading now supplies thirteen observed native DMA transfers and allocation updates, with119808 exact PCM bytes and playback intact. The destination/count setup and descriptor relocation are concrete reuse candidates; direct-call ABI, caller ownership, RAM-to-wave support and bounded failure handling remain open. Stereo WAV still needs deinterleaving. [Reuse contract and next steps](bluescsi-loader-reuse.md).


### Bounded stereo writes (checkpoint34, 2026-10-18)

Checkpoint34 qualifies guest-side stereo deinterleaving and bounded planar writes in an isolated native diagnostic. One4096-byte workspace holds2048 interleaved input bytes at physical004940,1024 left-channel bytes at005140 and1024 right-channel bytes at005540. The guest generates distinct16-bit left/right sequences, splits at most512 frames, and uses the bounded DMA adapter for each channel. Cases1,511,512 and513 frames preserve channel identity and sequence;513 requires512+1-frame chunks. All6148 payload bytes match exactly, including the two-byte-per-channel final tail. Ten payload DMA events match the expected source, destination, order and lengths.

Eight complete8192-byte channel/sentinel arenas match (65536 bytes), including every byte outside each payload. The13 previously loaded HDD samples retain all119808 PCM bytes, the HDD export is unchanged, and pre-diagnostic playback/release passes. No original firmware changed. Image SHA256:23a53f004a929af9120671464d05138ec40577947a41bd89e5ef58e7edf76e57.

The splitter measures32 code bytes, validation145 and DMA setup/polling80, totaling257 for these prototype pieces; the full diagnostic harness is1503 bytes. A conditional addition to the earlier2402-byte retained-code budget leaves415 of the3074-byte ceiling before parser, production ownership, publication and UI costs. This is a warning about the tight budget, not a linked fit measurement: the transport diagnostic still includes removable test code and these images are separate. The splitter assumes1..512 frames from its diagnostic caller; a production caller must validate that precondition. This design reads at most2048 PCM bytes per refill, within the reference parser's4096-byte maximum.

This closes only the bounded stereo write-path subcheck. Input is guest-generated, not read from WAV/BlueSCSI; destinations are test arenas, not native reserved/public samples. It does not prove stereo playback, pair-wide allocation, publication, rollback or cancellation between channels. Interrupts are masked, and physical DMA abort/quiescence remains unqualified. Next BS1 work is pair-wide ownership/reservation and right-channel failure rollback with descriptor publication held until both channels succeed. UI/code-reuse exploration remains deferred. BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-stereo-write-2026-10-18.json).


### Pair reservation and pre-publication rollback (checkpoint35, 2026-10-18)

Checkpoint35 qualifies pair-wide reservation and rollback before publication in a private native guest diagnostic. After ordinary HDD Load supplies13 samples, each attempt captures the original cursor and mirrors once, checks native free block capacity, and advances3616 plus the used-block mirror by two. Three attempts produce the observed sequence13->15->13, repeated three times. A65535-block request rejects without changing the native capacity or reserving storage. The retry therefore reuses blocks13/14 without a leaked allocation.

The left channel writes1024 bytes. Case1 then rejects an odd1025-byte right write; case2 cancels before the right write; case3 completes both1024-byte writes but deliberately rolls back without publication. Four read-only case captures verify the expected18432-byte pair region, all512 public48-byte descriptors unchanged, both allocation mirrors restored, native SDS backup1FA0 unchanged and all119808 existing PCM bytes exact. Unwritten right-channel bytes retain the sentinel. HDD export is unchanged and pre-diagnostic playback/release passes. The guest, not the host observer, performs the reservation and restoration.

The scoped reserve helper is43 bytes and rollback16 bytes inside a1450-byte harness. It checks a known13-block fixture and writes dedicated one-block channel extents; this is not a general slot allocator or complete32-bit address API. Interrupts are masked for the entire callback, so ownership is synchronous. Keeping an importer owner across interrupt/input service remains unqualified. No descriptor is constructed or published, and no in-flight DMA is aborted. The result establishes rollback before publication after right-channel rejection/cancellation, not atomic stereo import. Next: qualify safe staging/publication of the pair and its native object relationships, then interrupt-serviced ownership and combined size. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-rollback-2026-10-18.json).


### Staged stereo-pair publication (checkpoint36, 2026-10-18)

Checkpoint36 qualifies staged descriptor publication for a known native stereo template in an isolated guest diagnostic. It checks that public slots13/14 are empty, reserves26 blocks together (cursor13->39), copies the recorded pair into a private96-byte staging area, and rebases all ten32-bit fixed-point addresses by13 blocks. Allocation bases become13/26, counts remain13 each, and names retain the native7F,L/R suffix. All five points of each descriptor fall inside its reserved channel extent. This uses the recorded44.1kHz/root60 descriptor defaults; it does not construct arbitrary WAV metadata.

The guest writes239616 bytes of distinct deterministic channel data before copying either descriptor into public sample memory. Four read-only captures prove: staging alone leaves public descriptors and wave data unchanged; completed PCM still leaves both public slots empty; publication changes exactly the two intended48-byte records; a repeat rejects occupied slots without allocating or rewriting PCM. The cursor has one diagnostic write,39. All other510 descriptors,119808 existing PCM bytes, the SDS backup and the untouched allocation mirror remain exact. Template/staging guards pass in the corrected image. The original HDD export and pre-diagnostic playback/release also pass. Ordinary native Loop/Smoothing selection then recognizes the newly published pair through the usual partner-name mechanism; this is selection evidence, not an audition or persistence test of the new pair.

BUG-127 records and fixes a private diagnostic guard incorrectly placed inside the DMA source interval. V2 moves the template/guards to physical005A0E..005A72; staging is005B00..005B60. The final fresh run uses corrected ordinary UI coordinates and checks the full public descriptor table after selection. The accepted image SHA256 is d5df8827994664cf766d61eedd204c62817f49aad210091bd23f5e8cf08ce152; its complete diagnostic harness is1167 bytes, not a measured production publication footprint.

Interrupts remain masked across reservation, writes and publication. This protects the two sequential descriptor copies from ordinary CPU interrupt readers in this experiment; it does not establish a resumable importer owner, arbitrary reader exclusion or real-time behavior. Fixed slots and template-sized allocations leave free-slot scanning, general metadata construction, cancellation ownership, new-pair playback/Save/cold Load and complete code/RAM/stack fit open. Next BS1 work is interrupt-serviced transaction ownership and general descriptor construction with the bounded WAV writer, followed by integrated fit. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-publication-2026-10-18.json).


### Interrupt-serviced pair ownership (checkpoint37, 2026-10-18)

Checkpoint37 adds explicit interrupt service to the isolated stereo publication diagnostic. Its helper saves working registers and the current data selector, restores native data banks and the caller's interrupt masks from the saved PUSHA frame, permits interrupts only when the caller originally enabled them, then masks again and restores the diagnostic context. The final native run records 493 timer IOS reads at0000:CAD2 and 34 MIDI data reads at0000:CD1F during a 6.683714-second owned interval. These counts establish service activity, not worst-case latency, stack bounds or physical timing.

A separate private owner word at physical005BF0 protects the tested SDS entry. The five-byte hook at001F:6CDD calls a low-window gate and branches to the existing CANCEL response path when owned. With System Exclusive enabled through the native System menu, incoming commands01(header),03(request) and7D(CANCEL) reach that gate while cursor3616 is39. They do not change receive state2BBA, sender stateB1AE, the saved SDS allocation cursor, the reserved pair or existing samples. All239616 generated pair PCM bytes, all119808 existing PCM bytes, guards and the complete expected public descriptor table remain exact. Ordinary selection still builds stereo preview references512/513 using block bases13/26 and opposite pan bytes.

After publication the owner word clears. A normal header then passes through the same gate, reserves one block (39->40), and ordinary SDS cancellation rolls it back (40->39); all public descriptors, including the pair, remain exact. This positive control distinguishes actual command exclusion from disabled reception. Earlier runs received MIDI bytes but had System Exclusive disabled and never exercised admission; they are excluded from the exclusion claim. Initial instruction-fetch observation attempts were also inadequate for the native fetch path; final evidence uses data/register taps.

BUG-128 fixes an error path found in the private prototype: latching ownership before a failed reservation could leave the flag set. V2 reserves while masked and latches ownership only on success, before the first service window. A guest65535-block claim rejects with cursor13 and owner0, followed by the successful26-block claim and publication. The final harness is1601 bytes, including test delays, generated PCM, capacity rejection, template publication and unused diagnostic helpers; this is not an integrated production footprint. Accepted image SHA256:62b196966a95cfa6790a871e090ea8a2c5f0c578e4fb99e6b6a2f2025ffe000b.

The result qualifies this successful publication plus these three incoming SDS commands. It does not qualify every SysEx family (including manufacturer41), all SDS commands, user Exit/cancellation during the pair transaction, DMA timeout quiescence/release, arbitrary free-slot/metadata construction or general allocation exclusion. No native foreground dispatcher runs inside the helper. Broader register/stack/interrupt bounds, physical hardware and combined transport/parser/publication code fit remain open. Next: combine owner-preserving user cancellation with pair-wide rollback, extend competing-command coverage, then integrate and measure the full implementation. UI reuse stays deferred; BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-pair-owner-2026-10-18.json).


### Panel cancellation and pair rollback (checkpoint38, 2026-10-18)

Checkpoint38 adds ordinary panel Exit cancellation to the interrupt-serviced pair diagnostic. Three fresh native runs cancel at explicit service boundaries: before any PCM write, after the complete left channel, and after both channels but before publication. The raw four-row panel scan follows the previously qualified native Exit mapping; it latches an extension-owned cancellation word without forcing the native event queue. The callback unwinds its service/hold calls normally before cleanup.

Cleanup runs masked, checks DMA count0118 is zero and the expected allocation cursor is still39, restores the original cursor13 and both allocation mirrors, and zeroes the private96-byte descriptor staging area. A read-only capture sees owner1 after rollback and invalidation; a subsequent capture sees owner0. In all three runs, all512 public descriptors remain unchanged at cancellation, the SDS backup remains intact and all119808 existing PCM bytes are exact. Completed unpublished PCM remains in released storage; cancellation does not promise erasure. Whole368656-byte wave captures match the expected untouched/left-only/both-channel states, including every byte outside those payloads.

Each run then repeats the ordinary callback with Exit released. The cancellation latch resets, the same26 blocks are reserved again, and all239616 pair PCM bytes plus both rebased descriptors match exactly. Observed cursor writes are39,13,39 in each run. Native Loop/Smoothing again creates preview references512/513 with allocation bases13/26 and opposite pan values; the complete expected public table remains exact. Original HDD export and pre-diagnostic playback/release pass in each process. No production backend or original firmware changed, and no new defect was found.

The guest latch-to-owner-release interval is about223 microseconds in these runs. This is a native-model observation after input detection, not a bound on button-to-response latency, worst-case ISR cost or physical hardware. Timer IOS reads continue while owned. The full private harness is1882 bytes, including delays, generated PCM, fixed metadata and diagnostic helpers; it is not an integrated production size measurement. Image SHA256:be59793b78c7593e6df2cb87f5f2326dd9588e6158f55a853ec2456649cdaafc.

This closes only the tested cancellation boundaries before publication. It does not abort a DMA in flight, qualify a stalled transfer, or release ownership after an unknown DMA timeout. It does not establish cancellation after publication, simultaneous competing-SysEx/cancellation timing, every command family, arbitrary sample metadata/free-slot selection, new-pair playback/persistence, physical fidelity or complete code/RAM/stack fit. The existing ownership check is fixture-specific and cannot substitute for a general allocation lock. Next BS1 work is broader command exclusion and integration sizing, alongside the remaining WAV metadata and playback/persistence gates. UI reuse remains deferred; BS1 stays OPEN. [Evidence](../condensed/validation/bluescsi-pair-cancel-2026-10-18.json).

## Scoped WAV-derived public construction (checkpoints74-78)

The private integrated client now constructs descriptors from actual Toolbox
WAV reads. In a fresh sampler it reserves one4608-word block per channel for
2..4594-frame files, zeroes only those reservations, writes exact source PCM,
then publishes mono or paired stereo records. Twelve descriptors from eight
files match independently generated expectations; all other public records
and all wave bytes outside the reservations remain exact. Generated names,
44.1kHz/root60 and OneShot are the tested profile. Candidate points relative
to B are0,0,N-1,N+9,N+13; native preview audition passes but this is not final
inclusive/exclusive endpoint or physical interpolation qualification.

Cancellation before first publication restores cursor/mirrors and clears96-byte
staging; retry succeeds. Occupied-slot re-entry rejects without mutation.
The constructor deliberately limits cursor<=12 and fixed fresh slots. No
general free-slot search, competing-SysEx owner, permanent Partial/Patch
assignment or Save/cold Load is established. These remain feasibility work.
[Identity-bound evidence](../condensed/validation/bluescsi-integrated-client-2026-10-19.json).
