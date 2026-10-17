"""Portable media discovery uses byte-compatible OUT images without conversion."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from s760_media_paths import default_media_paths, stage_scsi_library


def test_roland_out_and_alternate_boot_name_are_discovered(tmp_path):
    boot = tmp_path / 'roms/BOOT/IC15.rom'
    system = tmp_path / 'roms/System/s760_224.OUT'
    boot.parent.mkdir(parents=True)
    system.parent.mkdir(parents=True)
    boot.write_bytes(bytes(32768))
    system.write_bytes(bytes(1474560))
    defaults = default_media_paths(tmp_path)
    assert defaults['bootRom'] == boot
    assert defaults['systemDisk'] == system
    assert defaults['mediaDirectory'] == tmp_path / 'roms/FDD'


def test_img_precedence_ambiguity_and_invalid_size(tmp_path):
    folder = tmp_path / 'roms/System'
    folder.mkdir(parents=True)
    (folder / 'one.OUT').write_bytes(bytes(1474560))
    (folder / 'two.img').write_bytes(bytes(1474560))
    assert default_media_paths(tmp_path)['systemDisk'] == folder / 'S760224.IMG'
    (folder / 'S760224.out').write_bytes(bytes(1474560))
    assert default_media_paths(tmp_path)['systemDisk'] == folder / 'S760224.out'
    (folder / 's760224.img').write_bytes(bytes(1474560))
    assert default_media_paths(tmp_path)['systemDisk'] == folder / 's760224.img'
    (folder / 's760224.img').write_bytes(b'invalid')
    assert default_media_paths(tmp_path)['systemDisk'] == folder / 'S760224.out'


def test_scsi_defaults_never_overwrite_private_disk_edits(tmp_path):
    library, state = tmp_path / 'library', tmp_path / 'state'
    library.mkdir()
    (library / 'HD0.img').write_bytes(b'original library')
    (library / 'CD1.iso').write_bytes(b'CD image')
    (library / 'README.txt').write_text('not a disk')
    stage_scsi_library(library, state)
    private = state / 'roms/SCSI/HD0.img'
    private.write_bytes(b'user edits')
    stage_scsi_library(library, state)
    assert private.read_bytes() == b'user edits'
    assert (state / 'roms/SCSI/CD1.iso').read_bytes() == b'CD image'
    assert not (state / 'roms/SCSI/README.txt').exists()
    assert (library / 'HD0.img').read_bytes() == b'original library'
