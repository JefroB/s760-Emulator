// =============================================================================
//  s760_mame_host.cpp
//
//  S760MameHost — MAME_Backend adapter SCAFFOLD (spec `mame-live-backend`,
//  task 6.1). See s760_mame_host.hpp for the full scaffold-vs-deferred contract.
//
//  What this scaffold does TODAY:
//    * init(): resolves `s760224.img` (from an explicit roms dir, else the
//      S760_ROMS_DIR environment variable, else a small set of relative
//      defaults — never a hard-coded absolute path), loads it into the owned
//      `maincpu`-region buffer, and returns true only when the image is present
//      and the expected size. It NEVER spawns a process and NEVER terminates the
//      host (Requirements 1.1, 1.4, 1.6).
//    * get_latest_video_frame() / get_lcd_surface(): serve authentic-blank
//      cached rasters (the MAME backend owns an LCD raster, so get_lcd_surface
//      returns true and fills all-zero when uninitialized).
//    * get_drive_manager() / get_recorder(): own real peripherals like the Core
//      backend so the Bridge's mount/telemetry accessors work.
//
//  Deferred (documented, see header):
//    * run_frame() returns false until the genuine machine is stepped (task 6.2).
//    * CRT/LCD rasterization from genuine VRAM (task 6.4) — the pure helpers it
//      will use (crt_should_rasterize/crt_blank, crt_line_double, lcd_rasterize)
//      already exist and are intentionally referenced here only via includes so
//      this translation unit links against them cleanly.
//    * Input / MIDI / disk-mount routing into the genuine MAME path (task 7.x).
// =============================================================================

#include "s760/s760_mame_host.hpp"

#include "s760/s760_bridge_protocol.hpp"
#include "s760/s760_crt_gate.hpp"      // crt_blank() — used by task 6.4
#include "s760/s760_crt_normalize.hpp" // crt_line_double() — used by task 6.4
#include "s760/s760_lcd_raster.hpp"    // lcd_rasterize() — used by task 6.4

#include <algorithm> // std::min, std::copy, std::fill_n
#include <cmath>     // std::lround
#include <cstdlib>   // std::getenv
#include <fstream>
#include <ios>
#include <utility>

