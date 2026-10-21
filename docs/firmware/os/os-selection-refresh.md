# Sample selection, stereo pairing and preview state

The SCSI session calls four page007F services through explicit fetch-selector writes. Their closure and page004B selection/name helpers have [694 byte-checked instruction anchors](../../condensed/validation/os-selection-refresh-2026-10-16.json). The local contracts below originated as static findings. The [2026-10-18 native follow-up](../../condensed/validation/bluescsi-stereo-ui-followup-2026-10-18.json) now exercises stereo preview selection and routing for one cold-loaded 44.1 kHz pair; construction, other rates and physical fidelity remain separate.

Page004B:6B2E maps current selection registers to the existing descriptor lookup6A26: types2/11 useRE7, type3 usesRE6, types4/12 useRFD, and type5 usesRWFE. Type1 selects index0. Type8 separately returns data0356:7060. Other types return zero.

## Existence and address flags

007F:488D reads indices from data0299:885C and886E, checks each type5 descriptor's word+2A, and stores boolean results in29E5/29E6. It repeats for currentRWFE into29E4. Zero block count means false on this path.

4AB2 clears245F, compares the32-bit fields at descriptor+10 and+14, and sets245F when the first is unsigned greater. The comparison is known; its complete UI meaning remains provisional.

## Stereo partner lookup

40CB first rejects a current descriptor with zero+2A. It copies16 name bytes into1C08, then finds the first7F marker. Only marker positions13 or14 qualify. The final name byte must be `L` or `R`; the routine swaps it and searches for the resulting16-byte name, excluding the current index. A match must have the same+2A block count. This supports a name-based stereo pairing interpretation without assuming a particular filename extension.

004B:6B9F performs the exact16-byte comparison and returns carry set with indexRW4C on a match. The type5 search scans512 indices when2460 is zero,510 when it equals2, and511 for other nonzero values. No match returnsFFFF with carry clear. The other supported type counts are1/64/128/255.

The selected partner index is retained inRWB8 and246A is set. Depending on2469, the caller either uses that partner or selects a single sample. Reserved type4 descriptor255 receives references at+10/+20, and paired records receive opposite signed byte valuesE0/20 at+14/+24. Under2A30, references512/513 substitute for the original indices, connecting the path to preview descriptors beyond the ordinary512 slots.

The native follow-up confirms the channel-routing role for these opposite values without calibrating the full pan scale. After cold Sample Load, entering Loop/Smoothing builds preview references512/513. Selecting L gives preview block bases0/13 and routingE0/20; selecting R gives13/0 and20/E0. Distinct recorded patterns remain on their original output channels with a common source-frame position, and mono selection centers the selected member. The source descriptors and allocations remain unchanged. This is a preview-selection contract, not proof that pairing names alone constructs every object needed by an importer. [Workflow and limits](../../project/bluescsi-feasibility.md#cold-load-selection-and-playback-follow-up).

## Permanent assignment follow-up

The [stock-OS assignment follow-up](../../condensed/validation/bluescsi-permanent-assignment-2026-10-18.json)
qualifies a separate permanent path for the same 44.1 kHz recorded pair.
Ordinary Partial SMT stereo search assigns public samples 0/1 to partial0
words +10/+20 and E0/20 to +14/+24; Patch Split Set maps its 88 keys to that
partial; Perform part1 selects patch0. Naming each object changes its initial
7F marker to space and makes the hierarchy eligible for Disk Save. The manual
explicitly excludes unnamed sounds from Disk operations (PDF page141).

Performance Save and fresh-process Load preserve all 736 bytes of the five
native records and all 239,616 sample allocation bytes. Cold Perform Play
auditions before entering Sample/Partial modes while preview partial255 still
has four FFFF references. Seven audio cases preserve L/R and common timing.
Read-only taps retain 238 object writes, replayed exactly with no dropped rows;
the validation byte-checks eleven original-OS store instructions. These are
internal store anchors, not callable construction ABIs. See the
[permanent hierarchy contract](../../project/bluescsi-sample-contract.md#permanent-playable-hierarchy-and-persistence)
for offsets, naming, disk serialization and scope. Arbitrary importer-driven
initialization, collision policy and transactional stereo publication remain open.

## Preview mapping remains partially bounded

438B acts only when2A30 is nonzero and applies additional display/mode gates. It copies five32-bit address fields, derives the end of allocated storage minus four words, and selects transformations using245D. An indexed table at data02E9:5C76 uses `42*mode + 6*descriptor_byte24`; each record supplies a mode byte and five address-source indices.

The caller bounds on both indices and all table values have not been established. The table is therefore still unclassified; a plausible decoded record is insufficient to claim its whole extent. Subsequent branches implement several address transformations for modes5 and above. These are decoded but not yet fully named or dynamically qualified.

The page010A:8000 callee reached throughCEC8 during sample-memory movement is now qualified: it forwards to0000:F8D8. That hook reads character(2,2) on CRT or(2,7) on LCD and acts only when the character equals0D. It writes a glyph91..94 at column18+R49 using R48's low two bits. Thus the five2-bit chunks generated by the caller form a conditional display update, not an unexplained memory-copy operation.

CRT character access uses hardware portsE800..E808 at address`0x1000+40*y+x`; LCD reads character/attribute planes at274E/284E with stride32. CRT write42A7 preserves the current attribute whenRF2 is zero. Both paths advance coordinates using their respective wrap rules. These local semantics are supported by the [display-helper anchors](../../condensed/validation/os-send-and-copy-helpers-2026-10-16.json); visual glyph meaning and physical display parity remain unvalidated. No original image or runtime behavior changed.
