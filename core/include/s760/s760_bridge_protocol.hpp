#pragma once

// =============================================================================
//  s760_bridge_protocol.hpp
//
//  SINGLE SOURCE OF TRUTH for the S-760 UI bridge wire protocol.
//
//  This header defines the message contract spoken between the React canonical
//  UI (`google-ui/`) and the in-process C++ bridge (`S760Bridge`, task 3.2).
//  Both the C++ bridge (task 3.2) and the React client (task 3.3,
//  `google-ui/src/bridge/S760BridgeClient.ts`) MUST conform to the framing,
//  enums, and schemas documented here. The TypeScript side mirrors these
//  definitions by hand; keep the two in sync and treat THIS file as canonical.
//
//  Spec: .kiro/specs/ui-consolidation/  (Requirements R5.2, R5.5; design
//        "Data Models / Bridge protocol" and "Components and Interfaces /
//        Bridge server").
//
//  ---------------------------------------------------------------------------
//  TRANSPORT (identical message contract across both)
//  ---------------------------------------------------------------------------
//  The bridge supports two transports behind ONE contract (design D1):
//    1. Plugin editor (primary): a native WebView JS<->C++ postMessage binding.
//       Control messages are delivered as JSON strings; display frames are
//       delivered as binary blobs (ArrayBuffer / byte span). No sockets.
//    2. Browser / standalone: a loopback WebSocket (fixed dev port, e.g.
//       ws://localhost:8760). Control messages are sent as WebSocket TEXT
//       frames (JSON); display frames are sent as WebSocket BINARY frames.
//
//  The React client is transport- and backend-agnostic (C++ Core now, MAME
//  later): the bytes on the wire are the same either way.
//
//  ---------------------------------------------------------------------------
//  MESSAGE CLASSES
//  ---------------------------------------------------------------------------
//    * Control    (Client -> Server): JSON, see S760ClientMessage below.
//    * Telemetry  (Server -> Client): JSON, see S760ServerTelemetry below.
//    * Frame      (Server -> Client): BINARY, see "Binary frame framing" below.
//
//  Direction of JSON vs binary is unambiguous:
//    - Over WebSocket: TEXT opcode => JSON (control/telemetry); BINARY opcode
//      => a display frame.
//    - Over the WebView binding: a string payload => JSON; a byte-buffer
//      payload => a display frame.
//
//  A single JSON control/telemetry message is exactly one transport message
//  (one WebSocket frame / one postMessage). JSON messages are UTF-8 encoded.
// =============================================================================

#include <cstdint>
#include <string>

