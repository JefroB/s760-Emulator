// Feature: mame-live-backend, Property 7: Telemetry carries fixed geometry and bounded fps
//
// =============================================================================
//  test_prop_telemetry.cpp — property-based test for the telemetry encoding
//  (spec `mame-live-backend`, task 4.5).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 7: Telemetry carries fixed geometry and bounded fps"
//        Validates: Requirements 5.3
//
//  Property 7 (design): For any backend telemetry snapshot, the encoded
//  telemetry reports crtWidth=640, crtHeight=480, lcdWidth=160, lcdHeight=64,
//  gotekWidth=128, gotekHeight=32, and a fps value within the range [0, 240].
//
//  Function under test (static, public — s760/s760_bridge.hpp):
//    std::string S760Bridge::encode_telemetry(const bridge::ServerTelemetry& t);
//
//  The bridge::ServerTelemetry struct (s760/s760_bridge_protocol.hpp) has
//  geometry fields that default to the protocol constants (crtWidth=640 etc.)
//  which is the contract this property enforces: telemetry carries FIXED
//  geometry. The fps field is a free value that must land within [0, 240].
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_prop_crt_gate.cpp. No RapidCheck. A seeded std::mt19937
//  drives >= 100 randomized iterations plus explicit fps boundary cases (0 and
//  240). Each iteration constructs a ServerTelemetry with randomized fps (within
//  [0, 240]) and randomized peaks/voices/currentMode/timestamp while LEAVING the
//  geometry fields at their protocol defaults, encodes it, and parses the
//  emitted JSON with a tiny inline number/string extractor to assert the fixed
//  geometry and bounded fps.
// =============================================================================

#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cmath>
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

// -----------------------------------------------------------------------------
//  Tiny inline JSON extractors — NOT a general parser, just enough to pull a
//  numeric value for a top-level `"key":<number>` pair out of the flat object
//  that encode_telemetry() produces. Written independently of the production
//  encoder so the property test is a genuine cross-check of the emitted bytes.
// -----------------------------------------------------------------------------

// Find the substring value immediately following `"key":` up to the next ',' or
// '}'. Returns the raw token (no surrounding quotes stripped). Asserts the key
// is present so a dropped field fails the test loudly.
std::string json_raw_value(const std::string& json, const std::string& key) {
    const std::string needle = "\"" + key + "\":";
    const std::size_t k = json.find(needle);
    assert(k != std::string::npos && "telemetry JSON is missing an expected key");
    std::size_t start = k + needle.size();
    std::size_t end = start;
    while (end < json.size() && json[end] != ',' && json[end] != '}') {
        ++end;
    }
    return json.substr(start, end - start);
}

// Parse a top-level numeric field as a long long (the geometry fields are
// emitted as plain integers by encode_telemetry).
long long json_int(const std::string& json, const std::string& key) {
    return std::stoll(json_raw_value(json, key));
}

// Parse a top-level numeric field as a double (fps is emitted either as an
// integer or a fixed-point decimal by encode_telemetry's num() helper).
double json_double(const std::string& json, const std::string& key) {
    return std::stod(json_raw_value(json, key));
}

// -----------------------------------------------------------------------------
//  The core assertion applied to every generated telemetry snapshot.
//
//  Confirms the emitted JSON carries the FIXED geometry constants and a bounded
//  fps. Also confirms the geometry constants are sourced from the protocol
//  single-source-of-truth (bridge::CRT_WIDTH etc.) so the test cannot silently
//  drift from the contract.
// -----------------------------------------------------------------------------
void check_snapshot(const bridge::ServerTelemetry& t) {
    const std::string json = S760Bridge::encode_telemetry(t);

    // --- Fixed geometry in the emitted JSON ---------------------------------
    assert(json_int(json, "crtWidth")    == 640 && "crtWidth must be 640");
    assert(json_int(json, "crtHeight")   == 480 && "crtHeight must be 480");
    assert(json_int(json, "lcdWidth")    == 160 && "lcdWidth must be 160");
    assert(json_int(json, "lcdHeight")   == 64  && "lcdHeight must be 64");
    assert(json_int(json, "gotekWidth")  == 128 && "gotekWidth must be 128");
    assert(json_int(json, "gotekHeight") == 32  && "gotekHeight must be 32");

    // --- fps within [0, 240] ------------------------------------------------
    const double fps = json_double(json, "fps");
    assert(fps >= 0.0 && fps <= 240.0 && "emitted fps out of [0,240] range");
}

