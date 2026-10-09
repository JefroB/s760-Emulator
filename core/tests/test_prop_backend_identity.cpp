// Feature: mame-live-backend, Property 6: Framing and telemetry bytes are backend-independent
//
// =============================================================================
//  test_prop_backend_identity.cpp — property-based test proving the framed
//  binary bytes and the telemetry field set the S760Bridge produces are
//  backend-independent (spec `mame-live-backend`, task 9.4).
//
//  Spec: .kiro/specs/mame-live-backend/
//        design "Property 6: Framing and telemetry bytes are backend-independent"
//        Validates: Requirements 5.2, 7.2
//
//  Property 6 (design): For any identical surface content and identical
//  telemetry snapshot, the framed binary bytes and the telemetry field set
//  produced for the MAME_Backend are byte-for-byte equal to those produced for
//  the Core_Backend (surfaceId set {0,1,2}, pixel-format set, 6-byte framing,
//  and telemetry fields are independent of which backend is active).
//
//  Key insight (design): S760Bridge::build_frame(...) and
//  S760Bridge::encode_telemetry(...) are STATIC and backend-independent by
//  construction — they take surface/telemetry inputs, not a host. The property
//  is that driving the Bridge with EITHER backend yields IDENTICAL bytes for
//  IDENTICAL inputs. This test validates both facets:
//
//    (A) End-to-end two-stub equality (the most direct validation of
//        "MAME bytes == Core bytes"): construct TWO IS760Host stubs — a
//        "CoreLike" stub and a "MameLike" stub — made to present IDENTICAL
//        surface content (same VideoFrame, same LCD behavior) and identical
//        telemetry sources (default recorders => identical zero peaks). Drive an
//        S760Bridge with each stub through the SAME op sequence (so their frame
//        counters match => identical telemetry timestamps), capture the emitted
//        frames + telemetry via callbacks, and assert the two byte streams are
//        byte-for-byte identical (same frame count, same bytes each; same
//        telemetry strings).
//
//    (B) Static-function determinism / backend-independence: for randomized
//        (surfaceId,w,h,format,payload) build_frame produces identical bytes on
//        repeated/independent calls (there is no backend input), and for a
//        randomized ServerTelemetry encode_telemetry produces identical bytes.
//
//  Style: dependency-free, self-contained assert() executable in the manner of
//  core/tests/test_bridge.cpp, test_host_seam.cpp, and
//  test_prop_frame_roundtrip.cpp. No RapidCheck. A seeded std::mt19937 drives
//  >= 100 randomized iterations.
// =============================================================================

#include "s760/s760_bridge.hpp"
#include "s760/s760_bridge_protocol.hpp"
#include "s760/s760_host_interface.hpp"
#include "s760/s760_libretro_host.hpp"
#include "s760/s760_drive_manager.hpp"
#include "s760/s760_recorder.hpp"

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
constexpr int kMinIterations = 200;

// -----------------------------------------------------------------------------
//  Configurable IS760Host stub.
//
//  Both the "CoreLike" and the "MameLike" stub are instances of this one class;
//  the ONLY thing that differs is a human-readable label. Both present IDENTICAL
//  surface content and identical telemetry sources (default recorder => zero
//  peaks). This models the property's precondition "identical surface content
//  and identical telemetry snapshot": the two bridges driven by these stubs must
//  produce byte-for-byte identical frames + telemetry regardless of which stub
//  (which "backend") is active.
//
//  The two stubs intentionally differ in internal strategy to mimic the real
//  Core vs MAME backends without needing the MAME binary:
//    * CoreLike  — like S760LibretroHost, returns false from get_lcd_surface()
//                  so the Bridge keeps its authentic-blank LCD path.
//    * MameLike  — exposes an LCD raster via get_lcd_surface(), but when its
//                  configured LCD content is all-zero it fills an all-zero (off)
//                  buffer — i.e. byte-identical to CoreLike's authentic-blank
//                  LCD for identical (blank) content. For non-blank identical
//                  content both stubs are driven to the same bytes.
//
//  For the end-to-end equality test we drive BOTH with identical CRT content and
//  identical (blank) LCD content, which is exactly the "identical surface
//  content" precondition of Property 6.
// -----------------------------------------------------------------------------
class ConfigurableHost : public IS760Host {
public:
    enum class LcdStrategy {
        ReturnFalse,  // Core-like: expose no LCD raster (Bridge blanks it)
        FillBuffer    // MAME-like: fill the buffer from configured LCD content
    };

    explicit ConfigurableHost(LcdStrategy strat) : m_lcd_strategy(strat) {}

    // Set the CRT content both stubs will return identically.
    void set_video_frame(const VideoFrame& vf) { m_video = vf; }

