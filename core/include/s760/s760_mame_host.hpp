#pragma once

// =============================================================================
//  s760_mame_host.hpp
//
//  S760MameHost — the MAME_Backend adapter (spec `mame-live-backend`, task 6.1).
//
//  SCAFFOLD STATUS (task 6.1)
//  --------------------------
//  This file + its .cpp are the *scaffold* for the in-process MAME `s760`
//  backend. They implement the full `IS760Host` contract so the S760Bridge can
//  be built/linked against this backend today, but the genuine MAME machine is
//  NOT yet wired in (the MAME `s760` driver / library is not linkable in this
//  build). Later tasks fill in the deferred pieces:
//
//    * task 6.2 — run_frame(): headless step of the MAME machine + refresh of
//                 the cached CRT/LCD rasters.
//    * task 6.4 — get_latest_video_frame() / get_lcd_surface(): rasterize from
//                 genuine VRAM (via the pure helpers already present:
//                 s760_crt_gate.hpp, s760_crt_normalize.hpp, s760_lcd_raster.hpp).
//    * task 7.x — handle_input_state() / send_midi_message() / disk mounting:
//                 route input/MIDI/mount into the genuine MAME input + FDC path.
//
//  Everything in this scaffold is written so those later tasks fill in behavior
//  WITHOUT changing this class's public surface. In particular the VRAM buffers
//  (m_vdp_vram, m_sed_vram) and cached rasters (m_crt_raster, m_lcd_raster) are
//  owned here now, ready for 6.2/6.4 to populate.
//
//  DESIGN CONSTRAINTS honored by the scaffold
//  ------------------------------------------
//    * C++ only, no Python (Requirement 1.6, 8.2).
//    * init() does NOT spawn/fork a process and NEVER terminates the host; it
//      returns false on failure (Requirements 1.1, 1.4, 6.6-adjacent). It
//      resolves `s760224.img` from a configured path / the S760_ROMS_DIR
//      environment variable (NO hard-coded absolute path), loads the image
//      bytes into an owned `maincpu`-region buffer, and returns true only when
//      the image is present and readable; false otherwise.
//    * Owns a S760DriveManager and S760SampleRecorder exactly like the Core
//      backend, so the Bridge's drive-manager / telemetry accessors work.
//
//  Spec: .kiro/specs/mame-live-backend/  (design "Components / 1. S760MameHost";
//        Requirements 1.1, 1.4, 1.6, 6.6).
// =============================================================================

#include "s760/s760_drive_manager.hpp"
#include "s760/s760_recorder.hpp"
#include "s760/s760_libretro_host.hpp" // VideoFrame + IS760Host (via that header)

#include <cstddef>
#include <cstdint>
#include <string>
#include <vector>

namespace s760 {

// Adapter wrapping the in-process MAME `s760` machine behind the one host
// surface the Bridge consumes. Implements IS760Host so the Bridge links against
// either this backend or S760LibretroHost with no call-site change
// (Requirement 1.2).
class S760MameHost : public IS760Host {
public:
    S760MameHost();
    explicit S760MameHost(std::string roms_dir);
    ~S760MameHost() override;

    S760MameHost(const S760MameHost&)            = delete;
    S760MameHost& operator=(const S760MameHost&) = delete;

    // -- Configuration ------------------------------------------------------
    // Optional explicit ROM directory. When unset, init() resolves the image
    // from the S760_ROMS_DIR environment variable (then a small set of sensible
    // relative defaults). Never a hard-coded absolute path.
    void set_roms_dir(std::string roms_dir) { m_roms_dir = std::move(roms_dir); }
    const std::string& roms_dir() const { return m_roms_dir; }

    // Absolute/relative path of the system image resolved by the last init()
    // attempt (empty if none was found). Useful for diagnostics/tests.
    const std::string& resolved_image_path() const { return m_resolved_image_path; }

    // -- IS760Host ----------------------------------------------------------

    // Locate `s760224.img`, load it into the owned maincpu-region buffer, and
    // return true only when the image is present and readable. Returns false on
    // any failure (image absent/unreadable, wrong size) WITHOUT spawning a
    // process or terminating the host (Requirements 1.1, 1.4).
    //
    // SCAFFOLD: full MAME machine bring-up (CPU/VDP/SED1335 devices) is deferred
    // to task 6.2. init() here only validates + loads the program image so the
    // backend-selection path (task 9.x) can treat a missing image as an
    // initialization failure and fall back to the Core backend.
    bool init() override;

