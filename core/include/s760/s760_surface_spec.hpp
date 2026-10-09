#pragma once

// =============================================================================
//  s760_surface_spec.hpp
//
//  Internal surface descriptor for the MAME live backend (spec
//  `mame-live-backend`, task 3.1). A `SurfaceSpec` pairs a protocol
//  `bridge::SurfaceId` with its fixed geometry and pixel format, and exposes a
//  helper returning the expected payload size via `bridge::payload_size`.
//
//  The three fixed instances mirror the protocol constants in
//  `s760_bridge_protocol.hpp` exactly:
//    * CRT  — SurfaceId::CRT  (0), 640x480, RGBA8888
//    * LCD  — SurfaceId::LCD  (1), 160x64,  MONO1
//    * OLED — SurfaceId::OLED (2), 128x32,  MONO1  (Gotek drive-bay readout)
//
//  This is a header-only, pure-data model: it introduces no runtime state and
//  no dependency beyond the canonical protocol header, so it is safe to use in
//  both the Core and MAME backends and in host-only tests with no MAME binary
//  present.
//
//  Spec: .kiro/specs/mame-live-backend/  (design "Data Models / Surface
//        descriptor"; Requirement 5.1).
// =============================================================================

#include <cstddef>
#include <cstdint>

#include "s760/s760_bridge_protocol.hpp"

namespace s760 {

// Internal surface descriptor. Mirrors the protocol's fixed geometry/format for
// a given surface so the backend can validate payloads against the single
// source of truth (`bridge::payload_size`) without duplicating the size math.
struct SurfaceSpec {
    bridge::SurfaceId   id;      // CRT=0, LCD=1, OLED=2
    uint16_t            width;   // 640 / 160 / 128
    uint16_t            height;  // 480 / 64  / 32
    bridge::PixelFormat format;  // RGBA8888 / MONO1

    // Expected payload size in bytes for this surface, computed via the
    // canonical protocol helper (RGBA8888 = w*h*4; MONO1 = ceil(w/8)*h).
    // Not `constexpr`: the protocol's `payload_size` is a runtime `inline`
    // function (it is the single source of truth and is not modified here).
    std::size_t expected_payload_size() const {
        return bridge::payload_size(format, width, height);
    }

    // Total binary message size (6-byte header + payload) for this surface.
    std::size_t message_size() const {
        return bridge::FRAME_HEADER_SIZE + expected_payload_size();
    }
};

// -----------------------------------------------------------------------------
//  Fixed surface specifications (mirror the protocol geometry constants).
// -----------------------------------------------------------------------------
//  OLED maps to the Gotek drive-bay readout geometry (GOTEK_WIDTH/HEIGHT).

inline constexpr SurfaceSpec CRT_SPEC{
    bridge::SurfaceId::CRT,
    bridge::CRT_WIDTH,
    bridge::CRT_HEIGHT,
    bridge::PixelFormat::RGBA8888,
};

inline constexpr SurfaceSpec LCD_SPEC{
    bridge::SurfaceId::LCD,
    bridge::LCD_WIDTH,
    bridge::LCD_HEIGHT,
    bridge::PixelFormat::MONO1,
};

inline constexpr SurfaceSpec OLED_SPEC{
    bridge::SurfaceId::OLED,
    bridge::GOTEK_WIDTH,
    bridge::GOTEK_HEIGHT,
    bridge::PixelFormat::MONO1,
};

// Free-function form of the payload-size helper for callers that have a spec by
// value and prefer a non-member call.
inline std::size_t expected_payload_size(const SurfaceSpec& spec) {
    return spec.expected_payload_size();
}

// Look up the fixed spec for a given surface id. Returns the CRT spec as a
// defensive default for any unexpected value (the enum has only three valid
// members).
inline constexpr SurfaceSpec spec_for(bridge::SurfaceId id) {
    switch (id) {
        case bridge::SurfaceId::CRT:  return CRT_SPEC;
        case bridge::SurfaceId::LCD:  return LCD_SPEC;
        case bridge::SurfaceId::OLED: return OLED_SPEC;
    }
    return CRT_SPEC;
}

} // namespace s760
