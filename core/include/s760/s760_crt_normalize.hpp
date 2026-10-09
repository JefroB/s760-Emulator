#pragma once

// s760_crt_normalize.hpp
// ----------------------
// Pure CRT geometry-normalization transform for the MAME live backend.
//
// The MAME `s760` driver's `crt_screen` rasterizes a 640x240 region
// (set_size(640,240) / set_visarea(0,639,0,239)), while the Bridge protocol
// (s760_bridge_protocol.hpp) advertises the CRT surface as 640x480 RGBA8888.
// This header declares a deterministic 2x vertical line-doubling transform that
// reconciles the two: source row `r` is copied to output rows `2r` and `2r+1`.
//
// Every output pixel is an exact byte-for-byte copy of a genuine source pixel;
// NO pixel content is fabricated or interpolated. The output buffer length is
// exactly bridge::payload_size(RGBA8888, 640, 480) = 640*480*4 bytes.
//
// Byte layout: this operates on RGBA8888 payload bytes (R,G,B,A per pixel) to
// match the Bridge's on-the-wire CRT payload semantics exactly — the Bridge
// treats each 32-bit CRT pixel as four raw bytes (0xAABBGGRR little-endian ==
// R,G,B,A byte order), so a byte-oriented interface aligns with the payload and
// needs no reinterpretation.
//
// This is pure logic with no dependency on the MAME scheduler, so the
// property/unit tests (design Property 4) can exercise it in-process with no
// MAME binary present (Requirement 8.5).
//
// Spec: .kiro/specs/mame-live-backend/ (design "CRT geometry reconciliation",
//       Property 4; Requirement 4.4).

#include "s760/s760_bridge_protocol.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace s760 {

// Line-double a `src_w` x `src_h` RGBA8888 raster up to `src_w` x `2*src_h`,
// returning exactly bridge::payload_size(RGBA8888, src_w, 2*src_h) bytes. With
// the default 640x240 source this yields payload_size(RGBA8888, 640, 480).
//
// Each source row r (RGBA bytes) is copied verbatim into output rows 2r and
// 2r+1, so every output pixel equals a genuine source pixel (no fabrication).
//
// `src`     : pointer to the source RGBA8888 payload (src_w*src_h*4 bytes).
// `src_len` : length in bytes of the source payload the caller is providing.
// `src_w`   : source width in pixels  (default 640).
// `src_h`   : source height in pixels (default 240).
//
// Robustness: the returned buffer is always exactly the target payload size.
// If `src` is null or `src_len` is smaller than the full source payload, only
// the rows fully present in `src` are copied; any remaining output rows are
// left as authentic-blank (all-zero) pixels. No bytes are read past `src_len`.
std::vector<uint8_t> crt_line_double(const uint8_t* src,
                                     std::size_t src_len,
                                     uint16_t src_w = 640,
                                     uint16_t src_h = 240);

} // namespace s760
