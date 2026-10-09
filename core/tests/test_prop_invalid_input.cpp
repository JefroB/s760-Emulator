// Feature: mame-live-backend, Property 12: Invalid input is ignored without state change
//
// =============================================================================
//  test_prop_invalid_input.cpp — property-based test for the invalid-input
//  ignore rules (spec `mame-live-backend`, task 7.8).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 12: Invalid input is ignored without state change"
//        Validates: Requirements 6.4
//
//  Property 12 (design): For any MOUSE_MOVE/MOUSE_CLICK coordinate outside
//  [0.0, 1.0], or any BUTTON_*/DIAL_DELTA whose id maps to no defined input,
//  processing the message leaves ALL emulated input state (key-matrix bits,
//  encoder detents, and VDP mouse registers) byte-for-byte unchanged.
//
//  Class under test (s760/s760_mame_host.hpp — tasks 7.1/7.3/7.5/7.7):
//    - void S760MameHost::apply_button(const std::string& id, bool pressed)
//          -> unknown id ignored (Requirement 6.4).
//    - void S760MameHost::apply_dial_delta(int)
//    - void S760MameHost::apply_dial_delta(const std::string& id, int delta)
//          -> unknown encoder id ignored (Requirement 6.4).
//    - static bool S760MameHost::is_defined_encoder(const std::string& id)
//          -> defined ids are {"ALPHA","VOLUME"}.
//    - void S760MameHost::apply_pointer(double x, double y)
//          -> out-of-range (x or y outside [0,1]) or NaN ignored, no VDP write.
//    State accessors:
//      key_arrows_matrix(), gotek_ctrl_matrix(), key_matrix(port),
//      encoder_detents(), vdp_reg(reg), pointer_x_pixels(), pointer_y_pixels().
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_prop_crt_gate.cpp / test_prop_pointer_scaling.cpp. No
//  RapidCheck. A seeded std::mt19937 drives >= 100 randomized iterations.
//
//  Strategy per iteration: establish an ARBITRARY valid prior state on a fresh
//  host (random DEFINED button presses, a DEFINED-encoder dial delta, and a
//  valid in-range pointer), SNAPSHOT the full input state (both key-matrix
//  bytes, encoder_detents(), and the full 256-byte VDP register file), then
//  feed an INVALID input and assert the snapshot is byte-for-byte unchanged.
// =============================================================================

#include "s760/s760_mame_host.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <array>
#include <cassert>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <limits>
#include <random>
#include <string>
#include <vector>

