// Feature: mame-live-backend, Property 11: Pointer coordinates scale deterministically into the VDP mouse registers
//
// =============================================================================
//  test_prop_pointer_scaling.cpp — property-based test for pointer coordinate
//  scaling into the RFSC16A VDP mouse registers (spec `mame-live-backend`,
//  task 7.6).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 11: Pointer coordinates scale deterministically into
//               the VDP mouse registers"
//        Validates: Requirements 6.3
//
//  Property 11 (design): For any normalized coordinate (x,y) with x,y in
//  [0.0,1.0], processing a MOUSE_MOVE/MOUSE_CLICK writes integer pixel
//  coordinates equal to round(x*CRT_WIDTH) and round(y*CRT_HEIGHT) into the
//  RFSC16A VDP mouse registers (0x20 X-Low, 0x21 X-High, 0x22 Y-Low, 0x24
//  Control), reconstructable from those registers.
//
//  Class under test (s760/s760_mame_host.hpp — task 7.5):
//    - void S760MameHost::apply_pointer(double x, double y)
//    - uint8_t  S760MameHost::vdp_reg(uint8_t reg) const
//    - uint16_t S760MameHost::pointer_x_pixels() const
//    - uint16_t S760MameHost::pointer_y_pixels() const
//
//  Scaling (matches production — std::lround on the double):
//    px = std::lround(x * bridge::CRT_WIDTH)    // x in [0,1] -> [0, 640]
//    py = std::lround(y * bridge::CRT_HEIGHT)   // y in [0,1] -> [0, 480]
//  Stored faithfully (x=1.0 -> 640, y=1.0 -> 480; no clamp to 639/479).
//
//  Register packing (design "MAME driver" notes):
//    0x20 (X-Low)  = px & 0xFF
//    0x21 (X-High) = (px >> 8) & 0x03     // px<=640 needs bits 8..9
//    0x22 (Y-Low)  = py & 0xFF
//    0x24 (Control) bit0 = (py >> 8) & 0x01  // py<=480 needs bit 8
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_prop_crt_gate.cpp. No RapidCheck. A seeded std::mt19937
//  drives >= 100 randomized iterations plus explicit boundary cases (0.0, 0.5,
//  1.0, and small/large fractions). Determinism is checked by applying the same
//  coordinate twice and comparing the register file.
// =============================================================================

#include "s760/s760_mame_host.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cmath>
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
//  Check a single in-range normalized coordinate (x, y).
//
//  For a FRESH host:
//    * apply_pointer(x, y) writes the mouse registers.
//    * expected px/py are computed with the SAME rounding as production
//      (std::lround on the double) so the oracle matches the implementation.
//    * reconstruction via pointer_x_pixels()/pointer_y_pixels() equals px/py.
//    * the individual register bytes match the documented packing.
//    * applying the same coordinate twice is deterministic (identical regs).
// -----------------------------------------------------------------------------
void check_coord(double x, double y, const char* label) {
    assert(x >= 0.0 && x <= 1.0 && "test bug: x out of [0,1]");
    assert(y >= 0.0 && y <= 1.0 && "test bug: y out of [0,1]");
    (void)label;

    S760MameHost host;
    host.apply_pointer(x, y);

    // Expected integer pixel coordinates — identical rounding to production.
    const long px = std::lround(x * static_cast<double>(bridge::CRT_WIDTH));
    const long py = std::lround(y * static_cast<double>(bridge::CRT_HEIGHT));

    // px in [0,640], py in [0,480] for in-range input.
    assert(px >= 0 && px <= bridge::CRT_WIDTH &&
           "px out of expected [0,640] range");
    assert(py >= 0 && py <= bridge::CRT_HEIGHT &&
           "py out of expected [0,480] range");

    // --- Reconstruction from the registers equals the scaled coordinate -----
    assert(host.pointer_x_pixels() == static_cast<uint16_t>(px) &&
           "pointer_x_pixels() != round(x*CRT_WIDTH)");
    assert(host.pointer_y_pixels() == static_cast<uint16_t>(py) &&
           "pointer_y_pixels() != round(y*CRT_HEIGHT)");

    // --- Individual register bytes match the documented packing -------------
    assert(host.vdp_reg(0x20) == static_cast<uint8_t>(px & 0xFF) &&
           "reg 0x20 (X-Low) mismatch");
    assert(host.vdp_reg(0x21) == static_cast<uint8_t>((px >> 8) & 0x03) &&
           "reg 0x21 (X-High) mismatch");
    assert(host.vdp_reg(0x22) == static_cast<uint8_t>(py & 0xFF) &&
           "reg 0x22 (Y-Low) mismatch");
    assert((host.vdp_reg(0x24) & 0x01) == static_cast<uint8_t>((py >> 8) & 0x01) &&
           "reg 0x24 (Control) bit0 (Y-High) mismatch");

    // --- Determinism: applying the same coordinate twice is identical -------
    S760MameHost host2;
    host2.apply_pointer(x, y);
    host2.apply_pointer(x, y);  // second application must not change the regs
    for (int r = 0; r < 0x100; ++r) {
        assert(host.vdp_reg(static_cast<uint8_t>(r)) ==
                   host2.vdp_reg(static_cast<uint8_t>(r)) &&
               "apply_pointer is not deterministic across runs/repeats");
    }
}

