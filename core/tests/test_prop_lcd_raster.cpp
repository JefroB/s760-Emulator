// Feature: mame-live-backend, Property 2: LCD surface is a pure function of SED1335 VRAM with exact size

#include "s760/s760_bridge_protocol.hpp"
#include "s760/s760_lcd_raster.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

// =============================================================================
//  test_prop_lcd_raster.cpp — property test for Property 2 of the
//  `mame-live-backend` spec (task 3.7).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 2: LCD surface is a pure function of SED1335 VRAM
//        with exact size"; Requirements 3.1, 3.2, 3.3, 3.4, 3.5.
//
//  Function under test (task 3.6, header s760/s760_lcd_raster.hpp):
//      std::vector<uint8_t> s760::lcd_rasterize(const uint8_t* sed_vram,
//                                               std::size_t vram_len,
//                                               bool sed_vram_active);
//
//  Property (restated): for ANY m_sed_vram buffer content, the produced LCD
//  surface is a deterministic function of ONLY that buffer (no other source, no
//  invented text), is MONO1 160x64, and has payload length exactly
//  payload_size(MONO1,160,64) == 1280; an all-zero, inactive VRAM yields an
//  all-zero (off) payload of that exact length.
//
//  This is a dependency-free, self-contained assert-style property test in the
//  style of the existing core tests (test_bridge.cpp / test_host_seam.cpp): no
//  RapidCheck. It runs a seeded std::mt19937 loop of >= 100 iterations over
//  randomized VRAM buffers (varying length and the active flag), interleaved
//  with explicit edge cases, and checks four sub-properties on every input:
//
//    (1) output length == bridge::payload_size(MONO1,160,64) == 1280.
//    (2) determinism: calling twice with the same input yields identical bytes.
//    (3) pure-from-VRAM: output equals a reference oracle derived SOLELY from
//        sed_vram (first min(1280,len) bytes copied, remainder zero), with the
//        all-zero + inactive case short-circuiting to all-zero.
//    (4) all-zero + inactive (or null) VRAM => every output byte is zero.
//
//  Runs with NO MAME binary present (Requirement 8.5): the function under test
//  is a pure VRAM->pixel transform decoupled from the MAME scheduler.
// =============================================================================

