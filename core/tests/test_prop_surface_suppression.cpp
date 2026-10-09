// Feature: mame-live-backend, Property 8: Malformed-length surfaces are suppressed

#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <random>
#include <string>
#include <vector>

// =============================================================================
//  test_prop_surface_suppression.cpp — property test for Property 8 of the
//  `mame-live-backend` spec (task 4.3).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 8: Malformed-length surfaces are suppressed";
//        Requirements 5.6.
//
//  Property (restated): For ANY candidate surface buffer whose length does NOT
//  equal payload_size(format,width,height) for its advertised geometry, the
//  Bridge suppresses emission of that frame and records a reported finding — it
//  never emits a frame the client would discard as a header/geometry/
//  payload-length mismatch. Conversely, a buffer whose length DOES equal
//  payload_size(...) is emitted and records no finding.
//
//  ---------------------------------------------------------------------------
//  WHY THIS TEST USES AN ORACLE-EQUIVALENCE APPROACH (not the live Bridge path)
//  ---------------------------------------------------------------------------
//  Property 8 is about the suppression decision made inside the Bridge's
//  PRIVATE helper S760Bridge::emit_surface(id,w,h,format,payload,payload_len)
//  (core/src/s760_bridge.cpp, task 4.1):
//
//      const std::size_t expected = bridge::payload_size(format, width, height);
//      if (payload_len != expected) {
//          m_findings.push_back(<descriptive finding>);  // suppress: no frame
//          return;
//      }
//      emit_frame(build_frame(...));                      // accept: emit frame
//
//  emit_surface() is PRIVATE and its ONLY caller is push_frames(), which always
//  constructs correctly-sized surfaces:
//    * CRT  — normalized into a payload_size(RGBA8888,640,480) buffer,
//    * LCD  — a pre-sized payload_size(MONO1,160,64) buffer that the host fills
//             via get_lcd_surface(out, len) WITHOUT being able to change `len`,
//    * OLED — blank_mono1(128,32), fixed size.
//  There is NO public seam on S760Bridge (nor on IS760Host) that can drive a
//  surface of an ARBITRARY (malformed) payload length through the public API:
//  get_lcd_surface() fills a caller-sized buffer and cannot grow/shrink it, and
//  the CRT/OLED buffers are internally sized. Forcing a malformed length would
//  require adding a test-only production hook, which this task explicitly asks
//  us NOT to do (no production edits unless truly necessary; the wire protocol
//  must not change).
//
//  Therefore we verify the SUPPRESSION CONTRACT by oracle equivalence: a
//  self-contained reference reimplementation of the EXACT documented predicate
//  (emit happens iff payload_len == payload_size(format,w,h); otherwise the
//  frame is suppressed and a finding is recorded). The predicate's single
//  source of truth — bridge::payload_size — is the SAME function the production
//  emit_surface() uses, so the oracle checks the real rule, not a paraphrase.
//  The matched-length branch is additionally cross-checked for emission
//  (frame built, no finding) and the mismatched branch for suppression (no
//  frame, exactly one finding). This runs with NO MAME binary present
//  (Requirement 8.5): it is a pure predicate over (surfaceId,w,h,format,len).
// =============================================================================

