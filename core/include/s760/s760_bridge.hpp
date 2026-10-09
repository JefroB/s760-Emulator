#pragma once

// =============================================================================
//  s760_bridge.hpp
//
//  In-process C++ UI bridge for the Roland S-760 React canonical UI.
//
//  `S760Bridge` sits between the React UI (`google-ui/`) and the emulation
//  backend (the `S760LibretroHost` each plugin / standalone instance owns). It
//  implements the wire protocol defined in `s760_bridge_protocol.hpp` (the
//  single source of truth from task 3.1) and exposes TWO transports behind ONE
//  message contract (design D1 / F6):
//
//    1. In-process message API  (PRIMARY, plugin WebView path — NO sockets):
//         - on_input(json)            : accept a S760ClientMessage JSON string
//         - set_frame_callback(cb)    : receive binary display frames
//         - set_telemetry_callback(cb): receive JSON telemetry strings
//         - pump()                    : advance the host + push frames/telemetry
//       The plugin editor's WebView binding wires its JS->C++ message channel to
//       on_input(), and the C++->JS channel to the two callbacks. This path
//       needs no socket library and is the primary plugin transport.
//
//    2. Loopback WebSocket server (ADDITIVE, standalone / plugin fallback):
//         - start_ws_server(port)     : bring up an RFC6455 loopback server
//         - stop_ws_server()
//       Standalone/browser dev uses a fixed dev port (default
//       bridge::STANDALONE_DEV_WS_PORT = 8760). Plugins that cannot use the
//       in-process binding may pass port 0 to bind an EPHEMERAL per-instance
//       port (avoids multi-instance conflicts) and read it back via ws_port().
//
//  Both transports share the SAME encode/decode and frame-production code: the
//  WebSocket server simply forwards client text frames into on_input() and
//  streams the produced binary/telemetry messages to connected clients.
//
//  WebSocket implementation / license: the RFC6455 server is a minimal,
//  self-contained implementation written for this project (no third-party
//  dependency), layered directly on the platform socket API (Winsock2 on
//  Windows, BSD sockets elsewhere). It is therefore covered by this project's
//  own license and introduces no external license obligations. The in-process
//  API path uses no socket code at all.
//
//  Spec: .kiro/specs/ui-consolidation/  (Requirements R5.1, R5.2, R5.3, R5.5;
//        design "Components and Interfaces / Bridge server — in-process C++").
// =============================================================================

#include "s760/s760_bridge_protocol.hpp"
// s760_libretro_host.hpp defines VideoFrame and then includes
// s760_host_interface.hpp in the correct order, so IS760Host (the host type the
// Bridge borrows) is available transitively. Including the interface header
// directly here would break that ordering (the interface header pulls in the
// libretro host before VideoFrame/IS760Host are defined).
#include "s760/s760_libretro_host.hpp"

#include <cstdint>
#include <functional>
#include <memory>
#include <mutex>
#include <string>
#include <vector>

namespace s760 {

// Opaque forward declaration of the WebSocket server implementation. Kept out
// of the header so that the (platform socket) includes do not leak into every
// translation unit that merely drives the in-process API.
namespace bridge_detail { class WsServer; }

// -----------------------------------------------------------------------------
//  S760Bridge
// -----------------------------------------------------------------------------
//  Thread-safety: on_input(), pump() and the callback setters are guarded by an
//  internal mutex so the in-process API and the WebSocket server thread can both
//  drive the bridge. Callbacks are invoked from whatever thread calls pump()
//  (plugin UI timer) and/or from the WS server thread; consumers must be
//  prepared for that (the WebView binding typically marshals to the UI thread).
class S760Bridge {
public:
    // A binary display frame already framed per the protocol
    // ([u8 surfaceId][u16 w LE][u16 h LE][u8 format][payload]).
    using FrameCallback     = std::function<void(const uint8_t* data, std::size_t len)>;
    // A JSON telemetry string (S760ServerTelemetry shape).
    using TelemetryCallback = std::function<void(const std::string& json)>;

    // The bridge borrows (does not own) the host. The host must outlive the
    // bridge. The host is an abstract IS760Host, so the Bridge drives either
    // the Core backend (S760LibretroHost) or the MAME backend (S760MameHost)
    // behind one contract (mame-live-backend Requirements 1.7, 7.2). Passing
    // nullptr is allowed for unit tests that only exercise the JSON/frame
    // encoding paths, but on_input()/pump() become no-ops that still produce
    // frames/telemetry from default/empty state where possible.
    explicit S760Bridge(IS760Host* host);
    ~S760Bridge();

    S760Bridge(const S760Bridge&) = delete;
    S760Bridge& operator=(const S760Bridge&) = delete;

    // --- In-process API (primary plugin transport) --------------------------

    // Accept one S760ClientMessage as a JSON string. Decodes and applies it to
    // the host (buttons/dials -> input map, notes -> MIDI, mouse -> pointer,
    // mount -> drive manager). Returns true if the message parsed and was a
    // recognized type; false on malformed JSON or unknown type (the message is
    // then ignored, per the design's error handling).
    bool on_input(const std::string& json);