namespace {

using namespace s760;

// Expected MONO1 160x64 payload length (single source of truth = the protocol).
const std::size_t kExpectedLen =
    bridge::payload_size(bridge::PixelFormat::MONO1,
                         bridge::LCD_WIDTH, bridge::LCD_HEIGHT); // 1280

// Independent reference oracle for Property 2's "pure function of VRAM" clause.
// Deliberately re-derives the expected output from scratch (not by calling the
// function under test) so it is a genuine cross-check:
//   * The surface is derived SOLELY from sed_vram (no font ROM, no registers).
//   * The MONO1 payload is the first min(1280, vram_len) VRAM bytes copied
//     verbatim; any remaining bytes are off (zero) — nothing fabricated.
//   * Blank rule: when there is no genuine data (inactive AND all-zero, or a
//     null buffer), the result is the all-zero (every pixel off) payload.
std::vector<uint8_t> oracle(const uint8_t* vram, std::size_t len, bool active) {
    std::vector<uint8_t> out(kExpectedLen, 0u);

    // Determine whether the VRAM holds genuine data (mirrors the activity gate:
    // active flag set, OR any VRAM byte non-zero).
    bool has_data = active;
    if (!has_data && vram != nullptr) {
        for (std::size_t i = 0; i < len; ++i) {
            if (vram[i] != 0u) { has_data = true; break; }
        }
    }

    if (!has_data || vram == nullptr) {
        return out; // all-zero (off) blank payload
    }

    const std::size_t copy_len = (len < kExpectedLen) ? len : kExpectedLen;
    for (std::size_t i = 0; i < copy_len; ++i) {
        out[i] = vram[i];
    }
    return out;
}

bool all_zero(const std::vector<uint8_t>& v) {
    for (uint8_t b : v) {
        if (b != 0u) return false;
    }
    return true;
}

// Apply the four sub-property checks to a single (vram, len, active) input.
// `label` is used only for diagnostics on failure.
void check_input(const uint8_t* vram, std::size_t len, bool active,
                 const char* label) {
    std::vector<uint8_t> got = lcd_rasterize(vram, len, active);

    // (1) Exact size: always MONO1 160x64 == 1280 bytes, regardless of input.
    assert(got.size() == kExpectedLen && "LCD payload length must be 1280");

    // (2) Determinism: same input -> identical output (no hidden/global state).
    std::vector<uint8_t> again = lcd_rasterize(vram, len, active);
    assert(again == got && "lcd_rasterize must be deterministic");

    // (3) Pure-from-VRAM: output matches the independent oracle derived SOLELY
    //     from sed_vram. This simultaneously proves "no other source / no
    //     invented content" and the direct 1-bit-plane mapping.
    std::vector<uint8_t> expected = oracle(vram, len, active);
    assert(got == expected && "LCD surface must be a pure function of VRAM");

    // (4) Blank rule: an inactive, all-zero (or null) VRAM yields all-off.
    bool genuine = active;
    if (!genuine && vram != nullptr) {
        for (std::size_t i = 0; i < len; ++i) {
            if (vram[i] != 0u) { genuine = true; break; }
        }
    }
    if (!genuine) {
        assert(all_zero(got) &&
               "inactive all-zero VRAM must yield an all-zero (off) payload");
    }

    (void)label;
}

// -----------------------------------------------------------------------------
//  Explicit edge cases (checked once each, independent of the random loop).
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] Property 2 edge cases (null / empty / all-zero / short)..."
              << std::endl;

    // Null buffer, inactive -> all-zero 1280.
    check_input(nullptr, 0, false, "null/inactive");
    // Null buffer, active -> still all-zero (no bytes to read, nothing invented).
    check_input(nullptr, 0, true, "null/active");

    // Empty buffer (non-null not required; len 0), both flags.
    std::vector<uint8_t> empty;
    check_input(empty.data(), 0, false, "empty/inactive");
    check_input(empty.data(), 0, true, "empty/active");

    // All-zero inactive VRAM of full driver size (4096) -> all-zero 1280.
    std::vector<uint8_t> zeros_full(4096, 0u);
    check_input(zeros_full.data(), zeros_full.size(), false, "zeros4096/inactive");
    {
        std::vector<uint8_t> got =
            lcd_rasterize(zeros_full.data(), zeros_full.size(), false);
        assert(all_zero(got) && "all-zero inactive VRAM must be all-off");
    }

    // All-zero but ACTIVE VRAM -> still all-zero payload (data is genuinely off).
    check_input(zeros_full.data(), zeros_full.size(), true, "zeros4096/active");
    {
        std::vector<uint8_t> got =
            lcd_rasterize(zeros_full.data(), zeros_full.size(), true);
        assert(all_zero(got) &&
               "active but all-zero VRAM must still be all-off (no invented text)");
    }

    // Short (< 1280) buffer with content -> copied bytes match, tail is off.
    {
        std::vector<uint8_t> shortbuf(100);
        for (std::size_t i = 0; i < shortbuf.size(); ++i) {
            shortbuf[i] = static_cast<uint8_t>(0x80u | (i & 0x7Fu)); // non-zero
        }
        check_input(shortbuf.data(), shortbuf.size(), true, "short100/active");
        std::vector<uint8_t> got =
            lcd_rasterize(shortbuf.data(), shortbuf.size(), true);
        for (std::size_t i = 0; i < shortbuf.size(); ++i) {
            assert(got[i] == shortbuf[i] && "short buffer bytes must copy verbatim");
        }
        for (std::size_t i = shortbuf.size(); i < kExpectedLen; ++i) {
            assert(got[i] == 0u && "bytes beyond VRAM length must be off (0)");
        }
    }

    // Exactly 1280 bytes of content -> whole payload is the VRAM, verbatim.
    {
        std::vector<uint8_t> exact(kExpectedLen);
        for (std::size_t i = 0; i < exact.size(); ++i) {
            exact[i] = static_cast<uint8_t>((i * 37u + 11u) & 0xFFu);
        }
        // ensure at least one non-zero so inactive still counts as genuine data
        exact[0] = 0xAB;
        check_input(exact.data(), exact.size(), false, "exact1280/inactive");
        std::vector<uint8_t> got =
            lcd_rasterize(exact.data(), exact.size(), false);
        assert(got == exact && "exact-1280 VRAM must map verbatim to payload");
    }

    // Larger than 1280 (full 4096) with content -> only first 1280 feed the image.
    {
        std::vector<uint8_t> big(4096);
        for (std::size_t i = 0; i < big.size(); ++i) {
            big[i] = static_cast<uint8_t>((i ^ 0x5Au) & 0xFFu);
        }
        check_input(big.data(), big.size(), true, "big4096/active");
        std::vector<uint8_t> got = lcd_rasterize(big.data(), big.size(), true);
        for (std::size_t i = 0; i < kExpectedLen; ++i) {
            assert(got[i] == big[i] && "first 1280 VRAM bytes must map verbatim");
        }
    }

    std::cout << "  -> edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations, seeded for reproducibility).