    // SCAFFOLD: returns false until task 6.2 wires headless stepping. Leaves the
    // cached surfaces unchanged (Requirement 1.5), which the all-blank initial
    // rasters already satisfy.
    bool run_frame() override;

    // Return the cached CRT VideoFrame (640x480 RGBA). SCAFFOLD: initially an
    // authentic-blank frame; task 6.4 populates it from genuine VDP VRAM via the
    // crt_gate/crt_normalize helpers.
    VideoFrame get_latest_video_frame() const override;

    // Fill a 160x64 MONO1 LCD surface from the cached LCD raster. Returns false
    // if `out` is null or `len` does not match payload_size(MONO1,160,64).
    // SCAFFOLD: the cached raster is all-zero (every pixel off) until task 6.4
    // rasterizes genuine m_sed_vram via lcd_rasterize(); the MAME backend DOES
    // own an LCD raster, so this returns true and fills the buffer (unlike the
    // Core backend, which returns false).
    bool get_lcd_surface(uint8_t* out, std::size_t len) const override;

    // -- MIDI delivery into the emulated OS (task 7.9, Requirement 6.8) -----
    //
    //  The Bridge converts a protocol NOTE_ON / NOTE_OFF into a 3-byte MIDI
    //  message (status 0x90/0x80 + note + velocity) and calls
    //  send_midi_message(msg, len). This is the host-facing seam that delivers
    //  those bytes to the emulated S-760 OS's MIDI input (Requirement 6.8).
    //
    //  HONEST DELIVERY SEAM (MAME MIDI UART not linkable in this build)
    //  ---------------------------------------------------------------
    //  The genuine in-process MAME `s760` machine (and its MIDI UART input) is
    //  NOT linkable in this build yet, so there is no real MIDI receiver to feed.
    //  Rather than silently drop the bytes (which would make delivery
    //  unobservable and untestable), send_midi_message() APPENDS the `len` bytes
    //  of `msg` to an owned, growable MIDI-in buffer (m_midi_in). That buffer is
    //  the recorded delivery queue: every byte the Bridge delivers is retained
    //  in order, so task 7.10's unit tests can assert NOTE_ON/NOTE_OFF bytes
    //  actually arrived. When task 6.2's genuine machine lands, the one place
    //  that DRAINS m_midi_in into the real MIDI UART replaces this buffer's
    //  consumer; the append-on-delivery contract here stays identical.
    //
    //  GUARDS: a null `msg` or a zero `len` is a no-op (nothing appended), so a
    //  malformed/empty delivery never corrupts the buffer or crashes.
    void send_midi_message(const uint8_t* msg, size_t len) override;

    // Const accessor over the recorded MIDI-in bytes (every byte delivered via
    // send_midi_message(), in order). Task 7.10's unit tests read this to verify
    // NOTE_ON (0x90 note vel) and NOTE_OFF (0x80 note vel) delivery. Task 6.2's
    // genuine machine drains these into the real MIDI UART.
    const std::vector<uint8_t>& midi_in_bytes() const { return m_midi_in; }

    // SCAFFOLD: stubbed (returns 0); task 7.1/7.3/7.5/7.7 implement the genuine
    // key-matrix / encoder / pointer input mapping.
    int16_t handle_input_state(unsigned port, unsigned device,
                               unsigned index, unsigned id) override;

