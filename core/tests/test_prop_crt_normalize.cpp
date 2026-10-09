// Feature: mame-live-backend, Property 4: CRT geometry normalization fabricates no pixels

#include "s760/s760_crt_normalize.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <random>
#include <vector>

// =============================================================================
//  test_prop_crt_normalize.cpp
//  --------------------------------------------------------------------------
//  Property-based test for the CRT 640x240 -> 640x480 line-doubling transform
//  (`s760::crt_line_double`, implemented in src/s760_crt_normalize.cpp).
//
//  Spec: .kiro/specs/mame-live-backend/  (design "CRT geometry reconciliation",
//        Property 4; Requirement 4.4).
//
//  Design Property 4 (CRT geometry normalization fabricates no pixels):
//    For any 640x240 RGBA source raster, the normalized 640x480 CRT surface has
//    payload length exactly payload_size(RGBA8888, 640, 480), and every output
//    row is an exact copy of a source row (2x line-doubling), so no output
//    pixel value is fabricated -- every output pixel equals a genuine source
//    pixel.
//
//  This is a dependency-free, self-contained assert-style executable in the
//  style of the existing core tests (see test_bridge.cpp / test_host_seam.cpp).
//  There is no RapidCheck/Hypothesis in this project, so the property is checked
//  as a loop of >= 100 iterations driven by a seeded std::mt19937 PRNG, plus
//  explicit edge cases (all-zero, all-0xFF). The transform is pure logic with no
//  MAME dependency, so this runs with no MAME binary present (Requirement 8.5).
//
//  For each generated 640x240 RGBA source raster the test asserts:
//    1. output length == bridge::payload_size(RGBA8888, 640, 480).
//    2. For every output row y, output row y is byte-identical to source row
//       y/2 (i.e. out rows 2r and 2r+1 both equal source row r) -- proving no
//       pixel value is fabricated.
// =============================================================================

namespace {

using namespace s760;

constexpr uint16_t kSrcW = 640;
constexpr uint16_t kSrcH = 240;
constexpr uint16_t kOutW = 640;
constexpr uint16_t kOutH = 480;

constexpr std::size_t kRowBytes = static_cast<std::size_t>(kSrcW) * 4u; // RGBA
constexpr std::size_t kSrcBytes = kRowBytes * kSrcH;

// Core property check against one source raster. Returns on success; aborts via
// assert() with a descriptive message on any violation.
void check_property_for_source(const std::vector<uint8_t>& src, const char* label) {
    assert(src.size() == kSrcBytes && "test bug: source raster wrong size");

    const std::vector<uint8_t> out =
        crt_line_double(src.data(), src.size(), kSrcW, kSrcH);

    // --- Assertion 1: exact protocol payload length (Requirement 4.4) --------
    const std::size_t expected =
        bridge::payload_size(bridge::PixelFormat::RGBA8888, kOutW, kOutH);
    assert(out.size() == expected &&
           "normalized CRT payload length != payload_size(RGBA8888,640,480)");
    (void)label;
    (void)expected;

    // --- Assertion 2: every output row is an exact copy of a source row ------
    // Output row y must byte-match source row y/2. This simultaneously proves
    // the 2x line-doubling (rows 2r and 2r+1 both == source row r) AND that no
    // output pixel value is fabricated (each output byte equals a genuine
    // source byte).
    for (std::size_t y = 0; y < kOutH; ++y) {
        const std::size_t src_row = y / 2u;
        const uint8_t* out_ptr = out.data() + y * kRowBytes;
        const uint8_t* src_ptr = src.data() + src_row * kRowBytes;
        const int cmp = std::memcmp(out_ptr, src_ptr, kRowBytes);
        assert(cmp == 0 &&
               "output row is not a byte-identical copy of source row y/2");
        (void)cmp;
    }
}

// Fill a raster with a constant byte value (edge cases: all-zero, all-0xFF).
std::vector<uint8_t> make_constant_source(uint8_t value) {
    return std::vector<uint8_t>(kSrcBytes, value);
}

// Fill a raster with pseudo-random bytes from the provided PRNG.
std::vector<uint8_t> make_random_source(std::mt19937& rng) {
    std::vector<uint8_t> src(kSrcBytes);
    std::uniform_int_distribution<unsigned> dist(0u, 255u);
    for (std::size_t i = 0; i < src.size(); ++i) {
        src[i] = static_cast<uint8_t>(dist(rng));
    }
    return src;
}

// -----------------------------------------------------------------------------
//  Test: Property 4 over explicit edge cases + >= 100 random rasters.
// -----------------------------------------------------------------------------
void test_property4_no_fabricated_pixels() {
    std::cout << "[TEST] Property 4: CRT normalization fabricates no pixels ..."
              << std::endl;

    // Explicit edge cases first.
    check_property_for_source(make_constant_source(0x00), "all-zero");
    check_property_for_source(make_constant_source(0xFF), "all-0xFF");

    // Seeded PRNG for reproducibility; a fixed seed keeps failures debuggable.
    std::mt19937 rng(0xC27A5760u);

    constexpr int kIterations = 200; // >= 100 per the testing convention
    for (int i = 0; i < kIterations; ++i) {
        const std::vector<uint8_t> src = make_random_source(rng);
        check_property_for_source(src, "random");
    }

    std::cout << "  -> verified " << (kIterations + 2)
              << " rasters (2 edge + " << kIterations << " random); "
              << "every output row is an exact source-row copy." << std::endl;
    std::cout << "  -> Property 4 PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==================================================" << std::endl;
    std::cout << "  S-760 MAME Live Backend — Property 4 Test Suite " << std::endl;
    std::cout << "  (CRT geometry normalization fabricates no pixels)" << std::endl;
    std::cout << "==================================================" << std::endl;

    try {
        test_property4_no_fabricated_pixels();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> PROPERTY 4 TEST PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