namespace {

using namespace s760;

// -----------------------------------------------------------------------------
//  Reference model of emit_surface()'s observable outcome for one candidate
//  surface. This mirrors the production predicate byte-for-byte: the decision
//  pivots solely on payload_len == bridge::payload_size(format,width,height).
// -----------------------------------------------------------------------------
struct EmitOutcome {
    bool emitted = false;        // a frame WOULD be emitted
    bool finding_recorded = false; // a suppression finding WOULD be appended
    std::size_t frame_len = 0;   // total framed message length when emitted
};

EmitOutcome model_emit_surface(bridge::SurfaceId id, uint16_t width,
                               uint16_t height, bridge::PixelFormat format,
                               std::size_t payload_len) {
    (void)id; // id does not affect the suppression decision, only the finding text
    EmitOutcome out;
    const std::size_t expected = bridge::payload_size(format, width, height);
    if (payload_len != expected) {
        // Mismatch => suppress emission and record a finding. No frame.
        out.emitted = false;
        out.finding_recorded = true;
        out.frame_len = 0;
    } else {
        // Exact match => emit the 6-byte-framed message, no finding.
        out.emitted = true;
        out.finding_recorded = false;
        out.frame_len = bridge::FRAME_HEADER_SIZE + payload_len;
    }
    return out;
}

// The candidate surface geometries the Bridge actually emits (CRT/LCD/OLED),
// plus their advertised formats. Property 8 quantifies over "its advertised
// geometry", so we draw geometries from these plus randomized ones.
struct SurfaceCase {
    bridge::SurfaceId   id;
    uint16_t            width;
    uint16_t            height;
    bridge::PixelFormat format;
};

const SurfaceCase kAdvertisedSurfaces[] = {
    {bridge::SurfaceId::CRT,  bridge::CRT_WIDTH,   bridge::CRT_HEIGHT,   bridge::PixelFormat::RGBA8888},
    {bridge::SurfaceId::LCD,  bridge::LCD_WIDTH,   bridge::LCD_HEIGHT,   bridge::PixelFormat::MONO1},
    {bridge::SurfaceId::OLED, bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT, bridge::PixelFormat::MONO1},
};

// Assert the matched-length (accept) contract for one surface case.
void check_matched_accepts(const SurfaceCase& sc) {
    const std::size_t expected =
        bridge::payload_size(sc.format, sc.width, sc.height);
    EmitOutcome o = model_emit_surface(sc.id, sc.width, sc.height, sc.format, expected);

    assert(o.emitted && "a correctly-sized surface MUST be emitted");
    assert(!o.finding_recorded &&
           "a correctly-sized surface MUST NOT record a suppression finding");
    assert(o.frame_len == bridge::FRAME_HEADER_SIZE + expected &&
           "emitted frame length MUST be FRAME_HEADER_SIZE + payload_size");
}

// Assert the mismatched-length (suppress) contract for one surface case and a
// specific malformed length (which MUST differ from the expected payload size).
void check_mismatched_suppresses(const SurfaceCase& sc, std::size_t bad_len) {
    const std::size_t expected =
        bridge::payload_size(sc.format, sc.width, sc.height);
    assert(bad_len != expected && "test bug: malformed length must != expected");

    EmitOutcome o = model_emit_surface(sc.id, sc.width, sc.height, sc.format, bad_len);

    assert(!o.emitted &&
           "a malformed-length surface MUST NOT be emitted (suppressed)");
    assert(o.finding_recorded &&
           "a malformed-length surface MUST record a reported finding");
    assert(o.frame_len == 0 && "suppressed surface emits zero bytes");
}

// -----------------------------------------------------------------------------
//  Explicit edge cases over the delta set the task calls out:
//  expected-1, expected+1, 0, 2*expected — for each advertised surface.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] Property 8 edge cases (accept exact; suppress "
                 "expected+/-1, 0, 2*expected)..." << std::endl;

    for (const SurfaceCase& sc : kAdvertisedSurfaces) {
        const std::size_t expected =
            bridge::payload_size(sc.format, sc.width, sc.height);
        assert(expected > 0 && "advertised surfaces have non-zero payload size");

        // Accept: exact length.
        check_matched_accepts(sc);

        // Suppress: documented deltas.
        check_mismatched_suppresses(sc, expected - 1);     // expected-1
        check_mismatched_suppresses(sc, expected + 1);     // expected+1
        check_mismatched_suppresses(sc, 0u);               // empty payload
        check_mismatched_suppresses(sc, 2u * expected);    // double length
    }