    // -- Button -> key-matrix bit mapping (task 7.1, Requirements 6.1, 6.4) --
    //
    //  The Bridge decodes a protocol BUTTON_PRESS / BUTTON_RELEASE carrying a
    //  string `id`. apply_button() is the genuine seam the Bridge's button
    //  routing invokes: it looks the `id` up in a static mapping table derived
    //  from INPUT_PORTS_START(s760) and sets (pressed==true) or clears
    //  (pressed==false) EXACTLY that one key-matrix bit in the owned matrix.
    //  An unknown `id` (one that maps to no defined input) is IGNORED, leaving
    //  the matrix byte-for-byte unchanged (Requirement 6.4).
    //
    //  INTERNAL "pressed = bit set" MODEL (documented vs IP_ACTIVE_LOW)
    //  ----------------------------------------------------------------
    //  The genuine MAME ioports are IP_ACTIVE_LOW: on real hardware a *pressed*
    //  button pulls its line LOW, so the raw port reads the bit as 0 while
    //  pressed and 1 while released. Because the genuine MAME ioports are not
    //  linkable in this build yet, this adapter owns a clear, testable
    //  abstraction instead: a bitmask per port where a SET bit means "that
    //  button is currently pressed" (logical-active-high). Task 6.2's genuine
    //  machine will translate this logical matrix to the ioport's active-low
    //  convention at the single seam that drives the real device; the adapter's
    //  own model stays "set bit == pressed" so press/release toggling is
    //  unambiguous and directly testable (task 7.2's property test reads the
    //  matrix bytes via key_matrix()).
    //
    //  STABLE PROTOCOL id STRINGS (documented so task 7.2 + UI wiring align):
    //    KEY_ARROWS port:
    //      "cursor_left"   -> bit 0x01  (IPT_JOYSTICK_LEFT)
    //      "cursor_right"  -> bit 0x02  (IPT_JOYSTICK_RIGHT)
    //      "cursor_up"     -> bit 0x04  (IPT_JOYSTICK_UP)
    //      "cursor_down"   -> bit 0x08  (IPT_JOYSTICK_DOWN)
    //      "enter"         -> bit 0x10  (IPT_BUTTON1, "Select / Enter")
    //    GOTEK_CTRL port:
    //      "gotek_prev"    -> bit 0x01  (IPT_BUTTON4, "Gotek Prev Image")
    //      "gotek_next"    -> bit 0x02  (IPT_BUTTON5, "Gotek Next Image")
    //      "gotek_select"  -> bit 0x04  (IPT_BUTTON6, "Gotek Select / Push")
    //  Any other id is ignored.
    void apply_button(const std::string& id, bool pressed);

    // -- Dial-delta encoder application (task 7.3, Requirement 6.2) ---------
    //
    //  The Bridge decodes a protocol DIAL_DELTA carrying a signed integer
    //  `delta`. apply_dial_delta() is the genuine seam the Bridge's DIAL_DELTA
    //  routing invokes: it applies `delta` as the emulated encoder's signed
    //  detent count FOR THE FRAME in which it is processed (Requirement 6.2).
    //
    //  PER-FRAME ACCUMULATION + RESET MODEL
    //  ------------------------------------
    //  The owned accumulator m_encoder_detents holds the encoder's signed
    //  detent count applied for the CURRENT frame. apply_dial_delta() ADDS the
    //  delta (m_encoder_detents += delta) so multiple DIAL_DELTA messages in a
    //  single frame sum into one net per-frame rotation (an encoder physically
    //  reports a running detent count within a sampling window). run_frame()
    //  resets the accumulator to 0 at the start of each successful advance (see
    //  its implementation), so each frame's applied detent count reflects ONLY
    //  that frame's deltas.
    //
    //  This cleanly satisfies Property 10: after a frame-boundary reset, a
    //  single apply_dial_delta(d) yields encoder_detents() == d (the applied
    //  detent count for the frame equals delta). A negative delta turns the
    //  encoder the other way; a zero delta is a no-op.
    //
    //  SCAFFOLD note (consistent with the rest of this adapter): the genuine
    //  MAME input device is not linkable in this build yet, so this adapter
    //  owns the signed accumulator as the clear, testable abstraction. Task
    //  6.2's genuine machine will translate m_encoder_detents into the real
    //  encoder device's per-frame step at the single seam that clocks it; the
    //  adapter's own model stays "applied detent count for the frame" so the
    //  behavior is unambiguous and directly testable (task 7.4's property test
    //  reads it via encoder_detents()).
    void apply_dial_delta(int delta);

