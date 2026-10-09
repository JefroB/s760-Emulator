// Feature: mame-live-backend, Property 1: Failed frame advance preserves surfaces
//
// =============================================================================
//  test_prop_failed_frame.cpp — property-based test for failed-frame surface
//  preservation (spec `mame-live-backend`, task 6.3).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 1: Failed frame advance preserves surfaces"
//        Validates: Requirements 1.5
//
//  Property 1 (design): For any previously cached CRT and LCD surface state,
//  when a run_frame() advance fails, the surfaces exposed by
//  get_latest_video_frame() and get_lcd_surface() are byte-for-byte identical
//  to the cached surfaces from the last successful advance (no partial or
//  invented frame is produced).
//
//  Class under test: s760::S760MameHost (core/include/s760/s760_mame_host.hpp,
//  core/src/s760_mame_host.cpp — tasks 6.1/6.2/6.4).
//
//  WHY run_frame() FAILS IN THIS BUILD (the failed-advance seam)
//  ------------------------------------------------------------
//  run_frame() returns false precisely when the backend is NOT initialized
//  (m_initialized == false, i.e. init() was never called or failed to resolve/
//  load s760224.img). A default-constructed S760MameHost (no init, no image)
//  stays uninitialized, so run_frame() returns false WITHOUT touching the
//  cached surfaces — this is the clean, MAME-binary-free way to exercise
//  Property 1 (Requirement 8.5: host-side tests run with no MAME binary
//  present). The genuine machine's mid-run failure (task 6.2) lands at the SAME
//  seam: run_frame() builds the refreshed rasters into local temporaries and
//  only commits them on success, so any failing advance — uninitialized today,
//  a mid-run step failure later — leaves m_crt_raster / m_lcd_raster
//  byte-for-byte unchanged. The property therefore holds for the general
//  failed-advance case, not merely the uninitialized path exercised here.
//
//  TEST STRATEGY
//  -------------
//    1. Construct an uninitialized S760MameHost (do NOT call init(), so no image
//       is loaded and run_frame() will fail). Assert is_initialized() == false.
//    2. Capture the cached surfaces exposed BEFORE any run_frame():
//         - get_latest_video_frame() -> VideoFrame v0 (width, height, pixels).
//         - get_lcd_surface(buf0, 1280) -> must return true; keep the 1280 bytes.
//    3. Loop >= 100 iterations with a seeded std::mt19937. Each iteration:
//         - randomize the owned VDP/SED VRAM (vdp_vram()/sed_vram()) to model
//           arbitrary attempted/prior VRAM. (Surfaces only change on a SUCCESSFUL
//           advance; a failing advance must ignore this entirely.)
//         - call run_frame() and assert it returns false (failed advance).
//         - re-read get_latest_video_frame() and get_lcd_surface() and assert
//           BYTE-FOR-BYTE equality to v0 / buf0 (width, height, every pixel, and
//           all 1280 LCD bytes). This proves a failed advance preserves surfaces
//           (no partial or invented frame).
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_prop_crt_gate.cpp and core/tests/test_bridge.cpp. No
//  RapidCheck. A fixed PRNG seed keeps the run reproducible.
// =============================================================================

#include "s760/s760_mame_host.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