    // Set the MONO1 LCD content the FillBuffer strategy will emit. Must be
    // payload_size(MONO1,160,64) bytes. For the identical-content property we
    // keep this all-zero so the FillBuffer path is byte-identical to the
    // ReturnFalse (authentic-blank) path.
    void set_lcd_content(const std::vector<uint8_t>& lcd) { m_lcd = lcd; }

    bool init() override { return true; }

    bool run_frame() override {
        ++m_frames;
        return true;
    }

    VideoFrame get_latest_video_frame() const override { return m_video; }

    bool get_lcd_surface(uint8_t* out, std::size_t len) const override {
        if (m_lcd_strategy == LcdStrategy::ReturnFalse) {
            return false; // Bridge keeps its authentic-blank LCD (all-zero).
        }
        // FillBuffer: copy configured content (defaults to all-zero => identical
        // to the authentic-blank buffer the Bridge pre-fills).
        if (out == nullptr) return false;
        for (std::size_t i = 0; i < len; ++i) {
            out[i] = (i < m_lcd.size()) ? m_lcd[i] : 0u;
        }
        return true;
    }

    void send_midi_message(const uint8_t* msg, size_t len) override {
        (void)msg;
        (void)len;
    }

    int16_t handle_input_state(unsigned, unsigned, unsigned, unsigned) override {
        return 0;
    }

    S760DriveManager& get_drive_manager() override { return m_drive_manager; }

    S760SampleRecorder& get_recorder() override { return m_recorder; }
    const S760SampleRecorder& get_recorder() const override { return m_recorder; }

    int frames() const { return m_frames; }

private:
    LcdStrategy          m_lcd_strategy;
    VideoFrame           m_video;
    std::vector<uint8_t> m_lcd;
    int                  m_frames = 0;
    S760DriveManager     m_drive_manager;
    S760SampleRecorder   m_recorder;
};

// Capture sink: records every emitted binary frame and every telemetry string
// from one Bridge, in emission order.
struct Capture {
    std::vector<std::vector<uint8_t>> frames;
    std::vector<std::string>          telemetry;
};

// Little-endian u16 read helper (frame header fields are LE on the wire).
uint16_t read_u16_le(const uint8_t* p) {
    return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8);
}

// Build a VideoFrame of fixed CRT geometry with random pixels (seeded).
VideoFrame make_random_crt_frame(std::mt19937& rng) {
    VideoFrame vf;
    vf.width  = bridge::CRT_WIDTH;
    vf.height = bridge::CRT_HEIGHT;
    vf.rgba_pixels.resize(static_cast<std::size_t>(vf.width) * vf.height);
    std::uniform_int_distribution<uint32_t> pix(0u, 0xFFFFFFFFu);
    for (auto& p : vf.rgba_pixels) p = pix(rng);
    return vf;
}

// Drive a Bridge over `host` through a SINGLE push_frames() (no advance) and
// capture its output. push_frames() produces the three surfaces + one telemetry
// message from the host's current state WITHOUT touching the frame counter, so
// two bridges constructed fresh and pushed once share frame counter 0 => their
// telemetry timestamps match.
Capture capture_push(IS760Host* host) {
    S760Bridge bridge(host);
    Capture cap;
    bridge.set_frame_callback([&](const uint8_t* data, std::size_t len) {
        cap.frames.emplace_back(data, data + len);
    });
    bridge.set_telemetry_callback([&](const std::string& json) {
        cap.telemetry.push_back(json);
    });
    bridge.push_frames();
    return cap;
}

// Assert two captures are byte-for-byte identical (same frame count, same bytes
// each, same telemetry strings). This is the core Property-6 assertion.
void assert_captures_identical(const Capture& a, const Capture& b,
                               const char* ctx) {
    assert(a.frames.size() == b.frames.size() &&
           "backend frame COUNT differs");
    for (std::size_t i = 0; i < a.frames.size(); ++i) {
        assert(a.frames[i].size() == b.frames[i].size() &&
               "backend frame LENGTH differs");
        assert(a.frames[i] == b.frames[i] &&
               "backend frame BYTES differ (framing is not backend-independent)");
    }
    assert(a.telemetry.size() == b.telemetry.size() &&
           "backend telemetry COUNT differs");
    for (std::size_t i = 0; i < a.telemetry.size(); ++i) {
        assert(a.telemetry[i] == b.telemetry[i] &&
               "backend telemetry BYTES differ (telemetry is not backend-independent)");
    }
    (void)ctx;
}

