#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <iostream>
#include <string>
#include <cassert>

// =============================================================================
//  test_currentmode.cpp — S760Bridge telemetry currentMode unit test.
//
//  Spec: .kiro/specs/mame-live-backend/ (task 4.6, Requirement R5.4).
//
//  R5.4: "WHERE a currentMode is derivable from genuine OS/display state, THE
//  Bridge SHALL report that value as the telemetry currentMode string;
//  otherwise THE Bridge SHALL report the EMPTY string as currentMode and SHALL
//  NOT report invented or fabricated mode content."
//
//  This UNIT test (not a property test) covers both branches of that rule:
//
//    1. NON-DERIVABLE branch (default): a freshly constructed S760Bridge has no
//       source of a derived mode (the derivation hook is future work and there
//       is no public setter). The Bridge's m_current_mode member therefore
//       defaults to the EMPTY string. We assert current_telemetry() reports
//       currentMode == "" and that encode_telemetry() emits "currentMode":""
//       — i.e. NO invented mode such as the old "PERFORM" default.
//
//    2. DERIVABLE branch: when a mode IS available, it is reported VERBATIM.
//       Since the Bridge exposes no public setter for a derived mode yet, the
//       testable seam for "report derived value where available" is the
//       telemetry-encoding boundary: encode_telemetry() on a ServerTelemetry
//       whose currentMode is a non-empty derived value (e.g. "SAMPLE") must
//       emit that exact value, "currentMode":"SAMPLE". This exercises the
//       reporting side of R5.4 without fabricating any state.
//
//  NOTE on future work: the derived-mode SOURCE (deriving a mode from genuine
//  OS/display state and populating m_current_mode) is not yet implemented and
//  there is no public setter on S760Bridge. The telemetry-encoding boundary is
//  the current testable seam for the "report derived value" side of R5.4; when
//  a derivation hook/setter is added, this test should also drive that path.
// =============================================================================

namespace {

using namespace s760;

// True if `needle` occurs anywhere in `json` (dependency-free check, matching
// the style of test_bridge.cpp).
bool contains(const std::string& json, const std::string& needle) {
    return json.find(needle) != std::string::npos;
}

// -----------------------------------------------------------------------------
//  Branch 1: NON-DERIVABLE (default) — currentMode is the EMPTY string, never
//  an invented value.
// -----------------------------------------------------------------------------
void test_currentmode_non_derivable_is_empty() {
    std::cout << "[TEST] currentMode non-derivable branch -> empty string..." << std::endl;

    // A null host is a valid construction for exercising the telemetry/encode
    // paths (see test_bridge.cpp). No derived mode source exists, so the
    // Bridge's currentMode must default to "".
    S760Bridge bridge(nullptr);

    bridge::ServerTelemetry t = bridge.current_telemetry();

    // The snapshot must carry an EMPTY currentMode (no invented "PERFORM" etc.).
    assert(t.currentMode.empty() && "non-derivable currentMode must be empty");

    // Encoded JSON must contain exactly "currentMode":"" (empty value), and must
    // NOT contain the previously-invented "PERFORM" default.
    std::string json = S760Bridge::encode_telemetry(t);
    assert(contains(json, "\"currentMode\":\"\"") &&
           "encoded telemetry must report currentMode as empty string");
    assert(!contains(json, "PERFORM") &&
           "encoded telemetry must not invent a mode (e.g. PERFORM)");

    std::cout << "  -> non-derivable branch reports empty currentMode (no invention). PASSED!"
              << std::endl;
}

// -----------------------------------------------------------------------------
//  Branch 2: DERIVABLE — when a mode IS available it is reported VERBATIM at the
//  telemetry-encoding boundary.
// -----------------------------------------------------------------------------
void test_currentmode_derivable_is_reported_verbatim() {
    std::cout << "[TEST] currentMode derivable branch -> reported verbatim..." << std::endl;

    // Simulate a derived mode becoming available: a ServerTelemetry whose
    // currentMode holds a genuine derived value. encode_telemetry must emit it
    // exactly, unchanged.
    bridge::ServerTelemetry t;
    t.currentMode = "SAMPLE";

    std::string json = S760Bridge::encode_telemetry(t);
    assert(contains(json, "\"currentMode\":\"SAMPLE\"") &&
           "encoded telemetry must report the derived mode verbatim");

    // A different derived value is likewise reported verbatim (guards against a
    // hard-coded string).
    bridge::ServerTelemetry t2;
    t2.currentMode = "EDIT";
    std::string json2 = S760Bridge::encode_telemetry(t2);
    assert(contains(json2, "\"currentMode\":\"EDIT\"") &&
           "encoded telemetry must report any derived mode verbatim");
    assert(!contains(json2, "SAMPLE") &&
           "derived mode must not leak a value from an unrelated snapshot");

    std::cout << "  -> derivable branch reports the derived mode verbatim. PASSED!"
              << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 currentMode Telemetry Tests " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_currentmode_non_derivable_is_empty();
        test_currentmode_derivable_is_reported_verbatim();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 currentMode TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
