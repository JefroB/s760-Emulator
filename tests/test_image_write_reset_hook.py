"""One-shot, opt-in interruption of incomplete fixture WRITE DMA only."""
from pathlib import Path
import os
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_incomplete_write_reset_admission(tmp_path):
    compiler = shutil.which("cl")
    if not compiler:
        candidates = list(Path("C:/Program Files/Microsoft Visual Studio").glob(
            "*/Community/VC/Tools/MSVC/*/bin/Hostx64/x64/cl.exe"))
        compiler = str(sorted(candidates)[-1]) if candidates else None
    if not compiler:
        pytest.skip("Visual C++ compiler required")
    env = dict(os.environ)
    if not env.get("INCLUDE"):
        vcvars = Path(compiler).parents[6] / "Auxiliary/Build/vcvars64.bat"
        setup = subprocess.run(f'cmd /d /c call "{vcvars}" >nul && set', capture_output=True, text=True)
        assert setup.returncode == 0
        env.update(line.split("=", 1) for line in setup.stdout.splitlines() if "=" in line and not line.startswith("="))
    source = tmp_path / "probe.cpp"
    source.write_text(r'''
#include <cstdint>
#include <cassert>
#include "s760_image_fixture.h"
int main() {
 s760_image_fixture f;
 for (const char *bad : {"", "0", "-1", "+1", " 1", "1x", "16777216", "999999999999999999999999"}) {
  f.configure("fixture",nullptr,bad);
  assert(!f.interrupt_write(1,512));assert(!f.interrupt_write(511,512));
 }
 f.configure(nullptr,nullptr,"1");assert(!f.interrupt_write(1,512));
 f.configure("fixture");assert(!f.interrupt_write(1,512));
 for (size_t cut : {size_t(1),size_t(255),size_t(511)}) {
  const auto text=std::to_string(cut);f.configure("fixture",nullptr,text.c_str());
  assert(!f.interrupt_write(cut-1,512));assert(f.interrupt_write(cut,512));
  assert(!f.interrupt_write(cut,512));f.reset();assert(!f.interrupt_write(cut,512));
 }
 f.configure("fixture",nullptr,"512");assert(!f.interrupt_write(512,512));
 f.configure("fixture",nullptr,"1");assert(!f.interrupt_write(1,1));assert(f.interrupt_write(1,512));
}
''')
    exe = tmp_path / "probe.exe"
    result = subprocess.run([compiler, "/nologo", "/std:c++17", "/EHsc", "/UNDEBUG",
                             f"/I{ROOT / 'mame-source/src/mame/roland'}", str(source), f"/Fe:{exe}"],
                            cwd=tmp_path, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    subprocess.run([str(exe)], cwd=tmp_path, check=True)
