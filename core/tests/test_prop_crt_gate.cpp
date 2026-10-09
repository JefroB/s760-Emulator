// Feature: mame-live-backend, Property 3: CRT rasterization and VRAM-activity inference gate
//
// =============================================================================
//  test_prop_crt_gate.cpp — property-based test for the CRT VRAM-activity
//  inference + rasterization gate (spec `mame-live-backend`, task 3.5).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 3: CRT rasterization and VRAM-activity inference gate"
//        Validates: Requirements 4.1, 4.3, 4.5
//
//  Property 3 (design): For any VDP VRAM content, when VDP_VRAM_Active is true,
//  or when it is false but at least one of the first 2400 bytes of m_vdp_vram is
//  non-zero, the backend rasterizes the CRT from m_vdp_vram (the inferred-active
//  decision equals the first-2400 non-zero scan); otherwise it emits the
//  authentic-blank CRT surface.
//
//  Functions under test (pure, s760/s760_crt_gate.hpp — task 3.4):
//    - bool crt_should_rasterize(bool vdp_vram_active, const uint8_t* vdp_vram,
//                                std::size_t vram_len);
//    - std::vector<uint8_t> crt_blank();
//    - inline constexpr std::size_t kVdpInferScanBytes = 2400;
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_bridge.cpp and core/tests/test_host_seam.cpp. No RapidCheck.
//  A seeded std::mt19937 drives >= 100 randomized iterations plus explicit edge
//  cases around the 2400-byte inference boundary. Each iteration checks the
//  gate against an independent reference oracle and verifies the authentic-blank
//  surface size + all-zero payload.
// =============================================================================

#include "s760/s760_crt_gate.hpp"
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

// -----------------------------------------------------------------------------
//  Reference oracle — an INDEPENDENT reimplementation of the gate decision.
//
//  The CRT is rasterized iff the explicit active flag is set OR any of the first
//  min(2400, len) bytes is non-zero. Deliberately written separately from the
//  production code so the property test is a genuine cross-check.
// -----------------------------------------------------------------------------
bool oracle_should_rasterize(bool vdp_vram_active,
                             const std::vector<uint8_t>& vram) {
    if (vdp_vram_active) {
        return true;
    }
    const std::size_t scan =
        (vram.size() < kVdpInferScanBytes) ? vram.size() : kVdpInferScanBytes;
    for (std::size_t i = 0; i < scan; ++i) {
        if (vram[i] != 0) {
            return true;
        }
    }
    return false;
}

// Assert crt_should_rasterize matches the oracle for both the active=false and
// active=true cases of this buffer, and that crt_blank() is a correctly-sized
// all-zero RGBA8888 surface.
void check_case(const std::vector<uint8_t>& vram, const char* label) {
    const uint8_t* ptr = vram.empty() ? nullptr : vram.data();

    // --- Gate matches the oracle (active = false) ---------------------------
    const bool got_inactive = crt_should_rasterize(false, ptr, vram.size());
    const bool exp_inactive = oracle_should_rasterize(false, vram);
    assert(got_inactive == exp_inactive &&
           "crt_should_rasterize(false,...) disagrees with first-2400 scan oracle");
    (void)label;

    // --- Gate matches the oracle (active = true => always rasterize) --------
    const bool got_active = crt_should_rasterize(true, ptr, vram.size());
    assert(got_active == true &&
           "crt_should_rasterize(true,...) must always rasterize");
    assert(got_active == oracle_should_rasterize(true, vram));

    // --- Authentic-blank CRT surface is exact size + fully zero -------------
    const std::vector<uint8_t> blank = crt_blank();
    const std::size_t expected_len = bridge::payload_size(
        bridge::PixelFormat::RGBA8888, bridge::CRT_WIDTH, bridge::CRT_HEIGHT);
    assert(blank.size() == expected_len &&
           "crt_blank() length != payload_size(RGBA8888,640,480)");
    for (std::size_t i = 0; i < blank.size(); ++i) {
        assert(blank[i] == 0 && "crt_blank() payload must be all zero");
    }
}

