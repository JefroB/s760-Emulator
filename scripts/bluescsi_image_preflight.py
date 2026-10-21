"""Read-only preflight for the S-760 IM1 BlueSCSI CD<id> library profile.

Checks names, layout and sector alignment, without opening image contents,
changing files or claiming that the S-760 can load the image format.
"""
import argparse
import json
import os
from pathlib import Path
import re

DEFAULT_COLLECTIONS = {1: "iso", 2: "img", 3: "iso", 6: "iso"}
SCOPE = "library naming/layout only; no image-format or hardware qualification"


def issue(code, path, message):
    return {"code": code, "path": str(path), "message": message}


def check_names(names, kind, folder):
    """Strict first-profile policy; intentionally narrower than BlueSCSI's filter."""
    errors = []
    displays = {}
    for name in names:
        path = f"{folder}/{name}"
        raw = name.encode("utf-8", errors="surrogatepass")
        if any(ord(c) < 32 or ord(c) > 126 for c in name):
            errors.append(issue("name-characters", path, "Use printable ASCII in image names."))
        if any(c in '<>:"/\\|?*' for c in name) or name.endswith((" ", ".")):
            errors.append(issue("fat-name", path, "Use a portable FAT filename without reserved characters or a trailing space/dot."))
        if not name or not re.match(r"[A-Za-z0-9]", name):
            errors.append(issue("name-start", path, "Start the name with an ASCII letter or digit; BlueSCSI skips other names."))
        if len(raw) > 32:
            errors.append(issue("name-length", path, "Rename to at most 32 ASCII bytes including the extension so the entire name is visible."))
        if len(folder.encode("ascii")) + 1 + len(raw) >= 64:
            errors.append(issue("path-length", path, "CD<id>/name must fit in 63 bytes plus NUL (upstream BUG-146)."))
        if Path(name).suffix.lower() != "." + kind:
            errors.append(issue("extension", path, f"Keep only .{kind} images in this collection; remove sidecars and other types."))
        # The pinned upstream getBlockSize parses the first underscore using
        # strtoul. Reject qualifying numeric prefixes even when they happen to
        # equal the default: this profile uses the configured target geometry.
        tail = name.partition("_")[2]
        match = re.match(r"\s*\+?([0-9]+)", tail, flags=re.ASCII)
        if match and 8 <= int(match[1]) <= 65536:
            errors.append(issue("block-size-override", path, "Rename the first underscore followed by a sector-size number; BlueSCSI derives block size from it."))
        display = raw[:32].lower()
        if display in displays:
            errors.append(issue("display-collision", path, f"First 32 display bytes collide with {displays[display]!r}; give both images distinct visible names."))
        else:
            displays[display] = name
    return errors


def linked(path):
    return path.is_symlink() or getattr(os.path, "isjunction", lambda p: False)(path)


def scan_library(root, *, self_id, collections=None):
    root = Path(root).absolute()
    collections = DEFAULT_COLLECTIONS if collections is None else collections
    errors, warnings, rows = [], [], []
    result = {"schema": 1, "scope": SCOPE, "root": str(root), "self_id": self_id,
              "collections": rows, "errors": errors, "warnings": warnings}
    valid_map = (type(self_id) is int and 0 <= self_id <= 7 and bool(collections)
                 and all(type(t) is int and 0 <= t <= 7 and k in ("iso", "img")
                         for t, k in collections.items()))
    if not valid_map:
        errors.append(issue("target-map", root, "Specify self ID and distinct collection target IDs in 0..7, with iso/img roles."))
    elif self_id in collections:
        errors.append(issue("self-id-collision", root, "A collection uses the sampler's own SCSI ID; choose a different target map."))
    if errors:
        result["passed"] = False
        return result
    if linked(root) or not root.is_dir():
        errors.append(issue("root", root, "Provide an existing SD root directory, not a symbolic link or junction."))
        result["passed"] = False
        return result
    for target, kind in sorted(collections.items()):
        folder = root / f"CD{target}"
        if linked(folder) or not folder.is_dir():
            errors.append(issue("missing-collection", folder, "Provide this real directory at the SD root; links/junctions are unsupported."))
            continue
        try:
            entries = sorted(folder.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            errors.append(issue("read-error", folder, str(exc)))
            continue
        row = {"target": target, "kind": kind, "folder": folder.name,
               "entry_count": len(entries), "image_count": 0, "sector_bytes": 2048 if kind == "iso" else 512}
        rows.append(row)
        if len(entries) > 100:
            errors.append(issue("entry-limit", folder, f"Found {len(entries)} entries; this profile allows at most 100 total entries per leaf."))
        names = []
        for entry in entries:
            try:
                if linked(entry):
                    errors.append(issue("linked-entry", entry, "Replace links/junctions with real image files."))
                elif entry.is_dir():
                    errors.append(issue("nested-folder", entry, "Move images into a configured CD<id> leaf; stock D7/D8 do not traverse folders."))
                elif not entry.is_file():
                    errors.append(issue("entry-type", entry, "Only regular image files are supported."))
                else:
                    names.append(entry.name)
                    size = entry.stat().st_size
                    if entry.suffix.lower() == "." + kind:
                        row["image_count"] += 1
                        if not size:
                            errors.append(issue("empty-image", entry, "Replace the empty file with a complete disk image."))
                        elif size % row["sector_bytes"]:
                            errors.append(issue("sector-alignment", entry, f"Size {size} is not a multiple of the profile's {row['sector_bytes']}-byte sectors; qualify its geometry separately."))
            except OSError as exc:
                errors.append(issue("read-error", entry, str(exc)))
        errors.extend(check_names(names, kind, folder.name))
        if not entries:
            warnings.append(issue("empty-collection", folder, "The collection is empty; the browser will show no images."))
    result["passed"] = not errors
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path, help="SD root, containing CD1, CD2, etc.")
    parser.add_argument("--self-id", type=int, required=True, help="Sampler's actual SCSI ID (0..7).")
    parser.add_argument("--collection", action="append", metavar="ID:iso|img", help="Repeat for an explicit target map; default 1:iso,2:img,3:iso,6:iso.")
    parser.add_argument("--json", action="store_true", help="Print a machine-readable report to stdout.")
    args = parser.parse_args()
    mapping = None
    if args.collection:
        mapping = {}
        for value in args.collection:
            try:
                target, kind = value.split(":")
                target = int(target)
                if target in mapping or kind not in ("iso", "img") or not 0 <= target <= 7:
                    raise ValueError
                mapping[target] = kind
            except ValueError:
                parser.error("--collection must be a unique ID:iso or ID:img with ID in 0..7")
    report = scan_library(args.root, self_id=args.self_id, collections=mapping)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print("PASS" if report["passed"] else "FAIL", "-", SCOPE)
        for row in report["collections"]:
            print(f"{row['folder']}: {row['image_count']} .{row['kind']} images, {row['entry_count']}/100 entries")
        for group in ("errors", "warnings"):
            for item in report[group]:
                print(f"{group[:-1].upper()} [{item['code']}] {item['path']}: {item['message']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
