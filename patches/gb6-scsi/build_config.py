"""Input/output paths provided by the public build.py entry point."""
import os
from pathlib import Path
SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]
OS_SOURCE = Path(os.environ["S760_PATCH_OS_INPUT"])
BOOT_SOURCE = Path(os.environ["S760_PATCH_BOOT_INPUT"])
OUTPUT = Path(os.environ["S760_PATCH_OUTPUT"])