// -----------------------------------------------------------------------------
//  Explicit edge cases around the 2400-byte inference boundary.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] CRT gate boundary edge cases..." << std::endl;

    // Empty / tiny buffers: no non-zero bytes => inactive gate stays false.
    check_case({}, "empty");
    check_case(std::vector<uint8_t>(1, 0), "single-zero");

    // All-zero buffers of various sizes (below, at, above 2400) => NOT inferred.
    const std::size_t zero_sizes[] = {
        std::size_t{1}, std::size_t{100}, kVdpInferScanBytes - 1,
        kVdpInferScanBytes, kVdpInferScanBytes + 1, kVdpInferScanBytes + 5000};
    for (std::size_t n : zero_sizes) {
        std::vector<uint8_t> z(n, 0);
        assert(crt_should_rasterize(false, z.data(), z.size()) == false &&
               "all-zero VRAM must NOT infer active");
        check_case(z, "all-zero-sized");
    }

    // Non-zero ONLY beyond byte 2400 => must NOT infer active (outside scan).
    {
        std::vector<uint8_t> v(kVdpInferScanBytes + 2000, 0);
        v[kVdpInferScanBytes] = 0x01;             // first byte past the scan window
        v[kVdpInferScanBytes + 1500] = 0xFF;
        assert(crt_should_rasterize(false, v.data(), v.size()) == false &&
               "non-zero only beyond byte 2400 must NOT infer active");
        check_case(v, "nonzero-beyond-2400");
    }

    // Single non-zero at index 2399 (last in-window byte) => MUST infer active.
    {
        std::vector<uint8_t> v(kVdpInferScanBytes + 100, 0);
        v[kVdpInferScanBytes - 1] = 0x7F;         // index 2399
        assert(crt_should_rasterize(false, v.data(), v.size()) == true &&
               "non-zero at index 2399 must infer active");
        check_case(v, "nonzero-at-2399");
    }

    // Single non-zero at index 2400 (first out-of-window byte) => NOT active.
    {
        std::vector<uint8_t> v(kVdpInferScanBytes + 100, 0);
        v[kVdpInferScanBytes] = 0x7F;             // index 2400
        assert(crt_should_rasterize(false, v.data(), v.size()) == false &&
               "non-zero at index 2400 must NOT infer active");
        check_case(v, "nonzero-at-2400");
    }

    // Non-zero within the first 2400 (index 0) => MUST infer active.
    {
        std::vector<uint8_t> v(kVdpInferScanBytes + 100, 0);
        v[0] = 0x01;
        assert(crt_should_rasterize(false, v.data(), v.size()) == true &&
               "non-zero at index 0 must infer active");
        check_case(v, "nonzero-at-0");
    }

    // Buffer SHORTER than the scan window with a non-zero inside it.
    {
        std::vector<uint8_t> v(100, 0);
        v[50] = 0xAA;
        assert(crt_should_rasterize(false, v.data(), v.size()) == true &&
               "non-zero inside short buffer must infer active");
        check_case(v, "short-nonzero");
    }

    std::cout << "  -> boundary edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  Generators vary the buffer size around and across the 2400 boundary, and the
//  density of non-zero bytes (including the all-zero case), so a meaningful mix
//  of infer-active / not-active decisions is produced. Every case is checked
//  against the independent oracle.
// -----------------------------------------------------------------------------
void test_randomized_property() {
    std::cout << "[TEST] CRT gate randomized property (>=" << kMinIterations
              << " iterations)..." << std::endl;

    std::mt19937 rng(0xC27A7E51u);  // fixed seed for reproducibility

    // Sizes concentrated around the 2400-byte inference boundary plus a wider
    // span, so both in-window and out-of-window regions are well exercised.
    std::uniform_int_distribution<int> size_mode(0, 3);
    std::uniform_int_distribution<std::size_t> small_size(0, 2 * kVdpInferScanBytes);
    std::uniform_int_distribution<int> near_boundary(-16, 16);
    std::uniform_int_distribution<std::size_t> big_size(0, 20000);

    // Byte-fill mode: how dense the non-zero content is.
    //   0 = all zero, 1 = sparse (mostly zero), 2 = dense, 3 = fully random.
    std::uniform_int_distribution<int> fill_mode(0, 3);
    std::uniform_int_distribution<int> byte_dist(0, 255);
    std::uniform_int_distribution<int> sparse_hit(0, 99);  // ~ probability knob

    int inferred_true = 0;
    int inferred_false = 0;

    for (int iter = 0; iter < kMinIterations; ++iter) {
        // --- choose a size ---
        std::size_t n = 0;
        switch (size_mode(rng)) {
            case 0:
                n = small_size(rng);
                break;
            case 1: {
                int delta = near_boundary(rng);
                long base = static_cast<long>(kVdpInferScanBytes) + delta;
                n = static_cast<std::size_t>(base < 0 ? 0 : base);
                break;
            }
            case 2:
                n = big_size(rng);
                break;
            default:
                n = static_cast<std::size_t>(byte_dist(rng));  // tiny buffers
                break;
        }

        // --- fill the buffer ---
        std::vector<uint8_t> vram(n, 0);
        const int mode = fill_mode(rng);
        if (mode == 1) {
            // Sparse: flip a few random bytes anywhere in the buffer.
            for (std::size_t i = 0; i < n; ++i) {
                if (sparse_hit(rng) < 2) {  // ~2% chance
                    vram[i] = static_cast<uint8_t>(1 + byte_dist(rng) % 255);
                }
            }
        } else if (mode == 2) {
            // Dense: most bytes non-zero.
            for (std::size_t i = 0; i < n; ++i) {
                vram[i] = static_cast<uint8_t>(
                    sparse_hit(rng) < 90 ? (1 + byte_dist(rng) % 255) : 0);
            }
        } else if (mode == 3) {
            for (std::size_t i = 0; i < n; ++i) {
                vram[i] = static_cast<uint8_t>(byte_dist(rng));
            }
        }
        // mode == 0 => leave all-zero.

        // --- check against the independent oracle ---
        check_case(vram, "random");

        if (oracle_should_rasterize(false, vram)) {
            ++inferred_true;
        } else {
            ++inferred_false;
        }
    }

    // Sanity: the generators must have produced BOTH outcomes, otherwise the
    // property loop would be vacuous (not actually exercising the gate).
    assert(inferred_true > 0 &&
           "generator never produced an infer-active case (vacuous test)");
    assert(inferred_false > 0 &&
           "generator never produced a not-active case (vacuous test)");

    std::cout << "  -> " << kMinIterations << " iterations: "
              << inferred_true << " infer-active, "
              << inferred_false << " not-active. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  S-760 CRT Gate Property Test (Prop 3)   " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_edge_cases();
        test_randomized_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 CRT GATE PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
