// =============================================================================
//  s760_lcd_raster.cpp
//
//  Implementation of the pure SED1335 LCD rasterizer (spec `mame-live-backend`,
//  task 3.6). See s760_lcd_raster.hpp for the full VRAM->pixel mapping rationale
//  and the exact layout contract. Every emitted pixel is derived SOLELY from the
//  provided SED1335 VRAM (Requirements 3.1, 3.4); an inactive, all-zero VRAM
//  yields an all-zero (off) payload (Requirement 3.2); the output length is
//  always payload_size(MONO1,160,64) (Requirement 3.5).
// =============================================================================

#include "s760/s760_lcd_raster.hpp"

namespace s760 {

std::vector<uint8_t> lcd_rasterize(const uint8_t* sed_vram,
                                   std::size_t vram_len,
                                   bool sed_vram_active) {
    // Fixed LCD geometry and MONO1 packing (from the canonical protocol).
    constexpr uint16_t    kWidth  = bridge::LCD_WIDTH;   // 160
    constexpr uint16_t    kHeight = bridge::LCD_HEIGHT;  // 64
    constexpr std::size_t kStride =
        static_cast<std::size_t>((kWidth + 7u) / 8u);    // 20 bytes/row
    const std::size_t     kPayload =
        bridge::payload_size(bridge::PixelFormat::MONO1, kWidth, kHeight); // 1280

    // Result is always exactly the MONO1 160x64 payload size, pre-zeroed so the
    // "off" state (bit == 0) is the default for every pixel.
    std::vector<uint8_t> out(kPayload, 0u);

    // Mirror lcd_update's activity gate: the SED1335 is considered to hold
    // genuine data when `m_sed_vram_active` is set, OR when any VRAM byte is
    // non-zero (the driver infers activity by scanning VRAM). When neither
    // holds, emit the defined all-zero (blank) payload (Requirement 3.2).
    bool has_data = sed_vram_active;
    if (!has_data && sed_vram != nullptr) {
        for (std::size_t i = 0; i < vram_len; ++i) {
            if (sed_vram[i] != 0u) {
                has_data = true;
                break;
            }
        }
    }

    if (!has_data || sed_vram == nullptr) {
        return out; // all-zero (every pixel off)
    }

    // Direct 1:1 copy of the SED1335 1-bit graphics plane into the MONO1
    // payload. The two bit layouts are identical: byte (y*20 + col) packs 8
    // horizontal pixels, MSB = leftmost. We therefore copy VRAM byte-for-byte
    // into the output, clamped to whatever VRAM bytes are actually readable
    // (missing bytes stay 0 = off, never fabricated).
    //
    //   out[y*20 + col] = sed_vram[y*20 + col]  (bit b of that byte is the
    //   pixel at x = col*8 + (7 - b); b7 = leftmost).
    const std::size_t copy_len = (vram_len < kPayload) ? vram_len : kPayload;
    for (std::size_t i = 0; i < copy_len; ++i) {
        out[i] = sed_vram[i];
    }

    (void)kStride; // documented stride; indexing above is contiguous row-major.
    return out;
}

} // namespace s760