    // -- id-aware DIAL_DELTA (task 7.7, Requirements 6.2, 6.4) --------------
    //
    //  The protocol's DIAL_DELTA carries BOTH a signed `delta` AND an `id`
    //  string that SELECTS WHICH ENCODER the delta applies to (see
    //  s760_bridge_protocol.hpp `ClientPayload`: `has_id`/`id` +
    //  `has_delta`/`delta`, and the comment "DIAL_DELTA : { id, delta } ... `id`
    //  selects which encoder"). The React client emits concrete encoder ids —
    //  "ALPHA" (the Value/Data alpha-dial) and "VOLUME" — via
    //  S760BridgeClient.sendDialDelta(id, delta).
    //
    //  This id-aware overload is the honest seam for Requirement 6.4's
    //  "DIAL_DELTA with an id that maps to no defined input": a `delta` whose
    //  `id` matches a DEFINED encoder is applied exactly as the id-less overload
    //  (accumulated into m_encoder_detents for the frame); a `delta` whose `id`
    //  is NOT a defined encoder is IGNORED, leaving m_encoder_detents
    //  byte-for-byte unchanged (no detent applied). This directly satisfies
    //  Property 12's DIAL_DELTA clause.
    //
    //  DEFINED ENCODER ids (the stable set the UI emits; any other id ignored):
    //    "ALPHA"  -> the single modeled encoder (Value/Data alpha-dial)
    //    "VOLUME" -> the single modeled encoder (volume rotary)
    //  Both route to the one owned m_encoder_detents accumulator; there is one
    //  modeled encoder in this build, so a defined id is a pass-through and an
    //  undefined id is the only ignore case. (Task 6.2's genuine machine can
    //  split these into distinct device encoders at the same seam without
    //  changing this ignore-on-unknown-id contract.)
    void apply_dial_delta(const std::string& id, int delta);

    // True when `id` is a DEFINED encoder (see apply_dial_delta(id,delta)
    // docs). Const so task 7.8's property test can assert the ignore boundary
    // without mutating state.
    static bool is_defined_encoder(const std::string& id);

    // Read the encoder's signed detent count applied FOR THE CURRENT FRAME
    // (the sum of this frame's DIAL_DELTA deltas; reset to 0 at each frame
    // boundary by run_frame()). Const so task 7.4's property test can observe
    // the applied detent count without mutating it.
    int encoder_detents() const { return m_encoder_detents; }

