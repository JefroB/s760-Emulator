#include "s760/s760_backend_selector.hpp"
#include "s760/s760_host_interface.hpp"
#include "s760/s760_drive_manager.hpp"
#include "s760/s760_recorder.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <memory>
#include <string>

// =============================================================================
//  test_backend_selector.cpp — unit tests for the backend selection factory.
//
//  Spec: .kiro/specs/mame-live-backend/ (task 9.2; Requirements 7.1, 7.3, 7.4,
//  7.5).
//
//  These are deterministic UNIT tests (not property tests). They drive the
//  TESTABLE injectable overload
//
//      select_backend(BackendKind requested,
//                     const HostFactory& make_core,
//                     const HostFactory& make_mame)
//
//  with stub HostFactory lambdas so the four selection/fallback paths are
//  exercised WITHOUT the real s760224.img or any MAME artifacts:
//
//    1. default-Core          : requested Core + available -> active Core.
//    2. explicit selection    : requested Mame/Core + available honors the
//                               request; parse_requested_backend token mapping.
//    3. MAME-unavailable       : requested Mame + make_mame null + make_core
//       fallback (R7.4)         available -> active Core, fellBackToCore=true.
//    4. both-unavailable error : requested Mame (or Core) + both null ->
//       (R7.5)                   bothUnavailable=true, host==null, error set.
//
//  "Available" factories return a std::make_unique<StubHost> (a minimal
//  IS760Host, mirroring test_host_seam.cpp); "unavailable" factories return a
//  null unique_ptr. This test does NOT modify production code — it only
//  consumes the public headers. Dependency-free assert() style, matching the
//  existing core tests.
// =============================================================================

