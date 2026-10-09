// Feature: mame-live-backend, Property 5: Frame framing round-trip and payload-length rule
//
// =============================================================================
//  test_prop_frame_roundtrip.cpp — property-based test for the binary frame
//  framing round-trip and the protocol's payload-length rule (spec
//  `mame-live-backend`, task 4.2).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 5: Frame framing round-trip and payload-length rule"
//        Validates: Requirements 5.1, 5.5
//
//  Property 5 (design): For any surface (surfaceId, width, height, format) with
//  a valid payload of length payload_size(format, width, height), parsing the
//  header of build_frame(...) recovers the same surfaceId, width, height, and
//  format; the total message length equals FRAME_HEADER_SIZE +
//  payload_size(format, width, height); and a decoder applying the protocol's
//  payload-length rule accepts the frame (does not discard it).
//
//  Function under test:
//    static std::vector<uint8_t>
//      S760Bridge::build_frame(bridge::SurfaceId id, uint16_t width,
//                              uint16_t height, bridge::PixelFormat format,
//                              const uint8_t* payload, std::size_t payload_len);
//  Header layout (s760_bridge_protocol.hpp):
//    [u8 surfaceId][u16 width LE][u16 height LE][u8 format][payload]
//  Protocol constants: FRAME_HEADER_SIZE == 6, SurfaceId {CRT=0,LCD=1,OLED=2},
//    PixelFormat {RGBA8888=0,MONO1=1}, payload_size(fmt,w,h).
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_bridge.cpp and core/tests/test_prop_crt_gate.cpp. No
//  RapidCheck. A seeded std::mt19937 drives >= 100 randomized iterations plus
//  the three fixed protocol geometries as explicit cases. Each iteration builds
//  a payload of exactly payload_size(format,width,height) random bytes, frames
//  it, and verifies the four round-trip/decode checks below.
// =============================================================================

#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"

#include <cassert>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <random>
#include <vector>

namespace {

using namespace s760;

// Minimum randomized iterations required by the design (>= 100).
constexpr int kMinIterations = 500;

// Little-endian u16 read helper — matches how a decoder reads the LE header
// fields (TS: DataView.getUint16(offset, /*littleEndian=*/true)). Written
// independently from the production encoder so this is a genuine cross-check.
uint16_t read_u16_le(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) |
           (static_cast<uint16_t>(p[1]) << 8);
}

// -----------------------------------------------------------------------------
//  Core property check for a single surface (id, width, height, format).
//
//  Builds a payload of EXACTLY payload_size(format,width,height) random bytes,
//  frames it via S760Bridge::build_frame, then asserts:
//    (1) total message length == FRAME_HEADER_SIZE + payload_size(...).
//    (2) parsed header recovers surfaceId / width / height / format.
//    (3) the payload bytes after the header are byte-identical to the input.
//    (4) the payload-length rule holds (decoder ACCEPTS the frame):
//        (msg.size() - FRAME_HEADER_SIZE) == payload_size(format,width,height).
// -----------------------------------------------------------------------------
void check_surface(bridge::SurfaceId id, uint16_t width, uint16_t height,
                   bridge::PixelFormat format, std::mt19937& rng,
                   const char* label) {
    const std::size_t expected_payload =
        bridge::payload_size(format, width, height);

    // Build a payload of EXACTLY the expected size with random bytes.
    std::vector<uint8_t> payload(expected_payload);
    std::uniform_int_distribution<int> byte_dist(0, 255);
    for (std::size_t i = 0; i < payload.size(); ++i) {
        payload[i] = static_cast<uint8_t>(byte_dist(rng));
    }

    const uint8_t* pptr = payload.empty() ? nullptr : payload.data();
    const std::vector<uint8_t> msg =
        S760Bridge::build_frame(id, width, height, format, pptr, payload.size());
    (void)label;

    // (1) total message length == header + payload_size.
    assert(msg.size() == bridge::FRAME_HEADER_SIZE + expected_payload &&
           "total message length != FRAME_HEADER_SIZE + payload_size(fmt,w,h)");
    assert(msg.size() >= bridge::FRAME_HEADER_SIZE &&
           "framed message shorter than the fixed header");

    // (2) parse the 6-byte header and recover every field.
    bridge::FrameHeader h{};
    h.surfaceId = static_cast<bridge::SurfaceId>(msg[0]);
    h.width     = read_u16_le(&msg[1]);
    h.height    = read_u16_le(&msg[3]);
    h.format    = static_cast<bridge::PixelFormat>(msg[5]);

    assert(h.surfaceId == id && "round-trip surfaceId mismatch");
    assert(h.width == width && "round-trip width mismatch (LE decode)");
    assert(h.height == height && "round-trip height mismatch (LE decode)");
    assert(h.format == format && "round-trip format mismatch");

    // (3) payload after the header is byte-for-byte identical to the input.
    for (std::size_t i = 0; i < expected_payload; ++i) {
        assert(msg[bridge::FRAME_HEADER_SIZE + i] == payload[i] &&
               "payload byte after header differs from input payload");
    }

    // (4) payload-length rule: a decoder re-deriving payload_size from the
    //     parsed header accepts (does not discard) the frame.
    const std::size_t decoded_payload_len = msg.size() - bridge::FRAME_HEADER_SIZE;
    const std::size_t rule_expected =
        bridge::payload_size(h.format, h.width, h.height);
    assert(decoded_payload_len == rule_expected &&
           "payload-length rule failed: decoder would discard the frame");
}