// -----------------------------------------------------------------------------
void test_random_property() {
    std::cout << "[TEST] Property 2 randomized loop (>=100 iterations)..."
              << std::endl;

    constexpr int kIterations = 500; // comfortably exceeds the 100 minimum

    std::mt19937 rng(0xBADC0FFEu); // fixed seed -> reproducible counterexamples
    std::uniform_int_distribution<int>  len_dist(0, 4096);   // vary VRAM length
    std::uniform_int_distribution<int>  byte_dist(0, 255);   // random bytes
    std::uniform_int_distribution<int>  active_dist(0, 1);   // vary active flag
    std::uniform_int_distribution<int>  shape_dist(0, 3);    // content shape

    for (int iter = 0; iter < kIterations; ++iter) {
        const std::size_t len = static_cast<std::size_t>(len_dist(rng));
        const bool active = active_dist(rng) != 0;
        std::vector<uint8_t> vram(len);

        // Mix content shapes so we exercise all-zero (blank path), sparse
        // (non-zero only early -> still genuine data), and dense random fills.
        const int shape = shape_dist(rng);
        switch (shape) {
            case 0:
                // all zero (exercises the blank short-circuit when inactive)
                break;
            case 1:
                // sparse: a few non-zero bytes near the front
                for (std::size_t i = 0; i < len; ++i) {
                    vram[i] = (i < 8u && (byte_dist(rng) & 1))
                                  ? static_cast<uint8_t>(1 + byte_dist(rng) % 255)
                                  : 0u;
                }
                break;
            default:
                // dense random
                for (std::size_t i = 0; i < len; ++i) {
                    vram[i] = static_cast<uint8_t>(byte_dist(rng));
                }
                break;
        }

        const uint8_t* ptr = vram.empty() ? nullptr : vram.data();
        check_input(ptr, len, active, "random");
    }

    std::cout << "  -> " << kIterations << " randomized iterations PASSED!"
              << std::endl;
}

} // namespace

int main() {
    std::cout << "=================================================" << std::endl;
    std::cout << "  S-760 LCD Raster Property Test (Property 2)    " << std::endl;
    std::cout << "=================================================" << std::endl;

    // Guard the single-source-of-truth size up front.
    assert(kExpectedLen == 1280u &&
           "payload_size(MONO1,160,64) must be 1280");

    try {
        test_edge_cases();
        test_random_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL LCD RASTER PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
