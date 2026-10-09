#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"
#include "s760/s760_host_interface.hpp"
#include "s760/s760_libretro_host.hpp"
#include "s760/s760_drive_manager.hpp"
#include "s760/s760_recorder.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <iostream>
#include <vector>

// =============================================================================
//  test_host_seam.cpp — compile/link + smoke test for the IS760Host seam.
//
//  Spec: .kiro/specs/mame-live-backend/ (task 1.4, Requirements 1.2, 1.7, 5.5).
//
//  Purpose (per task 1.4):
//    1. Prove BOTH a concrete `S760LibretroHost` AND a minimal stub `IS760Host`
//       compile AND link against the `S760Bridge`. Constructing an S760Bridge
//       with each host and exercising push_frames()/pump() is the compile/link
//       proof that both backends satisfy the one Bridge contract (Req 1.2).
//    2. Assert `bridge::PROTOCOL_VERSION == 1` (Req 1.7, 5.5).
//    3. Assert the protocol constants are unchanged: surface geometries
//       (CRT 640x480, LCD 160x64, OLED 128x32), FRAME_HEADER_SIZE == 6, and the
//       SurfaceId / PixelFormat enum values (Req 1.7, 5.5).
//
//  This is a smoke / compile-link test in the dependency-free assert() style of
//  the existing core tests (see test_bridge.cpp). It does NOT modify production
//  code; it only consumes the public headers.
// =============================================================================

namespace {

using namespace s760;

// -----------------------------------------------------------------------------
//  Minimal stub implementing IS760Host.
//
//  Every pure virtual on IS760Host is implemented here. The point is a
//  compile/link proof: if the stub (or S760LibretroHost) diverged from the
//  Bridge's expected host surface, constructing `S760Bridge(IS760Host*)` below
//  would fail to compile or link. The behavior is intentionally trivial — just
//  enough to be a valid, non-abstract backend the Bridge can drive.
// -----------------------------------------------------------------------------
class StubHost : public IS760Host {
public:
    bool init() override { return true; }

    bool run_frame() override {
        ++m_frames;
        return true;
    }

    VideoFrame get_latest_video_frame() const override {
        // Return an empty frame; the Bridge clips/normalizes to the fixed CRT
        // geometry, so an empty host frame still yields a protocol-correct CRT.
        return VideoFrame{};
    }

    bool get_lcd_surface(uint8_t* out, std::size_t len) const override {
        // Report no LCD raster so the Bridge keeps its authentic-blank LCD path
        // (identical to the Core backend's behavior).
        (void)out;
        (void)len;
        return false;
    }

