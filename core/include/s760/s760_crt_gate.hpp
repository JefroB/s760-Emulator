#pragma once

// =============================================================================
//  s760_crt_gate.hpp
//
//  Pure VDP VRAM-activity inference + CRT rasterization gate for the MAME live
//  backend (spec `mame-live-backend`, task 3.4).
//
//  This mirrors the gate logic in the MAME `s760` driver's `crt_update`
//  (`mame-source/src/mame/roland/s760.cpp`):
//
//      bool render_from_vram = m_vdp_vram_active;
//      if (!render_from_vram)
//          for (int i = 0; i < 2400; i++)
//              if (m_vdp_vram[i] != 0) { render_from_vram = true; ... break; }
//
//  i.e. the CRT is rasterized from genuine VDP VRAM when `VDP_VRAM_Active` is
//  true, OR when it is false but any of the first 2400 bytes of `m_vdp_vram`
//  are non-zero (the "inferred-active" scan). Otherwise the backend emits the
//  authentic-blank 640x480 CRT surface (a zero-filled RGBA8888 buffer of
//  `bridge::payload_size(RGBA8888, 640, 480)`).
//
//  These are PURE functions with no dependency on the MAME scheduler, so the
//  property test (task 3.5) can exercise them with no MAME binary present
//  (Requirement 8.5). This gate is intentionally self-contained and does NOT
//  depend on the CRT 640x240->640x480 normalization helper (task 3.2); the
//  caller is responsible for rasterizing + normalizing when the gate decides to
//  rasterize.
//
//  Spec: .kiro/specs/mame-live-backend/  (design "Property 3: CRT rasterization
//        and VRAM-activity inference gate"; Requirements 4.1, 4.3, 4.5).
// =============================================================================

#include <cstddef>
#include <cstdint>
#include <vector>

namespace s760 {

// Number of leading VDP VRAM bytes scanned to infer genuine OS activity when
// the explicit `VDP_VRAM_Active` flag is false. Matches the MAME driver's
// `crt_update` fallback scan length exactly.
inline constexpr std::size_t kVdpInferScanBytes = 2400;

// Decide whether the CRT should be rasterized from genuine VDP VRAM.
//
// Returns true when `vdp_vram_active` is true, OR (it is false but any of the
// first min(kVdpInferScanBytes, vram_len) bytes of `vdp_vram` are non-zero).
// Returns false otherwise (the caller should then produce `crt_blank()`).
//
// The inferred-active decision (when `vdp_vram_active` is false) is EXACTLY the
// first-2400-byte non-zero scan, matching the driver. A null `vdp_vram` or a
// `vram_len` of 0 contributes no non-zero bytes, so the result equals
// `vdp_vram_active` in that case.
bool crt_should_rasterize(bool vdp_vram_active,
                          const uint8_t* vdp_vram,
                          std::size_t vram_len);

// Produce the authentic-blank 640x480 CRT surface: a zero-filled RGBA8888
// buffer whose length is exactly `bridge::payload_size(RGBA8888, 640, 480)`.
// No fabricated pixel content — every byte is zero.
std::vector<uint8_t> crt_blank();

} // namespace s760
