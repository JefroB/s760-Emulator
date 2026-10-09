// =============================================================================
//  test_smoke_build.cpp — build/smoke tests for the MAME_Backend integration.
//
//  Spec: .kiro/specs/mame-live-backend/ (task 10.5).
//  Requirements: 1.1, 1.6, 6.5, 8.1, 8.2, 8.5.
//
//  This is a dependency-free, assert()-style smoke/build test in the same style
//  as the other core tests (see test_host_seam.cpp). It does NOT modify
//  production code; it only consumes the public headers and reads runtime
//  source files read-only via std::ifstream.
//
//  It mixes IN-PROCESS behavioral assertions (where a runtime assertion is
//  meaningful) with STATIC SOURCE CHECKS (where the contract is a source-level
//  invariant that cannot be observed at runtime). Each facet below documents
//  exactly what it checks and the markers it uses.
//
//  Robust file paths
//  -----------------
//  The static source scans open the runtime .cpp/.hpp files deterministically
//  using the compile-time definition S760_CORE_SRC_DIR, provided by
//  core/CMakeLists.txt via:
//      target_compile_definitions(s760_smoke_build_tests
//          PRIVATE S760_CORE_SRC_DIR="${CMAKE_CURRENT_SOURCE_DIR}")
//  CMAKE_CURRENT_SOURCE_DIR for core/CMakeLists.txt is the `core` directory, so
//  runtime headers live at ${S760_CORE_SRC_DIR}/include/s760/<name> and runtime
//  sources at ${S760_CORE_SRC_DIR}/src/<name>. This is preferred over __FILE__
//  because it does not depend on how the compiler spells the test's own path.
//
//  FACETS (one block each in main()):
//    1. Process model (R1.1): in-process behavioral assertion that
//       S760MameHost::init()/run_frame() are synchronous in-process calls that
//       return normally (false on this runner, which is fine) and never crash;
//       PLUS a static check that the MAME host/selector/bridge runtime TUs
//       contain no process-spawning calls (CreateProcess/fork/exec/system/popen).
//    2. Python-free runtime (R1.6, 8.2): static scan of the runtime/integration
//       C++ TUs asserts none contain Python markers. src/bindings.cpp is the
//       pybind module (NOT runtime/integration) and is EXCLUDED by not listing
//       it in the runtime set.
//    3. Pointer path uses absolute scaling (R6.5): static check that
//       s760_mame_host.cpp's apply_pointer uses absolute normalized->pixel
//       scaling (std::lround + CRT_WIDTH/CRT_HEIGHT) and NO wrapped-delta path;
//       PLUS a behavioral assertion that apply_pointer(0.5,0.5) -> (320,240) and
//       two different coords produce independent absolute results.
//    4. Host-only path, no MAME binary (R8.5, 8.1): construct an S760Bridge with
//       a nullptr host, push_frames(), and assert the three surfaces are framed
//       with correct geometry/format/payload sizes; assert PROTOCOL_VERSION==1.
//       (R8.1 build is validated by this test compiling+linking+running.)
// =============================================================================

#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"
#include "s760/s760_host_interface.hpp"
#include "s760/s760_libretro_host.hpp"
#include "s760/s760_mame_host.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

