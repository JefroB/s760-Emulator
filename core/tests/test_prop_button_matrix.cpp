// Feature: mame-live-backend, Property 9: Button press/release toggles exactly its matrix bit
//
// =============================================================================
//  test_prop_button_matrix.cpp — property-based test for the button id ->
//  key-matrix bit mapping (spec `mame-live-backend`, task 7.2).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 9: Button press/release toggles exactly its matrix bit"
//        Validates: Requirements 6.1
//
//  Property 9 (design): For any button id that maps to a defined
//  INPUT_PORTS_START(s760) key-matrix bit and for any prior key-matrix state, a
//  BUTTON_PRESS sets exactly that bit and a BUTTON_RELEASE clears exactly that
//  bit, leaving all other bits unchanged.
//
//  Class under test: s760::S760MameHost (core/include/s760/s760_mame_host.hpp).
//    - void    apply_button(const std::string& id, bool pressed);
//    - uint8_t key_matrix(const std::string& port) const;   // "KEY_ARROWS"/"GOTEK_CTRL"
//    - uint8_t key_arrows_matrix() const;
//    - uint8_t gotek_ctrl_matrix() const;
//
//  Defined id -> (port, bit) per the header's documented mapping:
//    KEY_ARROWS: cursor_left=0x01 cursor_right=0x02 cursor_up=0x04
//                cursor_down=0x08 enter=0x10
//    GOTEK_CTRL: gotek_prev=0x01 gotek_next=0x02 gotek_select=0x04
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_prop_crt_gate.cpp. No RapidCheck. A seeded std::mt19937
//  drives >= 100 randomized iterations. The test maintains its OWN dual-port
//  expected model (expected KEY_ARROWS byte + expected GOTEK_CTRL byte) and,
//  after EVERY apply_button, asserts BOTH port bytes equal the model — this is
//  how "exactly that bit changed, all other bits (both ports) unchanged" is
//  verified. Unknown ids are also exercised and must leave both bytes unchanged.
// =============================================================================

#include "s760/s760_mame_host.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>
#include <vector>

namespace {

using namespace s760;

// Minimum randomized iterations required by the design (>= 100).
constexpr int kMinIterations = 500;

// A defined button: its protocol id string, which port it belongs to, and the
// exact single matrix bit it toggles. This table is the test's INDEPENDENT
// restatement of the mapping documented in s760_mame_host.hpp — a genuine
// cross-check, not a reference back into production code.
struct DefinedButton {
    const char* id;
    const char* port;   // "KEY_ARROWS" or "GOTEK_CTRL"
    uint8_t     bit;
};

const DefinedButton kButtons[] = {
    {"cursor_left",  "KEY_ARROWS", 0x01},
    {"cursor_right", "KEY_ARROWS", 0x02},
    {"cursor_up",    "KEY_ARROWS", 0x04},
    {"cursor_down",  "KEY_ARROWS", 0x08},
    {"enter",        "KEY_ARROWS", 0x10},
    {"gotek_prev",   "GOTEK_CTRL", 0x01},
    {"gotek_next",   "GOTEK_CTRL", 0x02},
    {"gotek_select", "GOTEK_CTRL", 0x04},
};
constexpr std::size_t kNumButtons = sizeof(kButtons) / sizeof(kButtons[0]);

// The test's own dual-port expected model. A SET bit means "pressed" (matching
// the adapter's documented logical-active-high convention).
struct ExpectedModel {
    uint8_t key_arrows = 0;
    uint8_t gotek_ctrl = 0;

