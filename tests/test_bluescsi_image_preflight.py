"""Read-only library policy checks; these do not qualify image contents."""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("preflight", ROOT / "scripts/bluescsi_image_preflight.py")


def module():
    m = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(m)
    return m


def library(tmp_path, names=("Disc.iso",)):
    folder = tmp_path / "CD1"
    folder.mkdir()
    for name in names:
        (folder / name).write_bytes(bytes(2048))
    return folder


def check(tmp_path):
    return module().scan_library(tmp_path, self_id=7, collections={1: "iso"})


def codes(result):
    return {i["code"] for i in result["errors"]}


def test_valid_full_visible_name_and_read_only(tmp_path):
    name = "A" * 28 + ".iso"
    folder = library(tmp_path, [name])
    before = {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in folder.iterdir()}
    result = check(tmp_path)
    assert result["passed"] and result["collections"][0]["image_count"] == 1
    assert before == {p.name: (p.read_bytes(), p.stat().st_mtime_ns) for p in folder.iterdir()}
    assert result["scope"] == "library naming/layout only; no image-format or hardware qualification"


def test_100_passes_101_fails(tmp_path):
    folder = library(tmp_path, [f"Disc{i:03}.iso" for i in range(100)])
    assert check(tmp_path)["passed"]
    (folder / "Extra.iso").write_bytes(bytes(2048))
    assert "entry-limit" in codes(check(tmp_path))


def test_empty_collection_is_visible_warning(tmp_path):
    library(tmp_path, [])
    result = check(tmp_path)
    assert result["passed"] and result["warnings"][0]["code"] == "empty-collection"


def test_bug145_both_directions_are_rejected(tmp_path):
    library(tmp_path, ["A" * 29 + ".txt", "B" * 28 + ".txt.iso", "Z.iso"])
    result = check(tmp_path)
    assert {"name-length", "extension"} <= codes(result)
    assert not result["passed"]


def test_prefix_collision_and_64_byte_path_rejected(tmp_path):
    library(tmp_path, ["A" * 55 + "1.iso", "A" * 55 + "2.iso"])
    assert {"display-collision", "path-length", "name-length"} <= codes(check(tmp_path))


def test_non_ascii_and_unselectable_names(tmp_path):
    library(tmp_path, ["Caf\u00e9.iso", "_Disc.iso", ".Hidden.iso", " Space.iso"])
    assert {"name-characters", "name-start"} <= codes(check(tmp_path))


def test_wrong_type_nested_folder_and_hidden_sidecar(tmp_path):
    folder = library(tmp_path, ["Disk.img", "Readme.txt", ".DS_Store"])
    (folder / "More").mkdir()
    assert {"extension", "nested-folder", "name-start"} <= codes(check(tmp_path))


def test_block_size_override_rejected(tmp_path):
    library(tmp_path, ["Disc_512.iso", "Disc_2048.iso", "Disc_8more.iso"])
    result = check(tmp_path)
    assert sum(i["code"] == "block-size-override" for i in result["errors"]) == 3


def test_ordinary_underscore_is_allowed(tmp_path):
    library(tmp_path, ["Disc_Collection.iso", "Disc_1.iso", "Disc_65537.iso"])
    assert check(tmp_path)["passed"]


def test_size_must_be_nonzero_and_aligned(tmp_path):
    folder = library(tmp_path)
    (folder / "Disc.iso").write_bytes(b"bad")
    assert "sector-alignment" in codes(check(tmp_path))
    (folder / "Disc.iso").write_bytes(b"")
    assert "empty-image" in codes(check(tmp_path))


def test_duplicate_case_insensitive_display_name():
    m = module()
    issues = m.check_names(["Disc.iso", "DISC.ISO"], "iso", "CD1")
    assert any(i["code"] == "display-collision" for i in issues)


def test_portable_fat_names():
    issues = module().check_names(["Bad:Disc.iso", "Bad?.iso", "Disc.iso "], "iso", "CD1")
    assert sum(i["code"] == "fat-name" for i in issues) == 3


def test_self_id_collision_and_invalid_map(tmp_path):
    library(tmp_path)
    m = module()
    assert "self-id-collision" in codes(m.scan_library(tmp_path, self_id=1, collections={1: "iso"}))
    assert "target-map" in codes(m.scan_library(tmp_path, self_id=7, collections={8: "iso"}))


def test_missing_root_and_collection_do_not_create_directories(tmp_path):
    missing = tmp_path / "missing"
    assert "root" in codes(check(missing))
    assert not missing.exists()
    assert "missing-collection" in codes(check(tmp_path))
    assert not (tmp_path / "CD1").exists()


def test_linked_entries_are_rejected_without_following(tmp_path, monkeypatch):
    folder = library(tmp_path)
    m = module()
    monkeypatch.setattr(m, "linked", lambda p: p == folder / "Disc.iso")
    assert "linked-entry" in codes(m.scan_library(tmp_path, self_id=7, collections={1: "iso"}))
    monkeypatch.setattr(m, "linked", lambda p: p == folder)
    assert "missing-collection" in codes(m.scan_library(tmp_path, self_id=7, collections={1: "iso"}))


def test_unreadable_directory_is_actionable(tmp_path, monkeypatch):
    folder = library(tmp_path)
    original = Path.iterdir
    def denied(path):
        if path == folder:
            raise PermissionError("test access denied")
        return original(path)
    monkeypatch.setattr(Path, "iterdir", denied)
    assert "read-error" in codes(check(tmp_path))


def test_four_collection_default_profile(tmp_path):
    for target, ext in [(1, "iso"), (2, "img"), (3, "iso"), (6, "iso")]:
        folder = tmp_path / f"CD{target}"
        folder.mkdir()
        (folder / f"Disc.{ext}").write_bytes(bytes(2048))
    assert module().scan_library(tmp_path, self_id=7)["passed"]


def test_cli_machine_readable_failure_and_success(tmp_path):
    library(tmp_path)
    command = [sys.executable, str(SPEC.origin), str(tmp_path), "--self-id", "7", "--collection", "1:iso", "--json"]
    p = subprocess.run(command, capture_output=True, text=True)
    assert p.returncode == 0 and json.loads(p.stdout)["passed"]
    (tmp_path / "CD1" / "Bad.txt").write_bytes(b"text")
    p = subprocess.run(command, capture_output=True, text=True)
    assert p.returncode == 1 and not json.loads(p.stdout)["passed"]
