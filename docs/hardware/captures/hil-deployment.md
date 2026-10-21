# Preparing physical hardware experiments

Use the media and controller configuration already verified for the target S-760. Record the firmware, storage emulator model/firmware, selected image, SCSI IDs where applicable and MIDI/audio routing. Device configuration options are version-specific; use the device's own documentation rather than copying the former speculative FlashFloppy configuration from this repository.

Keep a known-good boot medium and a backup of writable media. Build each experiment into a separate output image, inspect its identity and format, and follow the capture recipe's loading instructions. The OS system disk and sample disks are different containers: this project uses a 1.44 MB OS image and 720 KiB sample images for the documented sample-disk builder. Do not assume that an arbitrary IMG has either format or overwrite boot media with a test payload.

The [TVFSTEP guide](tvf-transition-capture.md) names its builder and paired MIDI file. Confirm the loaded performance and routing on the physical screens before recording. Preserve the original capture and record setup differences from the recipe. A successfully generated image or native load verifies preparation only; physical acceptance requires the actual hardware result.

See [capture methodology](hardware-recording-parity-methodology.md), [manufacturer documentation](../ic-documentation-index.md), and the [project roadmap](../../project/completion-roadmap.md) for separately scoped hardware acceptance. No guessed USB filesystem, FlashFloppy setting or unverified deployment command is required by this guide.