namespace {

using namespace s760;

// -----------------------------------------------------------------------------
//  Minimal stub implementing IS760Host (same shape as test_host_seam.cpp).
//
//  Used only as the "available backend" product returned by a stub HostFactory
//  so the selector has a concrete, non-abstract IS760Host to hand back. Its
//  behavior is irrelevant to selection; it just has to be a valid instance.
// -----------------------------------------------------------------------------
class StubHost : public IS760Host {
public:
    bool init() override { return true; }
    bool run_frame() override { return true; }
    VideoFrame get_latest_video_frame() const override { return VideoFrame{}; }
    bool get_lcd_surface(uint8_t* out, std::size_t len) const override {
        (void)out;
        (void)len;
        return false;
    }
    void send_midi_message(const uint8_t* msg, size_t len) override {
        (void)msg;
        (void)len;
    }
    int16_t handle_input_state(unsigned port, unsigned device,
                               unsigned index, unsigned id) override {
        (void)port;
        (void)device;
        (void)index;
        (void)id;
        return 0;
    }
    S760DriveManager& get_drive_manager() override { return m_drive_manager; }
    S760SampleRecorder& get_recorder() override { return m_recorder; }
    const S760SampleRecorder& get_recorder() const override { return m_recorder; }

private:
    S760DriveManager m_drive_manager;
    S760SampleRecorder m_recorder;
};

// An "available" backend factory: constructs + returns a StubHost.
HostFactory make_available() {
    return []() -> std::unique_ptr<IS760Host> {
        return std::make_unique<StubHost>();
    };
}

// An "unavailable" backend factory: returns a null host.
HostFactory make_unavailable() {
    return []() -> std::unique_ptr<IS760Host> {
        return std::unique_ptr<IS760Host>(nullptr);
    };
}

// -----------------------------------------------------------------------------
//  Test 1: default-Core.
//
//  Requirement 7.1 (one backend selected and returned), 7.3 (default to Core
//  when no selection is supplied).
// -----------------------------------------------------------------------------
void test_default_core() {
    std::cout << "[TEST] default-Core selection ..." << std::endl;

    // Injectable overload: Core requested, both factories available.
    BackendSelectionResult r =
        select_backend(BackendKind::Core, make_available(), make_available());
    assert(r.requested == BackendKind::Core);
    assert(r.active == BackendKind::Core);
    assert(r.host != nullptr && "Core available -> host must be non-null");
    assert(r.fellBackToCore == false);
    assert(r.bothUnavailable == false);
    assert(r.error.empty());

    // parse_requested_backend: empty string resolves to the build default.
    assert(parse_requested_backend("", BackendKind::Core) == BackendKind::Core);

    // build_default_backend(): this test build is configured S760_BACKEND=core.
    assert(build_default_backend() == BackendKind::Core &&
           "this build must default to Core (S760_BACKEND=core)");

    // Zero-arg production overload uses build_default_backend() -> Core, and the
    // production make_core always yields a host (library-level availability).
    BackendSelectionResult def = select_backend();
    assert(def.active == BackendKind::Core);
    assert(def.host != nullptr && "default selection must yield a non-null Core host");
    assert(def.bothUnavailable == false);
    assert(def.fellBackToCore == false);

    std::cout << "  -> default-Core selection PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 2: explicit selection.
//
//  Requirement 7.3 (selection driven by a documented input). An explicit
//  request for an AVAILABLE backend is honored exactly.
// -----------------------------------------------------------------------------
void test_explicit_selection() {
    std::cout << "[TEST] explicit backend selection ..." << std::endl;

    // Explicit Mame, available -> active Mame (no fallback).
    BackendSelectionResult m =
        select_backend(BackendKind::Mame, make_available(), make_available());
    assert(m.requested == BackendKind::Mame);
    assert(m.active == BackendKind::Mame);
    assert(m.host != nullptr);
    assert(m.fellBackToCore == false);
    assert(m.bothUnavailable == false);
    assert(m.error.empty());

    // Explicit Core, available -> active Core.
    BackendSelectionResult c =
        select_backend(BackendKind::Core, make_available(), make_available());
    assert(c.requested == BackendKind::Core);
    assert(c.active == BackendKind::Core);
    assert(c.host != nullptr);
    assert(c.fellBackToCore == false);
    assert(c.bothUnavailable == false);

    // parse_requested_backend token mapping (case-insensitive); unknown ->
    // build default.
    assert(parse_requested_backend("mame", BackendKind::Core) == BackendKind::Mame);
    assert(parse_requested_backend("core", BackendKind::Mame) == BackendKind::Core);
    assert(parse_requested_backend("MAME", BackendKind::Core) == BackendKind::Mame);
    assert(parse_requested_backend("Core", BackendKind::Mame) == BackendKind::Core);
    assert(parse_requested_backend("bogus", BackendKind::Core) == BackendKind::Core);
    assert(parse_requested_backend("bogus", BackendKind::Mame) == BackendKind::Mame);

    std::cout << "  -> explicit backend selection PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 3: MAME-unavailable fallback (Requirement 7.4).
//
//  Mame requested but make_mame returns null; make_core is available -> the
//  selector falls back to Core, records the fallback, and returns a non-null
//  Core host without crashing.
// -----------------------------------------------------------------------------
void test_mame_unavailable_fallback() {
    std::cout << "[TEST] MAME-unavailable fallback (R7.4) ..." << std::endl;

    BackendSelectionResult r =
        select_backend(BackendKind::Mame, make_available(), make_unavailable());
    assert(r.requested == BackendKind::Mame);
    assert(r.active == BackendKind::Core && "must fall back to Core");
    assert(r.fellBackToCore == true && "fallback must be recorded");
    assert(r.host != nullptr && "fallback Core host must be non-null");
    assert(r.bothUnavailable == false);
    assert(r.error.empty());

    std::cout << "  -> MAME-unavailable fallback PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 4: both-unavailable error (Requirement 7.5).
//
//  When no backend can be initialized, the selector sets bothUnavailable, leaves
//  host null, populates an observable error, and returns WITHOUT crashing or
//  throwing (so the caller can surface the error and terminate backend startup).
// -----------------------------------------------------------------------------
void test_both_unavailable_error() {
    std::cout << "[TEST] both-unavailable error (R7.5) ..." << std::endl;

    // Mame requested, both factories null -> fall back attempted, both fail.
    BackendSelectionResult m =
        select_backend(BackendKind::Mame, make_unavailable(), make_unavailable());
    assert(m.requested == BackendKind::Mame);
    assert(m.bothUnavailable == true);
    assert(m.host == nullptr && "no backend -> host must be null");
    assert(!m.error.empty() && "observable error must be populated");

    // Core requested, Core factory null -> nothing to fall back to; still the
    // both-unavailable case. Asserting it does not crash/throw.
    BackendSelectionResult c =
        select_backend(BackendKind::Core, make_unavailable(), make_unavailable());
    assert(c.requested == BackendKind::Core);
    assert(c.bothUnavailable == true);
    assert(c.host == nullptr);
    assert(!c.error.empty());

    std::cout << "  -> both-unavailable error PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 Backend Selector Test Suite" << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_default_core();
        test_explicit_selection();
        test_mame_unavailable_fallback();
        test_both_unavailable_error();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 BACKEND SELECTOR TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