// -----------------------------------------------------------------------------
//  Single-source-of-truth check: the protocol constants ARE the fixed geometry.
// -----------------------------------------------------------------------------
void test_protocol_constants() {
    std::cout << "[TEST] telemetry geometry constants (single source)..."
              << std::endl;

    // The literals this test asserts against must equal the protocol constants
    // in s760_bridge_protocol.hpp — the authoritative source of the geometry.
    assert(bridge::CRT_WIDTH    == 640);
    assert(bridge::CRT_HEIGHT   == 480);
    assert(bridge::LCD_WIDTH    == 160);
    assert(bridge::LCD_HEIGHT   == 64);
    assert(bridge::GOTEK_WIDTH  == 128);
    assert(bridge::GOTEK_HEIGHT == 32);

    // A default-constructed telemetry snapshot inherits those constants, which
    // is the behavioral contract this property enforces.
    const bridge::ServerTelemetry def{};
    assert(def.crtWidth    == bridge::CRT_WIDTH);
    assert(def.crtHeight   == bridge::CRT_HEIGHT);
    assert(def.lcdWidth    == bridge::LCD_WIDTH);
    assert(def.lcdHeight   == bridge::LCD_HEIGHT);
    assert(def.gotekWidth  == bridge::GOTEK_WIDTH);
    assert(def.gotekHeight == bridge::GOTEK_HEIGHT);

    std::cout << "  -> protocol constants PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Explicit fps boundary cases (0 and 240) plus a few fixed interior values.
//  Geometry is left at the protocol defaults, per the contract.
// -----------------------------------------------------------------------------
void test_edge_cases() {
    std::cout << "[TEST] telemetry fps boundary edge cases..." << std::endl;

    const double fps_values[] = {0.0, 240.0, 30.0, 59.94, 60.0, 120.0, 239.999};
    for (double f : fps_values) {
        bridge::ServerTelemetry t{};  // geometry at protocol defaults
        t.fps = f;
        t.timestamp = 123456.0;
        t.peakL = 0.5;
        t.peakR = 0.25;
        t.activeVoices = 7;
        t.currentMode = "PATCH";
        check_snapshot(t);
    }

    std::cout << "  -> fps boundary edge cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  Each iteration generates an fps constrained to [0, 240] and randomized
//  timestamp/peaks/voices/currentMode, while LEAVING geometry at the protocol
//  defaults (the fixed-geometry contract). The emitted JSON must always report
//  the fixed geometry and a bounded fps.
// -----------------------------------------------------------------------------
void test_randomized_property() {
    std::cout << "[TEST] telemetry randomized property (>=" << kMinIterations
              << " iterations)..." << std::endl;

    std::mt19937 rng(0x7E1E3B07u);  // fixed seed for reproducibility

    std::uniform_real_distribution<double> fps_dist(0.0, 240.0);
    std::uniform_real_distribution<double> ts_dist(0.0, 1e12);
    std::uniform_real_distribution<double> peak_dist(0.0, 1.0);
    std::uniform_int_distribution<int> voices_dist(0, 24);
    std::uniform_int_distribution<int> mode_pick(0, 5);
    std::uniform_int_distribution<int> fps_mode(0, 2);

    const char* modes[] = {"", "PERFORM", "PATCH", "SAMPLE", "DISK", "MIDI"};

    int saw_zero_fps = 0;
    int saw_high_fps = 0;

    for (int iter = 0; iter < kMinIterations; ++iter) {
        bridge::ServerTelemetry t{};  // geometry fields left at protocol defaults

        // Generate fps within [0, 240]; occasionally pin the exact boundaries so
        // the loop also exercises them under the randomized path.
        double fps = 0.0;
        switch (fps_mode(rng)) {
            case 0: fps = 0.0;   break;
            case 1: fps = 240.0; break;
            default: fps = fps_dist(rng); break;
        }
        // Clamp defensively to the contract range (the generator already honors
        // it; this makes the input-space constraint explicit).
        if (fps < 0.0)   fps = 0.0;
        if (fps > 240.0) fps = 240.0;
        t.fps = fps;

        t.timestamp    = ts_dist(rng);
        t.peakL        = peak_dist(rng);
        t.peakR        = peak_dist(rng);
        t.activeVoices = voices_dist(rng);
        t.currentMode  = modes[mode_pick(rng)];

        check_snapshot(t);

        if (fps == 0.0)        ++saw_zero_fps;
        if (fps >= 200.0)      ++saw_high_fps;
    }

    // Sanity: the generator must have produced both low and high fps values so
    // the bounded-range assertion is genuinely exercised, not vacuous.
    assert(saw_zero_fps > 0 && "generator never produced fps == 0 (check loop)");
    assert(saw_high_fps > 0 && "generator never produced high fps (check loop)");

    std::cout << "  -> " << kMinIterations << " iterations PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  S-760 Telemetry Property Test (Prop 7)  " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_protocol_constants();
        test_edge_cases();
        test_randomized_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 TELEMETRY PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
