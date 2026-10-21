"""Reproduce the GB-6 + SCSI hardware-test candidate from user-owned originals."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
OS_SHA256 = "606e277e5f11a4ca1b59dadaf4e9a8395e6c8eed1e3674b4efa78bf3bf1767e4"
BOOT_SHA256 = "a0a980e284f18ee6f6854c3b37a1d88c06dd21548fb7ae488ac213c47798c2fb"
BASELINES = (
    (32768, "ef3b095445bbc1213e1b7ab38dc32a12dc2a0cb6aee3a7b845ff648c1941efc6"),
    (1474560, "3827ed4c46fd48abbec3095266164853033141d7bd15afe8dda0050d00e073cd"),
)


def build(boot_input: Path, os_input: Path, out_dir: Path) -> dict:
    boot_input, os_input, out_dir = (p.resolve() for p in (boot_input, os_input, out_dir))
    for path, (size, digest) in zip((boot_input, os_input), BASELINES):
        data = path.read_bytes()
        if len(data) != size or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError(f"Unrecognized original firmware: {path}")
    # A fresh directory prevents replacing existing outputs or either original.
    out_dir.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, S760_PATCH_BOOT_INPUT=str(boot_input),
               S760_PATCH_OS_INPUT=str(os_input), S760_PATCH_OUTPUT=str(out_dir))
    for helper in ("build_browser.py", "build_full.py"):
        subprocess.run([sys.executable, str(SOURCE / helper)], env=env, check=True)
    files = (("full.img", "S760224-BS-IM1.IMG", OS_SHA256),
             ("gb6.bin", "Roland_S-760_v1.11.GB6.BIN", BOOT_SHA256))
    for intermediate, name, digest in files:
        path = out_dir / intermediate
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise ValueError(f"Candidate hash mismatch: {intermediate}")
        path.rename(out_dir / name)
    manifest = dict(qualification="Experimental hardware-test candidate; IM1 incomplete",
                    os_file=files[0][1], os_bytes=1474560, os_sha256=OS_SHA256,
                    boot_file=files[1][1], boot_bytes=32768, boot_sha256=BOOT_SHA256,
                    gb6="Selectable v9 X4/Y4; same Boot ROM as GB-6-only",
                    hardware_guide="docs/project/bluescsi-hardware-test-guide.md")
    (out_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    (out_dir / "SHA256SUMS.txt").write_text("".join(f"{digest}  {name}\n" for _, name, digest in files))
    shutil.copyfile(SOURCE / "bluescsi.example.ini", out_dir / "bluescsi.example.ini")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--boot-input", type=Path, default=ROOT / "roms/BOOT/Roland_S-760_v1.11.BIN")
    parser.add_argument("--os-input", type=Path, default=ROOT / "S760224.IMG")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "temp/work/patches/gb6-scsi")
    args = parser.parse_args()
    print(json.dumps(build(args.boot_input, args.os_input, args.out_dir), indent=2))


if __name__ == "__main__":
    main()