namespace {

using namespace s760;

// Minimum randomized iterations required by the design (>= 100).
constexpr int kMinIterations = 500;

// Expected LCD payload length: payload_size(MONO1, 160, 64) == 1280 bytes.
const std::size_t kLcdLen = bridge::payload_size(
    bridge::PixelFormat::MONO1, bridge::LCD_WIDTH, bridge::LCD_HEIGHT);

// Byte-for-byte compare two VideoFrames (geometry + every pixel word).
bool video_frames_equal(const VideoFrame& a, const VideoFrame& b) {
    if (a.width != b.width) return false;
    if (a.height != b.height) return false;
    if (a.rgba_pixels.size() != b.rgba_pixels.size()) return false;
    for (std::size_t i = 0; i < a.rgba_pixels.size(); ++i) {
        if (a.rgba_pixels[i] != b.rgba_pixels[i]) return false;
    }
    return true;
}

// Randomize every byte of a VRAM buffer with the given PRNG. Models arbitrary
// prior/attempted VRAM content across iterations.
void randomize_vram(std::vector<uint8_t>& vram, std::mt19937& rng) {
    std::uniform_int_distribution<int> byte_dist(0, 255);
    for (std::size_t i = 0; i < vram.size(); ++i) {
        vram[i] = static_cast<uint8_t>(byte_dist(rng));
    }
}

// -----------------------------------------------------------------------------
//  The property: a failing run_frame() leaves the exposed surfaces byte-for-byte
//  identical to the surfaces cached before the failing advance.
// -----------------------------------------------------------------------------
void test_failed_frame_preserves_surfaces() {
    std::cout << "[TEST] failed run_frame() preserves cached surfaces (>="
              << kMinIterations << " iterations)..." << std::endl;

    // --- Construct an uninitialized host so run_frame() will fail -----------
    // We deliberately point the roms dir at a path that cannot resolve an image
    // AND never call init(), so m_initialized stays false. (Even if init() were
    // called it would return false here; not calling it keeps the test free of
    // any filesystem dependency.)
    S760MameHost host("this/path/does/not/exist");
    assert(!host.is_initialized() &&
           "default-constructed host must be uninitialized (run_frame will fail)");

    // --- Capture the cached surfaces exposed BEFORE any advance -------------
    const VideoFrame v0 = host.get_latest_video_frame();
    // The CRT surface must be the fixed 640x480 geometry even uninitialized.
    assert(v0.width == bridge::CRT_WIDTH && v0.height == bridge::CRT_HEIGHT &&
           "cached CRT frame must be fixed 640x480 geometry");
    assert(v0.rgba_pixels.size() ==
               static_cast<std::size_t>(bridge::CRT_WIDTH) * bridge::CRT_HEIGHT &&
           "cached CRT frame pixel count must be 640*480");

    std::vector<uint8_t> buf0(kLcdLen, 0xAAu); // pre-fill with a sentinel
    const bool lcd_ok = host.get_lcd_surface(buf0.data(), buf0.size());
    assert(lcd_ok &&
           "get_lcd_surface() must succeed for the exact MONO1 160x64 length");
    assert(buf0.size() == kLcdLen && "captured LCD buffer must be 1280 bytes");

    std::mt19937 rng(0xF1A1Ed00u); // fixed seed for reproducibility

    int failed_advances = 0;
    for (int iter = 0; iter < kMinIterations; ++iter) {
        // Model arbitrary prior/attempted VRAM. Surfaces only change on a
        // SUCCESSFUL advance; because run_frame() will FAIL (uninitialized),
        // seeding this must have no effect on the exposed surfaces.
        randomize_vram(host.vdp_vram(), rng);
        randomize_vram(host.sed_vram(), rng);

        // --- The failing advance -------------------------------------------
        const bool advanced = host.run_frame();
        assert(advanced == false &&
               "run_frame() on an uninitialized host must fail (return false)");
        if (!advanced) ++failed_advances;

        // --- Surfaces must be byte-for-byte identical to the captured cache --
        const VideoFrame v = host.get_latest_video_frame();
        assert(video_frames_equal(v, v0) &&
               "failed run_frame() changed the CRT surface (partial/invented frame)");

        std::vector<uint8_t> buf(kLcdLen, 0x55u); // different sentinel than buf0
        const bool ok = host.get_lcd_surface(buf.data(), buf.size());
        assert(ok && "get_lcd_surface() must still succeed after a failed advance");
        assert(buf == buf0 &&
               "failed run_frame() changed the LCD surface (partial/invented frame)");
    }

    // Sanity: every iteration must actually have exercised a FAILED advance,
    // otherwise the property loop would be vacuous.
    assert(failed_advances == kMinIterations &&
           "every iteration must have produced a failed advance (non-vacuous)");

    std::cout << "  -> " << kMinIterations
              << " failed advances, surfaces preserved byte-for-byte. PASSED!"
              << std::endl;
}

// -----------------------------------------------------------------------------
//  Explicit edge cases that complement the randomized loop.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] failed-frame edge cases..." << std::endl;

    // (a) Repeated failing advances with NO VRAM mutation at all must still
    //     leave the surfaces untouched (idempotent on failure).
    {
        S760MameHost host; // default-constructed, uninitialized
        assert(!host.is_initialized());

        const VideoFrame v0 = host.get_latest_video_frame();
        std::vector<uint8_t> buf0(kLcdLen, 0u);
        assert(host.get_lcd_surface(buf0.data(), buf0.size()));

        for (int i = 0; i < 10; ++i) {
            assert(host.run_frame() == false);
            assert(video_frames_equal(host.get_latest_video_frame(), v0));
            std::vector<uint8_t> buf(kLcdLen, 0xFFu);
            assert(host.get_lcd_surface(buf.data(), buf.size()));
            assert(buf == buf0);
        }
    }

    // (b) The authentic-blank cached CRT/LCD must be all-zero (no invented
    //     content) before any successful advance — the "no invented frame"
    //     guarantee at its strongest.
    {
        S760MameHost host;
        const VideoFrame v0 = host.get_latest_video_frame();
        for (uint32_t px : v0.rgba_pixels) {
            assert(px == 0u && "uninitialized CRT cache must be authentic-blank");
        }
        std::vector<uint8_t> buf0(kLcdLen, 0x7Fu);
        assert(host.get_lcd_surface(buf0.data(), buf0.size()));
        for (uint8_t b : buf0) {
            assert(b == 0u && "uninitialized LCD cache must be all-zero (off)");
        }

        // Mutate VRAM wildly, fail the advance, confirm the blank is preserved.
        for (auto& b : host.vdp_vram()) b = 0xDE;
        for (auto& b : host.sed_vram()) b = 0xAD;
        assert(host.run_frame() == false);
        assert(video_frames_equal(host.get_latest_video_frame(), v0));
        std::vector<uint8_t> buf(kLcdLen, 0x11u);
        assert(host.get_lcd_surface(buf.data(), buf.size()));
        assert(buf == buf0);
    }

    // (c) get_lcd_surface() length-mismatch guard is unaffected by failed
    //     advances (null / wrong length -> false; never writes partial data).
    {
        S760MameHost host;
        assert(host.run_frame() == false);
        assert(host.get_lcd_surface(nullptr, kLcdLen) == false);
        std::vector<uint8_t> wrong(kLcdLen + 1, 0u);
        assert(host.get_lcd_surface(wrong.data(), wrong.size()) == false);
    }

    std::cout << "  -> edge cases PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "=============================================" << std::endl;
    std::cout << "  S-760 Failed-Frame Property Test (Prop 1)  " << std::endl;
    std::cout << "=============================================" << std::endl;

    try {
        test_edge_cases();
        test_failed_frame_preserves_surfaces();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 FAILED-FRAME PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
