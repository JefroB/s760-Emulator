# Native rack media library

The embedded rack uses the same native floppy insertion and plugin checkpoint
as the audio engine. Its layout is unchanged.

## Choose a library

1. Press Gotek **Select** to open the existing image dialog.
2. Enter **Media folder**, then press **Scan folder**. Subfolders are included.
3. Choose **Library images**, or browse with Gotek Up/Down/encoder.
4. Press **Insert** to request the chosen image. The firmware still loads its
   contents through Disk/Load; selecting or scanning never loads a patch.

The startup folder is `<runtime root>/roms/FDD`. `.img` matching is case
insensitive. Discovery is sorted and does not follow symlinks. Limits are 1,024
images, 100,000 visited directory entries, depth32 and 4,096 bytes per path.
An invalid, inaccessible or oversized scan reports an error and keeps the prior
library. These are explicit limits, not silent truncation.

## Selection and recall

The host owns the folder, inventory, browse selection and inserted-source path.
The selected item can differ from the inserted disk. Both survive closing and
reopening the editor. Failed insertion retains the previous inserted label.

Native VST state version2 saves this metadata with the machine, pending MIDI,
resampler and PCM queues. Recall restores captured media bytes without remounting
or reopening a source image. A moved library/source does not prevent playback
from the checkpoint. To insert another image after moving files, scan the new
folder or enter its new path. Old version1 states remain readable but have an
unknown media label; no boot-disk identity is invented for them.

Hosts must suspend processing before state operations, as required by the
existing native state contract. Metadata is validated before machine restore;
corrupt archives are rejected. No disk writes are made to the source library.

## Qualification — 2026-10-11

SoundCheck native VST editor: configured recursive scan, rejected missing folder
without mutation, successful/failed insertion, uninserted selection across
close/reopen, screenshots and plugin removal pass.

Native VST state callbacks: original firmware loads ROBOFULL, saves pending-note
and active-note states, and restores into fresh native instances. Configured
folder, selection, inserted identity and inventory agree. A relocated private
library and mounted source do not affect exact playback: 240,000 stereo frames
at48kHz agree, with note-off silence, repeated recall and corruption rejection.
This qualifies the native state callbacks; it is not a claim about every DAW's
project workflow or the separate loaded-sample SoundCheck audio gate.

[Machine-readable evidence](../../condensed/validation/milestone-2-media-library-2026-10-11.json).