namespace s760 {
namespace bridge {

// -----------------------------------------------------------------------------
//  Protocol version
// -----------------------------------------------------------------------------
//  Bump PROTOCOL_VERSION on any breaking change to framing, enums, or schemas.
//  The server reports it in the handshake/telemetry so clients can detect a
//  mismatch and surface it rather than mis-decoding.
inline constexpr int PROTOCOL_VERSION = 1;

// Default standalone/browser dev WebSocket port (R5.2). Plugin editors use an
// ephemeral per-instance port (or the socket-less in-process API) instead, to
// avoid multi-instance port conflicts — do NOT hard-code 8760 for plugins.
inline constexpr uint16_t STANDALONE_DEV_WS_PORT = 8760;

// =============================================================================
//  CONTROL MESSAGES  (Client -> Server)   — JSON
// =============================================================================
//
//  Wire shape (JSON object):
//      {
//        "type": "<ClientMessageType>",
//        "payload": { ...fields below... }
//      }
//
//  `type` is one of the string tokens in ClientMessageType (see
//  to_string(ClientMessageType)). `payload` is an object; only the fields
//  relevant to the given `type` are present. All payload fields are OPTIONAL at
//  the JSON level (matching the TS `payload: { id?; delta?; ... }`), but each
//  message type REQUIRES the subset listed below. Unknown fields are ignored.
//
//  Field semantics per type:
//    BUTTON_PRESS    : { id }                 front-panel/soft button id pressed
//    BUTTON_RELEASE  : { id }                 same id released
//    DIAL_DELTA      : { id, delta }          rotary encoder; delta = signed
//                                             detent count (+CW / -CCW). `id`
//                                             selects which encoder.
//    MOUSE_MOVE      : { x, y }               pointer position (see note below)
//    MOUSE_CLICK     : { x, y, button }       click at (x,y); button index
//    MOUNT_DISK      : { diskPath }           absolute path of image to mount
//    NOTE_ON         : { note, velocity }     MIDI note on  (0..127, 1..127)
//    NOTE_OFF        : { note, velocity }     MIDI note off (velocity optional)
//
//  Pointer coordinate convention (MOUSE_MOVE / MOUSE_CLICK) — per task 3.3:
//    React is the pointer owner. x and y are NORMALIZED coordinates in the
//    range [0.0, 1.0] relative to the CRT surface (0,0 = top-left,
//    1,1 = bottom-right). This REPLACES the removed MAME 8-bit ±127-clamped
//    relative-delta path (task 1.8); the client applies its own
//    sensitivity/acceleration before emitting, and the backend scales the
//    normalized value to CRT pixels (crtWidth × crtHeight). Senders MUST NOT
//    send wrapped 8-bit deltas here.
//
//  `id` values are string identifiers agreed between React controls and the
//  backend input map (buttons and encoders). Treated as opaque strings by the
//  framing layer.
// -----------------------------------------------------------------------------

enum class ClientMessageType : uint8_t {
    BUTTON_PRESS = 0,
    BUTTON_RELEASE,
    DIAL_DELTA,
    MOUSE_MOVE,
    MOUSE_CLICK,
    MOUNT_DISK,
    NOTE_ON,
    NOTE_OFF,
};

// Canonical JSON token for each control message type. These exact strings are
// what appears in the `"type"` field on the wire and MUST match the TS union.
inline const char* to_string(ClientMessageType t) {
    switch (t) {
        case ClientMessageType::BUTTON_PRESS:   return "BUTTON_PRESS";
        case ClientMessageType::BUTTON_RELEASE: return "BUTTON_RELEASE";
        case ClientMessageType::DIAL_DELTA:     return "DIAL_DELTA";
        case ClientMessageType::MOUSE_MOVE:     return "MOUSE_MOVE";
        case ClientMessageType::MOUSE_CLICK:    return "MOUSE_CLICK";
        case ClientMessageType::MOUNT_DISK:     return "MOUNT_DISK";
        case ClientMessageType::NOTE_ON:        return "NOTE_ON";
        case ClientMessageType::NOTE_OFF:       return "NOTE_OFF";
    }
    return "UNKNOWN";
}

// Parse a JSON `type` token back to the enum. Returns false if unrecognized.
inline bool parse_client_message_type(const std::string& s, ClientMessageType& out) {
    if (s == "BUTTON_PRESS")   { out = ClientMessageType::BUTTON_PRESS;   return true; }
    if (s == "BUTTON_RELEASE") { out = ClientMessageType::BUTTON_RELEASE; return true; }
    if (s == "DIAL_DELTA")     { out = ClientMessageType::DIAL_DELTA;     return true; }
    if (s == "MOUSE_MOVE")     { out = ClientMessageType::MOUSE_MOVE;     return true; }
    if (s == "MOUSE_CLICK")    { out = ClientMessageType::MOUSE_CLICK;    return true; }
    if (s == "MOUNT_DISK")     { out = ClientMessageType::MOUNT_DISK;     return true; }
    if (s == "NOTE_ON")        { out = ClientMessageType::NOTE_ON;        return true; }
    if (s == "NOTE_OFF")       { out = ClientMessageType::NOTE_OFF;       return true; }
    return false;
}

// Optional-payload mirror of the TS `payload: { id?; delta?; x?; y?; button?;
// diskPath?; note?; velocity?; }`. `has_*` flags distinguish "field absent"
// from "field present with value 0" to match JSON's optional-key semantics.
// This struct is a convenience for the C++ bridge; the authoritative wire form
// is JSON. (The bridge in task 3.2 chooses its own JSON library to populate it.)
struct ClientPayload {
    bool        has_id       = false;  std::string id;        // button/encoder id
    bool        has_delta    = false;  double      delta = 0; // dial detents (signed)
    bool        has_x        = false;  double      x = 0;     // normalized [0,1]
    bool        has_y        = false;  double      y = 0;     // normalized [0,1]
    bool        has_button   = false;  int         button = 0;// mouse button index
    bool        has_diskPath = false;  std::string diskPath;  // mount path
    bool        has_note     = false;  int         note = 0;  // MIDI note 0..127
    bool        has_velocity = false;  int         velocity = 0; // MIDI vel 0..127
};

struct ClientMessage {
    ClientMessageType type{};
    ClientPayload     payload{};
};

// =============================================================================
//  TELEMETRY  (Server -> Client)   — JSON
// =============================================================================
//
//  Wire shape (JSON object) — mirrors the TS S760ServerTelemetry exactly:
//      {
//        "timestamp": <number ms>,
//        "fps":       <number>,
//        "crtWidth":  640, "crtHeight": 480,
//        "lcdWidth":  160, "lcdHeight": 64,
//        "gotekWidth":128, "gotekHeight":32,
//        "peakL":     <0..1>, "peakR": <0..1>,
//        "activeVoices": <int>,
//        "currentMode":  "<string>"
//      }
//
//  Surface dimensions are advertised in telemetry AND are fixed compile-time
//  constants here so both ends agree even before the first telemetry arrives.
//  `timestamp` is a monotonic millisecond value from the server. Telemetry is a
//  low-rate channel (status/metadata); per-pixel data NEVER travels in JSON —
//  it is sent as binary frames (see below).
// -----------------------------------------------------------------------------

// Fixed authoritative surface geometries (match design telemetry constants).
inline constexpr uint16_t CRT_WIDTH    = 640;
inline constexpr uint16_t CRT_HEIGHT   = 480;
inline constexpr uint16_t LCD_WIDTH    = 160;
inline constexpr uint16_t LCD_HEIGHT   = 64;
inline constexpr uint16_t GOTEK_WIDTH  = 128;
inline constexpr uint16_t GOTEK_HEIGHT = 32;

struct ServerTelemetry {
    double      timestamp    = 0.0;  // monotonic milliseconds (server clock)
    double      fps          = 0.0;  // frames/sec the backend is producing
    uint16_t    crtWidth     = CRT_WIDTH;
    uint16_t    crtHeight    = CRT_HEIGHT;
    uint16_t    lcdWidth     = LCD_WIDTH;
    uint16_t    lcdHeight    = LCD_HEIGHT;
    uint16_t    gotekWidth   = GOTEK_WIDTH;
    uint16_t    gotekHeight  = GOTEK_HEIGHT;
    double      peakL        = 0.0;  // 0..1 output peak, left
    double      peakR        = 0.0;  // 0..1 output peak, right
    int         activeVoices = 0;    // currently sounding voices
    std::string currentMode;         // e.g. "PERFORM", "PATCH", "SAMPLE", ...
};

// =============================================================================
//  BINARY FRAME FRAMING  (Server -> Client)   — one display surface per message
// =============================================================================
//
//  Per the design, display frames are sent as BINARY messages (not base64) to
//  avoid encoding overhead. Each binary transport message carries exactly ONE
//  surface frame with the following layout:
//
//      Offset  Size  Field        Notes
//      ------  ----  -----------  ----------------------------------------------
//        0      1    surfaceId    u8   SurfaceId enum (0=CRT,1=LCD,2=OLED)
//        1      2    width        u16  pixel width,  LITTLE-ENDIAN
//        3      2    height       u16  pixel height, LITTLE-ENDIAN
//        5      1    format       u8   PixelFormat enum
//        6      N    payload      raw pixel bytes (N = width*height*bytesPerPixel)
//
//      => fixed 6-byte header, then the payload. Total message length =
//         FRAME_HEADER_SIZE + payload bytes.
//
//  ENDIANNESS:
//    * The 16-bit header fields (width, height) are LITTLE-ENDIAN on the wire.
//      This matches the S-760 CPU (Intel MCS-96, little-endian) and the x86/ARM
//      hosts the bridge runs on, so the C++ side needs no byte-swap, and the TS
//      client reads them with DataView getUint16(offset, /*littleEndian=*/true).
//    * Pixel payload endianness is defined per-format below.
//
//  FRAME LENGTH / DELIMITING ON THE WIRE:
//    * The transport is message-oriented, so each binary frame is already
//      delimited by the transport:
//        - WebSocket BINARY frames carry their own length; one WS binary frame
//          == one surface frame. No extra length prefix is added.
//        - The WebView binding delivers one ArrayBuffer == one surface frame.
//    * The receiver still validates: payload length MUST equal
//      width*height*bytes_per_pixel(format); otherwise the frame is malformed
//      and MUST be discarded (see Error Handling in the design).
//    * NOTE: if a future transport is NOT message-framed (e.g. a raw byte
//      stream), a 4-byte LITTLE-ENDIAN u32 total-length prefix MUST be prepended
//      ahead of the 6-byte header. The message-oriented transports in this spec
//      (WebSocket, WebView postMessage) do NOT use that prefix.
//
//  SURFACES:
//    * 0 CRT   — OP-760 RFSC16A VDP output,  nominal 640×480, RGBA8888.
//    * 1 LCD   — Epson SED1335 front panel,  160×64,  MONO1 (1bpp) packed.
//    * 2 OLED  — Gotek drive-bay readout,    128×32,  MONO1 (1bpp) packed.
//    width/height in the header are authoritative for the actual payload size
//    (they SHOULD equal the fixed geometry constants above).
// -----------------------------------------------------------------------------

enum class SurfaceId : uint8_t {
    CRT  = 0,   // OP-760 RFSC16A VDP color output
    LCD  = 1,   // Epson SED1335 160x64 monochrome front panel
    OLED = 2,   // Gotek 128x32 monochrome drive-bay readout
};

enum class PixelFormat : uint8_t {
    // 32 bits per pixel, byte order on the wire is R,G,B,A (payload[0]=R of
    // pixel 0, payload[1]=G, payload[2]=B, payload[3]=A, then pixel 1 ...).
    // This is byte-addressed, so it is endianness-independent. Used by CRT.
    RGBA8888 = 0,