namespace {

using namespace s760;

#ifndef S760_CORE_SRC_DIR
#error "S760_CORE_SRC_DIR must be defined by CMake for the static source scans."
#endif

// -----------------------------------------------------------------------------
//  Source-file helpers (read-only).
// -----------------------------------------------------------------------------

// Join the compile-defined core source dir with a relative path. The directory
// separator '/' works on all toolchains including MSVC.
std::string core_path(const std::string& relative) {
    return std::string(S760_CORE_SRC_DIR) + "/" + relative;
}

// Read an entire source file into a string. Asserts the file opened (a missing
// runtime source is itself a build/integration regression this smoke test must
// catch, so we fail rather than silently skip).
std::string read_source(const std::string& relative) {
    const std::string full = core_path(relative);
    std::ifstream in(full, std::ios::binary);
    assert(in.is_open() && "runtime source file could not be opened for scan");
    std::ostringstream ss;
    ss << in.rdbuf();
    return ss.str();
}

bool contains(const std::string& haystack, const std::string& needle) {
    return haystack.find(needle) != std::string::npos;
}

// Extract the body of a named function/method from a source string so a scan
// can be scoped to just that function. Finds the first occurrence of `signature`
// then returns the substring from there to the matching closing brace. Falls
// back to the remainder of the file if brace matching fails (the scan then just
// has a wider scope, which is still conservative for PRESENCE checks).
std::string extract_function_body(const std::string& src, const std::string& signature) {
    const std::size_t sig = src.find(signature);
    assert(sig != std::string::npos && "function signature not found in source");
    const std::size_t open = src.find('{', sig);
    if (open == std::string::npos) return src.substr(sig);
    int depth = 0;
    for (std::size_t i = open; i < src.size(); ++i) {
        if (src[i] == '{') ++depth;
        else if (src[i] == '}') {
            --depth;
            if (depth == 0) return src.substr(sig, i - sig + 1);
        }
    }
    return src.substr(sig);
}

// The runtime / integration C++ translation units (the code executed to perform
// MAME_Backend integration at runtime). Header + source pairs. This set is the
// RUNTIME PATH per Requirements 1.6 / 8.2.
//
// NOTE: src/bindings.cpp is intentionally NOT in this list. bindings.cpp is the
// pybind11 module TU (the Python bindings), NOT part of the runtime/integration
// path, so it legitimately contains Python markers and must be excluded from the
// Python-free scan (documented exclusion, Requirement 8.2).
const std::vector<std::string>& runtime_translation_units() {
    static const std::vector<std::string> units = {
        "src/s760_mame_host.cpp",         "include/s760/s760_mame_host.hpp",
        "src/s760_backend_selector.cpp",  "include/s760/s760_backend_selector.hpp",
        "src/s760_bridge.cpp",            "include/s760/s760_bridge.hpp",
        "src/s760_crt_gate.cpp",          "include/s760/s760_crt_gate.hpp",
        "src/s760_crt_normalize.cpp",     "include/s760/s760_crt_normalize.hpp",
        "src/s760_lcd_raster.cpp",        "include/s760/s760_lcd_raster.hpp",
        "include/s760/s760_host_interface.hpp",
        "include/s760/s760_surface_spec.hpp",
        "src/s760_libretro_host.cpp",     "include/s760/s760_libretro_host.hpp",
    };
    return units;
}

// Little-endian u16 read helper (frame header fields are LE on the wire).
uint16_t read_u16_le(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8);
}

// Decode + validate one framed display message; return its parsed header.
bridge::FrameHeader decode_and_validate_frame(const std::vector<uint8_t>& f) {
    assert(f.size() >= bridge::FRAME_HEADER_SIZE && "frame smaller than header");
    bridge::FrameHeader h{};
    h.surfaceId = static_cast<bridge::SurfaceId>(f[0]);
    h.width     = read_u16_le(&f[1]);
    h.height    = read_u16_le(&f[3]);
    h.format    = static_cast<bridge::PixelFormat>(f[5]);
    const std::size_t payload_len = f.size() - bridge::FRAME_HEADER_SIZE;
    const std::size_t expected = bridge::payload_size(h.format, h.width, h.height);
    assert(payload_len == expected && "payload length != payload_size(format,w,h)");
    (void)payload_len;
    (void)expected;
    return h;
}

// =============================================================================
//  FACET 1 — Process model: no child process is spawned (Requirement 1.1).
// =============================================================================
void test_facet1_no_child_process() {
    std::cout << "[FACET 1] process model: no child process spawned (R1.1) ..." << std::endl;

    // ---- In-process behavioral contract -------------------------------------
    // A portable "no process was spawned" assertion is not available from inside
    // the test, so we assert the OBSERVABLE behavioral contract instead: the
    // adapter's init()/run_frame() are SYNCHRONOUS IN-PROCESS calls that return
    // normally and never crash. On this runner s760224.img is absent, so init()
    // returns false (which is fine) and never spawns/terminates anything; the
    // call simply returns. run_frame() likewise returns (false on the
    // uninitialized scaffold) in-process.
    S760MameHost host;
    const bool init_ok = host.init();   // returns false without the image; must not crash
    (void)init_ok;                       // either value is acceptable for this contract
    for (int i = 0; i < 5; ++i) {
        const bool advanced = host.run_frame(); // in-process synchronous call
        (void)advanced;
    }
    // Reaching here means both calls returned in-process without aborting.
    std::cout << "  -> init()/run_frame() are synchronous in-process calls (returned normally)."
              << std::endl;

    // ---- Static check: no process-spawning calls in the MAME runtime TUs ----
    // The adapter/selector/host/bridge contain NO fork/exec/CreateProcess/system/
    // popen call — emulation happens in-process. Markers scanned (process-spawn):
    const std::vector<std::string> spawn_markers = {
        "CreateProcess", "fork(", "execve", "execvp", "execl",
        "system(", "popen(", "posix_spawn", "ShellExecute",
    };
    const std::vector<std::string> process_model_tus = {
        "src/s760_mame_host.cpp", "include/s760/s760_mame_host.hpp",
        "src/s760_backend_selector.cpp", "include/s760/s760_backend_selector.hpp",
        "src/s760_bridge.cpp", "include/s760/s760_bridge.hpp",
    };
    for (const auto& tu : process_model_tus) {
        const std::string src = read_source(tu);
        for (const auto& marker : spawn_markers) {
            const bool found = contains(src, marker);
            if (found) {
                std::cerr << "  !! process-spawn marker '" << marker
                          << "' found in " << tu << std::endl;
            }
            assert(!found && "runtime TU must contain no process-spawning call (R1.1)");
        }
    }
    std::cout << "  -> no process-spawning calls in the MAME runtime TUs. PASSED!" << std::endl;
}