namespace {

using namespace s760;

// Minimum randomized iterations required by the design (>= 100).
constexpr int kMinIterations = 500;

// -----------------------------------------------------------------------------
//  Full snapshot of every piece of emulated input state Property 12 protects.
// -----------------------------------------------------------------------------
struct InputSnapshot {
    uint8_t                 key_arrows;
    uint8_t                 gotek_ctrl;
    int                     encoder_detents;
    std::array<uint8_t, 256> vdp_regs;
};

InputSnapshot snapshot(const S760MameHost& host) {
    InputSnapshot s;
    s.key_arrows      = host.key_arrows_matrix();
    s.gotek_ctrl      = host.gotek_ctrl_matrix();
    s.encoder_detents = host.encoder_detents();
    for (int r = 0; r < 256; ++r) {
        s.vdp_regs[static_cast<std::size_t>(r)] =
            host.vdp_reg(static_cast<uint8_t>(r));
    }
    return s;
}

// Assert two snapshots are byte-for-byte identical (nothing changed).
void assert_unchanged(const InputSnapshot& before, const InputSnapshot& after,
                      const char* what) {
    assert(before.key_arrows == after.key_arrows &&
           "KEY_ARROWS matrix changed by an invalid input");
    assert(before.gotek_ctrl == after.gotek_ctrl &&
           "GOTEK_CTRL matrix changed by an invalid input");
    assert(before.encoder_detents == after.encoder_detents &&
           "encoder detents changed by an invalid input");
    for (std::size_t r = 0; r < before.vdp_regs.size(); ++r) {
        assert(before.vdp_regs[r] == after.vdp_regs[r] &&
               "a VDP register changed by an invalid input");
    }
    (void)what;
}

// The DEFINED (valid) button ids — kept in sync with the production mapping
// table (INPUT_PORTS_START(s760)). Used ONLY to build arbitrary VALID prior
// state and to guard generated unknown ids against accidental collisions.
const std::vector<std::string>& defined_button_ids() {
    static const std::vector<std::string> ids = {
        "cursor_left", "cursor_right", "cursor_up", "cursor_down", "enter",
        "gotek_prev", "gotek_next", "gotek_select",
    };
    return ids;
}

bool is_defined_button(const std::string& id) {
    for (const std::string& d : defined_button_ids()) {
        if (id == d) return true;
    }
    return false;
}

// Establish an ARBITRARY valid prior state on a fresh host: a handful of random
// DEFINED button presses, a DEFINED-encoder dial delta, and a valid in-range
// pointer. This guarantees the snapshot is non-trivial (not all-zero) so the
// "unchanged" assertion is meaningful.
void establish_prior_state(S760MameHost& host, std::mt19937& rng) {
    const std::vector<std::string>& ids = defined_button_ids();
    std::uniform_int_distribution<std::size_t> pick(0, ids.size() - 1);
    std::uniform_int_distribution<int> coin(0, 1);

    const int presses = 1 + (coin(rng) ? 2 : 0);
    for (int i = 0; i < presses + 1; ++i) {
        host.apply_button(ids[pick(rng)], coin(rng) != 0);
    }

    // A defined-encoder dial delta (so encoder_detents() is non-zero sometimes).
    std::uniform_int_distribution<int> delta_dist(-50, 50);
    const char* enc = coin(rng) ? "ALPHA" : "VOLUME";
    host.apply_dial_delta(enc, delta_dist(rng));

    // A valid in-range pointer (writes the VDP mouse registers).
    std::uniform_real_distribution<double> unit(0.0, 1.0);
    host.apply_pointer(unit(rng), unit(rng));
}

// -----------------------------------------------------------------------------
//  Confirm the production ignore boundary agrees with this test's notion of
//  "defined" — guards against accidentally generating a defined id/encoder.
// -----------------------------------------------------------------------------
void test_defined_boundary() {
    std::cout << "[TEST] defined-set boundary sanity..." << std::endl;

    // The only defined encoders are ALPHA and VOLUME.
    assert(S760MameHost::is_defined_encoder("ALPHA"));
    assert(S760MameHost::is_defined_encoder("VOLUME"));
    assert(!S760MameHost::is_defined_encoder(""));
    assert(!S760MameHost::is_defined_encoder("alpha"));   // case-sensitive
    assert(!S760MameHost::is_defined_encoder("DATA"));
    assert(!S760MameHost::is_defined_encoder("cursor_left"));

    // The defined buttons are exactly the eight in the mapping table; a sample
    // of clearly-unknown ids must NOT be in it.
    for (const char* unknown : {"", "nope", "CURSOR_LEFT", "ALPHA", "f1",
                                "gotek", "enter2"}) {
        assert(!is_defined_button(unknown) &&
               "test's unknown-id set collides with a defined button");
    }

    std::cout << "  -> defined-set boundary PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Explicit edge cases around the pointer in/out-of-range boundary + NaN/inf.
//
//  -0.0 == 0.0 is VALID (in range) and WILL write the registers, so it is NOT
//  an invalid input; we therefore test the just-outside values -1e-9 and
//  1.0+1e-9, plus NaN and +/-inf, which must all be ignored.
// -----------------------------------------------------------------------------
void test_pointer_edge_cases() {
    std::cout << "[TEST] out-of-range pointer edge cases..." << std::endl;

    const double qnan = std::numeric_limits<double>::quiet_NaN();
    const double pinf = std::numeric_limits<double>::infinity();
    const double ninf = -std::numeric_limits<double>::infinity();

    // Each pair has at least one axis outside [0,1] (or NaN/inf). The valid
    // partner axis (0.5) proves only the OTHER axis makes it invalid.
    const std::pair<double, double> bad[] = {
        {-1e-9, 0.5},        // just below 0 on x
        {0.5, -1e-9},        // just below 0 on y
        {1.0 + 1e-9, 0.5},   // just above 1 on x
        {0.5, 1.0 + 1e-9},   // just above 1 on y
        {-0.5, 0.5},         // clearly below 0
        {0.5, 2.0},          // clearly above 1
        {-1000.0, 0.5},      // large negative magnitude
        {0.5, 1000.0},       // large positive magnitude
        {qnan, 0.5},         // NaN x
        {0.5, qnan},         // NaN y
        {qnan, qnan},        // NaN both
        {pinf, 0.5},         // +inf x
        {0.5, pinf},         // +inf y
        {ninf, 0.5},         // -inf x
        {0.5, ninf},         // -inf y
        {-1e-9, 2.0},        // both out of range
    };

    for (const auto& p : bad) {
        // On a FRESH host (all VDP regs zero), an invalid pointer must write
        // NOTHING: the register file stays all-zero and the reconstructed pixel
        // coordinates stay 0.
        S760MameHost fresh;
        const InputSnapshot before = snapshot(fresh);
        fresh.apply_pointer(p.first, p.second);
        const InputSnapshot after = snapshot(fresh);
        assert_unchanged(before, after, "fresh invalid pointer");
        assert(fresh.pointer_x_pixels() == 0 &&
               "invalid pointer wrote an X pixel coordinate");
        assert(fresh.pointer_y_pixels() == 0 &&
               "invalid pointer wrote a Y pixel coordinate");

        // On a host with arbitrary valid prior state, the invalid pointer must
        // leave that state untouched.
        std::mt19937 rng(0x12340000u);
        S760MameHost host;
        establish_prior_state(host, rng);
        const InputSnapshot b2 = snapshot(host);
        host.apply_pointer(p.first, p.second);
        const InputSnapshot a2 = snapshot(host);
        assert_unchanged(b2, a2, "prior-state invalid pointer");
    }

    std::cout << "  -> out-of-range pointer edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Explicit edge cases for unknown button / unknown dial encoder ids.
// -----------------------------------------------------------------------------
void test_unknown_id_edge_cases() {
    std::cout << "[TEST] unknown button / dial id edge cases..." << std::endl;

    const char* unknown_ids[] = {
        "", " ", "unknown", "CURSOR_LEFT", "Enter", "cursor_leftx",
        "gotek", "ALPHA", "VOLUME", "f1", "123", "shift+a",
    };

    std::mt19937 rng(0x55AA55AAu);
    std::uniform_int_distribution<int> coin(0, 1);
    std::uniform_int_distribution<int> delta_dist(-1000, 1000);

    for (const char* uid : unknown_ids) {
        const std::string id = uid;

        // Unknown BUTTON id -> ignored.
        {
            S760MameHost host;
            establish_prior_state(host, rng);
            const InputSnapshot before = snapshot(host);
            host.apply_button(id, coin(rng) != 0);
            const InputSnapshot after = snapshot(host);
            // Only assert ignore for ids that truly are not defined buttons.
            if (!is_defined_button(id)) {
                assert_unchanged(before, after, "unknown button id");
            }
        }

        // Unknown DIAL encoder id -> ignored (id-aware overload).
        {
            S760MameHost host;
            establish_prior_state(host, rng);
            const InputSnapshot before = snapshot(host);
            host.apply_dial_delta(id, delta_dist(rng));
            const InputSnapshot after = snapshot(host);
            if (!S760MameHost::is_defined_encoder(id)) {
                assert_unchanged(before, after, "unknown dial encoder id");
            }
        }
    }

    std::cout << "  -> unknown id edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  Each iteration: build arbitrary valid prior state, snapshot it, then feed
//  exactly one INVALID input of a randomly chosen kind and assert no change.
// -----------------------------------------------------------------------------

// Generate a random id string that is guaranteed NOT to be a defined button
// AND NOT a defined encoder (so it is genuinely "maps to no defined input").
std::string gen_unknown_id(std::mt19937& rng) {
    static const char alphabet[] =
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-+ ";
    std::uniform_int_distribution<int> len_dist(0, 10);
    std::uniform_int_distribution<int> ch(0, static_cast<int>(sizeof(alphabet) - 2));

    for (int attempt = 0; attempt < 64; ++attempt) {
        const int n = len_dist(rng);
        std::string s;
        s.reserve(static_cast<std::size_t>(n));
        for (int i = 0; i < n; ++i) s.push_back(alphabet[ch(rng)]);
        if (!is_defined_button(s) && !S760MameHost::is_defined_encoder(s)) {
            return s; // confirmed unknown to BOTH id spaces
        }
    }
    // Fallback that is overwhelmingly unlikely to be a defined id.
    return std::string("zzz_unknown_") + std::to_string(rng());
}

// Generate an out-of-range / NaN / inf pointer coordinate pair (at least one
// axis invalid). Returns {x, y}.
std::pair<double, double> gen_invalid_pointer(std::mt19937& rng) {
    std::uniform_int_distribution<int> kind(0, 5);
    std::uniform_real_distribution<double> below(-1000.0, -1e-9);
    std::uniform_real_distribution<double> above(1.0 + 1e-9, 1000.0);
    std::uniform_real_distribution<double> valid(0.0, 1.0);

    const double qnan = std::numeric_limits<double>::quiet_NaN();
    const double pinf = std::numeric_limits<double>::infinity();
    const double ninf = -std::numeric_limits<double>::infinity();

    auto bad_val = [&](int k) -> double {
        switch (k) {
            case 0: return below(rng);
            case 1: return above(rng);
            case 2: return qnan;
            case 3: return pinf;
            default: return ninf;
        }
    };

    // Decide which axis/axes are invalid (at least one).
    std::uniform_int_distribution<int> which(0, 2); // 0=x bad,1=y bad,2=both bad
    std::uniform_int_distribution<int> badkind(0, 4);
    const int w = which(rng);
    double x, y;
    if (w == 0) {
        x = bad_val(badkind(rng));
        y = valid(rng);
    } else if (w == 1) {
        x = valid(rng);
        y = bad_val(badkind(rng));
    } else {
        x = bad_val(badkind(rng));
        y = bad_val(badkind(rng));
    }
    (void)kind;
    return {x, y};
}

void test_randomized_property() {
    std::cout << "[TEST] invalid-input ignore randomized property (>="
              << kMinIterations << " iterations)..." << std::endl;

    std::mt19937 rng(0xDEADBEEFu);
    std::uniform_int_distribution<int> which_invalid(0, 2); // 0=pointer,1=button,2=dial
    std::uniform_int_distribution<int> coin(0, 1);
    std::uniform_int_distribution<int> delta_dist(
        -1000000, 1000000);

    int ptr_cases = 0, btn_cases = 0, dial_cases = 0;

    for (int iter = 0; iter < kMinIterations; ++iter) {
        S760MameHost host;
        establish_prior_state(host, rng);
        const InputSnapshot before = snapshot(host);

        switch (which_invalid(rng)) {
            case 0: {
                const auto p = gen_invalid_pointer(rng);
                // Sanity: at least one axis really is out of [0,1].
                const bool x_ok = (p.first >= 0.0 && p.first <= 1.0);
                const bool y_ok = (p.second >= 0.0 && p.second <= 1.0);
                assert((!x_ok || !y_ok) &&
                       "generator produced an in-range pointer (vacuous)");
                host.apply_pointer(p.first, p.second);
                ++ptr_cases;
                break;
            }
            case 1: {
                const std::string id = gen_unknown_id(rng);
                assert(!is_defined_button(id) &&
                       "generated button id is actually defined (vacuous)");
                host.apply_button(id, coin(rng) != 0);
                ++btn_cases;
                break;
            }
            default: {
                const std::string id = gen_unknown_id(rng);
                assert(!S760MameHost::is_defined_encoder(id) &&
                       "generated encoder id is actually defined (vacuous)");
                host.apply_dial_delta(id, delta_dist(rng));
                ++dial_cases;
                break;
            }
        }

        const InputSnapshot after = snapshot(host);
        assert_unchanged(before, after, "randomized invalid input");
    }

    // The three invalid-input kinds must all have been exercised, otherwise the
    // loop would only cover part of Property 12.
    assert(ptr_cases > 0 && "no invalid-pointer case generated (incomplete)");
    assert(btn_cases > 0 && "no unknown-button case generated (incomplete)");
    assert(dial_cases > 0 && "no unknown-dial case generated (incomplete)");

    std::cout << "  -> " << kMinIterations << " iterations: " << ptr_cases
              << " pointer, " << btn_cases << " button, " << dial_cases
              << " dial. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "=================================================" << std::endl;
    std::cout << "  S-760 Invalid-Input Ignore Property Test (P12)  " << std::endl;
    std::cout << "=================================================" << std::endl;

    try {
        test_defined_boundary();
        test_pointer_edge_cases();
        test_unknown_id_edge_cases();
        test_randomized_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 INVALID-INPUT IGNORE PROPERTY TESTS PASSED "
                 "SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