    // -- Pointer -> VDP mouse-register scaling (task 7.5, Requirements 6.3, 6.5)
    //
    //  The Bridge decodes a protocol MOUSE_MOVE / MOUSE_CLICK carrying NORMALIZED
    //  coordinates (x, y), each in [0.0, 1.0]. apply_pointer() is the genuine
    //  seam the Bridge's pointer routing invokes for in-range coordinates: it
    //  scales (x, y) by the CRT pixel width/height, rounds to integer pixel
    //  coordinates, and writes them into the genuine RFSC16A VDP mouse registers
    //  through the vdp_w() path.
    //
    //  OUT-OF-RANGE / NaN GUARD (task 7.7, Requirement 6.4, Property 12)
    //  -----------------------------------------------------------------
    //  The protocol defines pointer coordinates as NORMALIZED values in the
    //  INCLUSIVE range [0.0, 1.0] (0.0 and 1.0 are BOTH valid: x==1.0 -> px==640,
    //  y==1.0 -> py==480). apply_pointer() first guards the input: if x or y is
    //  outside [0.0, 1.0], OR is NaN (NaN compares false to every bound, so it
    //  is treated as out-of-range), the call RETURNS IMMEDIATELY without writing
    //  ANY VDP register. The owned m_vdp_regs is left byte-for-byte unchanged on
    //  an out-of-range/NaN pointer (Requirement 6.4). Only an in-range (x,y) ever
    //  reaches the scaling + vdp_w writes below, so valid behavior is unchanged.
    //
    //  ABSOLUTE normalized->pixel scaling ONLY (NO +/-127 relative-delta path)
    //  ----------------------------------------------------------------------
    //  Requirement 6.5 forbids reintroducing the invented 8-bit +/-127
    //  relative-delta crosshair path removed in ui-consolidation task 1.8. This
    //  seam deliberately computes ABSOLUTE pixel coordinates from the normalized
    //  input and never a wrapped signed delta: there is no accumulator, no +/-127
    //  clamp, no previous-position subtraction anywhere in this path.
    //
    //  SCALING (Property 11)
    //  ---------------------
    //    px = round(x * bridge::CRT_WIDTH)    // x in [0,1] -> [0, 640]
    //    py = round(y * bridge::CRT_HEIGHT)   // y in [0,1] -> [0, 480]
    //  The rounded value is stored FAITHFULLY (no clamping-away of the exact
    //  endpoint): x==1.0 yields px==640, y==1.0 yields py==480. Property 11
    //  requires the stored integer pixel coords to EQUAL round(x*CRT_WIDTH) /
    //  round(y*CRT_HEIGHT) and be reconstructable from the registers, so we must
    //  not clamp 640->639 / 480->479.
    //
    //  REGISTER LAYOUT (per design "MAME driver" notes: 0x20 X-Low, 0x21 X-High
    //  (1 bit), 0x22 Y-Low, 0x24 Control) and how >8-bit values are packed:
    //    reg 0x20 (Mouse X Low)  = px & 0xFF            // low 8 bits of X
    //    reg 0x21 (Mouse X High) = (px >> 8) & 0x03     // high bits of X (px<=640
    //                                                   //   needs bits 8..9)
    //    reg 0x22 (Mouse Y Low)  = py & 0xFF            // low 8 bits of Y
    //    reg 0x24 (Mouse Control)= control byte, carrying:
    //                                bit0 = (py >> 8) & 0x01  // Y high bit (py<=480
    //                                                         //   needs bit 8)
    //                                bit7 = kMouseUpdateValid  // "coords valid /
    //                                                         //   updated this write"
    //  Design calls 0x21 "X-High (1 bit)"; because round(1.0*640)=640=0x280 needs
    //  two high bits (8 and 9), we store the full high byte masked to 0x03 so the
    //  exact value is always reconstructable. CRT_HEIGHT=480=0x1E0 needs 9 bits,
    //  so Y's single high bit is packed into Control bit0 (there is no dedicated
    //  Y-High register in the design's list). This mapping is deterministic and
    //  fully reconstructable (see pointer_x_pixels()/pointer_y_pixels()).
    //
    //  SCAFFOLD note: the genuine MAME VDP device is not linkable in this build
    //  yet, so apply_pointer() routes through this adapter's own vdp_w() into an
    //  owned register file (see m_vdp_regs). Task 6.2's genuine machine routes
    //  the same vdp_w(reg, value) calls to the real RFSC16A VDP; the register
    //  semantics above stay identical so task 7.6's property test can recover the
    //  pixel coordinates from the registers.
    void apply_pointer(double x, double y);

    // Read one owned VDP register byte (the value last written via vdp_w()).
    // Recognized here are the mouse registers 0x20/0x21/0x22/0x24; any index in
    // [0, 0xFF] returns its stored byte (0 if never written). Const so task
    // 7.6's property test can read the registers back.
    uint8_t vdp_reg(uint8_t reg) const { return m_vdp_regs[reg]; }

    // Reconstruct the absolute X pixel coordinate most recently written by
    // apply_pointer(), from registers 0x20 (X-Low) and 0x21 (X-High):
    //     x_pixels = ((0x21 & 0x03) << 8) | 0x20
    // Equals round(x * bridge::CRT_WIDTH) for the last in-range pointer.
    uint16_t pointer_x_pixels() const;

    // Reconstruct the absolute Y pixel coordinate most recently written by
    // apply_pointer(), from register 0x22 (Y-Low) and the Y high bit packed in
    // 0x24 (Control) bit0:
    //     y_pixels = ((0x24 & 0x01) << 8) | 0x22
    // Equals round(y * bridge::CRT_HEIGHT) for the last in-range pointer.
    uint16_t pointer_y_pixels() const;

    // Read the current logical key-matrix bitmask for a port (set bit ==
    // pressed). Recognized port names are "KEY_ARROWS" and "GOTEK_CTRL";
    // any other name returns 0. Const so tests (task 7.2) can observe the
    // matrix without mutating it.
    uint8_t key_matrix(const std::string& port) const;

    // Convenience direct accessors for the two owned port bytes.
    uint8_t key_arrows_matrix() const { return m_key_arrows_matrix; }
    uint8_t gotek_ctrl_matrix() const { return m_gotek_ctrl_matrix; }

    // Owned drive manager (FDD/SCSI) — identical to the Core backend so the
    // Bridge's get_drive_manager().mount_floppy() path works (Requirement 6.6).
    S760DriveManager& get_drive_manager() override { return m_drive_manager; }

