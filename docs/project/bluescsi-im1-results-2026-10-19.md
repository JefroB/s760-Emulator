# IM1 image mounting: first native qualification batch

**Date:** 2026-10-19. **Decision:** IM1 remains in progress. The stock target-folder mechanism has scoped native passes; a complete browser, automatic handoff, full fit/recovery and physical acceptance remain open.

The user confirms **BlueSCSI V2 with the very latest firmware**. That is the hardware baseline. Exact installed build/configuration readback is pending; it does not prevent the independent work below. Source contracts cover official release v2026.08.17 and the reviewed main revision. [Active plan](bluescsi-image-mount-plan.md), [command contract](bluescsi-image-mount-protocol.md), [identity-bound results and reproduction sources](../condensed/validation/bluescsi-im1-native-2026-10-19.json).

## What passed

| IM1 area | New evidence | Boundary |
| --- | --- | --- |
| Baseline | Immutable original OS/ROM, native executable, private images and source identities recorded | Mouse/CRT research baseline; combined production patches and installed target map remain open |
| Source contract | Pinned upstream command implementation executed in a host harness: 29 assertions | Full upstream Toolbox source plus extracted switch/tray/readiness functions; hardware/filesystem/settings dependencies are stubbed |
| Collection layout | Four separate 100-image folders: three ISO targets and one IMG target | One collection per SCSI target, bounded by available IDs |
| Guest switching | 144 actual guest commands across IDs 1, 2, 3 and 6; each 18-command matrix invoked twice through ordinary UI input | Source-backed opt-in emulator profile, not physical BlueSCSI |
| Selection identity | Entries 0 and 99, same basenames in different target folders, exact capacity and sector payloads | 512-byte IMG and 2,048-byte optical geometry |
| Media changes | Expected NOT READY, medium-absent sense, UNIT ATTENTION, media-change sense, then readiness | Bounded diagnostic sequence; broader fault/reset recovery remains open |
| Valid IMG loading | Two distinct valid Roland image variants mount, Scan/Load and play; 13 allocations / 119,808 sample bytes match in each independent run | Existing native Disk controls perform the scan/load; images differ in PCM amplitude |
| Valid optical loading | A compatible raw Roland image mounted as ISO loads through native CD1 Scan/Load and plays with the same exact sample oracle | 10MiB test volume, not arbitrary CD/ISO9660 format or a large commercial-library claim |
| Same-session reload | B-to-A mount, native rescan/reload, 119,808 final exact bytes and both playback/release checks pass | Native clear-memory confirmation is required when replacing loaded content |
| Error cases | Upstream host checks plus synthetic SPC checks cover empty/101-entry directories, truncated listing, invalid selection/open failure, protected writes and recovery | Actual image-mount failure is not reliably reported by D8; verify resulting media |
| Fit | 1,451-byte guest command diagnostic; 1,475 bytes for the alternating-image variant | Complete production code/UI/ownership/stack is not included |
| Regression | 748 backend tests pass with zero skips; ordinary boot/load/playback passes; fixture-disabled wave RAM matches all 33,554,432 prior reference bytes | These do not establish physical timing or complete feature acceptance |

The 144-command matrix includes 16 exact sector reads, totaling 26,624 bytes, plus eight full 4,000-byte directory responses. All fixture/library files remain unchanged. The sample-byte checks and actual Perform playback are separate acceptance evidence from the synthetic sector fixtures.

## Folder layout that can actually use the stock commands

```text
SD root/
    bluescsi.ini
    Existing writable save/boot image(s), on separate target(s)
    CD1/    ISO collection A: up to 100 images
    CD3/    ISO collection B: up to 100 images
    CD6/    ISO collection C: up to 100 images
    CD2/    Dedicated IMG collection: up to 100 images
```

This supports the tested scale of **300 ISOs plus 100 IMGs**. The browser can label the collections and select their targets. Physical IMG configuration must explicitly establish the disk type/block size and align `ImgDir` with the Toolbox folder when cycling is enabled. This example does not move the user's files, reserve their SCSI IDs or qualify their installed configuration.

