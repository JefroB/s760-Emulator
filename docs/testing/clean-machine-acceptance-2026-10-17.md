# Clean-machine handoff acceptance — 2026-10-17

The user accepted the clean-machine handoff and closed this gate on 2026-10-17
under a reduced, explicitly approved scope.

## Observations reported by the user

The GitHub acceptance ZIP was downloaded and extracted with File Explorer on a
separate clean Windows machine. The first launch failed at the packaged .NET
initializer (BUG-105). After receiving the unblocking/re-extraction instructions,
the user reported that the executable runs, launches and finds both the IC15 ROM
and system disk. The user did not identify which remediation was performed.

The accepted archive SHA-256 is
`b1dd036c9331058fb2db0dde75d038e985fc75d5919c19040766460f5cdb08f9`.
Windows version, prerequisite installation history and device-driver identities
were not supplied with this report.

## User-approved scope

The user had no sample disk on that machine and explicitly accepted the handoff
without the remaining load/play/edit/sample/save/restore repetitions. Those
steps are **waived for this gate**, not reported as observed passes. Earlier
workstation workflow evidence retains its original environment and scope.

This closes the clean-machine handoff/setup gate by user acceptance. It does not
create missing test recordings, complete historical manual result files, claim
another DAW was tested, or qualify a final release tag. Later package revisions
retain their own identity and workstation verification records; they are not
implicitly reported as executed on this clean machine.

The default-media-folder/IMG-or-OUT update is delivered as a separate package
revision so the accepted archive and its evidence remain recoverable.
