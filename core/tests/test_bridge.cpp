#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"
#include "s760/s760_libretro_host.hpp"

#include <iostream>
#include <vector>
#include <string>
#include <cassert>
#include <cstdint>
#include <cstring>

// =============================================================================
//  test_bridge.cpp — S760Bridge in-process loopback / integration test.
//
//  Spec: .kiro/specs/ui-consolidation/ (task 3.5, Requirement R5.2).
//
//  Exercises the in-process bridge API end-to-end: construct the bridge (the
//  host may be null per the 3.2 design — the bridge still produces authentic
//  frames/telemetry from defaults), register frame + telemetry callbacks, feed
//  S760ClientMessage JSON through on_input(), and assert the produced binary
//  display frames + telemetry match the protocol contract in
//  s760_bridge_protocol.hpp.
// =============================================================================

namespace {

using namespace s760;

// Collected binary display frames (one per emit_frame call).
struct CapturedFrame {
    std::vector<uint8_t> bytes;
};

// Little-endian u16 read helper (frame header fields are LE on the wire).
uint16_t read_u16_le(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8);
}

// Decode + validate a single framed display message against the protocol:
//   [u8 surfaceId][u16 w LE][u16 h LE][u8 format][payload]
// Returns the parsed header and asserts the payload length matches
// payload_size(format, w, h).
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

// Minimal substring/field presence check for the telemetry JSON. We assert on
// the exact S760ServerTelemetry key set and the fixed geometry values rather
// than pulling in a JSON parser (matches the dependency-free test style).
bool telemetry_has(const std::string& json, const std::string& needle) {
    return json.find(needle) != std::string::npos;
}