    // 1 bit per pixel, packed 8 pixels per byte, MSB = leftmost pixel. Rows are
    // packed left-to-right, top-to-bottom; each row starts on a byte boundary
    // (stride = ceil(width/8) bytes). 1 = lit/on, 0 = off. React applies the
    // backlight tint (SED1335 emerald/amber, Gotek). Used by LCD and OLED.
    MONO1 = 1,
};

// Fixed binary frame header size in bytes: u8 + u16 + u16 + u8.
inline constexpr std::size_t FRAME_HEADER_SIZE = 6;

// Bytes per pixel for a format (0 for sub-byte/packed formats like MONO1).
inline constexpr int bytes_per_pixel(PixelFormat f) {
    switch (f) {
        case PixelFormat::RGBA8888: return 4;
        case PixelFormat::MONO1:    return 0; // sub-byte; use payload_size()
    }
    return 0;
}

// Exact payload size in bytes for a frame of the given format and dimensions.
// RGBA8888 => width*height*4. MONO1 => ceil(width/8)*height (row-byte-aligned).
inline std::size_t payload_size(PixelFormat f, uint16_t width, uint16_t height) {
    switch (f) {
        case PixelFormat::RGBA8888:
            return static_cast<std::size_t>(width) * height * 4u;
        case PixelFormat::MONO1:
            return static_cast<std::size_t>((width + 7u) / 8u) * height;
    }
    return 0;
}

// Total binary message size = header + payload.
inline std::size_t frame_message_size(PixelFormat f, uint16_t width, uint16_t height) {
    return FRAME_HEADER_SIZE + payload_size(f, width, height);
}

// Parsed view of a binary frame header. Decoders fill this from the first
// FRAME_HEADER_SIZE bytes (little-endian u16 fields) and then validate that the
// remaining byte count equals payload_size(format, width, height).
struct FrameHeader {
    SurfaceId   surfaceId{};
    uint16_t    width  = 0;
    uint16_t    height = 0;
    PixelFormat format{};
};

} // namespace bridge
} // namespace s760