// =============================================================================
//  FACET 2 — Python-free runtime (Requirements 1.6, 8.2).
// =============================================================================
void test_facet2_python_free_runtime() {
    std::cout << "[FACET 2] Python-free runtime TUs (R1.6, 8.2) ..." << std::endl;

    // Python markers that would indicate the runtime/integration path pulled in
    // CPython or pybind, or had Python source leak in. Documented marker list:
    const std::vector<std::string> python_markers = {
        "#include <Python.h>",
        "#include \"Python.h\"",
        "pybind11",
        "PyObject",
        "PyRun_",
        "Py_Initialize",
        "import ",     // a Python import statement (never valid C++)
    };

    for (const auto& tu : runtime_translation_units()) {
        const std::string src = read_source(tu);
        for (const auto& marker : python_markers) {
            const bool found = contains(src, marker);
            if (found) {
                std::cerr << "  !! Python marker '" << marker
                          << "' found in runtime TU " << tu << std::endl;
            }
            assert(!found && "runtime/integration TU must contain no Python (R1.6, 8.2)");
        }
    }

    // Positive confirmation that the EXCLUDED bindings TU does exist and IS the
    // pybind module (documents WHY it is excluded: it legitimately uses pybind).
    const std::string bindings = read_source("src/bindings.cpp");
    assert(contains(bindings, "pybind11") &&
           "src/bindings.cpp is expected to be the pybind module (excluded from runtime scan)");

    std::cout << "  -> "
              << runtime_translation_units().size()
              << " runtime TUs contain no Python; bindings.cpp (pybind) excluded. PASSED!"
              << std::endl;
}

// =============================================================================
//  FACET 3 — Pointer path uses absolute scaling, not wrapped 8-bit deltas
//            (Requirement 6.5).
// =============================================================================
void test_facet3_pointer_absolute_scaling() {
    std::cout << "[FACET 3] pointer path uses absolute scaling (R6.5) ..." << std::endl;

    // ---- Static check scoped to apply_pointer -------------------------------
    const std::string mame_src = read_source("src/s760_mame_host.cpp");
    const std::string body = extract_function_body(mame_src, "S760MameHost::apply_pointer");

    // PRESENCE of the absolute-scaling markers (preferred over proving a
    // negative): the body rounds the normalized coordinate scaled by the CRT
    // pixel dimensions. Markers: std::lround + CRT_WIDTH + CRT_HEIGHT.
    assert(contains(body, "std::lround") &&
           "apply_pointer must use std::lround absolute rounding (R6.5)");
    assert(contains(body, "CRT_WIDTH") &&
           "apply_pointer must scale by CRT_WIDTH (R6.5)");
    assert(contains(body, "CRT_HEIGHT") &&
           "apply_pointer must scale by CRT_HEIGHT (R6.5)");

    // ABSENCE of the removed wrapped 8-bit +/-127 relative-delta path. Markers:
    //   "127"  — the +/-127 relative clamp used by the removed crosshair path.
    //   "+="   — a delta-accumulation pattern (absolute scaling assigns fresh
    //            pixel values; it never accumulates a running position).
    assert(!contains(body, "127") &&
           "apply_pointer must NOT contain a +/-127 relative-delta clamp (R6.5)");
    assert(!contains(body, "+=") &&
           "apply_pointer must NOT accumulate a running pointer delta (R6.5)");
    std::cout << "  -> apply_pointer: absolute-scaling markers present, no wrapped-delta path."
              << std::endl;

    // ---- In-process behavioral contract -------------------------------------
    // apply_pointer(0.5,0.5) -> absolute center pixel (round(0.5*640)=320,
    // round(0.5*480)=240) on a fresh host.
    S760MameHost host;
    host.apply_pointer(0.5, 0.5);
    assert(host.pointer_x_pixels() == 320 && "0.5*640 must be absolute 320");
    assert(host.pointer_y_pixels() == 240 && "0.5*480 must be absolute 240");

    // Two different absolute coords produce INDEPENDENT absolute results — not a
    // delta accumulation. After a second write, the registers reflect ONLY the
    // new absolute coordinate (0.25*640=160, 0.75*480=360), not 320+160 etc.
    host.apply_pointer(0.25, 0.75);
    assert(host.pointer_x_pixels() == 160 && "second write is absolute (0.25*640=160)");
    assert(host.pointer_y_pixels() == 360 && "second write is absolute (0.75*480=360)");

    // Endpoints are faithful absolutes (1.0 -> full extent, not clamped away).
    host.apply_pointer(0.0, 1.0);
    assert(host.pointer_x_pixels() == 0 && "0.0 -> absolute 0");
    assert(host.pointer_y_pixels() == 480 && "1.0*480 -> absolute 480 (faithful)");

    std::cout << "  -> apply_pointer yields absolute, independent pixel coords. PASSED!"
              << std::endl;
}

