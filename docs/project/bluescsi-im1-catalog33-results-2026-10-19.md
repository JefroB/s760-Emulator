# IM1 compact catalog and code headroom

The native candidate retains each D7 mount index and all32 filename bytes in33 bytes per image, dropping only wire byte1. The pinned stock onListFiles(...,true) skips directories before emitting that byte, so it is always1 on this path. Wire records remain40 bytes; all4000 bytes are drained and validated. This representation is specific to the image picker, not D0 folder browsing.

Catalog storage falls3400 ->3300 bytes. Its physical start moves4B80 ->4BE0 (data alias4FE0); resources stay58D0. Replacing index*34 with index*33 saves three code bytes, exactly funding the skip-type check. Code remains2814 bytes. Mandatory GB-6 v9 and all retained SDS fixes remain disjoint.

Named fit is **7776/8002 bytes**, leaving226 total: gaps3/98/12/13/100. **98 bytes directly follow code**, up from2. This is useful headroom, not complete-fit GO.

The exact candidate passes ordinary native GB-6 input for0/1/100-entry catalogs, rejects101, compares all retained bytes including32-byte filenames, preserves code and immutable originals, and rebuilds identically. Cancellation/retry, failed D8 open and same-/other-target recovery, exact native Load/playback and retained SDS cancel/retry pass. Incoming SDS during D7 drains then returns Busy; incoming SDS during D8/readiness leaves drive unchanged and queues no Load, with explicit recovery afterward. All128 realtime MIDI clocks arrive before D7 completes. Library hashes remain unchanged in the hash-protected workflows.

General disk and remote/local SDS sender admission remains open. Native1FA4 is the manufacturer41 Remote Mode session flag, not a generic disk-busy flag; the admission work must trace actual foreground/modal ownership. Full stack/ISR bounds, UI/filename policy, IMG/stereo/controller/cache/reset/Save and physical acceptance remain open. No new physical or worst-case timing claim follows from these tests.

Candidate SHA-256: `b299af70002fb4e16177179bab3cf8b38a51bab03aaa3d7ed9cc1b422d7184d7`. Selectable boot ROM remains `a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb`; no additional boot-ROM patch. The previous IRQ timing measurements remain evidence on their previous hash. No runtime/emulator source changed.

[Validation](../condensed/validation/bluescsi-im1-catalog33-2026-10-19.json). [Active roadmap](bluescsi-image-mount-plan.md).
