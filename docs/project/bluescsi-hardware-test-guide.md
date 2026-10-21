# S-760 Image Library: first hardware test

This is an **experimental hardware-test candidate**, not a completed IM1 or
release qualification. The native UI/load/save and recovery evidence is recorded
in the [mounting roadmap](bluescsi-image-mount-plan.md). Complete stack/alias
proofs and physical media/configuration acceptance remain separate.

## OS disk

Build the [GB-6 + SCSI patch bundle](../../patches/gb6-scsi/README.md)
from your original firmware. Its default output folder is
`temp/work/patches/gb6-scsi/`.

- `S760224-BS-IM1.IMG`: patched 1,474,560-byte OS floppy image.
- SHA256: `606e277e5f11a4ca1b59dadaf4e9a8395e6c8eed1e3674b4efa78bf3bf1767e4`.
- `SHA256SUMS.txt` and `bluescsi.example.ini` accompany it.

Put the OS image on the Gotek USB and select it using your usual system-disk
boot procedure. Keep your already working GB-6 boot ROM installed. This OS
retains the **GB-6 v9** code; this handoff does not require another ROM burn.
The OS floppy image is separate from the HDD image collection below.

## SD-card layout

Use these exact directories immediately under the BlueSCSI SD-card root:

```text
SD root/
  bluescsi.ini
  CD1/
    Roland01.iso
    ... up to 100 ISO images
  CD2/
    Work01.img
    ... up to 100 compatible HDD images
  CD3/
    Roland02.iso
    ... up to 100 ISO images
  CD6/
    Roland03.iso
    ... up to 100 ISO images
```

| Folder | Browser collection | Target class | Sector size |
| :-- | :-- | :-- | --: |
| CD1 | ISO A, ID1 | CD-ROM | 2048 |
| CD2 | IMG, ID2 | Hard disk | 512 |
| CD3 | ISO B, ID3 | CD-ROM | 2048 |
| CD6 | ISO C, ID6 | CD-ROM | 2048 |

**The HDD folder is named `CD2` intentionally.** The Toolbox picker looks in
`CD<target ID>` even when that target is a hard disk. Renaming it `HD2` or using
arbitrary nested folders does not redirect the picker. The four-button target
map is fixed in this candidate: capacity is 300 ISO images plus 100 HDD images.
[Command/source contract](bluescsi-image-mount-protocol.md).

For the first test, start with one known-good image in each collection you will
use. Keep each filename within **32 printable ASCII characters including the
extension**, beginning with a letter or digit. Avoid numeric underscore names
such as `Disc_512.iso`, which can override sector size. Keep folders flat and
image-only: no subfolders, text files, covers, cue sheets or other sidecars.
The conservative supported limit is 100 total entries per collection.

## BlueSCSI configuration

Merge the accompanying example's sections into your existing `bluescsi.ini`;
replace the example filenames with files actually present. It explicitly sets
IDs1/3/6 to `Type=2`, `BlockSize=2048`, and ID2 to `Type=0`, `BlockSize=512`.
Each `Img0` points at an initial image in the corresponding folder. Preserve
other devices/settings you use and resolve duplicate IDs. The S-760 self ID
must differ from1/2/3/6; use7 if available.

These keys are documented in the [official configuration reference](https://bluescsi.com/docs/bluescsi.ini).
The [current disk implementation](https://github.com/BlueSCSI/BlueSCSI-v2/blob/main/src/BlueSCSI_disk.cpp)
applies the configured device type and preserves it when switching images.
This template is source-reviewed; the actual board configuration still needs
hardware verification. `ImgDir` does not change the Toolbox picker's folder.

When the card is connected to the computer, run the existing read-only checker
from `D:\S-760`, substituting the SD drive and actual sampler ID:

```powershell
python scripts/bluescsi_image_preflight.py E:\ --self-id 7
```

See the [preflight rules](bluescsi-library-preflight.md). Passing does not verify
the Roland filesystem or the board's target configuration. The stock-firmware
error-reporting fixes reviewed locally are not assumed to be installed on your
BlueSCSI; do not flash anything as part of this first test.

## Test order

1. Record the BlueSCSI firmware version and configured target IDs/sector sizes
   from its `log.txt`; note the S-760 self ID and controller mode.
2. Boot this OS disk. Confirm GB-6 selection still works, then open **Disk** to
   reach **Image Library / Collections**. ISO A, IMG, ISO B and ISO C should
   correspond to IDs1/2/3/6.
3. Open a populated ISO collection. Confirm the displayed filenames match that
   folder. Select a known image: the browser should hand off to native Disk
   Load. Load a familiar performance and check its samples and playback.
4. Repeat with a different ISO collection. With more than seven entries, check
   Next, Previous and Collections. Exit and reopen the browser.
5. Select a **spare copy** of a known compatible HDD image from CD2. Confirm
   native Load/playback, then Save a small recognizable change. Select another
   image, reselect the test HDD image, and load again to verify persistence.
   ISO collections should remain read-only. Do not use Initialize, Format,
   Delete or Optimize during this first round.
6. Restart the sampler and repeat explicit selection/Load. Do not assume the
   selected image survives a BlueSCSI reset. Do not deliberately cut power
   during a write; emulator soft-reset evidence is not a physical write test.

Report the first failing step, exact screen/message, selected collection and
filename, and the relevant BlueSCSI log. On a SCSI error or uncertain mount,
stop the test before saving and re-establish the selected image explicitly.