// =============================================================================
//  FACET 4 — Host-only framing/decode/sizing with NO MAME binary present
//            (Requirements 8.5, 8.1).
// =============================================================================
void test_facet4_host_only_path() {
    std::cout << "[FACET 4] host-only framing/decode/sizing, no MAME binary (R8.5, 8.1) ..."
              << std::endl;

    // PROTOCOL_VERSION pinned at 1 (compile + runtime).
    static_assert(bridge::PROTOCOL_VERSION == 1, "PROTOCOL_VERSION must remain 1");
    assert(bridge::PROTOCOL_VERSION == 1);

    // Construct the Bridge with a nullptr host (the host-only encode path): no
    // backend, no MAME binary, no process. push_frames() produces the three
    // surfaces from default/empty state.
    S760Bridge bridge(nullptr);

    std::vector<std::vector<uint8_t>> frames;
    int telemetry_count = 0;
    bridge.set_frame_callback([&](const uint8_t* data, std::size_t len) {
        frames.emplace_back(data, data + len);
    });
    bridge.set_telemetry_callback([&](const std::string&) { ++telemetry_count; });

    bridge.push_frames();

    bool saw_crt = false, saw_lcd = false, saw_oled = false;
    for (const auto& f : frames) {
        const bridge::FrameHeader h = decode_and_validate_frame(f);
        switch (h.surfaceId) {
            case bridge::SurfaceId::CRT:
                saw_crt = true;
                assert(h.width == bridge::CRT_WIDTH && h.height == bridge::CRT_HEIGHT);
                assert(h.format == bridge::PixelFormat::RGBA8888);
                assert(f.size() - bridge::FRAME_HEADER_SIZE == 640u * 480u * 4u);
                break;
            case bridge::SurfaceId::LCD:
                saw_lcd = true;
                assert(h.width == bridge::LCD_WIDTH && h.height == bridge::LCD_HEIGHT);
                assert(h.format == bridge::PixelFormat::MONO1);
                assert(f.size() - bridge::FRAME_HEADER_SIZE == ((160u + 7u) / 8u) * 64u);
                break;
            case bridge::SurfaceId::OLED:
                saw_oled = true;
                assert(h.width == bridge::GOTEK_WIDTH && h.height == bridge::GOTEK_HEIGHT);
                assert(h.format == bridge::PixelFormat::MONO1);
                assert(f.size() - bridge::FRAME_HEADER_SIZE == ((128u + 7u) / 8u) * 32u);
                break;
        }
    }
    assert(saw_crt && "host-only path must produce a CRT frame");
    assert(saw_lcd && "host-only path must produce an LCD frame");
    assert(saw_oled && "host-only path must produce an OLED frame");

    std::cout << "  -> host-only path produced CRT/LCD/OLED with correct framing + sizes. PASSED!"
              << std::endl;
}

// =============================================================================
//  Light re-assert: both backends satisfy IS760Host (subsumed by host_seam, but
//  a cheap compile/link re-assert here keeps this smoke test self-contained).
// =============================================================================
void test_both_backends_are_hosts() {
    std::cout << "[SMOKE] both backends satisfy IS760Host ..." << std::endl;
    S760LibretroHost core_host;
    S760MameHost     mame_host;
    IS760Host* a = &core_host;   // compile/link proof: Core backend is an IS760Host
    IS760Host* b = &mame_host;   // compile/link proof: MAME backend is an IS760Host
    assert(a != nullptr && b != nullptr);
    // Each is drivable by a Bridge (construct + encode-only push_frames()).
    S760Bridge ba(a);
    S760Bridge bb(b);
    ba.push_frames();
    bb.push_frames();
    std::cout << "  -> both backends build + drive against the Bridge. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 Build/Smoke Test Suite     " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_facet1_no_child_process();
        test_facet2_python_free_runtime();
        test_facet3_pointer_absolute_scaling();
        test_facet4_host_only_path();
        test_both_backends_are_hosts();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 BUILD/SMOKE TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
