"""Prepare BUG-137/145/146 BlueSCSI-v2 source fixes without modifying the input tree.

The generated patch modifies upstream GPL-3.0-or-later source. This script does
not build, install or flash BlueSCSI firmware. Only the pinned reviewed inputs
are accepted; different revisions require review rather than a fuzzy rewrite.
"""
from pathlib import Path
import argparse
import difflib
import hashlib
import json


REVISIONS = {
    "5e64e3b4a09088c67a2a6728385600ea67ddbe0d": {
        "BlueSCSI_Toolbox.cpp": "f945b7fdfd9681484a148dea403cef5344d44341aa4a761567be65d87323488a",
        "BlueSCSI_disk.cpp": "fd7f18accd4aaec20e6ce40c85261bbbd9fa17415ac9b4d19239e5461aced3f8",
    },
    "4d0f96fe520688c666f34e6282a2f448f340a617": {
        "BlueSCSI_Toolbox.cpp": "f945b7fdfd9681484a148dea403cef5344d44341aa4a761567be65d87323488a",
        "BlueSCSI_disk.cpp": "83c16d9c7b4f74936a060cf43f92e836c463057a87bb04befc90d90043acca26",
    },
}


def replace_once(source, before, after):
    if source.count(before) != 1:
        raise ValueError("Expected exactly one reviewed source block")
    return source.replace(before, after, 1)


def patch_toolbox(source):
    # Compare the same pre-display-truncation name used by onListFiles. Never
    # use the 32-byte wire label to decide whether an entry consumes an index.
    source = replace_once(source, '''        // truncate filename the same way listing does, before validating name
        if (len > MAX_MAC_PATH)
            name[MAX_MAC_PATH] = 0x0;
        dbgmsg("TOOLBOX COUNT FILES: truncated filename is '", name, "'");
''', '''        // Validate the same name as listing and selection, before wire truncation.
        dbgmsg("TOOLBOX COUNT FILES: filename is '", name, "'");
''')
    source = replace_once(source, '        size_t len = file.getName(name, MAX_FILE_PATH);\n        file.close();',
                          '        file.getName(name, MAX_FILE_PATH);\n        file.close();')
    source = replace_once(source, '''        // truncate filename the same way listing does, before validating name
        size_t len = file_test.getName(name, MAX_FILE_PATH);
        if (len > MAX_MAC_PATH)
            name[MAX_MAC_PATH] = 0x0;
''', '''        // Index the same pre-display-truncation name used by count and listing.
        file_test.getName(name, MAX_FILE_PATH);
''')
    return replace_once(source, '''    next_cd.getName(name, sizeof(name));
    next_cd.close();
    snprintf(full_path, (MAX_FILE_PATH * 2), "%s/%s", img_dir, name);
    switchNextImage(img, full_path);
''', '''    bool valid = next_cd.isOpen() && next_cd.getName(name, sizeof(name)) > 0;
    next_cd.close();
    int path_length = snprintf(full_path, sizeof(full_path), "%s/%s", img_dir, name);
    // The switcher accepts MAX_FILE_PATH - 1 bytes plus NUL. Reject a long
    // path before closing the current image; never mount a truncated prefix.
    if (!valid || path_length < 0 || path_length >= MAX_FILE_PATH ||
        !switchNextImage(img, full_path))
    {
        scsiDev.dataLen = 0;
        scsiDev.status = CHECK_CONDITION;
        scsiDev.target->sense.code = ILLEGAL_REQUEST;
        scsiDev.target->sense.asc = INVALID_FIELD_IN_CDB;
        scsiDev.phase = STATUS;
    }
''')


def patch_disk(source):
    return replace_once(source, '''        strncpy(filename, next_filename, MAX_FILE_PATH);
''', '''        size_t length = 0;
        while (length < sizeof(filename) && next_filename[length] != '\\0')
            ++length;
        if (length == sizeof(filename))
        {
            logmsg("Switch to next image failed because target path is too long.");
            return false;
        }
        memcpy(filename, next_filename, length + 1);
''')


def prepare(source_root, destination):
    source_root, destination = Path(source_root), Path(destination)
    names = list(next(iter(REVISIONS.values())))
    before = {name: (source_root / "src" / name).read_bytes() for name in names}
    hashes = {name: hashlib.sha256(data).hexdigest() for name, data in before.items()}
    revision = next((r for r, h in REVISIONS.items() if h == hashes), None)
    if revision is None:
        raise ValueError("Source hashes do not match either pinned BlueSCSI-v2 revision")
    patchers = {"BlueSCSI_Toolbox.cpp": patch_toolbox, "BlueSCSI_disk.cpp": patch_disk}
    after = {name: patchers[name](data.decode("utf-8")).encode("utf-8") for name, data in before.items()}
    patch = "".join("".join(difflib.unified_diff(
        before[name].decode("utf-8").splitlines(keepends=True),
        after[name].decode("utf-8").splitlines(keepends=True),
        fromfile="a/src/" + name, tofile="b/src/" + name)) for name in names)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / "src").mkdir()
    for name, data in after.items():
        (destination / "src" / name).write_bytes(data)
    (destination / "filenames.patch").write_bytes(patch.encode("utf-8"))
    manifest = {"revision": revision, "bugs": [137, 145, 146], "input_sha256": hashes,
                "output_sha256": {n: hashlib.sha256(v).hexdigest() for n, v in after.items()},
                "scope": "source patch only; no device firmware installation or hardware qualification"}
    (destination / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Pinned upstream checkout containing src/")
    parser.add_argument("destination", type=Path, help="New directory for two patched files and a diff")
    args = parser.parse_args()
    try:
        report = prepare(args.source, args.destination)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
