# IM1: writable IMG, Copy, Optimize and stereo qualification

2026-10-20. The current combined OS passes native Save to a browser-mounted writable IMG, verified selection away/back, and a fresh-process Load with exact samples and playback. Copy overwrite Yes/No, both native Optimize options on fragmented media, and Akai stereo Convert Load also pass. **IM1 remains open** for the complete native stack, service-time, shared-resource and conflicting-operation/reset contracts.

The user's media policy is explicit: **FDD and SCSI IMG disks are writable; ISO/CD media are read-only.** Intentional IMG write protection must still be respected. This supersedes the earlier all-library-read-only fixture assumption. It requires no additional browser OS or Boot ROM change.

## Accepted results

| Check | Observed result |
| --- | --- |
| Writable mounted IMG, BUG-167 | Native ISO Load supplies 13 sample clusters. Browser selects HD2 `Save.img`; native Save persists all 119,808 expected PCM bytes. The resulting 10MiB image matches the reference image byte for byte. The ISO source and other IMG remain unchanged. |
| IMG selection and persistence | The accepted run verifies CD2 catalogs, D8 indices 0 then 1, and native Disk Load/drive2 after each selection. A fresh emulator process mounts the saved IMG, loads 13 clusters/119,808 exact bytes and plays/releases. |
| Copy overwrite No | Distinct source/destination PCM with matching names. No leaves the destination byte-identical; fresh Load and playback reproduce the original destination. |
| Copy overwrite Yes | Yes replaces all 13 sample allocations with the source's exact PCM. Fresh Load/playback passes; its peak is twice the No case, matching the deliberately doubled source amplitude. |
| Optimize with fragmented sample storage | Both **Sort in Alphabetical Order** and **Correction for Time Indication** selected through F1 All On. The directory changes by 240 bytes; all 13 name-to-PCM associations remain exact. Fresh native Load reproduces 119,808 expected bytes and playback. Sample clusters remain scattered; this is not a defragmentation command. |
| Akai stereo on current OS | Browser mounts the genuine String Ensembles CD; native Convert Load reproduces 30 samples, 15 L/R pairs and 13,568,196 converted PCM bytes against original-firmware reference hashes. Three notes and release pass; playback survives browser Exit. |
| Write-error controls | Ten synthetic SPC cases pass, including protected IMG/optical refusal, completed write persistence, interrupted DATA OUT with unchanged backing, invalid range, and missing/resized backing returning CHECK CONDITION with WRITE ERROR sense `03/0C`, followed by NOT READY. These are peripheral tests, separate from firmware acceptance. |
| Regression | **773 backend tests pass**, with no failures, errors or skips. Fixture-disabled native panel/menu and three Disk/Load voice trials pass. Exported floppy, post-stress floppy and four display artifacts are byte-identical to the previous executable's results. No whole-WAV timing equivalence is claimed. |

The fragmented fixture relocates sample clusters from 116–128 to 202, 209, …, 286 while preserving FAT termination, directory references and PCM. Independent before/after name-to-PCM checks distinguish directory sorting from data loss. The native loader follows hierarchy order, which need not equal sorted disk-directory order.

## Volume Dump FD: partial result

Native Volume Load populates `TXW:TX812 waves`, then Volume Dump FD initializes a private 720KB IMG and saves it into slot1. The exported dump changes 147,395 bytes. A fresh process lists the saved volume and begins restoration, but requests source media **`SINE BIN0023`**. Inserting the originating ROBOFULL fixture and retrying does not satisfy that request; sample allocation remains zero.

This establishes populated save and cold directory recognition, **not a complete restore**. The matching source-media dependency remains unresolved. It is not diagnosed as a browser defect. [Captured request](../condensed/validation/bluescsi-im1-volume-dump-media-request-2026-10-20.png).

## Native safety analysis

The static interrupt graph decodes 9,181 instructions in 152 functions with fetch pages `000F/001F/002D/0000`. All modeled indirect branches resolve under the recorded parser/envelope state-domain assumptions. Local maximum extra stack is 36 bytes for control root `001F:4000`, 22 for MIDI parser `000F:213A`, zero beyond the UART stub, and six beyond the wave-end stub. Timer entry/saves plus control and one allowed wave-end interrupt give a **conditional 62-byte interrupt contribution**.

That is not a full stack bound. It assumes the stated mutable-state domains and interrupt masks, excludes other active Disk/FDC owners, and still needs the browser's complete native caller/callee chain. It must not simply be added to the earlier 166-byte custom contribution and called a total proof.

The MIDI parser at `000F:213A` drains a live ring while arrivals remain enabled. No explicit per-service quota was identified. A finite stack graph therefore does not establish maximum service time. The next feasibility work must bound arrival/service behavior or establish a bounded scheduling workaround, then close indirect ownership and conflicting native Disk/reset cases. No firmware change implementing such a workaround is claimed here.

## Fixture write contract and identities

BUG-167 fixes only the explicit `S760_TOOLBOX_IMAGE_ROOT` test profile. Completed WRITE commands to a writable 512-byte disk image are flushed to its selected backing file; interrupted DATA OUT never commits. Missing/resized backing invalidates the selected media and returns an error. Optical targets and intentionally protected IMG files reject writes. Ordinary native media retain their private working-image/explicit-export behavior; FDD behavior is unchanged.

Use private image copies for this opt-in fixture. Completed file writes survive selection and process restart; restoring an emulator checkpoint does not undo those writes. The tests do not qualify host filesystem crash atomicity, competing external writers, or physical BlueSCSI write durability.

| Artifact | SHA-256 |
| --- | --- |
| Unchanged combined OS, GB-6 v9/SDS included | `6297274dd5c33b0b37409d3cddcd53e40b8af6140f2c416fc0213181cd3ba628` |
| Unchanged selectable GB-6 Boot ROM | `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb` |
| Current emulator with writable IMG fix | `7c994e8679c51e71801ce7c4ad570983b5a7a7e55f1ae135ed5fc58dda658962` |
| Earlier emulator used for Copy, Optimize and populated dump Save | `5720c78bdc2e129d7f2264b524b86ab914a3c109cf86194a5131484952399540` |

Each accepted case retains its actual executable hash. The OS still occupies **6,452/8,002 named bytes**, leaving **1,550 free**, including **1,332 code-adjacent**. Original OS and Boot ROM hashes remain unchanged.

The durable [validation](../condensed/validation/bluescsi-im1-final-gates-2026-10-20.json) contains ten accepted native case records, partial Volume Dump observations, conditional decoded graph, source scripts and synthetic results. Native acceptance uses ordinary physical inputs and runtime APIs with read-only observers. Excluded probes include missed pointer rows, an incorrect sorted-directory PCM oracle and an initial Optimize attempt with no options selected; their outcomes are not promoted to passes. The corrected IMG reselect run explicitly asserts target, command indices and handoff.

Remaining compatibility work is now the complete Volume Dump restore, additional Roland stereo/geometries and predecessor-only final-image persistence/controller cases. Physical configuration, available IDs, actual library preflight and hardware timing remain separate. RC-100 input remains waived by the user. The [active roadmap](bluescsi-image-mount-plan.md) retains these gates; no full IM1 GO is claimed.