// -----------------------------------------------------------------------------
//  Test 1: in-process loopback — send input, assert frame + telemetry response.
// -----------------------------------------------------------------------------
void test_bridge_loopback_frames_and_telemetry() {
    std::cout << "[TEST] S760Bridge in-process loopback (frames + telemetry)..." << std::endl;

    // Per the 3.2 design, a null host is a valid construction for exercising the
    // encode/frame-production paths; the bridge produces authentic-size frames
    // and default telemetry.
    S760Bridge bridge(nullptr);

    std::vector<CapturedFrame> frames;
    std::vector<std::string>   telemetry;

    bridge.set_frame_callback([&](const uint8_t* data, std::size_t len) {
        CapturedFrame cf;
        cf.bytes.assign(data, data + len);
        frames.push_back(std::move(cf));
    });
    bridge.set_telemetry_callback([&](const std::string& json) {
        telemetry.push_back(json);
    });

    // Send a valid input (note on). With a null host this is a no-op on the
    // backend but MUST still parse+accept (returns true).
    assert(bridge.on_input(R"({"type":"NOTE_ON","payload":{"note":60,"velocity":100}})") == true);

    // Produce one round of surfaces + telemetry without advancing the host.
    bridge.push_frames();

    // --- Assert: at least one binary frame per surface (CRT/LCD/OLED) --------
    assert(frames.size() >= 3 && "expected at least 3 display frames (CRT/LCD/OLED)");

    bool saw_crt = false, saw_lcd = false, saw_oled = false;
    for (const auto& f : frames) {
        bridge::FrameHeader h = decode_and_validate_frame(f.bytes);
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

    // --- Assert: a telemetry message matching S760ServerTelemetry shape ------
    assert(!telemetry.empty() && "no telemetry delivered");
    const std::string& t = telemetry.back();
    assert(telemetry_has(t, "\"timestamp\":"));
    assert(telemetry_has(t, "\"fps\":"));
    assert(telemetry_has(t, "\"crtWidth\":640"));
    assert(telemetry_has(t, "\"crtHeight\":480"));
    assert(telemetry_has(t, "\"lcdWidth\":160"));
    assert(telemetry_has(t, "\"lcdHeight\":64"));
    assert(telemetry_has(t, "\"gotekWidth\":128"));
    assert(telemetry_has(t, "\"gotekHeight\":32"));
    assert(telemetry_has(t, "\"peakL\":"));
    assert(telemetry_has(t, "\"peakR\":"));
    assert(telemetry_has(t, "\"activeVoices\":"));
    assert(telemetry_has(t, "\"currentMode\":"));

    std::cout << "  -> delivered " << frames.size() << " frames + "
              << telemetry.size() << " telemetry message(s)." << std::endl;
    std::cout << "  -> S760Bridge Loopback Frame/Telemetry Tests PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 2: on_input accepts valid messages, rejects malformed / unknown.
// -----------------------------------------------------------------------------
void test_bridge_on_input_contract() {
    std::cout << "[TEST] S760Bridge on_input() message contract..." << std::endl;

    S760Bridge bridge(nullptr);

    // Valid messages across the full S760ClientMessage type set -> true.
    assert(bridge.on_input(R"({"type":"BUTTON_PRESS","payload":{"id":"F1"}})") == true);
    assert(bridge.on_input(R"({"type":"BUTTON_RELEASE","payload":{"id":"F1"}})") == true);
    assert(bridge.on_input(R"({"type":"DIAL_DELTA","payload":{"id":"enc1","delta":-3}})") == true);
    assert(bridge.on_input(R"({"type":"MOUSE_MOVE","payload":{"x":0.5,"y":0.25}})") == true);
    assert(bridge.on_input(R"({"type":"MOUSE_CLICK","payload":{"x":0.1,"y":0.9,"button":0}})") == true);
    assert(bridge.on_input(R"({"type":"NOTE_ON","payload":{"note":64,"velocity":90}})") == true);
    assert(bridge.on_input(R"({"type":"NOTE_OFF","payload":{"note":64}})") == true);
    // Unknown fields must be ignored (still a valid, recognized message).
    assert(bridge.on_input(R"({"type":"BUTTON_PRESS","payload":{"id":"F1","bogus":123}})") == true);

    // Malformed JSON -> false.
    assert(bridge.on_input("not json at all") == false);
    assert(bridge.on_input("{ broken ") == false);
    assert(bridge.on_input(R"({"type":)") == false);
    assert(bridge.on_input("") == false);

    // Well-formed JSON but unknown / missing type -> false.
    assert(bridge.on_input(R"({"type":"TELEPORT","payload":{}})") == false);
    assert(bridge.on_input(R"({"payload":{"id":"F1"}})") == false);

    std::cout << "  -> S760Bridge on_input() Contract Tests PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test 3: loopback with a real (unloaded) host — pump() advances + emits.
//  The host is constructed but no core is loaded; pump() still produces the
//  three surfaces + telemetry (CRT sourced from the empty host video frame).
// -----------------------------------------------------------------------------
void test_bridge_pump_with_host() {
    std::cout << "[TEST] S760Bridge pump() with a live (unloaded) host..." << std::endl;

    S760LibretroHost host;
    S760Bridge bridge(&host);

    int frame_count = 0;
    int telemetry_count = 0;
    std::vector<CapturedFrame> frames;

    bridge.set_frame_callback([&](const uint8_t* data, std::size_t len) {
        CapturedFrame cf;
        cf.bytes.assign(data, data + len);
        frames.push_back(std::move(cf));
        ++frame_count;
    });
    bridge.set_telemetry_callback([&](const std::string&) { ++telemetry_count; });

    // A valid note drives the host MIDI queue (no core loaded -> queued only).
    assert(bridge.on_input(R"({"type":"NOTE_ON","payload":{"note":48,"velocity":120}})") == true);

    // Advance one bridge tick.
    bridge.pump();

    // One pump => 3 surfaces + 1 telemetry.
    assert(frame_count >= 3 && "pump() must emit CRT/LCD/OLED frames");
    assert(telemetry_count >= 1 && "pump() must emit telemetry");

    // Every emitted frame must still be well-formed per the protocol.
    for (const auto& f : frames) {
        (void)decode_and_validate_frame(f.bytes);
    }

    std::cout << "  -> S760Bridge pump()+host Tests PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 Bridge Loopback Test Suite " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_bridge_loopback_frames_and_telemetry();
        test_bridge_on_input_contract();
        test_bridge_pump_with_host();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 BRIDGE TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
