# IM1 native browser results — 2026-10-19

**Decision:** IM1 remains OPEN. The first CRT browser-to-native ISO load/playback route passes in the opt-in source-backed emulator profile. Complete fit, recovery, controller and physical qualification remain open.

This supplements the [earlier native mount results](bluescsi-im1-results-2026-10-19.md). The [active plan](bluescsi-image-mount-plan.md) is the working checkpoint list; [machine-readable evidence](../condensed/validation/bluescsi-im1-ui-2026-10-19.json) contains the initial identities, decoded code, byte differences, command records, observed states and private prototype sources. [Exit/filename follow-up evidence](../condensed/validation/bluescsi-im1-exit-filenames-2026-10-19.json) records the current passing V8 build; [upstream filename boundaries](../condensed/validation/bluescsi-filename-boundaries-2026-10-19.json) records14 host assertions.

## Passing scope

- Native menu field hit testing, highlighting, text/bitmap drawing and ordinary mouse/panel input are reused. The prototype has seven image rows, Previous/Collections and Next. The keyboard graphics are cleared across the screen width; the body is blue. The green title strip follows the reused native popup highlighter. Footer/help ownership is still unfinished.
- Four collections on targets1/2/3/6 each return100 records. ISO A is paged through all15 pages to the last page beginning at98; choosing its second row sends `D8 63`, the actual protocol index99. Other collections were entered at page0, not exhaustively paged in this UI run.
- A valid Roland ISO at index99 mounts, handles readiness/sense and capacity, closes the browser through native event2, and opens native Disk Load on CD1 without manual Scan. Native Load restores13 sample allocations and119,808 exact bytes matching variant B, rather than variant A. Native Perform audition has peak0.0084738135 and44,100 silent release frames.
- Reopening starts at collections, and IDs3/2/6 each fetch a fresh100-entry catalog. All403 files in the private library fixture remain byte-identical. This count includes ignored ancillary/nested files; it is not a claim of403 mountable images.
- Follow-up V8 fixes native Exit by deriving the parent from the native stack and queueing native close/reopen/redraw. Native popup save refuses areas over620 cells; the40x20 browser exceeds that bound. Empty/loaded Perform restores correctly, repeated Exit has stable depth, and playback/release remains intact afterward. A separate Disk Load return matches all307,200 RGB pixels before/after. The mount path suppresses parent reload while handing off to Disk Load.
- A59-byte ASCII full filename at index99 mounts and loads the same119,808 exact sample bytes; its unique first32 bytes are displayed. Fully visible names remain limited to32 bytes including extension. This does not qualify arbitrary long-name prefixes or physical behavior.
- The scope uses an unchanged native executable from the preceding748-test batch. No C++ changed here; those backend tests were not repeated for this firmware-only UI experiment. Original OS/ROM identities are unchanged.

## Defects and limits

BUG-141 fixed a buffer lifetime violation: sense/capacity overwrite the listing buffer, so a successful mount now invalidates the old list and regenerates collection labels. BUG-142 fixed page redraw reopening popup contexts and handing native Disk Load an unclosed browser context. The failed older run still loaded exact B bytes but could not reach normal Perform playback; it is not an end-to-end pass.

BUG-140 remains OPEN: an experimental full-screen descriptor crashes on entry. The passing version uses the known popup descriptor contract and native clearing primitives. BUG-144 is FIXED in V8 through native parent reload. The older native-v7 and event0F-only candidates remain recorded failures. Footer/help, other parent/controller contexts, error presentation, long-name collisions and LCD/GB-6 remain unfinished. BUG-145/146 record upstream filtering/path hazards;32-byte fully distinguishable names are the first profile, while59 bytes is a bounded candidate with one passing native example.

BUG-143 fixes a private Windows snapshot-file reader/replacement race with a bounded retry. The failed run is retained. The first run imported the earlier helper; follow-up V8 runs use the retry version but do not deterministically force the collision branch. No guest RAM/register/PC forcing was used.

## Partial size census

| Component | Bytes |
| --- | ---: |
| Linked browser, sender, first native handoff and Exit code | 2,597 |
| Screen resources, labels and target table | 639 |
| One100-record listing buffer | 4,000 |
| Control/context extent | 92 |
| **Named total / candidate region** | **7,328 /8,002** |

The remaining674 named bytes are split across gaps. This is not a complete fit result or a guarantee that every gap is usable. Discovery, integrated operation ownership/cancellation/recovery, retained GB-6/SDS/error-path repairs, complete native refresh/cache handling and full caller/ISR stack bounds are excluded. The local callback prologue alone is76 bytes; native drawing and transport call depth is additional. Duplicate callback save/restore code offers an optimization candidate, not a measured saving.

The successful browser uses fixed diagnostic collection IDs, masks interrupts during its scoped transaction and does not qualify physical timing, competing operations, repeated automatic refresh, browser-to-IMG loading, distinct stereo media, writable-save integration or hardware parity. Earlier manual IMG and same-session reload evidence remains valid within its own scope. Stock firmware still provides one `CD<target ID>` picker folder per target, with at most100 images per folder; this work adds no arbitrary-path mount command.

## Next gate work

Qualify filename/filter/collision handling (BUG-145/146), repeated native refresh and the dedicated IMG route through this browser. Integrate discovery, operation ownership and retained repairs, and measure the whole build before a feature-level GO. Qualify the user's physical target/configuration map separately.