namespace s760 {

namespace {

// Fixed geometry of the owned RFSC16A VDP VRAM window. The MAME driver's VDP
// VRAM feeds a 640x240 raster + the first 2400 bytes gate the CRT (see
// s760_crt_gate.hpp / crt_update). A conservative 64 KiB window comfortably
// covers the active region and leaves room for task 6.2 to size it exactly to
// the genuine device once the MAME machine is wired.
constexpr std::size_t kVdpVramBytes = 0x10000;

// The Epson SED1335 VRAM is 4096 bytes in the MAME driver (`m_sed_vram[4096]`),
// of which the first 1280 feed the 160x64 MONO1 image (see s760_lcd_raster.hpp).
constexpr std::size_t kSedVramBytes = 4096;

// Expected size of the Ver. 2.24 system disk image, mapped as the `maincpu`
// ROM region by ROM_START(s760): ROM_REGION16_LE(0x168000, "maincpu", 0).
// (1,474,560 bytes — a standard 1.44 MB floppy.)
constexpr std::size_t kMaincpuRegionBytes = 0x168000;

// The system-disk image filename loaded as the maincpu region.
constexpr char kImageFileName[] = "s760224.img";

// Join a directory and a filename with a '/' separator (both path separators
// work on Windows; '/' keeps the code portable and avoids backslash escaping).
std::string join_path(const std::string& dir, const char* name) {
    if (dir.empty()) return name;
    char last = dir.back();
    if (last == '/' || last == '\\') return dir + name;
    return dir + "/" + name;
}

// True if the file at `path` exists, is readable, and has exactly
// `kMaincpuRegionBytes` bytes (the fixed disk-image size).
bool is_readable_image(const std::string& path) {
    std::ifstream f(path, std::ios::binary | std::ios::ate);
    if (!f.is_open()) return false;
    const std::streamoff size = f.tellg();
    return size == static_cast<std::streamoff>(kMaincpuRegionBytes);
}

} // namespace

S760MameHost::S760MameHost() : S760MameHost(std::string{}) {}

S760MameHost::S760MameHost(std::string roms_dir)
    : m_roms_dir(std::move(roms_dir)),
      m_vdp_vram(kVdpVramBytes, 0u),
      m_sed_vram(kSedVramBytes, 0u) {
    reset_cached_surfaces();
}

S760MameHost::~S760MameHost() = default;

void S760MameHost::reset_cached_surfaces() {
    // Authentic-blank CRT: a zero-filled RGBA8888 buffer of the exact protocol
    // payload size. Identical in content to crt_blank(); sized here directly so
    // the scaffold has no behavioral dependency on that helper (task 6.4 will
    // use crt_blank()/crt_line_double() to produce genuine frames).
    m_crt_raster.assign(
        bridge::payload_size(bridge::PixelFormat::RGBA8888,
                             bridge::CRT_WIDTH, bridge::CRT_HEIGHT),
        0u);

    // All-zero (every pixel off) MONO1 160x64 LCD raster.
    m_lcd_raster.assign(
        bridge::payload_size(bridge::PixelFormat::MONO1,
                             bridge::LCD_WIDTH, bridge::LCD_HEIGHT),
        0u);
}

std::string S760MameHost::resolve_image_path() const {
    // 1) Explicit roms dir configured on this host.
    if (!m_roms_dir.empty()) {
        const std::string candidate = join_path(m_roms_dir, kImageFileName);
        if (is_readable_image(candidate)) return candidate;
    }

    // 2) S760_ROMS_DIR environment variable (honored by tests/mame_harness.py).
    if (const char* env = std::getenv("S760_ROMS_DIR"); env && *env) {
        const std::string candidate = join_path(env, kImageFileName);
        if (is_readable_image(candidate)) return candidate;
    }

    // 3) Sensible relative defaults (no hard-coded absolute path). These mirror
    //    the project's layout where images live under roms/s760 or the repo root.
    static const char* const kRelativeDefaults[] = {
        "roms/s760",
        "roms",
        ".",
    };
    for (const char* dir : kRelativeDefaults) {
        const std::string candidate = join_path(dir, kImageFileName);
        if (is_readable_image(candidate)) return candidate;
    }

    return std::string{}; // nothing readable found
}

bool S760MameHost::init() {
    // Start from a clean, honest state: not initialized, surfaces blank.
    m_initialized = false;
    m_vdp_vram_active = false;
    m_sed_vram_active = false;
    m_maincpu_region.clear();
    reset_cached_surfaces();

    // Resolve the system-disk image WITHOUT spawning any process (Requirement
    // 1.1) and WITHOUT ever terminating the host on failure (Requirement 1.4).
    m_resolved_image_path = resolve_image_path();
    if (m_resolved_image_path.empty()) {
        return false; // image absent/unreadable -> graceful init failure
    }

    // Load the image bytes into the owned maincpu-region buffer.
    std::ifstream f(m_resolved_image_path, std::ios::binary);
    if (!f.is_open()) {
        return false;
    }

    std::vector<uint8_t> bytes(kMaincpuRegionBytes);
    f.read(reinterpret_cast<char*>(bytes.data()),
           static_cast<std::streamsize>(kMaincpuRegionBytes));
    if (!f || f.gcount() != static_cast<std::streamsize>(kMaincpuRegionBytes)) {
        return false; // short read -> graceful failure, nothing retained
    }

    m_maincpu_region = std::move(bytes);
    m_initialized = true;

    // SCAFFOLD: the genuine MAME `s760` machine (N8097BH CPU + s760_mem map +
    // VDP/SED1335 devices) is constructed and begins executing in task 6.2.
    // Loading the program image is the honest, verifiable prerequisite for that
    // bring-up; init() returning true here means "the backend has its program
    // image and did not fail", not "the OS has booted". No process was spawned.
    return true;
}

bool S760MameHost::run_frame() {
    // -------------------------------------------------------------------------
    //  run_frame() — advance exactly one emulated video frame, then refresh the
    //  cached CRT + LCD rasters from the owned VRAM buffers (Requirements 1.3,
    //  1.5). See the "advance one frame" / honesty notes below.
    //
    //  HONEST LIMITATION (MAME core not linkable in this build)
    //  --------------------------------------------------------
    //  The genuine in-process MAME `s760` machine (N8097BH CPU + s760_mem map +
    //  the RFSC16A VDP / Epson SED1335 devices) is NOT linkable in this build
    //  yet, so there is no real CPU to clock for "one 60 Hz video frame" and no
    //  genuine device to tick the VRAM. We therefore implement the frame-advance
    //  as a well-defined SEAM: a backend that has loaded its program image
    //  (`m_initialized`) performs one deterministic refresh of its cached
    //  rasters FROM the owned VRAM buffers (m_vdp_vram / m_sed_vram) using the
    //  pure helpers (crt_gate / crt_normalize / lcd_raster). When task 6.2's
    //  genuine machine lands, the single `advance_one_frame()` step below is the
    //  one place that clocks the real CPU/devices; the raster-refresh logic that
    //  follows stays identical because it already reads from the owned VRAM the
    //  genuine devices will populate.
    //
    //  Requirement 1.5 (unchanged-on-failure) is satisfied structurally: the new
    //  rasters are built into LOCAL TEMPORARIES and only committed to
    //  m_crt_raster / m_lcd_raster on success. Any early `return false` leaves
    //  the previously cached surfaces byte-for-byte unchanged.
    // -------------------------------------------------------------------------

    // Failure path #1: no program image loaded (init() not called or it failed).
    // Return false and leave the cached surfaces exactly as they were
    // (Requirement 1.5). No partial or invented frame is produced.
    if (!m_initialized) {
        return false;
    }

    // --- Begin-frame: reset the per-frame encoder detent accumulator --------
    // (task 7.3, Requirement 6.2). m_encoder_detents holds the encoder's signed
    // detent count applied FOR THE CURRENT FRAME; apply_dial_delta() accumulates
    // this frame's DIAL_DELTA deltas into it. Resetting to 0 at the START of a
    // successful advance ensures each frame's applied detent count reflects only
    // that frame's deltas, so a single apply_dial_delta(d) after this boundary
    // yields encoder_detents() == d (Property 10). This is the only line
    // run_frame() needs for the dial seam; the rest of its logic is unchanged.
    m_encoder_detents = 0;

    // --- Advance exactly one emulated video frame (headless seam) -----------
    // With the genuine MAME machine absent, this step is a no-op clock: it does
    // not fabricate any VRAM content. When task 6.2 wires the real machine, the
    // single call that steps the CPU/devices for one 60 Hz frame goes HERE, and
    // it populates m_vdp_vram / m_sed_vram / m_vdp_vram_active / m_sed_vram_active
    // before the raster refresh below. We deliberately read the owned VRAM as-is
    // so the refresh is an honest function of whatever VRAM currently holds
    // (all-zero today -> authentic-blank surfaces).

    // --- Build the new CRT raster into a TEMPORARY --------------------------
    // Decide rasterize-vs-blank via the pure gate (task 3.4 logic), exactly
    // mirroring the MAME driver's crt_update gate (explicit active flag OR the
    // first-2400-byte non-zero inference scan).
    std::vector<uint8_t> next_crt;
    const bool rasterize_crt = crt_should_rasterize(
        m_vdp_vram_active, m_vdp_vram.data(), m_vdp_vram.size());

    if (rasterize_crt) {
        // HONEST CHOICE: the gate says the VDP VRAM is genuine, but there is no
        // genuine VDP rasterizer wired in this build to turn m_vdp_vram into a
        // 640x240 RGBA raster — that is task 6.4 / a future hook. Rather than
        // INVENT screen content (forbidden by Requirements 4.1/4.6 — no
        // fabricated pixels, no chrome), we emit the authentic-blank CRT here
        // too. The structural path (gate -> rasterize/normalize -> commit) is
        // fully in place; task 6.4 replaces this blank with the genuine VDP
        // 640x240 rasterization fed through crt_line_double(...). This keeps the
        // backend honest: the only pixels it ever emits are genuine (today:
        // none), never fabricated.
        //
        // When 6.4 lands, this branch becomes, concretely:
        //     std::vector<uint8_t> src_640x240 = rasterize_vdp(m_vdp_vram ...);
        //     next_crt = crt_line_double(src_640x240.data(),
        //                                src_640x240.size(), 640, 240);
        next_crt = crt_blank();
    } else {
        // VDP inactive and the first 2400 bytes all zero -> authentic-blank
        // 640x480 RGBA CRT surface of the exact protocol payload size.
        next_crt = crt_blank();
    }

    // --- Build the new LCD raster into a TEMPORARY --------------------------
    // The SED1335 has no MAME screen device, so the adapter rasterizes it here
    // each frame via the pure lcd_rasterize() helper (task 3.6), deriving every
    // pixel SOLELY from m_sed_vram (Requirements 3.1/3.4). All-zero/inactive
    // VRAM yields an all-zero (off) 1280-byte MONO1 payload (Requirement 3.2).
    std::vector<uint8_t> next_lcd =
        lcd_rasterize(m_sed_vram.data(), m_sed_vram.size(), m_sed_vram_active);

    // --- Validate the temporaries before committing ------------------------
    // Both rasters must match the exact protocol payload size for their surface
    // before we overwrite the cached surfaces. If either is malformed we treat
    // the advance as failed and leave the cached surfaces unchanged
    // (Requirement 1.5) rather than committing a bad surface.
    const std::size_t crt_expected = bridge::payload_size(
        bridge::PixelFormat::RGBA8888, bridge::CRT_WIDTH, bridge::CRT_HEIGHT);
    const std::size_t lcd_expected = bridge::payload_size(
        bridge::PixelFormat::MONO1, bridge::LCD_WIDTH, bridge::LCD_HEIGHT);

    if (next_crt.size() != crt_expected || next_lcd.size() != lcd_expected) {
        return false; // cached surfaces untouched
    }

    // --- Commit on success --------------------------------------------------
    // Only now do we overwrite the cached rasters. Up to this point every
    // early return left m_crt_raster / m_lcd_raster byte-for-byte unchanged.
    m_crt_raster = std::move(next_crt);
    m_lcd_raster = std::move(next_lcd);
    return true;
}

VideoFrame S760MameHost::get_latest_video_frame() const {
    // -------------------------------------------------------------------------
    //  get_latest_video_frame() — task 6.4 (Requirements 4.1, 4.6).
    //
    //  Serve the cached CRT raster as a fixed-geometry 640x480 RGBA VideoFrame.
    //  Every emitted pixel comes EXACTLY from m_crt_raster, which run_frame()
    //  (task 6.2) builds solely from genuine VDP VRAM (via the crt_gate +
    //  crt_blank/crt_line_double helpers) or leaves as the authentic-blank
    //  (all-zero) buffer. This method NEVER fabricates pixels and NEVER
    //  reintroduces the CRT chrome removed in ui-consolidation (banner, mode
    //  ribbon, soft-button bar, rack panel) — it is a pure read of the cache
    //  (Requirement 4.6).
    //
    //  Geometry is pinned to bridge::CRT_WIDTH x bridge::CRT_HEIGHT (640x480,
    //  Requirement 4.1) regardless of the cached raster's state. If the cache
    //  is uninitialized/empty or shorter than a full frame, the uncovered
    //  pixels stay authentic-blank (all-zero) rather than invented.
    // -------------------------------------------------------------------------
    VideoFrame frame;
    frame.width = bridge::CRT_WIDTH;
    frame.height = bridge::CRT_HEIGHT;

    // Default every pixel to authentic-blank (0). Any pixel we cannot source
    // from the cached raster therefore stays blank — never fabricated.
    const std::size_t pixel_count =
        static_cast<std::size_t>(bridge::CRT_WIDTH) * bridge::CRT_HEIGHT;
    frame.rgba_pixels.assign(pixel_count, 0u);

    // Pack the cached RGBA byte raster (R,G,B,A per pixel) into 32-bit pixels.
    // On the wire the CRT payload is byte order R,G,B,A (payload[0]=R, [1]=G,
    // [2]=B, [3]=A); packing as r | (g<<8) | (bl<<16) | (a<<24) stores those
    // bytes in that order in memory on the little-endian hosts the Bridge runs
    // on, matching the CRT payload semantics. Only the pixels actually present
    // in the cache are copied; the rest remain authentic-blank.
    const std::size_t copyable_pixels =
        std::min<std::size_t>(pixel_count, m_crt_raster.size() / 4u);
    for (std::size_t p = 0; p < copyable_pixels; ++p) {
        const std::size_t b = p * 4u;
        const uint32_t r = m_crt_raster[b + 0];
        const uint32_t g = m_crt_raster[b + 1];
        const uint32_t bl = m_crt_raster[b + 2];
        const uint32_t a = m_crt_raster[b + 3];
        frame.rgba_pixels[p] = r | (g << 8) | (bl << 16) | (a << 24);
    }
    return frame;
}

bool S760MameHost::get_lcd_surface(uint8_t* out, std::size_t len) const {
    // -------------------------------------------------------------------------
    //  get_lcd_surface() — task 6.4 (Requirements 3.1, 4.7).
    //
    //  Fill the caller's buffer with the cached 160x64 MONO1 LCD raster. That
    //  raster is produced by run_frame() (task 6.2) via the pure lcd_rasterize()
    //  helper, deriving every bit SOLELY from the genuine SED1335 VRAM
    //  (m_sed_vram) — no font ROM, no control registers, no invented content
    //  (Requirement 3.1). Unlike the Core backend (which returns false), the
    //  MAME backend owns an LCD raster, so this returns true and fills the
    //  buffer whenever the geometry/length match (Requirement 4.7).
    //
    //  Returns false ONLY on a null buffer or a length that does not equal
    //  payload_size(MONO1, 160, 64); in that case the Bridge keeps its
    //  authentic-blank LCD behavior. If the cached raster size were ever to
    //  mismatch the expected length, the buffer is filled with zeros (every
    //  pixel off) rather than fabricated content.
    // -------------------------------------------------------------------------
    const std::size_t expected =
        bridge::payload_size(bridge::PixelFormat::MONO1,
                             bridge::LCD_WIDTH, bridge::LCD_HEIGHT);
    if (out == nullptr || len != expected) {
        return false; // null / geometry-length mismatch -> Bridge keeps blank
    }

    if (m_lcd_raster.size() == expected) {
        std::copy(m_lcd_raster.begin(), m_lcd_raster.end(), out);
    } else {
        // Defensive: a cache of unexpected size is treated as "no genuine data"
        // (all pixels off), never fabricated.
        std::fill_n(out, expected, static_cast<uint8_t>(0));
    }
    return true;
}

void S760MameHost::send_midi_message(const uint8_t* msg, size_t len) {
    // -------------------------------------------------------------------------
    //  send_midi_message() — task 7.9 (Requirement 6.8).
    //
    //  Deliver the MIDI bytes the Bridge produced from a NOTE_ON / NOTE_OFF into
    //  the emulated OS. The genuine in-process MAME `s760` MIDI UART is not
    //  linkable in this build yet, so this is the HONEST delivery seam: append
    //  the `len` bytes of `msg` to the owned MIDI-in buffer (m_midi_in) in
    //  order, making delivery observable/testable (task 7.10). Task 6.2's
    //  genuine machine drains m_midi_in into the real MIDI UART; the
    //  append-on-delivery contract here stays identical.
    //
    //  GUARD: a null buffer or zero length is a no-op (nothing appended) so an
    //  empty/malformed delivery never corrupts the buffer or crashes.
    // -------------------------------------------------------------------------
    if (msg == nullptr || len == 0) {
        return; // nothing to deliver
    }
    m_midi_in.insert(m_midi_in.end(), msg, msg + len);
}

// ---------------------------------------------------------------------------
//  Disk mounting adapter seam (task 7.9, Requirements 6.6, 6.7)
// ---------------------------------------------------------------------------
bool S760MameHost::mount_disk(const std::string& path) {
    // Delegate to the owned drive manager's mount_floppy(), the SAME path the
    // Bridge already uses for MOUNT_DISK (Requirement 6.6). mount_floppy()
    // returns true on success and false on a path that cannot be opened/mounted,
    // KEEPING the currently mounted image and NOT crashing on failure
    // (Requirement 6.7). We simply surface that bool and record a diagnostic.
    const bool ok = m_drive_manager.mount_floppy(path);
    m_last_mount_ok = ok;
    // On failure record the offending path for reporting/tests; clear it on
    // success. The current image is left untouched by mount_floppy() on failure.
    m_last_mount_error = ok ? std::string{} : path;
    return ok;
}

int16_t S760MameHost::handle_input_state(unsigned port, unsigned device,
                                         unsigned index, unsigned id) {
    // The libretro-style polling signature (port/device/index/id) is the
    // Core backend's convention; the MAME backend's genuine input seam is
    // apply_button() (and the later encoder/pointer seams of tasks 7.3/7.5),
    // which the Bridge's BUTTON_PRESS / BUTTON_RELEASE routing invokes. This
    // polling stub stays a no-op (returns 0) for the MAME backend; wiring the
    // Bridge to call apply_button() is a separate (later) concern.
    (void)port;
    (void)device;
    (void)index;
    (void)id;
    return 0;
}

// ---------------------------------------------------------------------------
//  Button -> key-matrix bit mapping (task 7.1, Requirements 6.1, 6.4)
// ---------------------------------------------------------------------------
namespace {

// Which owned port byte a mapped button lives in.
enum class MamePort { KeyArrows, GotekCtrl };

struct KeyMatrixBit {
    const char* id;    // stable protocol id string (see header docs)
    MamePort    port;  // owning INPUT_PORTS_START(s760) port
    uint8_t     bit;   // the single bit this id sets/clears
};

// Static mapping table derived verbatim from INPUT_PORTS_START(s760) in
// mame-source/src/mame/roland/s760.cpp:
//
//   PORT_START("KEY_ARROWS")
//     0x01 IPT_JOYSTICK_LEFT   "Cursor Left"
//     0x02 IPT_JOYSTICK_RIGHT  "Cursor Right"
//     0x04 IPT_JOYSTICK_UP     "Cursor Up"
//     0x08 IPT_JOYSTICK_DOWN   "Cursor Down"
//     0x10 IPT_BUTTON1         "Select / Enter"
//   PORT_START("GOTEK_CTRL")
//     0x01 IPT_BUTTON4         "Gotek Prev Image"
//     0x02 IPT_BUTTON5         "Gotek Next Image"
//     0x04 IPT_BUTTON6         "Gotek Select / Push"
//
// The chosen id strings are the stable, documented set task 7.2 and the UI
// wiring align on (see s760_mame_host.hpp apply_button() docs). Any id not in
// this table maps to no defined input and is ignored (Requirement 6.4).
constexpr KeyMatrixBit kKeyMatrixMap[] = {
    {"cursor_left",  MamePort::KeyArrows, 0x01},
    {"cursor_right", MamePort::KeyArrows, 0x02},
    {"cursor_up",    MamePort::KeyArrows, 0x04},
    {"cursor_down",  MamePort::KeyArrows, 0x08},
    {"enter",        MamePort::KeyArrows, 0x10},
    {"gotek_prev",   MamePort::GotekCtrl, 0x01},
    {"gotek_next",   MamePort::GotekCtrl, 0x02},
    {"gotek_select", MamePort::GotekCtrl, 0x04},
};

// Resolve an id string to its mapping entry, or nullptr when unknown.
const KeyMatrixBit* find_key_matrix_bit(const std::string& id) {
    for (const KeyMatrixBit& e : kKeyMatrixMap) {
        if (id == e.id) return &e;
    }
    return nullptr;
}

} // namespace

void S760MameHost::apply_button(const std::string& id, bool pressed) {
    const KeyMatrixBit* entry = find_key_matrix_bit(id);
    if (entry == nullptr) {
        // Unknown id maps to no defined input -> ignore, no state change
        // (Requirement 6.4).
        return;
    }

    // Pick the owned port byte and set (press) or clear (release) EXACTLY the
    // mapped bit, leaving every other bit untouched (Requirement 6.1).
    uint8_t& port_byte = (entry->port == MamePort::KeyArrows)
                             ? m_key_arrows_matrix
                             : m_gotek_ctrl_matrix;
    if (pressed) {
        port_byte |= entry->bit;    // set exactly that bit
    } else {
        port_byte &= static_cast<uint8_t>(~entry->bit); // clear exactly that bit
    }
}

// ---------------------------------------------------------------------------
//  Dial-delta encoder application (task 7.3, Requirement 6.2)
// ---------------------------------------------------------------------------
void S760MameHost::apply_dial_delta(int delta) {
    // Apply `delta` as the emulated encoder's signed detent count FOR THE FRAME
    // in which it is processed (Requirement 6.2). We ACCUMULATE so multiple
    // DIAL_DELTA messages within one frame sum into one net per-frame rotation;
    // run_frame() resets m_encoder_detents to 0 at the start of each successful
    // advance, so each frame's applied detent count reflects only that frame's
    // deltas. After a frame-boundary reset, a single apply_dial_delta(d) yields
    // encoder_detents() == d (Property 10). A zero delta is a harmless no-op.
    m_encoder_detents += delta;
}

namespace {

// The DEFINED encoder ids the UI emits via DIAL_DELTA (see
// s760_bridge_protocol.hpp "DIAL_DELTA : { id, delta } ... `id` selects which
// encoder" and google-ui S760BridgeClient: "ALPHA" (Value/Data alpha-dial) and
// "VOLUME"). Any id not in this set maps to no defined input and is ignored
// (Requirement 6.4). Both route to the one modeled encoder in this build.
constexpr const char* kDefinedEncoderIds[] = {
    "ALPHA",
    "VOLUME",
};

} // namespace

bool S760MameHost::is_defined_encoder(const std::string& id) {
    for (const char* defined : kDefinedEncoderIds) {
        if (id == defined) return true;
    }
    return false;
}

void S760MameHost::apply_dial_delta(const std::string& id, int delta) {
    // id-aware DIAL_DELTA (task 7.7, Requirements 6.2, 6.4). A delta whose `id`
    // is NOT a defined encoder maps to no defined input and is IGNORED, leaving
    // m_encoder_detents byte-for-byte unchanged (Requirement 6.4 / Property 12).
    if (!is_defined_encoder(id)) {
        return; // unknown encoder id -> no detent applied, no state change
    }
    // Defined encoder: apply exactly as the id-less overload (there is one
    // modeled encoder in this build, so every defined id routes to it).
    apply_dial_delta(delta);
}

uint8_t S760MameHost::key_matrix(const std::string& port) const {
    if (port == "KEY_ARROWS") return m_key_arrows_matrix;
    if (port == "GOTEK_CTRL") return m_gotek_ctrl_matrix;
    return 0; // unrecognized port name
}

// ---------------------------------------------------------------------------
//  Pointer -> VDP mouse-register scaling (task 7.5, Requirements 6.3, 6.5)
// ---------------------------------------------------------------------------
namespace {

// VDP mouse register indices (design "MAME driver" notes).
constexpr uint8_t kVdpMouseXLow  = 0x20; // Mouse X Low  (low 8 bits of X)
constexpr uint8_t kVdpMouseXHigh = 0x21; // Mouse X High (high bits of X)
constexpr uint8_t kVdpMouseYLow  = 0x22; // Mouse Y Low  (low 8 bits of Y)
constexpr uint8_t kVdpMouseCtrl  = 0x24; // Mouse Control

// Control-byte layout written on a pointer update:
//   bit0 = Y high bit (py >> 8), since CRT_HEIGHT=480 needs 9 bits and the
//          design's register list has no dedicated Y-High register.
//   bit7 = "mouse coordinates valid / updated this write" flag — the documented
//          constant that marks a genuine pointer update came through the vdp_w
//          path (distinguishes a written register file from the all-zero reset).
constexpr uint8_t kMouseCtrlYHighBit  = 0x01;
constexpr uint8_t kMouseUpdateValid   = 0x80;

} // namespace

void S760MameHost::apply_pointer(double x, double y) {
    // OUT-OF-RANGE / NaN GUARD FIRST (task 7.7, Requirement 6.4, Property 12).
    // Normalized coordinates are valid only in the INCLUSIVE range [0.0, 1.0].
    // If either axis is outside that range -- or is NaN (any comparison with NaN
    // is false, so `!(x >= 0.0 && x <= 1.0)` is true for NaN) -- IGNORE the
    // message entirely: return before touching any VDP register, leaving the
    // owned m_vdp_regs byte-for-byte unchanged. 0.0 and 1.0 are both accepted
    // (x==1.0 -> px==640, y==1.0 -> py==480), so in-range behavior below is
    // unchanged.
    const bool x_in_range = (x >= 0.0 && x <= 1.0);
    const bool y_in_range = (y >= 0.0 && y <= 1.0);
    if (!x_in_range || !y_in_range) {
        return; // out-of-range / NaN -> no VDP write, no state change (R6.4)
    }

    // ABSOLUTE normalized->pixel scaling ONLY (Requirements 6.3, 6.5). There is
    // deliberately NO +/-127 relative-delta path here: no accumulator, no clamp
    // to a signed 8-bit range, no previous-position subtraction. Every write is
    // a fresh absolute pixel coordinate derived from the normalized input.
    //
    // Scale and round EXACTLY per Property 11:
    //     px = round(x * CRT_WIDTH)   (x in [0,1] -> [0, 640])
    //     py = round(y * CRT_HEIGHT)  (y in [0,1] -> [0, 480])
    // std::lround performs round-half-away-from-zero on a double; for the
    // non-negative in-range inputs this is the ordinary "round to nearest".
    // We store the rounded value FAITHFULLY and do NOT clamp 640->639 / 480->479,
    // so the registers always reconstruct exactly round(x*640) / round(y*480).
    const long px = std::lround(x * static_cast<double>(bridge::CRT_WIDTH));
    const long py = std::lround(y * static_cast<double>(bridge::CRT_HEIGHT));

    const uint16_t px_u = static_cast<uint16_t>(px);
    const uint16_t py_u = static_cast<uint16_t>(py);

    // Build the Control byte: Y high bit (bit0) + the "coords valid/updated" flag
    // (bit7). The Y high bit lets pointer_y_pixels() reconstruct the full 9-bit Y.
    const uint8_t control =
        static_cast<uint8_t>(((py_u >> 8) & 0x01) ? kMouseCtrlYHighBit : 0u) |
        kMouseUpdateValid;

    // Write through the single modeled vdp_w path (task 6.2's genuine machine
    // routes these same calls to the real RFSC16A VDP).
    vdp_w(kVdpMouseXLow,  static_cast<uint8_t>(px_u & 0xFF));         // 0x20
    vdp_w(kVdpMouseXHigh, static_cast<uint8_t>((px_u >> 8) & 0x03));  // 0x21
    vdp_w(kVdpMouseYLow,  static_cast<uint8_t>(py_u & 0xFF));         // 0x22
    vdp_w(kVdpMouseCtrl,  control);                                  // 0x24
}

uint16_t S760MameHost::pointer_x_pixels() const {
    // Reconstruct X from 0x20 (low 8 bits) + 0x21 (high bits, masked to 0x03).
    return static_cast<uint16_t>(
        ((static_cast<uint16_t>(m_vdp_regs[kVdpMouseXHigh]) & 0x03) << 8) |
        m_vdp_regs[kVdpMouseXLow]);
}

uint16_t S760MameHost::pointer_y_pixels() const {
    // Reconstruct Y from 0x22 (low 8 bits) + the Y high bit packed in 0x24 bit0.
    return static_cast<uint16_t>(
        ((static_cast<uint16_t>(m_vdp_regs[kVdpMouseCtrl]) & kMouseCtrlYHighBit) << 8) |
        m_vdp_regs[kVdpMouseYLow]);
}

} // namespace s760
