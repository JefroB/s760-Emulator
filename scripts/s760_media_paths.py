"""Default user-supplied media locations in a portable standalone package."""
from pathlib import Path
import shutil

ROM_FOLDERS = ('BOOT', 'System', 'FDD', 'SCSI')


def discover_image(folder, preferred, suffixes, size):
    """Prefer known filenames; accept a single correctly sized alternative."""
    folder = Path(folder)
    files = sorted((p for p in folder.glob('*') if p.is_file()), key=lambda p: p.name.casefold())
    candidates = [p for p in files if p.suffix.lower() in suffixes and p.stat().st_size == size]
    for name in preferred:
        match = next((p for p in candidates if p.name.casefold() == name.casefold()), None)
        if match is not None:
            return match
    return candidates[0] if len(candidates) == 1 else folder / preferred[0]


def default_media_paths(root):
    root = Path(root) / 'roms'
    return {
        'bootRom': discover_image(root / 'BOOT', ('Roland_S-760_v1.11.BIN',), ('.bin', '.rom'), 32768),
        'systemDisk': discover_image(root / 'System', ('S760224.IMG', 'S760224.OUT'), ('.img', '.out'), 1474560),
        'mediaDirectory': root / 'FDD',
    }


def stage_scsi_library(library, state):
    """Seed private backing media without replacing an instance's existing disks."""
    library, destination = Path(library), Path(state) / 'roms' / 'SCSI'
    for source in sorted(library.glob('*')):
        if source.is_symlink() or not source.is_file() or source.suffix.lower() not in ('.img', '.iso', '.hda'):
            continue
        destination.mkdir(parents=True, exist_ok=True)
        target = destination / source.name
        if not target.exists():
            # Exclusive creation preserves an existing disk even during a race.
            created = False
            try:
                with source.open('rb') as incoming, target.open('xb') as outgoing:
                    created = True
                    shutil.copyfileobj(incoming, outgoing)
            except FileExistsError:
                continue
            except BaseException:
                if created and target.exists():
                    target.unlink()
                raise