// Verify a capture carries exactly the protocol surface set {0:CRT,1:LCD,2:OLED}
// with the fixed geometry + canonical formats and 6-byte framing. This asserts
// the "surfaceId set, pixel-format set, 6-byte framing" clause of Property 6.
void assert_protocol_surface_set(const Capture& cap) {
    bool saw_crt = false, saw_lcd = false, saw_oled = false;
    for (const auto& f : cap.frames) {
        assert(f.size() >= bridge::FRAME_HEADER_SIZE && "frame smaller than header");
        auto id   = static_cast<bridge::SurfaceId>(f[0]);
        uint16_t w = read_u16_le(&f[1]);
        uint16_t h = read_u16_le(&f[3]);
        auto fmt  = static_cast<bridge::PixelFormat>(f[5]);
        std::size_t payload = f.size() - bridge::FRAME_HEADER_SIZE;
        assert(payload == bridge::payload_size(fmt, w, h) &&
               "payload length != payload_size(fmt,w,h)");
        switch (id) {
            case bridge::SurfaceId::CRT:
                saw_crt = true;
                assert(w == bridge::CRT_WIDTH && h == bridge::CRT_HEIGHT);
                assert(fmt == bridge::PixelFormat::RGBA8888);
                break;
            case bridge::SurfaceId::LCD:
                saw_lcd = true;
                assert(w == bridge::LCD_WIDTH && h == bridge::LCD_HEIGHT);
                assert(fmt == bridge::PixelFormat::MONO1);
                break;
            case bridge::SurfaceId::OLED:
                saw_oled = true;
                assert(w == bridge::GOTEK_WIDTH && h == bridge::GOTEK_HEIGHT);
                assert(fmt == bridge::PixelFormat::MONO1);
                break;
        }
    }
    assert(saw_crt && saw_lcd && saw_oled &&
           "capture is missing one of the {CRT,LCD,OLED} surfaces");
    assert(!cap.telemetry.empty() && "capture carries no telemetry");
}