    // Register the sinks that pump() (and the WS server) push to. Either may be
    // left unset.
    void set_frame_callback(FrameCallback cb);
    void set_telemetry_callback(TelemetryCallback cb);

    // Advance one host frame and push the three display surfaces + telemetry to
    // the registered callbacks (and to any connected WebSocket clients). This is
    // the per-tick entry point a plugin UI timer / standalone loop calls.
    void pump();

    // Produce the current surfaces/telemetry WITHOUT advancing the host. Useful
    // for tests and for pushing an initial frame on connect.
    void push_frames();

    // --- Encoding helpers (shared by both transports; also unit-testable) ----

    // Build a protocol binary frame for a surface. The payload length must match
    // bridge::payload_size(format, width, height); the returned buffer is the
    // full framed message (6-byte header + payload).
    static std::vector<uint8_t> build_frame(bridge::SurfaceId id,
                                            uint16_t width, uint16_t height,
                                            bridge::PixelFormat format,
                                            const uint8_t* payload,
                                            std::size_t payload_len);

    // Serialize telemetry to the canonical JSON wire form.
    static std::string encode_telemetry(const bridge::ServerTelemetry& t);

    // Parse a S760ClientMessage JSON string into the typed struct. Returns false
    // on malformed JSON or an unrecognized `type`. Exposed for task 3.5 tests.
    static bool decode_client_message(const std::string& json,
                                      bridge::ClientMessage& out);

    // Snapshot current telemetry from the host (peaks, voices, mode, fps).
    bridge::ServerTelemetry current_telemetry() const;

    // --- Reported findings (surface-suppression log) ------------------------

    // Return a snapshot of the findings recorded by the Bridge. A finding is
    // recorded whenever a candidate surface could not be produced with the
    // advertised geometry/format/exact payload length and its emission was
    // therefore suppressed, rather than emitting a malformed frame the client
    // would discard (mame-live-backend Requirement 5.6). The returned vector is
    // a copy; the accessor is thread-safe. This is additive to the public API
    // and does not alter the wire protocol (PROTOCOL_VERSION stays 1).
    std::vector<std::string> findings() const;

    // --- Optional loopback WebSocket server ---------------------------------

    // Start the RFC6455 loopback server. `port` == 0 binds an ephemeral port
    // (recommended for plugins); a non-zero port (e.g.
    // bridge::STANDALONE_DEV_WS_PORT) is used for standalone dev. Returns true
    // on success. Safe to call once; call stop_ws_server() before re-starting.
    bool start_ws_server(uint16_t port = bridge::STANDALONE_DEV_WS_PORT);
    void stop_ws_server();
    bool ws_running() const;
    // The actual bound port (useful when started with port 0). 0 if not running.
    uint16_t ws_port() const;

private:
    void apply_message(const bridge::ClientMessage& msg);
    void emit_frame(const std::vector<uint8_t>& framed);
    void emit_telemetry(const std::string& json);

    // Validate a candidate surface payload against the protocol's exact
    // payload-length rule, then either build + emit the 6-byte-framed message
    // or (on a mismatch) suppress emission and record a descriptive finding
    // (mame-live-backend Requirement 5.6). Centralizes the suppression guard so
    // every surface (CRT/LCD/OLED) is routed through one place. The caller must
    // hold m_mutex (findings are guarded by it). Correctly-sized surfaces are
    // emitted byte-for-byte identically to a direct build_frame()/emit_frame().
    void emit_surface(bridge::SurfaceId id, uint16_t width, uint16_t height,
                      bridge::PixelFormat format,
                      const uint8_t* payload, std::size_t payload_len);
    // Snapshot telemetry assuming m_mutex is already held by the caller.
    bridge::ServerTelemetry current_telemetry_locked() const;

    // Fill a MONO1 (1bpp packed) blank surface of the given geometry. The host
    // does not yet expose SED1335/OLED buffers (F2/F3), so these surfaces are
    // produced as authentic-blank frames of the correct size/format.
    static std::vector<uint8_t> blank_mono1(uint16_t width, uint16_t height);

    IS760Host* m_host = nullptr;

    mutable std::mutex m_mutex;
    FrameCallback      m_frame_cb;
    TelemetryCallback  m_telemetry_cb;
    uint64_t           m_frame_counter = 0;
    // Telemetry currentMode. Per mame-live-backend Requirement 5.4, the Bridge
    // reports a mode string ONLY where it is derivable from genuine OS/display
    // state; otherwise it reports the EMPTY string and never invents mode
    // content. The default is therefore "" (not derivable yet). A derivation
    // hook / setter may populate this from real OS state when that becomes
    // available; nothing writes an invented default here.
    std::string        m_current_mode;

    // Reported findings (surface-suppression log). Guarded by m_mutex. A
    // descriptive message is appended whenever emit_surface() rejects a
    // candidate surface whose payload length does not match
    // payload_size(format, width, height) (mame-live-backend Requirement 5.6).
    // Accessed as a snapshot copy via the public findings() accessor.
    std::vector<std::string> m_findings;

    std::unique_ptr<bridge_detail::WsServer> m_ws;
};

} // namespace s760
