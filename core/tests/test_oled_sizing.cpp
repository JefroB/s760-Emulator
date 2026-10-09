#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <vector>

// =============================================================================
//  test_oled_sizing.cpp — unit test for the OLED authentic-blank surface sizing.
//
//  Spec: .kiro/specs/mame-live-backend/ (task 6.5, Requirement 4.7).
//
//  Requirement 4.7: the OLED_Surface (SurfaceId::OLED, Gotek drive-bay readout)
//  is React-owned — the MAME_Driver does not emulate the Gotek OLED. The
//  Bridge emits an authentic-blank 128x32 MONO1 OLED surface whose payload
//  length equals payload_size(MONO1, 128, 32), so the client always has a
//  stable surface to composite.
//
//  This is a UNIT test in the dependency-free assert() style of the existing
//  core tests (see test_bridge.cpp / test_host_seam.cpp). It constructs an
//  S760Bridge with a nullptr host (valid encode-only construction), captures
//  the emitted frames via a frame callback, finds the OLED frame (surfaceId
//  byte == 2), and asserts its geometry, format, framing length, payload
//  length, and that the payload is authentic-blank (all zero). It does NOT
//  modify production code; it only consumes the public headers.
// =============================================================================

namespace {

using namespace s760;

// Little-endian u16 read helper (frame header fields are LE on the wire).
uint16_t read_u16_le(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8);
}

// -----------------------------------------------------------------------------
//  Test 1: payload_size(MONO1, 128, 32) is the single source of truth == 512.
//
//  MONO1 packs 8 pixels/byte with row-byte alignment, so the payload is
//  ceil(128/8) * 32 == 16 * 32 == 512 bytes.
// -----------------------------------------------------------------------------
void test_oled_payload_size_constant() {
    std::cout << "[TEST] payload_size(MONO1, 128, 32) == 512 ..." << std::endl;

    const std::size_t expected =
        bridge::payload_size(bridge::PixelFormat::MONO1,
                             bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT);
    assert(expected == 512u && "payload_size(MONO1,128,32) must be 512");

    // Geometry constants are the protocol's advertised OLED/Gotek geometry.
    assert(bridge::GOTEK_WIDTH == 128);
    assert(bridge::GOTEK_HEIGHT == 32);

    std::cout << "  -> payload_size(MONO1,128,32) == " << expected
              << " (ceil(128/8)*32). PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 2: the Bridge emits a 128x32 MONO1 authentic-blank OLED surface.
// -----------------------------------------------------------------------------
void test_oled_authentic_blank_surface_sizing() {
    std::cout << "[TEST] OLED authentic-blank 128x32 MONO1 surface sizing ..." << std::endl;

    // A nullptr host is a valid encode-only construction (per the Bridge design)
    // and is sufficient here: the OLED surface is React-owned and emitted as an
    // authentic-blank MONO1 buffer regardless of the backend (Requirement 4.7).
    S760Bridge bridge(nullptr);

    std::vector<std::vector<uint8_t>> frames;
    bridge.set_frame_callback([&](const uint8_t* data, std::size_t len) {
        frames.emplace_back(data, data + len);
    });

    // Produce one round of surfaces without advancing the host.
    bridge.push_frames();

    // payload_size(MONO1, 128, 32) is the single source of truth for the
    // expected OLED payload length.
    const std::size_t expected_payload =
        bridge::payload_size(bridge::PixelFormat::MONO1,
                             bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT);
    assert(expected_payload == 512u);

    // Find the OLED frame by its surfaceId byte (== 2).
    const std::vector<uint8_t>* oled = nullptr;
    for (const auto& f : frames) {
        assert(f.size() >= bridge::FRAME_HEADER_SIZE && "frame smaller than header");
        if (f[0] == static_cast<uint8_t>(bridge::SurfaceId::OLED)) {
            assert(oled == nullptr && "more than one OLED frame emitted");
            oled = &f;
        }
    }
    assert(oled != nullptr && "no OLED frame (surfaceId == 2) delivered");

    const std::vector<uint8_t>& f = *oled;

    // 1. Header: width (LE) == 128, height (LE) == 32, format == MONO1 (1).
    const uint16_t width  = read_u16_le(&f[1]);
    const uint16_t height = read_u16_le(&f[3]);
    const uint8_t  format = f[5];
    assert(width == bridge::GOTEK_WIDTH && "OLED header width must be 128");
    assert(height == bridge::GOTEK_HEIGHT && "OLED header height must be 32");
    assert(format == static_cast<uint8_t>(bridge::PixelFormat::MONO1) &&
           "OLED format must be MONO1 (1)");

    // 2. Total frame length == FRAME_HEADER_SIZE + payload_size(MONO1,128,32)
    //    == 6 + 512 == 518.
    const std::size_t expected_total = bridge::FRAME_HEADER_SIZE + expected_payload;
    assert(expected_total == 518u);
    assert(f.size() == expected_total && "OLED frame length must be 6 + 512 == 518");

    // 3. Payload length (frame.size() - 6) == payload_size(MONO1,128,32) == 512.
    const std::size_t payload_len = f.size() - bridge::FRAME_HEADER_SIZE;
    assert(payload_len == expected_payload && "OLED payload length must be 512");

    // 4. The OLED payload is authentic-blank (all 512 bytes zero).
    for (std::size_t i = bridge::FRAME_HEADER_SIZE; i < f.size(); ++i) {
        assert(f[i] == 0u && "OLED payload must be authentic-blank (all zero)");
    }

    std::cout << "  -> OLED frame: " << width << "x" << height
              << " MONO1, total " << f.size() << " bytes ("
              << bridge::FRAME_HEADER_SIZE << " header + " << payload_len
              << " payload), authentic-blank. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 OLED Sizing Unit Test      " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_oled_payload_size_constant();
        test_oled_authentic_blank_surface_sizing();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 OLED SIZING TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