    // -- Disk mounting adapter seam (task 7.9, Requirements 6.6, 6.7) -------
    //
    //  The Bridge already routes a protocol MOUNT_DISK straight through
    //  get_drive_manager().mount_floppy(diskPath), so Requirement 6.6's mount
    //  path ALREADY works via the owned m_drive_manager (see s760_bridge.cpp
    //  case T::MOUNT_DISK). This thin convenience method is the adapter-level
    //  seam over that same path: it delegates to m_drive_manager.mount_floppy()
    //  and returns its bool so a caller/test (task 7.10) has one place to drive
    //  and observe mounting at the S760MameHost surface.
    //
    //  SUCCESS / FAILURE CONTRACT (Requirement 6.7)
    //  --------------------------------------------
    //  Returns true when the image mounts, false when the path cannot be opened
    //  or mounted. S760DriveManager::mount_floppy() KEEPS the currently mounted
    //  image on failure and does NOT crash on a bad path, so this method
    //  surfaces that false WITHOUT throwing and WITHOUT disturbing the current
    //  image. A failure also records a diagnostic (see last_mount_ok() /
    //  last_mount_error()) for tests and reporting; it never terminates the host.
    bool mount_disk(const std::string& path);

    // Diagnostics for the most recent mount_disk() attempt (task 7.9/7.10).
    // last_mount_ok() is true iff the last mount_disk() succeeded; it starts
    // false (no attempt made yet). last_mount_error() holds the path of the
    // last failed mount (empty when the last attempt succeeded or none was
    // made). Const so tests observe the outcome without mutating state.
    bool last_mount_ok() const { return m_last_mount_ok; }
    const std::string& last_mount_error() const { return m_last_mount_error; }

    // Owned sample recorder (telemetry peaks parity + future audio).
    S760SampleRecorder& get_recorder() override { return m_recorder; }
    const S760SampleRecorder& get_recorder() const override { return m_recorder; }

    // -- Scaffold accessors (for later tasks 6.2/6.4/7.x + tests) -----------
    // These expose the owned emulator-state buffers so the deferred tasks can
    // populate/read them without changing the public IS760Host surface.
    bool is_initialized() const { return m_initialized; }
    bool vdp_vram_active() const { return m_vdp_vram_active; }
    bool sed_vram_active() const { return m_sed_vram_active; }

    std::vector<uint8_t>&       vdp_vram()       { return m_vdp_vram; }
    const std::vector<uint8_t>& vdp_vram() const { return m_vdp_vram; }
    std::vector<uint8_t>&       sed_vram()       { return m_sed_vram; }
    const std::vector<uint8_t>& sed_vram() const { return m_sed_vram; }

    // The owned maincpu-region image bytes loaded by init() (size == the fixed
    // disk-image size on success, empty otherwise).
    const std::vector<uint8_t>& maincpu_region() const { return m_maincpu_region; }

private:
    // Reset the cached CRT raster to an authentic-blank 640x480 RGBA buffer and
    // the cached LCD raster to an all-zero (off) 160x64 MONO1 buffer. Called
    // from the constructor so the surfaces are protocol-correct before any
    // successful run_frame(); task 6.2/6.4 overwrite them with genuine rasters.
    void reset_cached_surfaces();

    // Resolve the on-disk path to `s760224.img` from the configured roms dir /
    // the S760_ROMS_DIR environment variable / relative defaults. Returns an
    // empty string when no readable candidate exists. Never hard-codes an
    // absolute path.
    std::string resolve_image_path() const;

    // Write one byte to a VDP register (task 7.5). This is the single modeled
    // "vdp_w path": every VDP-register write apply_pointer() performs goes
    // through here, storing into the owned m_vdp_regs register file. The genuine
    // MAME machine (task 6.2) routes this exact (reg, value) seam to the real
    // RFSC16A VDP's vdp_w(); the adapter owns the register file until then so
    // the write path is modeled honestly and is directly testable.
    void vdp_w(uint8_t reg, uint8_t value) { m_vdp_regs[reg] = value; }

    // --- Configuration -----------------------------------------------------
    std::string m_roms_dir;             // explicit ROM dir (optional)
    std::string m_resolved_image_path;  // path chosen by the last init()

