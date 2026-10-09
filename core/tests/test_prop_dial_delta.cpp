// Feature: mame-live-backend, Property 10: Dial delta is applied as a signed detent count
//
// =============================================================================
//  test_prop_dial_delta.cpp — property-based test for the dial-delta detent
//  application seam (spec `mame-live-backend`, task 7.4).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 10: Dial delta is applied as a signed detent count"
//        Validates: Requirements 6.2
//
//  Property 10 (design): For any signed integer `delta` in a DIAL_DELTA for a
//  defined encoder, the encoder's applied detent count FOR THE FRAME in which it
//  is processed equals `delta`.
//
//  Class under test (core/include/s760/s760_mame_host.hpp):
//    - void apply_dial_delta(int delta)                       (task 7.3)
//    - void apply_dial_delta(const std::string& id, int delta)(task 7.7)
//    - int  encoder_detents() const                           (applied count)
//    - static bool is_defined_encoder(const std::string& id)
//
//  MODELLING "the frame in which it is processed"
//  ----------------------------------------------
//  m_encoder_detents accumulates (`+= delta`) and run_frame() resets it to 0 at
//  the START of each successful advance — but ONLY when the host is initialized
//  (run_frame() on a default-constructed/uninitialized host returns false
//  WITHOUT resetting). To keep this test MAME/image-free and deterministic, we
//  do NOT rely on run_frame() to establish the frame boundary. Instead we model
//  "the frame in which it is processed" by starting from the known zero initial
//  state: a freshly constructed S760MameHost has encoder_detents() == 0 (its
//  constructor initializes m_encoder_detents = 0). A single apply_dial_delta(d)
//  from that zero state therefore yields encoder_detents() == d — exactly "the
//  applied detent count for the frame equals delta". For each sub-case we
//  construct a FRESH host so the accumulator starts at 0.
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_prop_crt_gate.cpp. No RapidCheck. A seeded std::mt19937 drives
//  >= 100 randomized iterations over signed deltas spanning negative/zero/
//  positive (bounded range to avoid signed overflow in the accumulation sum),
//  plus explicit edge values (0, +1, -1, and the bound endpoints).
// =============================================================================

#include "s760/s760_mame_host.hpp"

#include <cassert>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

using namespace s760;

// Minimum randomized iterations required by the design (>= 100).
constexpr int kMinIterations = 500;

// Bounded delta range. Kept well inside int limits so that accumulating two
// deltas (d1 + d2) in the per-frame-sum sub-case cannot overflow a signed int.
constexpr int kDeltaMin = -100000;
constexpr int kDeltaMax = 100000;

// -----------------------------------------------------------------------------
//  Core property check for a single signed delta.
//
//  Each clause constructs a FRESH host (accumulator starts at 0 — the frame
//  boundary) and asserts the applied detent count for that frame equals delta.
// -----------------------------------------------------------------------------
void check_delta(int delta) {
    // --- id-less overload: fresh/zero state -> single delta == delta --------
    {
        S760MameHost host;
        assert(host.encoder_detents() == 0 &&
               "fresh host must start with zero applied detents");
        host.apply_dial_delta(delta);
        assert(host.encoder_detents() == delta &&
               "apply_dial_delta(delta) from zero must yield encoder_detents()==delta");
    }

    // --- id-aware overload for the defined encoder "ALPHA" ------------------
    {
        S760MameHost host;
        assert(S760MameHost::is_defined_encoder("ALPHA") &&
               "ALPHA must be a defined encoder");
        host.apply_dial_delta("ALPHA", delta);
        assert(host.encoder_detents() == delta &&
               "apply_dial_delta(\"ALPHA\",delta) must yield encoder_detents()==delta");
    }

    // --- id-aware overload for the defined encoder "VOLUME" -----------------
    {
        S760MameHost host;
        assert(S760MameHost::is_defined_encoder("VOLUME") &&
               "VOLUME must be a defined encoder");
        host.apply_dial_delta("VOLUME", delta);
        assert(host.encoder_detents() == delta &&
               "apply_dial_delta(\"VOLUME\",delta) must yield encoder_detents()==delta");
    }
}