    void send_midi_message(const uint8_t* msg, size_t len) override {
        (void)msg;
        (void)len;
        ++m_midi_messages;
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

    int frames() const { return m_frames; }

private:
    int m_frames = 0;
    int m_midi_messages = 0;
    S760DriveManager m_drive_manager;
    S760SampleRecorder m_recorder;
};

// Little-endian u16 read helper (frame header fields are LE on the wire).
uint16_t read_u16_le(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8);
}

// Decode + validate a single framed display message against the protocol and
// return its parsed header.
bridge::FrameHeader decode_and_validate_frame(const std::vector<uint8_t>& f) {
    assert(f.size() >= bridge::FRAME_HEADER_SIZE && "frame smaller than header");

    bridge::FrameHeader h{};
    h.surfaceId = static_cast<bridge::SurfaceId>(f[0]);
    h.width     = read_u16_le(&f[1]);
    h.height    = read_u16_le(&f[3]);
    h.format    = static_cast<bridge::PixelFormat>(f[5]);

    std::size_t payload_len = f.size() - bridge::FRAME_HEADER_SIZE;
    std::size_t expected = bridge::payload_size(h.format, h.width, h.height);
    assert(payload_len == expected && "payload length != payload_size(format,w,h)");
    (void)payload_len;
    (void)expected;
    return h;
}

// Drive the Bridge with a given host and assert it produces the three
// protocol-correct surfaces. Reused for both backends so the two call sites are
// a direct compile/link proof that each satisfies the one Bridge contract.
void exercise_bridge_contract(IS760Host* host, const char* label) {
    std::cout << "[TEST] S760Bridge drives host: " << label << " ..." << std::endl;

    S760Bridge bridge(host);

    std::vector<std::vector<uint8_t>> frames;
    int telemetry_count = 0;

    bridge.set_frame_callback([&](const uint8_t* data, std::size_t len) {
        frames.emplace_back(data, data + len);
    });
    bridge.set_telemetry_callback([&](const std::string&) { ++telemetry_count; });

    // push_frames() produces surfaces without advancing; pump() advances the
    // host (run_frame()) then emits. Exercising BOTH proves the host surface
    // links for the frame-production and the advance paths.
    bridge.push_frames();
    bridge.pump();

    bool saw_crt = false, saw_lcd = false, saw_oled = false;
    for (const auto& f : frames) {
        bridge::FrameHeader h = decode_and_validate_frame(f);
        switch (h.surfaceId) {
            case bridge::SurfaceId::CRT:
                saw_crt = true;
                assert(h.width == bridge::CRT_WIDTH && h.height == bridge::CRT_HEIGHT);
                assert(h.format == bridge::PixelFormat::RGBA8888);
                break;
            case bridge::SurfaceId::LCD:
                saw_lcd = true;
                assert(h.width == bridge::LCD_WIDTH && h.height == bridge::LCD_HEIGHT);
                assert(h.format == bridge::PixelFormat::MONO1);
                break;
            case bridge::SurfaceId::OLED:
                saw_oled = true;
                assert(h.width == bridge::GOTEK_WIDTH && h.height == bridge::GOTEK_HEIGHT);
                assert(h.format == bridge::PixelFormat::MONO1);
                break;
        }
    }

    assert(saw_crt && "no CRT frame delivered");
    assert(saw_lcd && "no LCD frame delivered");
    assert(saw_oled && "no OLED frame delivered");
    assert(telemetry_count >= 1 && "no telemetry delivered");

    std::cout << "  -> " << label << " satisfies the Bridge contract (compile/link proof)."
              << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 1: both a stub IS760Host and a concrete S760LibretroHost compile/link
//          against the Bridge. Also exercises the nullptr-host construction the
//          Bridge supports for encode-only use.
// -----------------------------------------------------------------------------
void test_both_backends_satisfy_bridge_contract() {
    // Stub backend.
    StubHost stub;
    assert(stub.init() == true);
    exercise_bridge_contract(&stub, "StubHost (IS760Host)");
    assert(stub.frames() >= 1 && "pump() must have advanced the stub host");

    // Concrete Core backend (no core loaded; the Bridge still produces frames).
    S760LibretroHost host;
    exercise_bridge_contract(&host, "S760LibretroHost (Core backend)");

    // nullptr host construction is explicitly allowed (encode-only path).
    exercise_bridge_contract(nullptr, "nullptr host (encode-only)");

    std::cout << "  -> Both backends + nullptr satisfy the one Bridge contract. PASSED!"
              << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 2: PROTOCOL_VERSION is pinned at 1.
// -----------------------------------------------------------------------------
void test_protocol_version_pinned() {
    std::cout << "[TEST] PROTOCOL_VERSION == 1 ..." << std::endl;
    static_assert(bridge::PROTOCOL_VERSION == 1,
                  "PROTOCOL_VERSION must remain 1 (Req 1.7, 5.5)");
    assert(bridge::PROTOCOL_VERSION == 1);
    std::cout << "  -> PROTOCOL_VERSION pinned at 1. PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 3: protocol constants are unchanged (geometry, header size, enum values).
// -----------------------------------------------------------------------------
void test_protocol_constants_unchanged() {
    std::cout << "[TEST] protocol constants unchanged ..." << std::endl;

    // Fixed surface geometries.
    static_assert(bridge::CRT_WIDTH == 640 && bridge::CRT_HEIGHT == 480,
                  "CRT geometry must be 640x480");
    static_assert(bridge::LCD_WIDTH == 160 && bridge::LCD_HEIGHT == 64,
                  "LCD geometry must be 160x64");
    static_assert(bridge::GOTEK_WIDTH == 128 && bridge::GOTEK_HEIGHT == 32,
                  "OLED/Gotek geometry must be 128x32");

    // Fixed binary frame header size.
    static_assert(bridge::FRAME_HEADER_SIZE == 6,
                  "FRAME_HEADER_SIZE must be 6");

    // SurfaceId enum values.
    static_assert(static_cast<uint8_t>(bridge::SurfaceId::CRT) == 0, "SurfaceId::CRT == 0");
    static_assert(static_cast<uint8_t>(bridge::SurfaceId::LCD) == 1, "SurfaceId::LCD == 1");
    static_assert(static_cast<uint8_t>(bridge::SurfaceId::OLED) == 2, "SurfaceId::OLED == 2");

    // PixelFormat enum values.
    static_assert(static_cast<uint8_t>(bridge::PixelFormat::RGBA8888) == 0,
                  "PixelFormat::RGBA8888 == 0");
    static_assert(static_cast<uint8_t>(bridge::PixelFormat::MONO1) == 1,
                  "PixelFormat::MONO1 == 1");

    // Runtime payload_size spot-checks against the two formats.
    assert(bridge::payload_size(bridge::PixelFormat::RGBA8888,
                                bridge::CRT_WIDTH, bridge::CRT_HEIGHT) == 640u * 480u * 4u);
    assert(bridge::payload_size(bridge::PixelFormat::MONO1,
                                bridge::LCD_WIDTH, bridge::LCD_HEIGHT) == ((160u + 7u) / 8u) * 64u);
    assert(bridge::payload_size(bridge::PixelFormat::MONO1,
                                bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT) == ((128u + 7u) / 8u) * 32u);

    std::cout << "  -> protocol constants unchanged. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 Host Seam Test Suite       " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_both_backends_satisfy_bridge_contract();
        test_protocol_version_pinned();
        test_protocol_constants_unchanged();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 HOST SEAM TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
