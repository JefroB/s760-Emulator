# Ordinary SCSI loader reuse investigation

2026-10-18 — checkpoint28; native observations and bounded static decoding.

A fresh original-OS HDD Load identifies actual native reuse candidates. Thirteen DMA launches at003B:7A1E use control84 with9216-byte gate counts and wave-word destinations8+i*4608 for i=0..12. Their119808 PCM bytes match independent disk extraction exactly, and subsequent playback/silent release pass. The HDD export and original firmware remain unchanged. Three additional8192-byte launches use wave address00FFCC08; their purpose is not established here and they are excluded from the sample-transfer total.

Thirteen actual cursor increments at0119:9110 advance3616 from0 to13. Byte-checked code at0119:90F3 masks descriptor rate+2C to three bits, copies the prior cursor to descriptor+28, adds the global block count1C5C to3616, and derives the address relocation base from the old cursor times1200 plus361A/361C. These stores establish inputs and side effects, not a complete allocator entry point: free-space checks, descriptor search, caller state and rollback still require closure.

The observed DMA tail at003B:79F3..7A5C takes RWBC for0118, saves/restores flags and the115 mask, enables interrupts, writes84 to011D, polls SPC statusE408 and returns carry/RBB status. Its repeated wait path is not a qualified bounded Toolbox operation. The separately decoded003B:7CD0 helper reads the destination globals3644/3646, sets C00E/C00C, clears011A/011C and sets0118 fromRWBC; this run does not establish that helper as the observed caller. All three instruction spans match the original image and decode exactly to their stated boundaries.

Reuse direction: retain native wave-DMA and descriptor relocation mechanisms where a complete calling contract can be proved; do not reimplement Roland disk loading. A direct SCSI-to-wave transfer does not deinterleave stereo WAV, and the observed disk path assumes native block/state preparation. The next investigation is the RAM-to-wave helper and its caller, followed by a bounded private invocation with exact write extents. No callable service has been approved for importer use yet, no firmware bytes changed, and no code-size savings are claimed. Full WAV/stereo sizing and BS1 remain open.

[Evidence](../condensed/validation/bluescsi-loader-reuse-2026-10-18.json).


### RAM-to-wave helper boundary

Checkpoint29 byte-checks70 instructions across five original-OS spans (213 bytes), clarifying the RAM-to-wave reuse boundary. All ranges are end-exclusive and use page005A; file=4800+(page<<10)+(logical&3FFF).

| Routine | Established static behavior | Importer consequence |
| --- | --- | --- |
| 6A31..6A7C | Destination words come from RW2C/RW2E; source is fixed physical0EC002; count is fixed2400 hex bytes; controlBC; waits for0118=0 | Copies9216 bytes, so cannot directly consume the proposed4096-byte buffer |
| 70DF..7113 | Sets1200 wave words, advances destination globals, doubles count to2400 bytes and calls005A:73C1 throughCE14 | Native block mover prepares state outside the helper; not a general WAV writer |
| 7113..7132 | Doubles RW42 into byte count, writes R48 as DMA control and waits for0118=0 | Paired read-side caller suppliesA7; no deadline in this wait |
| 73C1..73E1 | Saves RWDA/RWB0, sets controlBC and fixed source0ED712, invokes7401, restores saved words; RW58 is overwritten | Destination and count must already be prepared; source is not parameterized |
| 7401..7418 | Reads011D, writes RB0 to011D, loops on0118 until zero, reads011D and returns | Small mechanism but no bounds validation, timeout or cancellation path |

Current emulator code implementsBC as contiguous CPU-RAM-to-wave copy andA7 as its inverse, preserving byte order. It accepts positive even lengths within both modeled memories, advances both addresses and clears the count synchronously. This is a driver implementation fact, not a physical timing guarantee; rejected bounds leave the count pending and therefore cannot make the native wait safe. No new guest execution is claimed by this static checkpoint.

Reuse decision: use the established DMA mechanism through a bounded importer adapter, not unchanged fixed-source/block wrappers. The adapter must validate a positive even count no larger than4096, source ownership, destination within the reserved channel, exclusive DMA ownership, caller state restoration, and failure cleanup. Timeout alone does not prove a physical DMA has stopped; abort/quiescence must be qualified before freeing its reservation. Stereo data needs deinterleaving before contiguous per-channel DMA. Do not borrow0EC002 or0ED712 without separate lifetime proof, and do not count their native allocations as free importer memory. Next is a private guest adapter and exact source/destination sentinel tests, including final partial chunks, failure and cancellation. Full code fit, native adapter ABI, physical DMA behavior and atomic stereo publication remain open.

[Evidence](../condensed/validation/bluescsi-ram-wave-reuse-2026-10-18.json).


### Native bounded-write diagnostic (checkpoint30, 2026-10-18)

Checkpoint30 runs a private guest RAM-to-wave adapter through the ordinary Save System callback after HDD Load. Three successful copies of2,4094 and4096 bytes match exactly. Six cases reject zero, odd and oversized lengths, source overrun, destination overrun and cancellation before launch. Each case checks its complete8192-byte destination/sentinel region:73728 exact bytes total. The DMA log matches18 initialization writes plus exactly three accepted payload writes; rejected cases perform no payload DMA. All119808 existing HDD sample bytes remain exact, the disk export is unchanged, and playback/release before the diagnostic passes.

The adapter occupies145 bytes for validation and80 for setup/polling, inside a1305-byte diagnostic harness. It uses the4096-byte RAM workspace at physical004940, explicit byte counts and word destinations in a fixed high-word1 test arena. Count polling is capped at256 iterations. These are prototype sizes, not a production32-bit API or combined browser fit. Interrupts remain masked during this diagnostic; no realtime responsiveness is claimed. Timeout return does not prove DMA abort/quiescence, and this run exercises neither stalled DMA nor cancellation after launch. Allocation ownership and atomic stereo publication remain open.

BUG-126 affected the first diagnostic image: results at005900 overlapped the source tail and were overwritten by later pattern fills. The observed first result64028 fails acceptance. V2 places results at005A00 and the marker at005AF0; all nine cases then pass. This fixes a private harness layout error, not original firmware. The accepted image SHA256 is89bccdd29734d10dd1e3fa80c0144e848c7bc21f9cdb880f06f5b1043843c0ac. Original firmware is unchanged. Next: generalize channel-address bounds, perform deinterleaving with distinct L/R fixtures, and qualify ownership/abort before integrating this adapter. BS1 remains OPEN. [Evidence](../condensed/validation/bluescsi-wave-adapter-2026-10-18.json).