// Accumulation within a single frame: two deltas d1 then d2 from a fresh host
// sum to d1 + d2 (documents the per-frame running count; a single delta is the
// special case d2 == 0 yielding exactly delta).
void check_accumulation(int d1, int d2) {
    S760MameHost host;
    assert(host.encoder_detents() == 0);
    host.apply_dial_delta(d1);
    assert(host.encoder_detents() == d1 &&
           "first delta must set the applied detent count to d1");
    host.apply_dial_delta(d2);
    assert(host.encoder_detents() == d1 + d2 &&
           "two deltas in one frame must sum to d1+d2");
}

// -----------------------------------------------------------------------------
//  Explicit edge values: zero, +1, -1, and the bound endpoints.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] Dial-delta edge values..." << std::endl;

    const int edges[] = {0, 1, -1, kDeltaMin, kDeltaMax, 2, -2, 42, -42};
    for (int d : edges) {
        check_delta(d);
    }

    // A zero delta is a no-op: fresh host stays at 0.
    {
        S760MameHost host;
        host.apply_dial_delta(0);
        assert(host.encoder_detents() == 0 && "zero delta must be a no-op");
    }

    // Accumulation edge cases (single delta == d1, zero follow-up).
    check_accumulation(0, 0);
    check_accumulation(5, 0);
    check_accumulation(0, 7);
    check_accumulation(10, -10);     // nets to zero within the frame
    check_accumulation(-3, -4);
    check_accumulation(kDeltaMax, kDeltaMin);

    std::cout << "  -> edge values PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  Generates signed deltas spanning negative/zero/positive. Confirms the
//  generator actually produced all three sign classes (non-vacuous).
// -----------------------------------------------------------------------------
void test_randomized_property() {
    std::cout << "[TEST] Dial-delta randomized property (>=" << kMinIterations
              << " iterations)..." << std::endl;

    std::mt19937 rng(0xD1A1DE17u);  // fixed seed for reproducibility
    std::uniform_int_distribution<int> delta_dist(kDeltaMin, kDeltaMax);

    int neg = 0, zero = 0, pos = 0;

    for (int iter = 0; iter < kMinIterations; ++iter) {
        const int delta = delta_dist(rng);

        // Property 10: applied detent count for the frame equals delta.
        check_delta(delta);

        // Per-frame accumulation with a second independent delta.
        const int delta2 = delta_dist(rng);
        check_accumulation(delta, delta2);

        if (delta < 0) ++neg;
        else if (delta == 0) ++zero;
        else ++pos;
    }

    // Non-vacuity: the generator must have produced both signs. (Hitting exactly
    // 0 is rare across the wide range, so we assert on negative + positive.)
    assert(neg > 0 && "generator never produced a negative delta (vacuous test)");
    assert(pos > 0 && "generator never produced a positive delta (vacuous test)");

    // Also exercise explicit zero once more inside the randomized phase so the
    // zero-sign class is covered deterministically regardless of RNG draw.
    check_delta(0);
    ++zero;

    std::cout << "  -> " << kMinIterations << " iterations: "
              << neg << " negative, " << zero << " zero, " << pos
              << " positive. PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Undefined-encoder ignore boundary (adjacent to Property 10 / 6.2): an
//  undefined id must NOT apply any detent. This keeps the "defined encoder"
//  qualifier of Property 10 honest — only defined encoders apply the delta.
// -----------------------------------------------------------------------------
void test_undefined_encoder_ignored() {
    std::cout << "[TEST] Undefined encoder id is ignored (defined-encoder qualifier)..."
              << std::endl;

    const char* undefined[] = {"", "alpha", "Volume", "ENCODER", "DIAL", "x"};
    for (const char* id : undefined) {
        assert(!S760MameHost::is_defined_encoder(id) &&
               "test id expected to be undefined");
        S760MameHost host;
        host.apply_dial_delta(id, 12345);
        assert(host.encoder_detents() == 0 &&
               "undefined encoder id must apply no detent (state unchanged)");
    }

    std::cout << "  -> undefined-encoder ignore PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << " S-760 Dial-Delta Property Test (Prop 10) " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_edge_cases();
        test_randomized_property();
        test_undefined_encoder_ignored();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 DIAL-DELTA PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
