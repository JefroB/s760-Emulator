"""Compatibility entry point; maintained implementation: patches/boot-rom/patch_gb6_boot_rom.py."""
from pathlib import Path as _Path
import sys as _sys
_impl = _Path(__file__).resolve().parents[1] / "patches/boot-rom/patch_gb6_boot_rom.py"
_sys.path.insert(0, str(_impl.parent))
__file__ = str(_impl)
exec(compile(_impl.read_text(encoding="utf-8"), __file__, "exec"), globals())
