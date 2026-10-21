"""Execute the pinned upstream functions with host filesystem/SPC substitutes.

This qualifies the source patch, not a built RP2040/RP2350 firmware or hardware.
Upstream GPL source comes from the repository's existing durable evidence.
"""
from pathlib import Path
import hashlib
from functools import lru_cache
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from patch_bluescsi_filenames import patch_disk, patch_toolbox, prepare

ARCHIVE = ROOT / "docs/condensed/validation/bluescsi-filename-boundaries-2026-10-19.json"


@lru_cache(maxsize=1)
def compiler_environment(compiler):
    env = dict(os.environ)
    if os.name == "nt" and not env.get("INCLUDE"):
        vcvars = Path(compiler).parents[6] / "Auxiliary/Build/vcvars64.bat"
        if vcvars.is_file():
            result = subprocess.run(f'cmd /d /c call "{vcvars}" >nul && set',
                                    capture_output=True, text=True, timeout=60)
            assert result.returncode == 0, "Visual C++ environment setup failed"
            env.update(line.split("=", 1) for line in result.stdout.splitlines() if "=" in line and not line.startswith("="))
    return env


def sources():
    data = json.loads(ARCHIVE.read_text(encoding="utf-8"))["sources"]
    for entry in data.values():
        if "text" in entry:
            # Historical evidence read_text() normalized local CRLF files.
            encodings = [entry["text"].encode(), entry["text"].replace("\n", "\r\n").encode()]
            assert entry["sha256"] in {hashlib.sha256(b).hexdigest() for b in encodings}
    return data


def build_host(directory, patched):
    directory.mkdir()
    source = sources()
    env = source["env.hpp"]["text"]
    env = env.replace("fs::path sdroot;", "fs::path sdroot; int audio_calls=0; int get_name_mode=0;")
    env = env.replace("#define strcasecmp _stricmp", "#ifdef _WIN32\n#define strcasecmp _stricmp\n#else\n#include <strings.h>\n#endif")
    env = env.replace("return a.size();}", "return get_name_mode==2 && a.size()>=n ? 0 : (get_name_mode==1 ? std::min(a.size(),n-1) : a.size());}")
    env = env.replace("void audio_stop(int){}", "void audio_stop(int){++audio_calls;}")
    # Deterministic pre-fix detection without executing an unbounded C-string
    # read: the old stack array's first64 bytes contain no NUL at this boundary.
    env = env.replace("++switch_calls;auto &i=images[id];", "if(!std::memchr(name,0,MAX_FILE_PATH))throw std::runtime_error(\"unterminated switch path\");++switch_calls;auto &i=images[id];")
    env += "\n#define INVALID_FIELD_IN_CDB 0x2400\n"
    (directory / "env.hpp").write_text(env, encoding="utf-8")
    toolbox = source["BlueSCSI_Toolbox.cpp"]["text"]
    disk = source["upstream_functions.inc"]["text"]
    if patched:
        toolbox, disk = patch_toolbox(toolbox), patch_disk(disk)
    (directory / "BlueSCSI_Toolbox.cpp").write_text(toolbox, encoding="utf-8")
    (directory / "upstream_functions.inc").write_text(disk, encoding="utf-8")
    for name in ["BlueSCSI_Toolbox.h", "bluescsi_toolbox.h"]:
        (directory / name).write_text(source["BlueSCSI_Toolbox.h"]["text"], encoding="utf-8")
    for name in ["BlueSCSI_disk.h", "BlueSCSI_cdrom.h", "BlueSCSI_log.h", "minIni.h", "SdFat.h", "scsi2sd_time.h", "sd.h", "mode.h"]:
        (directory / name).write_text('#include "env.hpp"\n', encoding="utf-8")
    shutil.copyfile(ROOT / "tests/fixtures/bluescsi_filenames/main.cpp", directory / "main.cpp")
    compiler = shutil.which("cl" if os.name == "nt" else "c++")
    if not compiler:
        pytest.skip("Host C++17 compiler is required for upstream source execution")
    exe = directory / ("regression.exe" if os.name == "nt" else "regression")
    cmd = ([compiler, "/nologo", "/std:c++17", "/EHsc", "/W3", "/I.", "/Fe:" + str(exe), "main.cpp"] if os.name == "nt" else
           [compiler, "-std=c++17", "-Wall", "-Wextra", "-I.", "main.cpp", "-o", str(exe)])
    result = subprocess.run(cmd, cwd=directory, env=compiler_environment(compiler), capture_output=True, text=True, timeout=120)
    (directory / "build.log").write_text(result.stdout + result.stderr, encoding="utf-8")
    assert result.returncode == 0, result.stdout + result.stderr
    return exe


@pytest.fixture(scope="module")
def binaries(tmp_path_factory):
    work = tmp_path_factory.mktemp("bluescsi-upstream-filenames")
    return {state: build_host(work / state, state == "after") for state in ["before", "after"]}


@pytest.mark.parametrize("scenario", ["filters", "paths", "errors", "switch-index", "switch-open", "switch-missing"])
def test_recorded_defects_fail_before_fix(binaries, tmp_path, scenario):
    result = subprocess.run([str(binaries["before"]), str(tmp_path), scenario, "0"], capture_output=True, text=True, timeout=30)
    assert result.returncode == 1 and "FAIL checks=" in result.stderr
    if scenario.startswith("switch-"):
        assert "status=0" in result.stdout
        assert "BUG137 failed D8 must report CHECK CONDITION" in result.stderr


@pytest.mark.parametrize("scenario", ["filters", "boundaries", "capacity", "paths", "errors", "switch-index", "switch-open", "switch-missing"])
@pytest.mark.parametrize("get_name_mode", [0, 1, 2])
def test_patched_upstream_filename_contract(binaries, tmp_path, scenario, get_name_mode):
    result = subprocess.run([str(binaries["after"]), str(tmp_path), scenario, str(get_name_mode)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "PASS checks=" in result.stdout
    if scenario.startswith("switch-"):
        rows = [line for line in result.stdout.splitlines() if line.startswith("SWITCH_ERROR")]
        assert len(rows) == 4
        assert all("status=2 phase=3 data=0 sense=5 asc=9216" in row for row in rows)


@pytest.mark.parametrize("patcher,name", [(patch_toolbox, "BlueSCSI_Toolbox.cpp"), (patch_disk, "upstream_functions.inc")])
def test_patcher_rejects_already_patched_or_unreviewed_block(patcher, name):
    original = sources()[name]["text"]
    with pytest.raises(ValueError):
        patcher(patcher(original))
    with pytest.raises(ValueError):
        patcher("unreviewed source")


def test_unknown_checkout_is_rejected_before_output_creation(tmp_path):
    (tmp_path / "src").mkdir()
    for name in ["BlueSCSI_disk.cpp", "BlueSCSI_Toolbox.cpp"]:
        (tmp_path / "src" / name).write_text("unknown source")
    out = tmp_path / "output"
    with pytest.raises(ValueError, match="hashes"):
        prepare(tmp_path, out)
    assert not out.exists()