// Pick a random SurfaceId from {CRT, LCD, OLED}.
bridge::SurfaceId random_surface_id(std::mt19937& rng) {
    static const bridge::SurfaceId ids[] = {
        bridge::SurfaceId::CRT, bridge::SurfaceId::LCD, bridge::SurfaceId::OLED};
    std::uniform_int_distribution<int> pick(0, 2);
    return ids[pick(rng)];
}

// Pick a random PixelFormat from {RGBA8888, MONO1}.
bridge::PixelFormat random_format(std::mt19937& rng) {
    std::uniform_int_distribution<int> pick(0, 1);
    return pick(rng) == 0 ? bridge::PixelFormat::RGBA8888
                          : bridge::PixelFormat::MONO1;
}

// -----------------------------------------------------------------------------
//  Explicit cases: the three fixed protocol geometries, in both formats.
// -----------------------------------------------------------------------------
void test_fixed_geometries() {
    std::cout << "[TEST] frame round-trip — fixed protocol geometries..."
              << std::endl;

    std::mt19937 rng(0x5EEDF00Du);

    // The three advertised surface geometries with their canonical formats.
    check_surface(bridge::SurfaceId::CRT, bridge::CRT_WIDTH, bridge::CRT_HEIGHT,
                  bridge::PixelFormat::RGBA8888, rng, "CRT 640x480 RGBA8888");
    check_surface(bridge::SurfaceId::LCD, bridge::LCD_WIDTH, bridge::LCD_HEIGHT,
                  bridge::PixelFormat::MONO1, rng, "LCD 160x64 MONO1");
    check_surface(bridge::SurfaceId::OLED, bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT,
                  bridge::PixelFormat::MONO1, rng, "OLED 128x32 MONO1");

    // Cross the three geometries with the opposite format too, to exercise the
    // round-trip independently of the canonical surface/format pairing.
    check_surface(bridge::SurfaceId::CRT, bridge::CRT_WIDTH, bridge::CRT_HEIGHT,
                  bridge::PixelFormat::MONO1, rng, "CRT geom as MONO1");
    check_surface(bridge::SurfaceId::LCD, bridge::LCD_WIDTH, bridge::LCD_HEIGHT,
                  bridge::PixelFormat::RGBA8888, rng, "LCD geom as RGBA8888");
    check_surface(bridge::SurfaceId::OLED, bridge::GOTEK_WIDTH, bridge::GOTEK_HEIGHT,
                  bridge::PixelFormat::RGBA8888, rng, "OLED geom as RGBA8888");

    std::cout << "  -> fixed-geometry cases PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Randomized property loop (>= 100 iterations) with a seeded PRNG.
//
//  Each iteration picks a random surfaceId, random format, and random small-ish
//  width/height in [1, 256]. The payload is sized to EXACTLY
//  payload_size(format,width,height) so the valid-payload precondition holds.
// -----------------------------------------------------------------------------
void test_randomized_property() {
    std::cout << "[TEST] frame round-trip randomized property (>="
              << kMinIterations << " iterations)..." << std::endl;

    std::mt19937 rng(0xF2A3E117u);  // fixed seed for reproducibility

    // Small-ish dimensions keep RGBA payloads bounded (256*256*4 = 256 KiB max)
    // while still exercising LE encode/decode across the full low/high byte of
    // the u16 header fields.
    std::uniform_int_distribution<int> dim_dist(1, 256);

    int rgba_cases = 0;
    int mono_cases = 0;

    for (int iter = 0; iter < kMinIterations; ++iter) {
        const bridge::SurfaceId id = random_surface_id(rng);
        const bridge::PixelFormat fmt = random_format(rng);
        const uint16_t w = static_cast<uint16_t>(dim_dist(rng));
        const uint16_t h = static_cast<uint16_t>(dim_dist(rng));

        check_surface(id, w, h, fmt, rng, "random");

        if (fmt == bridge::PixelFormat::RGBA8888) {
            ++rgba_cases;
        } else {
            ++mono_cases;
        }
    }

    // Sanity: both formats must have been exercised, otherwise the loop would
    // only cover one side of the payload-size rule.
    assert(rgba_cases > 0 && "generator never produced an RGBA8888 case");
    assert(mono_cases > 0 && "generator never produced a MONO1 case");

    std::cout << "  -> " << kMinIterations << " iterations: "
              << rgba_cases << " RGBA8888, " << mono_cases
              << " MONO1. PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  S-760 Frame Round-Trip Property (Prop 5)" << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_fixed_geometries();
        test_randomized_property();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 FRAME ROUND-TRIP PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
