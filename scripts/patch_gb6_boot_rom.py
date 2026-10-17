#!/usr/bin/env python3
"""Patch the original Roland S-760 IC15 Boot ROM v1.11 (Roland_S-760_v1.11.BIN)
to add the 4th selectable controller option: mode 3 = 'GB-6 +CRT'.

Never modifies the original source ROM in place.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from build_gb6_combo import (
    BOOT_SOURCE_SHA256,
    DEFAULT_BOOT_SOURCE,
    DEFAULT_OUT_DIR,
    patch_boot_rom_bytes,
)


def patch_boot_rom_file(
    source_path: Path = DEFAULT_BOOT_SOURCE,
    output_path: Path | None = None,
    overwrite: bool = True,
) -> dict[str, object]:
    source = Path(source_path).resolve()
    out = Path(output_path).resolve() if output_path else (DEFAULT_OUT_DIR / "Roland_S-760_v1.11.GB6.BIN").resolve()
    if out == source:
        raise ValueError("Output path must never equal the original Boot ROM source file")

    orig = source.read_bytes()
    patched = patch_boot_rom_bytes(orig)

    out.parent.mkdir(parents=True, exist_ok=True)
    mode = "wb" if overwrite else "xb"
    with out.open(mode) as f:
        f.write(patched)

    diff_offsets = [i for i, (a, b) in enumerate(zip(orig, patched)) if a != b]
    return {
        "boot_source": str(source),
        "boot_source_sha256": BOOT_SOURCE_SHA256,
        "boot_output": str(out),
        "boot_output_sha256": hashlib.sha256(patched).hexdigest(),
        "boot_size": len(patched),
        "boot_diff_bytes": len(diff_offsets),
        "boot_diff_offsets_hex": [f"0x{off:04X}" for off in diff_offsets],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_BOOT_SOURCE, help="Path to unmodified Roland_S-760_v1.11.BIN")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUT_DIR / "Roland_S-760_v1.11.GB6.BIN",
        help="Output path for patched IC15 Boot ROM (.BIN)",
    )
    args = parser.parse_args()
    report = patch_boot_rom_file(source_path=args.input, output_path=args.output, overwrite=True)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