// -----------------------------------------------------------------------------
//  Explicit boundary / representative cases.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] pointer scaling boundary cases..." << std::endl;

    const double xs[] = {0.0, 0.5, 1.0};
    const double ys[] = {0.0, 0.5, 1.0};
    for (double x : xs) {
        for (double y : ys) {
            check_coord(x, y, "corner/center");
        }
    }

    // Small and large fractions (and values that land on rounding half-points).
    const double fracs[] = {
        1e-9, 0.001, 0.0007812,   // ~0.5/640 near a sub-pixel boundary
        1.0 / 640.0,              // smallest X pixel step
        1.0 / 480.0,              // smallest Y pixel step
        0.5 / 640.0,              // X round-half point
        0.5 / 480.0,              // Y round-half point
        0.123456789, 0.333333333, 0.666666666,
        0.999, 0.9999, 1.0 - 1e-9
    };
    for (double f : fracs) {
        double x = f, y = f;
        if (x < 0.0) x = 0.0; if (x > 1.0) x = 1.0;
        if (y < 0.0) y = 0.0; if (y > 1.0) y = 1.0;
        check_coord(x, y, "fraction");
    }

    // Exact x=1.0 -> px=640 (needs two high bits: 0x280), y=1.0 -> py=480.
    {
        S760MameHost host;
        host.apply_pointer(1.0, 1.0);
        assert(host.pointer_x_pixels() == 640 && "x=1.0 must reconstruct to 640");
        assert(host.pointer_y_pixels() == 480 && "y=1.0 must reconstruct to 480");
        // 640 = 0x280 -> low=0x80, high bits = (0x280>>8)&0x03 = 0x02.
        assert(host.vdp_reg(0x20) == 0x80 && "x=1.0 low byte");
        assert(host.vdp_reg(0x21) == 0x02 && "x=1.0 high bits");
        // 480 = 0x1E0 -> low=0xE0, Y high bit = (0x1E0>>8)&0x01 = 0x01.
        assert(host.vdp_reg(0x22) == 0xE0 && "y=1.0 low byte");
        assert((host.vdp_reg(0x24) & 0x01) == 0x01 && "y=1.0 high bit");
    }

    std::cout << "  -> boundary cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  x and y are drawn uniformly in [0,1]. Every draw is checked against the
//  independent lround-based oracle and verified reconstructable + deterministic.
// -----------------------------------------------------------------------------
void test_randomized_property() {
    std::cout << "[TEST] pointer scaling randomized property (>="
              << kMinIterations << " iterations)..." << std::endl;

    std::mt19937 rng(0xB01DFACEu);  // fixed seed for reproducibility
    std::uniform_real_distribution<double> unit(0.0, 1.0);

    for (int iter = 0; iter < kMinIterations; ++iter) {
        const double x = unit(rng);
        const double y = unit(rng);
        check_coord(x, y, "random");
    }

    std::cout << "  -> " << kMinIterations << " iterations PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "===============================================" << std::endl;
    std::cout << "  S-760 Pointer Scaling Property Test (Prop 11) " << std::endl;
    std::cout << "===============================================" << std::endl;

    try {
        test_edge_cases();
        test_randomized_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 POINTER SCALING PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