// -----------------------------------------------------------------------------
//  Test A: end-to-end two-stub (two-backend) byte-identity property.
//
//  >= 100 iterations. Each iteration generates a random CRT VideoFrame and sets
//  BOTH stubs to return that IDENTICAL frame (and identical all-zero LCD
//  content). Drives one Bridge per stub via push_frames() and asserts the two
//  captures are byte-for-byte identical, AND that each capture carries the full
//  protocol surface set with 6-byte framing.
// -----------------------------------------------------------------------------
void test_end_to_end_backend_identity() {
    std::cout << "[TEST] end-to-end two-backend byte-identity (>="
              << kMinIterations << " iterations)..." << std::endl;

    std::mt19937 rng(0x5760B6DEu); // fixed seed for reproducibility

    const std::vector<uint8_t> blank_lcd(
        bridge::payload_size(bridge::PixelFormat::MONO1,
                             bridge::LCD_WIDTH, bridge::LCD_HEIGHT), 0u);

    for (int iter = 0; iter < kMinIterations; ++iter) {
        // Identical surface content presented to BOTH backends.
        VideoFrame vf = make_random_crt_frame(rng);

        ConfigurableHost core_like(ConfigurableHost::LcdStrategy::ReturnFalse);
        ConfigurableHost mame_like(ConfigurableHost::LcdStrategy::FillBuffer);
        core_like.set_video_frame(vf);
        mame_like.set_video_frame(vf);
        core_like.set_lcd_content(blank_lcd);
        mame_like.set_lcd_content(blank_lcd);

        // Both bridges are fresh (frame counter 0) and pushed exactly once, so
        // their telemetry timestamps match => telemetry must be byte-identical.
        Capture core_cap = capture_push(&core_like);
        Capture mame_cap = capture_push(&mame_like);

        assert_protocol_surface_set(core_cap);
        assert_protocol_surface_set(mame_cap);
        assert_captures_identical(core_cap, mame_cap, "two-stub identical content");
    }

    std::cout << "  -> " << kMinIterations
              << " iterations: Core and MAME stubs produced byte-identical "
                 "frames + telemetry. PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test B1: cross-check against the real Core backend (S760LibretroHost).
//
//  An unloaded S760LibretroHost returns an empty VideoFrame and false from
//  get_lcd_surface() => the Bridge produces an authentic-blank CRT + blank LCD +
//  blank OLED. A CoreLike stub configured with the SAME (empty) content must
//  yield byte-identical output, proving the stubs faithfully model the real
//  backend's wire bytes.
// -----------------------------------------------------------------------------
void test_against_real_core_backend() {
    std::cout << "[TEST] stub vs real S760LibretroHost byte-identity..."
              << std::endl;

    S760LibretroHost real_core; // unloaded: empty frame, no LCD raster

    ConfigurableHost stub(ConfigurableHost::LcdStrategy::ReturnFalse);
    // Leave the stub's video frame empty (default) and LCD content empty, to
    // match the unloaded real core.

    Capture real_cap = capture_push(&real_core);
    Capture stub_cap = capture_push(&stub);

    assert_protocol_surface_set(real_cap);
    assert_protocol_surface_set(stub_cap);
    assert_captures_identical(real_cap, stub_cap,
                              "real core vs CoreLike stub (empty content)");

    std::cout << "  -> real Core backend and CoreLike stub produced byte-"
                 "identical frames + telemetry. PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test B2: static build_frame determinism / backend-independence.
//
//  build_frame has NO backend input, so for any (id,w,h,format,payload) it must
//  produce identical bytes on repeated/independent calls. >= 100 iterations.
// -----------------------------------------------------------------------------
void test_build_frame_determinism() {
    std::cout << "[TEST] build_frame determinism (>=" << kMinIterations
              << " iterations)..." << std::endl;

    std::mt19937 rng(0xB1A5E117u);
    std::uniform_int_distribution<int> dim(1, 64);
    std::uniform_int_distribution<int> byte_dist(0, 255);

    const bridge::SurfaceId ids[] = {bridge::SurfaceId::CRT,
                                     bridge::SurfaceId::LCD,
                                     bridge::SurfaceId::OLED};
    std::uniform_int_distribution<int> pick_id(0, 2);
    std::uniform_int_distribution<int> pick_fmt(0, 1);

    for (int iter = 0; iter < kMinIterations; ++iter) {
        bridge::SurfaceId id = ids[pick_id(rng)];
        bridge::PixelFormat fmt = pick_fmt(rng) == 0
                                      ? bridge::PixelFormat::RGBA8888
                                      : bridge::PixelFormat::MONO1;
        uint16_t w = static_cast<uint16_t>(dim(rng));
        uint16_t h = static_cast<uint16_t>(dim(rng));

        std::vector<uint8_t> payload(bridge::payload_size(fmt, w, h));
        for (auto& b : payload) b = static_cast<uint8_t>(byte_dist(rng));
        const uint8_t* pptr = payload.empty() ? nullptr : payload.data();

        auto f1 = S760Bridge::build_frame(id, w, h, fmt, pptr, payload.size());
        auto f2 = S760Bridge::build_frame(id, w, h, fmt, pptr, payload.size());
        assert(f1 == f2 && "build_frame is not deterministic for identical input");
    }

    std::cout << "  -> build_frame is deterministic / backend-independent. "
                 "PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
//  Test B3: static encode_telemetry determinism / backend-independence.
//
//  encode_telemetry has NO backend input, so for any ServerTelemetry snapshot it
//  must produce identical bytes on repeated/independent calls. >= 100 iterations
//  over randomized but protocol-valid telemetry (fixed geometry; fps in [0,240];
//  random peaks/voices/timestamp/mode).
// -----------------------------------------------------------------------------
void test_encode_telemetry_determinism() {
    std::cout << "[TEST] encode_telemetry determinism (>=" << kMinIterations
              << " iterations)..." << std::endl;

    std::mt19937 rng(0x7E1E3717u);
    std::uniform_real_distribution<double> peak(0.0, 1.0);
    std::uniform_real_distribution<double> fps(0.0, 240.0);
    std::uniform_real_distribution<double> ts(0.0, 1.0e9);
    std::uniform_int_distribution<int> voices(0, 24);
    std::uniform_int_distribution<int> mode_pick(0, 3);
    const char* modes[] = {"", "PERFORM", "PATCH", "SAMPLE"};

    for (int iter = 0; iter < kMinIterations; ++iter) {
        bridge::ServerTelemetry t; // geometry fields default to protocol consts
        t.timestamp    = ts(rng);
        t.fps          = fps(rng);
        t.peakL        = peak(rng);
        t.peakR        = peak(rng);
        t.activeVoices = voices(rng);
        t.currentMode  = modes[mode_pick(rng)];

        std::string a = S760Bridge::encode_telemetry(t);
        std::string b = S760Bridge::encode_telemetry(t);
        assert(a == b &&
               "encode_telemetry is not deterministic for identical snapshot");

        // The encoded telemetry must carry the fixed-geometry field set that is
        // backend-independent per Property 6 / Requirement 5.2 / 7.2.
        assert(a.find("\"crtWidth\":640")   != std::string::npos);
        assert(a.find("\"crtHeight\":480")  != std::string::npos);
        assert(a.find("\"lcdWidth\":160")   != std::string::npos);
        assert(a.find("\"lcdHeight\":64")   != std::string::npos);
        assert(a.find("\"gotekWidth\":128") != std::string::npos);
        assert(a.find("\"gotekHeight\":32") != std::string::npos);
    }

    std::cout << "  -> encode_telemetry is deterministic / backend-independent. "
                 "PASSED!" << std::endl;
}

} // namespace

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  S-760 Backend-Identity Property (Prop 6) " << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_end_to_end_backend_identity();
        test_against_real_core_backend();
        test_build_frame_determinism();
        test_encode_telemetry_determinism();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 BACKEND-IDENTITY PROPERTY TESTS PASSED SUCCESSFULLY! <<<"
              << std::endl;
    return 0;
}
