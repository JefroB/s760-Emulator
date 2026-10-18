#!/usr/bin/env python3
"""Patch the original Roland S-760 OS 2.24 System Disk (S760224.IMG)
to add the 4th selectable controller option: mode 3 = 'GB-6 +CRT' (while preserving
Mode 1 = Mouse+CRT and Mode 2 = RC100+CRT).

Never modifies the original S760224.IMG in place.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_gb6_combo import (
    DEFAULT_OS_SOURCE,
    DEFAULT_OUT_DIR,
    OS_SOURCE_SHA256,
    patch_os_disk_bytes,
)


def patch_os_disk_file(
    source_path: Path = DEFAULT_OS_SOURCE,
    output_path: Path | None = None,
    profile: str = "v9",
    overwrite: bool = True,
) -> dict[str, object]:
    source = Path(source_path).resolve()
    out = (
        Path(output_path).resolve()
        if output_path
        else (DEFAULT_OUT_DIR / f"S760224.GB6-SELECTABLE-{profile}.IMG").resolve()
    )
    if out == source:
        raise ValueError("Output path must never equal the original S760224.IMG source file")

    orig = source.read_bytes()
    patched = patch_os_disk_bytes(orig, profile=profile)

    out.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if overwrite else "xb"
    with out.open(mode) as f:
        f.write(patched)

    diff_bytes = sum(1 for a, b in zip(orig, patched) if a != b)
    return {
        "profile": profile,
        "os_source": str(source),
        "os_source_sha256": OS_SOURCE_SHA256,
        "os_output": str(out),
        "os_output_sha256": hashlib.sha256(patched).hexdigest(),
        "os_size": len(patched),
        "os_diff_bytes": diff_bytes,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_OS_SOURCE, help="Path to unmodified S760224.IMG")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output path for patched OS 2.24 disk image (defaults to temp/work/gb6_combo/S760224.GB6-SELECTABLE-<profile>.IMG)",
    )
    parser.add_argument(
        "--profile",
        choices=("v8", "v9"),
        default="v9",
        help="GB-6 scaling profile: v9 (equal X*4, Y*4) or v8 (wider X*8, Y*4)",
    )
    args = parser.parse_args()
    report = patch_os_disk_file(
        source_path=args.input,
        output_path=args.output,
        profile=args.profile,
        overwrite=True,
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