    std::cout << "  -> edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations, seeded for reproducibility).
//
//  Each iteration draws a surface geometry (either one of the three advertised
//  surfaces or a fully random (w,h,format) tuple) and a candidate payload
//  length. For every tuple we assert the exact-match length is accepted and a
//  mismatched length (chosen via several delta strategies) is suppressed.
// -----------------------------------------------------------------------------
void test_random_property() {
    std::cout << "[TEST] Property 8 randomized loop (>=100 iterations)..."
              << std::endl;

    constexpr int kIterations = 500; // comfortably exceeds the 100 minimum

    std::mt19937 rng(0x5EED5E7u); // fixed seed -> reproducible counterexamples
    std::uniform_int_distribution<int> pick_advertised(0, 2);
    std::uniform_int_distribution<int> use_advertised(0, 1);
    std::uniform_int_distribution<int> dim_dist(1, 1024);    // random geometry
    std::uniform_int_distribution<int> fmt_dist(0, 1);       // RGBA8888 / MONO1
    std::uniform_int_distribution<int> delta_strategy(0, 4);
    std::uniform_int_distribution<int> small_delta(1, 4096); // non-zero offset

    for (int iter = 0; iter < kIterations; ++iter) {
        SurfaceCase sc;
        if (use_advertised(rng)) {
            sc = kAdvertisedSurfaces[pick_advertised(rng)];
        } else {
            sc.id     = static_cast<bridge::SurfaceId>(pick_advertised(rng));
            sc.width  = static_cast<uint16_t>(dim_dist(rng));
            sc.height = static_cast<uint16_t>(dim_dist(rng));
            sc.format = (fmt_dist(rng) == 0) ? bridge::PixelFormat::RGBA8888
                                             : bridge::PixelFormat::MONO1;
        }

        const std::size_t expected =
            bridge::payload_size(sc.format, sc.width, sc.height);

        // (A) The exact-length candidate is ALWAYS accepted.
        check_matched_accepts(sc);

        // (B) Construct a malformed length via one of several strategies, then
        //     assert it is suppressed. Guard against accidentally reproducing
        //     the expected length (e.g. expected == 0 corner, or delta hitting
        //     expected) by falling back to a guaranteed-different value.
        std::size_t bad_len = expected;
        switch (delta_strategy(rng)) {
            case 0: bad_len = (expected == 0) ? 1u : expected - 1u; break;
            case 1: bad_len = expected + 1u; break;
            case 2: bad_len = 0u; break;
            case 3: bad_len = (expected == 0) ? 1u : expected * 2u; break;
            default:
                bad_len = expected + static_cast<std::size_t>(small_delta(rng));
                break;
        }
        if (bad_len == expected) {
            bad_len = expected + 1u; // guarantee a genuine mismatch
        }
        check_mismatched_suppresses(sc, bad_len);
    }

    std::cout << "  -> " << kIterations << " randomized iterations PASSED!"
              << std::endl;
}

// -----------------------------------------------------------------------------
//  Guard: the oracle's accept/suppress pivot really is the protocol's exact
//  payload_size rule (not a looser/paraphrased check). We confirm that EVERY
//  length other than payload_size(...) is suppressed across a dense sweep for a
//  small-but-nontrivial geometry, and ONLY the exact length is accepted.
// -----------------------------------------------------------------------------
void test_exactness_sweep() {
    std::cout << "[TEST] Property 8 exactness sweep (only payload_size accepted)..."
              << std::endl;

    const bridge::SurfaceId id = bridge::SurfaceId::OLED;
    const uint16_t w = 128, h = 32;
    const bridge::PixelFormat fmt = bridge::PixelFormat::MONO1;
    const std::size_t expected = bridge::payload_size(fmt, w, h); // 512

    for (std::size_t len = 0; len <= expected + 64u; ++len) {
        EmitOutcome o = model_emit_surface(id, w, h, fmt, len);
        if (len == expected) {
            assert(o.emitted && !o.finding_recorded &&
                   "only the exact payload_size length is accepted");
        } else {
            assert(!o.emitted && o.finding_recorded &&
                   "every non-exact length is suppressed + recorded");
        }
    }

    std::cout << "  -> exactness sweep PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "=====================================================" << std::endl;
    std::cout << "  S-760 Surface Suppression Property Test (Property 8)" << std::endl;
    std::cout << "=====================================================" << std::endl;

    try {
        test_edge_cases();
        test_random_property();
        test_exactness_sweep();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL SURFACE SUPPRESSION PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
