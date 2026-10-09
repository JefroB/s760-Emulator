// s760_crt_normalize.cpp
// ----------------------
// Implementation of the pure CRT 640x240 -> 640x480 line-doubling transform.
// See s760_crt_normalize.hpp for the contract and spec references
// (.kiro/specs/mame-live-backend/, Property 4, Requirement 4.4).

#include "s760/s760_crt_normalize.hpp"

#include <cstring>

namespace s760 {

std::vector<uint8_t> crt_line_double(const uint8_t* src,
                                     std::size_t src_len,
                                     uint16_t src_w,
                                     uint16_t src_h) {
    // Output geometry is the source width by twice the source height (2x
    // vertical line-doubling). The output payload length is exactly the
    // protocol's RGBA8888 payload size for that geometry.
    const uint16_t out_w = src_w;
    const uint16_t out_h = static_cast<uint16_t>(src_h * 2u);

    const std::size_t out_size =
        bridge::payload_size(bridge::PixelFormat::RGBA8888, out_w, out_h);

    // Start fully zeroed so any rows we cannot source stay authentic-blank
    // (no fabricated pixels) and the length is guaranteed exact.
    std::vector<uint8_t> out(out_size, 0u);

    // Bytes per source/output row (RGBA8888 => 4 bytes per pixel).
    const std::size_t row_bytes = static_cast<std::size_t>(src_w) * 4u;
    if (src == nullptr || row_bytes == 0u) {
        return out; // nothing genuine to copy; authentic-blank of exact size
    }

    // Only copy rows that are fully present in the provided source buffer, so
    // we never read past src_len (no fabricated or out-of-bounds bytes).
    const std::size_t available_rows =
        (row_bytes == 0u) ? 0u : (src_len / row_bytes);
    const std::size_t rows =
        (available_rows < static_cast<std::size_t>(src_h))
            ? available_rows
            : static_cast<std::size_t>(src_h);

    for (std::size_t r = 0; r < rows; ++r) {
        const uint8_t* src_row = src + r * row_bytes;
        // Source row r is duplicated to output rows 2r and 2r+1. Both are exact
        // byte-for-byte copies of a genuine source row.
        uint8_t* dst_row0 = out.data() + (2u * r) * row_bytes;
        uint8_t* dst_row1 = out.data() + (2u * r + 1u) * row_bytes;
        std::memcpy(dst_row0, src_row, row_bytes);
        std::memcpy(dst_row1, src_row, row_bytes);
    }

    return out;
}

} // namespace s760