    // --- Emulator state (owned; SCAFFOLD placeholders for the MAME machine) --
    // The genuine MAME `s760` machine instance is introduced in task 6.2. Until
    // then these buffers stand in as the owned seam the later tasks fill:
    //   * m_maincpu_region : the ROM_REGION16_LE("maincpu") contents (the disk
    //                        image bytes), loaded by init().
    //   * m_vdp_vram       : RFSC16A VDP VRAM (feeds crt_update / the CRT gate).
    //   * m_sed_vram       : Epson SED1335 VRAM (feeds lcd_update / lcd_rasterize).
    std::vector<uint8_t> m_maincpu_region;
    std::vector<uint8_t> m_vdp_vram;
    std::vector<uint8_t> m_sed_vram;

    bool m_initialized      = false;
    bool m_vdp_vram_active  = false;    // mirrors s760_state::m_vdp_vram_active
    bool m_sed_vram_active  = false;    // mirrors s760_state::m_sed_vram_active

    // --- Owned key-matrix state (task 7.1, Requirements 6.1, 6.4) ----------
    // Logical-active-high bitmasks per INPUT_PORTS_START(s760) port: a SET bit
    // means that button is currently pressed. apply_button() sets/clears
    // exactly one bit here; key_matrix() reads them. Both start at 0 (nothing
    // pressed). See apply_button()'s header comment for the active-low mapping
    // note and the stable id-string set.
    uint8_t m_key_arrows_matrix = 0;    // KEY_ARROWS port bit-state
    uint8_t m_gotek_ctrl_matrix = 0;    // GOTEK_CTRL port bit-state

    // --- Owned VDP register file (task 7.5, Requirements 6.3, 6.5) ---------
    // A small 256-byte register file standing in for the genuine RFSC16A VDP
    // registers until task 6.2's machine is linkable. apply_pointer() writes the
    // mouse registers (0x20 X-Low, 0x21 X-High, 0x22 Y-Low, 0x24 Control)
    // through vdp_w(); task 7.6's property test reads them back via vdp_reg() /
    // pointer_x_pixels() / pointer_y_pixels(). All bytes start at 0 (no pointer
    // written yet). See apply_pointer()'s header comment for the exact layout
    // and reconstruction formula.
    uint8_t m_vdp_regs[0x100] = {0};

    // --- Owned encoder detent accumulator (task 7.3, Requirement 6.2) ------
    // The encoder's signed detent count applied FOR THE CURRENT FRAME.
    // apply_dial_delta() accumulates into this (+= delta); run_frame() resets
    // it to 0 at the start of each successful advance so each frame's applied
    // detent count reflects only that frame's deltas. Starts at 0 (no rotation).
    int m_encoder_detents = 0;

    // --- Owned MIDI-in delivery buffer (task 7.9, Requirement 6.8) ---------
    // Every byte delivered via send_midi_message() is appended here in order
    // (NOTE_ON -> 0x90 note vel, NOTE_OFF -> 0x80 note vel from the Bridge).
    // This is the honest, observable delivery queue the genuine machine (task
    // 6.2) drains into the real MIDI UART. Starts empty (no MIDI delivered yet).
    std::vector<uint8_t> m_midi_in;

    // --- Owned mount diagnostics (task 7.9, Requirements 6.6, 6.7) ---------
    // Outcome of the most recent mount_disk() attempt. m_last_mount_ok starts
    // false (no attempt yet) and becomes true/false per attempt; on a failed
    // mount m_last_mount_error records the offending path (empty on success).
    bool        m_last_mount_ok = false;
    std::string m_last_mount_error;

    // --- Cached display rasters (protocol-shaped) --------------------------
    // m_crt_raster : 640x480 RGBA8888 payload (payload_size(RGBA8888,640,480)).
    // m_lcd_raster : 160x64  MONO1    payload (payload_size(MONO1,160,64)=1280).
    std::vector<uint8_t> m_crt_raster;  // RGBA bytes (R,G,B,A per pixel)
    std::vector<uint8_t> m_lcd_raster;  // packed MONO1

    // Owned peripherals (identical to the Core backend).
    S760DriveManager  m_drive_manager;
    S760SampleRecorder m_recorder;
};

} // namespace s760
