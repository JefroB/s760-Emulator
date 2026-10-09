#pragma once

// IS760Host
// ---------
// Abstract host-surface interface extracted from S760LibretroHost so that the
// S760Bridge can drive either the existing Core backend (S760LibretroHost) or
// the new MAME backend (S760MameHost) behind one contract.
//
// The method set mirrors exactly what the Bridge consumes today. The methods
// run_frame(), get_latest_video_frame(), send_midi_message(),
// handle_input_state(), and get_drive_manager() keep identical name, return
// type, and parameter types/order to the S760LibretroHost declarations so the
// Bridge compiles and links against either backend with no change to its call
// sites (see .kiro/specs/mame-live-backend, Requirements 1.2, 1.7, 7.2).
//
// This is an internal refactor seam only: no public Bridge API or protocol
// symbol changes.

#include "s760/s760_drive_manager.hpp"
#include "s760/s760_recorder.hpp"
#include "s760/s760_libretro_host.hpp" // VideoFrame (shared surface struct)

#include <cstddef>
#include <cstdint>

namespace s760 {

// VideoFrame and S760SampleRecorder are declared in s760_libretro_host.hpp /
// s760_recorder.hpp and reused verbatim so the surface and telemetry types are
// identical across backends.

class IS760Host {
public:
    virtual ~IS760Host() = default;

    // Load / initialize the backend. Returns false on failure without spawning
    // a process or terminating the host (Requirement 1.4).
    virtual bool init() = 0;

    // Advance exactly one emulated frame. Returns false if a frame cannot be
    // advanced, leaving previously cached surfaces unchanged (Requirement 1.5).
    virtual bool run_frame() = 0;

    // CRT raster as a 640x480 RGBA VideoFrame. Matches S760LibretroHost's
    // signature exactly (name, return type, const-ness).
    virtual VideoFrame get_latest_video_frame() const = 0;

    // Fill a MONO1 160x64 LCD surface buffer derived solely from controller
    // VRAM. Returns false when the backend exposes no LCD raster (the Core
    // backend returns false so the Bridge keeps its authentic-blank behavior).
    virtual bool get_lcd_surface(uint8_t* out, std::size_t len) const = 0;

    // Deliver a MIDI message to the emulated OS. Matches S760LibretroHost.
    virtual void send_midi_message(const uint8_t* msg, size_t len) = 0;

    // Route an input-state query/update into the backend. Matches
    // S760LibretroHost's signature exactly (parameter types and order).
    virtual int16_t handle_input_state(unsigned port, unsigned device,
                                       unsigned index, unsigned id) = 0;

    // Access the hardware drive manager (FDD / SCSI) for disk mounting. Matches
    // S760LibretroHost's non-const accessor return type.
    virtual S760DriveManager& get_drive_manager() = 0;

    // --- Telemetry accessors ------------------------------------------------
    // The Bridge sources its telemetry peaks from the host's sample recorder
    // (see S760Bridge::current_telemetry). This accessor is kept on the
    // interface for parity and future audio work (audio is Out-of-Scope for
    // this spec, but the surface must not preclude it). Both overloads match
    // S760LibretroHost's declarations exactly (name, return type, const-ness).
    virtual S760SampleRecorder& get_recorder() = 0;
    virtual const S760SampleRecorder& get_recorder() const = 0;
};

} // namespace s760
