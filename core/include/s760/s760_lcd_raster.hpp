#pragma once

// =============================================================================
//  s760_lcd_raster.hpp
//
//  Pure SED1335 LCD rasterizer for the MAME live backend (spec
//  `mame-live-backend`, task 3.6). Derives a 160x64 MONO1 LCD surface SOLELY
//  from the genuine Epson SED1335 VRAM (`m_sed_vram`), with no other source.
//
//  This is the VRAM->pixel transform the `S760MameHost` adapter calls each
//  pumped frame to produce `SurfaceId::LCD`, since the MAME `machine_config`
//  registers no `lcd_screen` device (design "Research notes" + Requirement
//  3.3). It is extracted as a pure, header-light function so the property test
//  (task 3.7) can exercise it in-process with no MAME binary present
//  (Requirement 8.5).
//
//  ---------------------------------------------------------------------------
//  VRAM -> PIXEL MAPPING (replicates lcd_update's genuine 1-bit graphics plane)
//  ---------------------------------------------------------------------------
//  The S-760 driver's `lcd_update` (mame-source/src/mame/roland/s760.cpp)
//  composes up to two layers:
//    * a TEXT layer (disp_mode & 0x01) that indexes a hardcoded FONT ROM via
//      get_font_glyph() at the SAD1 character-matrix base, and
//    * a 1-bit GRAPHICS plane (disp_mode & 0x04) read directly from VRAM at the
//      SAD2 base with layout `byte_offset = y*20 + (x/8)`, bit `(0x80 >> (x%8))`.
//
//  Requirements 3.1 and 3.4 require every emitted pixel to be derived SOLELY
//  from `m_sed_vram` with NO other source and NO invented content. The TEXT
//  layer depends on a separate font-ROM table and on the SED1335 control
//  registers (SAD1/SAD2/disp_mode/overlay_mode), none of which are VRAM — so a
//  VRAM-only function cannot reproduce it without inventing content. The 1-bit
//  GRAPHICS plane, by contrast, is a direct, lossless, byte-for-byte image of
//  VRAM and maps 1:1 onto the MONO1 output (identical bit layout):
//
//      MONO1 (protocol): 1bpp, MSB = leftmost pixel, row stride =
//        ceil(160/8) = 20 bytes, 64 rows => payload_size(MONO1,160,64)=1280.
//      SED1335 gfx plane: byte at (y*20 + x/8), bit (0x80 >> (x%8)), 1 = on.
//
//  Because the two layouts are identical, this rasterizer maps SED1335 graphics
//  VRAM straight into the MONO1 payload: output byte[y*20 + col] = sed_vram[y*20
//  + col] for col in [0,20), y in [0,64) (the first 1280 bytes of VRAM). Every
//  output bit is a genuine VRAM bit; nothing is fabricated.
//
//  Blank rule (Requirement 3.2): when `sed_vram_active` is false AND the VRAM is
//  all zero, the result is an all-zero (every pixel off) 1280-byte payload. With
//  the direct mapping above this falls out naturally (all-zero VRAM -> all-zero
//  payload), and the function additionally short-circuits to a defined all-zero
//  payload in that case so the "no genuine data" state is explicit.
//
//  Determinism (Requirement 3.5): the output depends only on the function's
//  inputs (`sed_vram`, `vram_len`, `sed_vram_active`); there is no global or
//  hidden state.
//
//  Spec: .kiro/specs/mame-live-backend/  (Requirements 3.1, 3.2, 3.4, 3.5;
//        design "Property 2" and "Components / S760MameHost::get_lcd_surface").
// =============================================================================

#include <cstddef>
#include <cstdint>
#include <vector>

#include "s760/s760_bridge_protocol.hpp"

namespace s760 {

// Rasterize the genuine SED1335 VRAM into a 160x64 MONO1 LCD payload.
//
//   sed_vram        : pointer to the SED1335 VRAM bytes (`m_sed_vram`). May be
//                     null, in which case the VRAM is treated as empty.
//   vram_len        : number of readable bytes at `sed_vram` (the driver's VRAM
//                     is 4096 bytes; only the first 1280 feed the 160x64 image).
//   sed_vram_active : the driver's `m_sed_vram_active` gate (true once a genuine
//                     SED1335 write has occurred).
//
// Returns exactly `bridge::payload_size(MONO1, 160, 64)` == 1280 bytes. Every
// bit is read directly from `sed_vram` (MSB = leftmost pixel, 20-byte row
// stride) — no font ROM, no control registers, no invented content. When
// `sed_vram_active` is false and the VRAM is all zero, returns an all-zero
// (all pixels off) payload.
std::vector<uint8_t> lcd_rasterize(const uint8_t* sed_vram,
                                   std::size_t vram_len,
                                   bool sed_vram_active);

} // namespace s760