The logical `/Library/ISO_A` layout in the plan remains an organizational example. Stock D7/DA/D8 directly use `CD<id>` and skip subfolders. D9 shared-directory selection does not redirect them. A collection-per-target approach can cover hundreds of images, but supporting more folders than available IDs still needs another mechanism. No arbitrary-path mount command was found in the reviewed stock SCSI implementation.

## Native workflow and the reload confirmation

Private OS diagnostics run the S-760 CPU's bounded SCSI sender through the ordinary Save System callback. They preserve the original files, return normally and use read-only observers. Lua register writes are restricted to the separately labeled synthetic SPC tests; they are not firmware acceptance.

For valid-content tests, the guest selects the image and drains media-change responses. Ordinary Disk Scan/Load then loads the volume, and Perform playback verifies nonzero audio and silent release. The IMG variants share metadata but contain distinct PCM, so a stale sample payload cannot satisfy both exact-byte oracles.

The first same-session B-to-A test stopped at the normal **Clear Internal Memory Before Loading** confirmation. That is expected native behavior. An intermediate rerun also used the wrong pointer coordinate scale. The corrected harness answers Yes through normal mouse input at runtime coordinates 54,62. The final run passes: A replaces B with 119,808 exact final sample bytes, both variants release silently, and the A/B playback peak ratio is 1.999979. Neither failed attempt is counted as successful native reloading. See BUG-139 and the retained attempt records.

## Footprint and ownership

The main diagnostic round-trips 490 instructions and uses these physical regions, all end-exclusive:

| Resource | Physical extent | Bytes |
| --- | --- | --- |
| Guest code | `003D3E..0042E9` | 1,451 |
| Buffer and guards | `0043FE..005402` | 4,100 |
| Diagnostic CDB cases | `005404..0055B4` | 432 |
| Diagnostic result records | `005600..005840` | 576 |
| Control state | `005BF0..005C0A` | 26 |
| **Named diagnostic total** | Within the 8,002-byte candidate | **6,585** |

These regions do not overlap; 1,417 candidate bytes are unassigned in this diagnostic inventory. Code remains exact across the captured native menu/load/playback snapshots. This is not a complete production fit result. Discovery, file-list UI, native handoff, retained SDS/error repairs, additional mutable state and full stack/interrupt bounds must be linked and measured. The 76-byte local prologue count excludes nested callee and ISR depth. Diagnostic tables/results may only be removed from the census after a replacement path is qualified.

## Fixture contract and remaining work

`S760_TOOLBOX_IMAGE_ROOT` enables the new emulator fixture. Place target folders `CD0` through `CD6` beneath that private root and stage an existing native target image for each target used. Normal operation with this flag absent retains the prior path; the old D0/D1/D2/D9 file fixture is separate. Use the image fixture alone for these tests.

The fixture implements D7/DA/D8, minimal discovery/device metadata, selected-media reads, not-ready/unit-attention transitions, virtual eject/load and read-only targets. Sorting and symlink exclusion are host-fixture choices. Images are bounded to 64MiB and the configured 512/2,048-byte geometry; these are fixture limits, not BlueSCSI limits. Empty and failed selections retain the upstream handler's discarded-result behavior. Reset/recall invalidates the fixture's external selection and requires explicit re-selection; upstream automatic reset/cycling behavior is not yet qualified. Shared-folder metadata subcommands and arbitrary path mounting are absent from this profile.

Upstream ImageBackingStore tests the filesystem read-only attribute and opens such files read-only. Its disk write handler also rejects optical targets and nonwritable backing files. That establishes an IMG protection mechanism to test on the SD card; the emulator directly enforces a read-only policy and does not prove those attributes are set on physical files.

Next work is collection/image UI, automatic native refresh/handoff, distinct stereo media, combined ownership/cancellation/recovery, complete fit and controller parity. Physical tests must verify the user's available targets, IMG read-only attributes, representative libraries, separate writable save destination and media-reset behavior. A feature-level GO is still premature.

BUG-137 remains open as an external failure-reporting risk. BUG-138 corrects private fixture-environment propagation; BUG-139 corrects native confirmation handling. The initial sandboxed full-suite attempt was stopped after native socket failures/delays; the complete elevated suite passes. No firmware originals were changed.