    // Mutate the model exactly as a correct apply_button(defined id) should.
    void apply(const DefinedButton& b, bool pressed) {
        uint8_t& port = (std::string(b.port) == "KEY_ARROWS") ? key_arrows
                                                              : gotek_ctrl;
        if (pressed) {
            port |= b.bit;      // set exactly that bit
        } else {
            port &= ~b.bit;     // clear exactly that bit
        }
    }
};

// Assert BOTH port bytes of the host equal the expected model, via every
// accessor the host exposes. This is the "all other bits unchanged" check: the
// only bit that may differ from the prior state is the one just toggled, and
// the model captures exactly that.
void assert_matches(const S760MameHost& host, const ExpectedModel& m,
                    const char* label) {
    assert(host.key_arrows_matrix() == m.key_arrows &&
           "KEY_ARROWS matrix diverged from expected model");
    assert(host.gotek_ctrl_matrix() == m.gotek_ctrl &&
           "GOTEK_CTRL matrix diverged from expected model");
    // The named-port accessor must agree with the direct accessors.
    assert(host.key_matrix("KEY_ARROWS") == m.key_arrows &&
           "key_matrix(\"KEY_ARROWS\") disagrees with key_arrows_matrix()");
    assert(host.key_matrix("GOTEK_CTRL") == m.gotek_ctrl &&
           "key_matrix(\"GOTEK_CTRL\") disagrees with gotek_ctrl_matrix()");
    (void)label;
}

// -----------------------------------------------------------------------------
//  Direct Property-9 check: for a GIVEN prior state and a GIVEN defined button,
//  a press sets exactly that bit (all other bits of BOTH ports unchanged), and
//  a release clears exactly that bit (all other bits unchanged).
// -----------------------------------------------------------------------------
void check_press_release(const DefinedButton& b, const ExpectedModel& prior) {
    S760MameHost host;

    // --- Install the prior key-matrix state via the model's own presses -----
    // We reconstruct `prior` on the host by pressing every bit the model has
    // set. Because each press sets exactly one bit, the host's two bytes end up
    // equal to `prior` (verified immediately below).
    for (const auto& bb : kButtons) {
        const uint8_t& want = (std::string(bb.port) == "KEY_ARROWS")
                                  ? prior.key_arrows
                                  : prior.gotek_ctrl;
        if (want & bb.bit) {
            host.apply_button(bb.id, true);
        }
    }
    assert_matches(host, prior, "prior-installed");

    const bool was_set =
        ((std::string(b.port) == "KEY_ARROWS") ? prior.key_arrows
                                               : prior.gotek_ctrl) &
        b.bit;

    // --- BUTTON_PRESS sets exactly that bit --------------------------------
    ExpectedModel expect = prior;
    expect.apply(b, true);
    host.apply_button(b.id, true);
    assert_matches(host, expect, "after-press");

    // The targeted bit is now set regardless of its prior value...
    {
        const uint8_t port_byte = host.key_matrix(b.port);
        assert((port_byte & b.bit) == b.bit &&
               "BUTTON_PRESS did not set the mapped bit");
    }
    // ...and every OTHER bit equals the prior (idempotent when already set).
    {
        const uint8_t prior_byte =
            (std::string(b.port) == "KEY_ARROWS") ? prior.key_arrows
                                                  : prior.gotek_ctrl;
        const uint8_t now_byte = host.key_matrix(b.port);
        const uint8_t other = static_cast<uint8_t>(~b.bit);
        assert((now_byte & other) == (prior_byte & other) &&
               "BUTTON_PRESS altered a bit other than the mapped one");
    }
    (void)was_set;

    // --- BUTTON_RELEASE clears exactly that bit ----------------------------
    ExpectedModel expect2 = expect;
    expect2.apply(b, false);
    host.apply_button(b.id, false);
    assert_matches(host, expect2, "after-release");

    // The targeted bit is now clear...
    {
        const uint8_t port_byte = host.key_matrix(b.port);
        assert((port_byte & b.bit) == 0 &&
               "BUTTON_RELEASE did not clear the mapped bit");
    }
    // ...and every OTHER bit equals the state before the release (== prior's
    // other bits, since press/release only touch the mapped bit).
    {
        const uint8_t before_release = expect.key_arrows;  // (recompute per port)
        (void)before_release;
        const uint8_t prior_other =
            ((std::string(b.port) == "KEY_ARROWS") ? expect.key_arrows
                                                   : expect.gotek_ctrl);
        const uint8_t now_byte = host.key_matrix(b.port);
        const uint8_t other = static_cast<uint8_t>(~b.bit);
        assert((now_byte & other) == (prior_other & other) &&
               "BUTTON_RELEASE altered a bit other than the mapped one");
    }
}

// -----------------------------------------------------------------------------
//  Explicit edge cases.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] button-matrix edge cases..." << std::endl;

    // Fresh host: both ports start cleared.
    {
        S760MameHost host;
        assert(host.key_arrows_matrix() == 0 && "KEY_ARROWS must start at 0");
        assert(host.gotek_ctrl_matrix() == 0 && "GOTEK_CTRL must start at 0");
        assert(host.key_matrix("KEY_ARROWS") == 0);
        assert(host.key_matrix("GOTEK_CTRL") == 0);
    }

    // Each defined button from the all-clear prior state (press then release).
    for (const auto& b : kButtons) {
        check_press_release(b, ExpectedModel{});
    }

    // Each defined button from the all-SET prior state (so the pressed bit is
    // already set before the press, and the released bit is set before release).
    {
        ExpectedModel all_set;
        all_set.key_arrows = 0x1F;  // all five KEY_ARROWS bits
        all_set.gotek_ctrl = 0x07;  // all three GOTEK_CTRL bits
        for (const auto& b : kButtons) {
            check_press_release(b, all_set);
        }
    }

    // Press is idempotent: pressing an already-pressed button twice leaves the
    // single bit set and nothing else changed; a release then clears it once.
    {
        S760MameHost host;
        host.apply_button("enter", true);
        host.apply_button("enter", true);
        assert(host.key_arrows_matrix() == 0x10 && "double-press must set once");
        assert(host.gotek_ctrl_matrix() == 0x00 && "other port unchanged");
        host.apply_button("enter", false);
        host.apply_button("enter", false);
        assert(host.key_arrows_matrix() == 0x00 && "double-release must clear");
    }

