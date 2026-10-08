#include "s760/s760_disk.hpp"
#include <cstring>
#include <algorithm>
#include <stdexcept>
#include <cstdint>

namespace s760 {

namespace {
    inline uint16_t read_le16(const uint8_t* p) {
        return static_cast<uint16_t>(p[0]) | (static_cast<uint16_t>(p[1]) << 8);
    }

    inline uint32_t read_le32(const uint8_t* p) {
        return static_cast<uint32_t>(p[0]) |
               (static_cast<uint32_t>(p[1]) << 8) |
               (static_cast<uint32_t>(p[2]) << 16) |
               (static_cast<uint32_t>(p[3]) << 24);
    }

    inline void write_le16(uint8_t* p, uint16_t v) {
        p[0] = static_cast<uint8_t>(v & 0xFF);
        p[1] = static_cast<uint8_t>((v >> 8) & 0xFF);
    }

    inline void write_le32(uint8_t* p, uint32_t v) {
        p[0] = static_cast<uint8_t>(v & 0xFF);
        p[1] = static_cast<uint8_t>((v >> 8) & 0xFF);
        p[2] = static_cast<uint8_t>((v >> 16) & 0xFF);
        p[3] = static_cast<uint8_t>((v >> 24) & 0xFF);
    }

    inline bool range_fits(size_t offset, size_t length, size_t total_size) {
        return (length <= total_size) && (offset <= total_size - length);
    }

    inline size_t safe_align_512(size_t n) {
        if (n > SIZE_MAX - 511) return SIZE_MAX;
        return (n + 511) & ~size_t(511);
    }

    void copy_string_padded(char* dest, size_t dest_len, const std::string& src) {
        std::memset(dest, ' ', dest_len);
        size_t to_copy = std::min(dest_len, src.size());
        std::memcpy(dest, src.data(), to_copy);
    }

