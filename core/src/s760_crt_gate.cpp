// =============================================================================
//  s760_crt_gate.cpp
//
//  Implementation of the pure VDP VRAM-activity inference + CRT rasterization
//  gate (spec `mame-live-backend`, task 3.4). See s760_crt_gate.hpp for the
//  contract and the mirrored MAME `crt_update` gate logic.
// =============================================================================

#include "s760/s760_crt_gate.hpp"

#include "s760/s760_bridge_protocol.hpp"

namespace s760 {

bool crt_should_rasterize(bool vdp_vram_active,
                          const uint8_t* vdp_vram,
                          std::size_t vram_len) {
    // Explicit flag wins: a genuine vdp_w VRAM-port write set it true.
    if (vdp_vram_active) {
        return true;
    }

    // Inferred-active scan: exactly the first 2400 bytes (or fewer if the
    // buffer is shorter), matching the MAME driver's crt_update fallback. A
    // null buffer contributes no non-zero bytes.
    if (vdp_vram == nullptr) {
        return false;
    }

    const std::size_t scan = (vram_len < kVdpInferScanBytes)
                                 ? vram_len
                                 : kVdpInferScanBytes;
    for (std::size_t i = 0; i < scan; ++i) {
        if (vdp_vram[i] != 0) {
            return true;
        }
    }
    return false;
}

std::vector<uint8_t> crt_blank() {
    // Authentic-blank CRT: zero-filled RGBA8888 buffer of the protocol's exact
    // CRT payload size (640x480x4). No fabricated pixel content.
    const std::size_t n = bridge::payload_size(
        bridge::PixelFormat::RGBA8888, bridge::CRT_WIDTH, bridge::CRT_HEIGHT);
    return std::vector<uint8_t>(n, 0);
}

} // namespace s760
