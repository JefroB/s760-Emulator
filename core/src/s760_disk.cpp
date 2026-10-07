#include "s760/s760_disk.hpp"
#include <cstring>
#include <algorithm>
#include <stdexcept>

namespace s760 {

namespace {
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
    std::vector<uint8_t> img(total, 0);

    // Sector 0: Volume Header
    const char banner[] = "S770 MR25A\0S-760 Disk Ver. 2.24\0Copyright Roland\0";
    std::memcpy(&img[0], banner, sizeof(banner) - 1);

    copy_string_padded(reinterpret_cast<char*>(&img[0x40]), 16, m_volume_name);

    uint32_t num_p = static_cast<uint32_t>(m_patches.size());
    uint32_t num_s = static_cast<uint32_t>(m_samples.size());
    std::memcpy(&img[0x60], &num_p, 4);
    std::memcpy(&img[0x64], &num_s, 4);

    // Sectors 1-35: Allocation Map (0x0F = free)
    for (size_t i = SECTOR_SIZE; i < 36 * SECTOR_SIZE && i < img.size(); ++i) {
        img[i] = 0x0F;
    }

    // Sector 36 (Offset 0x4800): Patch Records (256 bytes each)
    size_t offset = 36 * SECTOR_SIZE;
    for (const auto& p : m_patches) {
        if (offset + 256 > img.size()) break;
        RolandPatchRecord rec;
        rec.id = p.id;
        copy_string_padded(rec.name, sizeof(rec.name), p.name);
        rec.level = p.level;
        rec.pan = p.pan;
        for (size_t i = 0; i < 4 && i < p.partials.size(); ++i) {
            rec.partials[i] = p.partials[i];
        }
        std::memcpy(&img[offset], &rec, 256);
        offset += 256;
    }

    // Offset 0x10000: Sample Records & Waveforms
    offset = 0x10000;
    for (const auto& s : m_samples) {
        if (offset + 256 > img.size()) break;
        RolandSampleRecord s_hdr;
        s_hdr.id = s.id;
        copy_string_padded(s_hdr.name, sizeof(s_hdr.name), s.name);
        s_hdr.sample_rate = s.sample_rate;
        s_hdr.loop_start = s.loop_start;
        s_hdr.loop_end = s.loop_end;
        s_hdr.root_key = s.root_key;
        s_hdr.length_bytes = static_cast<uint32_t>(s.pcm_data.size());

        std::memcpy(&img[offset], &s_hdr, 256);
        offset += 256;

        size_t slen = s.pcm_data.size();
        if (offset + slen <= img.size()) {
            std::memcpy(&img[offset], s.pcm_data.data(), slen);
        }
        offset += (slen + 511) & ~511; // Align to 512-byte sector
    }

    return img;
}

std::vector<uint8_t> RolandS760Disk::build_scsi_image_mb(size_t size_mb) const {
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
        std::memcpy(&info.num_patches, data + 0x60, 4);
        std::memcpy(&info.num_samples, data + 0x64, 4);
    }

    // Patches
    size_t offset = 36 * SECTOR_SIZE;
    uint32_t patch_limit = std::min(info.num_patches, uint32_t(64));
    for (uint32_t i = 0; i < patch_limit; ++i) {
        if (offset + 256 > size) break;
        const auto* rec = reinterpret_cast<const RolandPatchRecord*>(data + offset);
        Patch p;
        p.id = rec->id;
        p.name = string_from_padded(rec->name, 16);
        p.level = rec->level;
        p.pan = rec->pan;
        for (int k = 0; k < 4; ++k) {
            p.partials.push_back(rec->partials[k]);
        }
        info.patches.push_back(p);
        offset += 256;
    }

    // Samples
    offset = 0x10000;
    uint32_t sample_limit = std::min(info.num_samples, uint32_t(64));
    for (uint32_t i = 0; i < sample_limit; ++i) {
        if (offset + 256 > size) break;
        const auto* s_hdr = reinterpret_cast<const RolandSampleRecord*>(data + offset);
        Sample s;
        s.id = s_hdr->id;
        s.name = string_from_padded(s_hdr->name, 16);
        s.sample_rate = s_hdr->sample_rate;
        s.loop_start = s_hdr->loop_start;
        s.loop_end = s_hdr->loop_end;
        s.root_key = s_hdr->root_key;

        uint32_t slen = s_hdr->length_bytes;
        offset += 256;

        if (offset + slen <= size) {
            s.pcm_data.assign(data + offset, data + offset + slen);
        }
        info.samples.push_back(s);
        offset += (slen + 511) & ~511;
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
        std::memcpy(&num_patches, out.data() + 0x60, 4);
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