    std::string string_from_padded(const char* src, size_t len) {
        std::string s(src, len);
        size_t last = s.find_last_not_of(" \t\r\n\0");
        if (last == std::string::npos) return "";
        return s.substr(0, last + 1);
    }
}

RolandS760Disk::RolandS760Disk(std::string volume_name) {
    set_volume_name(volume_name);
}

void RolandS760Disk::set_volume_name(const std::string& name) {
    m_volume_name = name.substr(0, 16);
    while (m_volume_name.size() < 16) {
        m_volume_name.push_back(' ');
    }
}

const std::string& RolandS760Disk::get_volume_name() const {
    return m_volume_name;
}

void RolandS760Disk::add_patch(uint16_t patch_id, const std::string& patch_name, 
                               const std::vector<uint16_t>& partial_ids, 
                               uint8_t level, int8_t pan) {
    Patch p;
    p.id = patch_id;
    p.name = patch_name.substr(0, 16);
    while (p.name.size() < 16) p.name.push_back(' ');
    p.level = level;
    p.pan = pan;
    p.partials = partial_ids;
    if (p.partials.empty()) {
        p.partials = {1, 2};
    }
    m_patches.push_back(p);
}

void RolandS760Disk::add_sample(uint16_t sample_id, const std::string& sample_name,
                                uint32_t sample_rate, const std::vector<uint8_t>& pcm_data,
                                uint32_t loop_start, uint32_t loop_end, uint8_t root_key) {
    Sample s;
    s.id = sample_id;
    s.name = sample_name.substr(0, 16);
    while (s.name.size() < 16) s.name.push_back(' ');
    s.sample_rate = sample_rate;
    s.pcm_data = pcm_data;
    s.loop_start = loop_start;
    s.loop_end = (loop_end == 0) ? static_cast<uint32_t>(pcm_data.size() / 2) : loop_end;
    s.root_key = root_key;
    m_samples.push_back(s);
}

std::vector<uint8_t> RolandS760Disk::build_image(size_t size_bytes) const {
    size_t total = (size_bytes > 0) ? size_bytes : FLOPPY_1440_SIZE;
    if (total < 512) {
        throw std::invalid_argument("Requested image size is too small");
    }
    std::vector<uint8_t> img(total, 0);

    // Sector 0: Volume Header
    const char banner[] = "S770 MR25A\0S-760 Disk Ver. 2.24\0Copyright Roland\0";
    size_t banner_len = sizeof(banner) - 1;
    if (banner_len <= img.size()) {
        std::memcpy(&img[0], banner, banner_len);
    }

    if (img.size() >= 0x50) {
        copy_string_padded(reinterpret_cast<char*>(&img[0x40]), 16, m_volume_name);
    }

    uint32_t num_p = static_cast<uint32_t>(m_patches.size());
    uint32_t num_s = static_cast<uint32_t>(m_samples.size());
    if (img.size() >= 0x68) {
        write_le32(&img[0x60], num_p);
        write_le32(&img[0x64], num_s);
    }

    // Sectors 1-35: Allocation Map (0x0F = free)
    for (size_t i = SECTOR_SIZE; i < 36 * SECTOR_SIZE && i < img.size(); ++i) {
        img[i] = 0x0F;
    }

    // Sector 36 (Offset 0x4800): Patch Records (256 bytes each)
    size_t offset = 36 * SECTOR_SIZE;
    for (const auto& p : m_patches) {
        if (!range_fits(offset, 256, img.size())) break;
        std::vector<uint8_t> rec_buf(256, 0);
        write_le16(&rec_buf[0x00], p.id);
        copy_string_padded(reinterpret_cast<char*>(&rec_buf[0x02]), 16, p.name);
        rec_buf[0x12] = p.level;
        rec_buf[0x13] = static_cast<uint8_t>(p.pan);
        for (size_t i = 0; i < 4 && i < p.partials.size(); ++i) {
            write_le16(&rec_buf[0x20 + i * 2], p.partials[i]);
        }
        std::memcpy(&img[offset], rec_buf.data(), 256);
        offset += 256;
    }

    // Offset 0x10000: Sample Records & Waveforms
    offset = 0x10000;
    for (const auto& s : m_samples) {
        if (!range_fits(offset, 256, img.size())) break;
        std::vector<uint8_t> s_buf(256, 0);
        write_le16(&s_buf[0x00], s.id);
        copy_string_padded(reinterpret_cast<char*>(&s_buf[0x02]), 16, s.name);
        write_le32(&s_buf[0x12], s.sample_rate);
        write_le32(&s_buf[0x16], s.loop_start);
        write_le32(&s_buf[0x1A], s.loop_end);
        s_buf[0x1E] = s.root_key;
        uint32_t slen = static_cast<uint32_t>(s.pcm_data.size());
        write_le32(&s_buf[0x20], slen);

        std::memcpy(&img[offset], s_buf.data(), 256);
        offset += 256;

        if (range_fits(offset, slen, img.size())) {
            std::memcpy(&img[offset], s.pcm_data.data(), slen);
        }
        offset += safe_align_512(slen);
    }

    return img;
}

std::vector<uint8_t> RolandS760Disk::build_scsi_image_mb(size_t size_mb) const {
    if (size_mb == 0 || size_mb > 2048) {
        throw std::invalid_argument("Invalid SCSI image size in MB");
    }
    return build_image(size_mb * 1024 * 1024);
}

DiskInfo RolandS760Disk::parse(const uint8_t* data, size_t size) {
    if (!data || size < 512) {
        throw std::invalid_argument("Disk image too small or null");
    }

    DiskInfo info;
    std::string banner(reinterpret_cast<const char*>(data), std::min(size, size_t(32)));
    info.is_roland = (banner.find("S770") != std::string::npos) ||
                     (banner.find("S-760") != std::string::npos) ||
                     (banner.find("S-550") != std::string::npos) ||
                     (banner.find("S-330") != std::string::npos) ||
                     (banner.find("W-30") != std::string::npos) ||
                     (banner.find("Roland") != std::string::npos);

    if (size >= 0x50) {
        info.volume_name = string_from_padded(reinterpret_cast<const char*>(data + 0x40), 16);
    }
    if (size >= 0x68) {
        info.num_patches = read_le32(data + 0x60);
        info.num_samples = read_le32(data + 0x64);
    }

    // Patches
    size_t offset = 36 * SECTOR_SIZE;
    uint32_t patch_limit = std::min(info.num_patches, uint32_t(64));
    for (uint32_t i = 0; i < patch_limit; ++i) {
        if (!range_fits(offset, 256, size)) break;
        Patch p;
        p.id = read_le16(data + offset);
        p.name = string_from_padded(reinterpret_cast<const char*>(data + offset + 2), 16);
        p.level = data[offset + 0x12];
        p.pan = static_cast<int8_t>(data[offset + 0x13]);
        for (int k = 0; k < 4; ++k) {
            p.partials.push_back(read_le16(data + offset + 0x20 + k * 2));
        }
        info.patches.push_back(p);
        offset += 256;
    }

    // Samples
    offset = 0x10000;
    uint32_t sample_limit = std::min(info.num_samples, uint32_t(64));
    for (uint32_t i = 0; i < sample_limit; ++i) {
        if (!range_fits(offset, 256, size)) break;
        Sample s;
        s.id = read_le16(data + offset);
        s.name = string_from_padded(reinterpret_cast<const char*>(data + offset + 2), 16);
        s.sample_rate = read_le32(data + offset + 0x12);
        s.loop_start = read_le32(data + offset + 0x16);
        s.loop_end = read_le32(data + offset + 0x1A);
        s.root_key = data[offset + 0x1E];
        uint32_t slen = read_le32(data + offset + 0x20);

        offset += 256;

        // Strict validation: must have even byte length and fit entirely in image data
        if (slen > 0 && (slen % 2 == 0) && range_fits(offset, slen, size)) {
            s.pcm_data.assign(data + offset, data + offset + slen);
            info.samples.push_back(s);
        }
        offset += safe_align_512(slen);
    }

    return info;
}

RolandS760Disk RolandS760Disk::from_image(const uint8_t* data, size_t size) {
    DiskInfo info = parse(data, size);
    RolandS760Disk disk(info.volume_name);
    for (const auto& p : info.patches) {
        disk.add_patch(p.id, p.name, p.partials, p.level, p.pan);
    }
    for (const auto& s : info.samples) {
        disk.add_sample(s.id, s.name, s.sample_rate, s.pcm_data, s.loop_start, s.loop_end, s.root_key);
    }
    return disk;
}

std::vector<uint8_t> RolandS760Disk::optimize_disk(const uint8_t* data, size_t size) {
    if (!data || size < 512) {
        return (data && size > 0) ? std::vector<uint8_t>(data, data + size) : std::vector<uint8_t>();
    }

    std::vector<uint8_t> out(data, data + size);
    // Clear allocation map sectors 1-35
    for (size_t i = 512; i < 36 * 512 && i < out.size(); ++i) {
        out[i] = 0x0F;
    }

    uint32_t num_patches = 0;
    if (out.size() >= 0x64) {
        num_patches = read_le32(out.data() + 0x60);
    }

    size_t patch_sectors = (num_patches * 256 + 511) / 512;
    for (size_t s = 36; s < 36 + patch_sectors; ++s) {
        if (512 + s < 36 * 512 && 512 + s < out.size()) {
            out[512 + s] = 0x00; // Marked allocated
        }
    }

    return out;
}

} // namespace s760