    // Unknown ids never change either port (ties to 6.4; reinforces 6.1's
    // "exactly that bit"). Mix some content in first, then fire unknown ids.
    {
        S760MameHost host;
        host.apply_button("cursor_up", true);     // KEY_ARROWS 0x04
        host.apply_button("gotek_next", true);    // GOTEK_CTRL 0x02
        const uint8_t ka = host.key_arrows_matrix();
        const uint8_t gc = host.gotek_ctrl_matrix();
        const char* unknown[] = {"",       "ENTER",  "cursor",  "Cursor_Left",
                                 "button", "gotek",  "0x01",    "cursor_left "};
        for (const char* u : unknown) {
            host.apply_button(u, true);
            host.apply_button(u, false);
            assert(host.key_arrows_matrix() == ka &&
                   "unknown id must not alter KEY_ARROWS");
            assert(host.gotek_ctrl_matrix() == gc &&
                   "unknown id must not alter GOTEK_CTRL");
        }
    }

    std::cout << "  -> edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  Each iteration (a) builds a RANDOM prior dual-port state and a RANDOM defined
//  target button and runs the direct Property-9 press/release check; and (b)
//  drives a RANDOM sequence of apply_button operations (defined + unknown ids,
//  press + release) against a single host while mirroring every DEFINED op into
//  the expected model, asserting BOTH port bytes after EACH op. This long
//  interleaved sequence is the strongest "all other bits unchanged across
//  arbitrary history" check.
// -----------------------------------------------------------------------------
void test_randomized_property() {
    std::cout << "[TEST] button-matrix randomized property (>=" << kMinIterations
              << " iterations)..." << std::endl;

    std::mt19937 rng(0xB17C0DE5u);  // fixed seed for reproducibility

    std::uniform_int_distribution<int> ka_byte(0, 0x1F);  // KEY_ARROWS valid bits
    std::uniform_int_distribution<int> gc_byte(0, 0x07);  // GOTEK_CTRL valid bits
    std::uniform_int_distribution<std::size_t> pick(0, kNumButtons - 1);
    std::uniform_int_distribution<int> coin(0, 1);
    std::uniform_int_distribution<int> seq_len(1, 24);
    std::uniform_int_distribution<int> op_kind(0, 9);  // ~20% unknown ids

    const std::string unknown_ids[] = {"", "ENTER", "nope", "cursor_LEFT",
                                       "gotek_push", "xyz"};
    std::uniform_int_distribution<std::size_t> pick_unknown(
        0, (sizeof(unknown_ids) / sizeof(unknown_ids[0])) - 1);

    int presses = 0, releases = 0, unknowns = 0;

    for (int iter = 0; iter < kMinIterations; ++iter) {
        // --- (a) direct Property-9 check from a random prior + random target --
        ExpectedModel prior;
        prior.key_arrows = static_cast<uint8_t>(ka_byte(rng));
        prior.gotek_ctrl = static_cast<uint8_t>(gc_byte(rng));
        const DefinedButton& target = kButtons[pick(rng)];
        check_press_release(target, prior);

        // --- (b) interleaved random sequence against a live host + model -----
        S760MameHost host;
        ExpectedModel model;  // starts all-clear; mirrors host
        const int n = seq_len(rng);
        for (int s = 0; s < n; ++s) {
            const bool pressed = coin(rng) != 0;
            if (op_kind(rng) < 8) {
                // Defined button: apply to host AND mirror into the model.
                const DefinedButton& b = kButtons[pick(rng)];
                host.apply_button(b.id, pressed);
                model.apply(b, pressed);
                if (pressed) ++presses; else ++releases;
            } else {
                // Unknown id: apply to host; model must NOT change.
                const std::string& u = unknown_ids[pick_unknown(rng)];
                host.apply_button(u, pressed);
                ++unknowns;
            }
            // After EVERY op, both ports must equal the model (this is the
            // "exactly that bit; all others unchanged" invariant over history).
            assert_matches(host, model, "sequence-step");
        }
    }

    // Sanity: the generators exercised presses, releases, and unknown ids.
    assert(presses > 0 && "generator produced no presses (vacuous)");
    assert(releases > 0 && "generator produced no releases (vacuous)");
    assert(unknowns > 0 && "generator produced no unknown-id ops (vacuous)");

    std::cout << "  -> " << kMinIterations << " iterations: " << presses
              << " presses, " << releases << " releases, " << unknowns
              << " unknown-id ops. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==============================================" << std::endl;
    std::cout << "  S-760 Button Matrix Property Test (Prop 9)  " << std::endl;
    std::cout << "==============================================" << std::endl;

    try {
        test_edge_cases();
        test_randomized_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 BUTTON MATRIX PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
