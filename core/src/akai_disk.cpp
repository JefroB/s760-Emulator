#include "s760/akai_disk.hpp"
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

    inline size_t safe_align_2048(size_t n) {
        if (n > SIZE_MAX - 2047) return SIZE_MAX;
        return (n + 2047) & ~size_t(2047);
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

AkaiS1000Disk::AkaiS1000Disk(std::string volume_name) {
    set_volume_name(volume_name);
}

void AkaiS1000Disk::set_volume_name(const std::string& name) {
    m_volume_name = name.substr(0, 12);
    while (m_volume_name.size() < 12) {
        m_volume_name.push_back(' ');
    }
}

const std::string& AkaiS1000Disk::get_volume_name() const {
    return m_volume_name;
}

void AkaiS1000Disk::add_program(uint16_t prog_num, const std::string& prog_name,
                                uint8_t midi_channel, uint8_t keygroup_count) {
    AkaiProgram p;
    p.num = prog_num;
    p.name = prog_name.substr(0, 12);
    while (p.name.size() < 12) p.name.push_back(' ');
    p.midi_channel = midi_channel;
    p.keygroups = keygroup_count;
    m_programs.push_back(p);
}

void AkaiS1000Disk::add_sample(const std::string& sample_name, uint32_t sample_rate,
                               const std::vector<uint8_t>& pcm_data,
                               uint32_t loop_start, uint32_t loop_end,
                               uint8_t root_key) {
    AkaiSample s;
    s.name = sample_name.substr(0, 12);
    while (s.name.size() < 12) s.name.push_back(' ');
    s.sample_rate = sample_rate;
    s.data = pcm_data;
    s.loop_start = loop_start;
    s.loop_end = (loop_end == 0) ? static_cast<uint32_t>(pcm_data.size() / 2) : loop_end;
    s.root_key = root_key;
    m_samples.push_back(s);
}

std::vector<uint8_t> AkaiS1000Disk::build_iso(size_t total_mb) const {
    if (total_mb == 0 || total_mb > 2048) {
        throw std::invalid_argument("Invalid ISO total size in MB (must be 1..2048 MB)");
    }
    size_t total_bytes = total_mb * 1024 * 1024;
    std::vector<uint8_t> img(total_bytes, 0);

    // Block 0: Akai S1000 Header
    const char magic[] = "AKAI S1000 CD-ROM VOL";
    size_t magic_len = sizeof(magic) - 1;
    if (magic_len <= img.size()) {
        std::memcpy(&img[0], magic, magic_len);
    }
    if (img.size() >= 0x2C) {
        copy_string_padded(reinterpret_cast<char*>(&img[0x20]), 12, m_volume_name);
    }

    uint32_t num_progs = static_cast<uint32_t>(m_programs.size());
    uint32_t num_samps = static_cast<uint32_t>(m_samples.size());
    if (img.size() >= 0x38) {
        write_le32(&img[0x30], num_progs);
        write_le32(&img[0x34], num_samps);
    }

    // Block 1: Program Directory (150-byte records)
    size_t offset = CD_BLOCK_SIZE;
    for (const auto& p : m_programs) {
        if (!range_fits(offset, 150, img.size())) break;
        std::vector<uint8_t> p_rec(150, 0);
        write_le16(&p_rec[0], p.num);
        copy_string_padded(reinterpret_cast<char*>(&p_rec[2]), 12, p.name);
        p_rec[0x0E] = p.midi_channel;
        p_rec[0x0F] = p.keygroups;

        std::memcpy(&img[offset], p_rec.data(), 150);
        offset += 150;
    }

    // Sample Directory & Waveform Blocks (starting at block 4)
    offset = 4 * CD_BLOCK_SIZE;
    for (const auto& s : m_samples) {
        if (!range_fits(offset, 150, img.size())) break;
        std::vector<uint8_t> s_hdr(150, 0);
        copy_string_padded(reinterpret_cast<char*>(&s_hdr[0]), 12, s.name);
        write_le32(&s_hdr[0x0C], s.sample_rate);
        write_le32(&s_hdr[0x10], s.loop_start);
        write_le32(&s_hdr[0x14], s.loop_end);
        s_hdr[0x18] = s.root_key;
        uint32_t slen = static_cast<uint32_t>(s.data.size());
        write_le32(&s_hdr[0x1A], slen);

        std::memcpy(&img[offset], s_hdr.data(), 150);
        offset += 150;

        if (range_fits(offset, slen, img.size())) {
            std::memcpy(&img[offset], s.data.data(), slen);
        }
        offset += safe_align_2048(slen);
    }

    return img;
}

AkaiDiskInfo AkaiS1000Disk::parse(const uint8_t* data, size_t size) {
    if (!data || size < 1024) {
        throw std::invalid_argument("Akai image too small or null");
    }

    AkaiDiskInfo info;
    std::string banner(reinterpret_cast<const char*>(data), std::min(size, size_t(64)));
    info.is_akai = (banner.find("AKAI") != std::string::npos) || (banner.find("S1000") != std::string::npos);

    if (size >= 0x2C) {
        info.volume_name = string_from_padded(reinterpret_cast<const char*>(data + 0x20), 12);
    }
    if (size >= 0x38) {
        info.num_programs = read_le32(data + 0x30);
        info.num_samples = read_le32(data + 0x34);
    }

    // Programs
    size_t offset = CD_BLOCK_SIZE;
    uint32_t prog_limit = std::min(info.num_programs, uint32_t(32));
    for (uint32_t i = 0; i < prog_limit; ++i) {
        if (!range_fits(offset, 150, size)) break;
        AkaiProgram p;
        p.num = read_le16(data + offset);
        p.name = string_from_padded(reinterpret_cast<const char*>(data + offset + 2), 12);
        p.midi_channel = data[offset + 0x0E];
        p.keygroups = data[offset + 0x0F];
        info.programs.push_back(p);
        offset += 150;
    }

    // Samples
    offset = 4 * CD_BLOCK_SIZE;
    uint32_t sample_limit = std::min(info.num_samples, uint32_t(32));
    for (uint32_t i = 0; i < sample_limit; ++i) {
        if (!range_fits(offset, 150, size)) break;
        AkaiSample s;
        s.name = string_from_padded(reinterpret_cast<const char*>(data + offset), 12);
        s.sample_rate = read_le32(data + offset + 0x0C);
        s.loop_start = read_le32(data + offset + 0x10);
        s.loop_end = read_le32(data + offset + 0x14);
        s.root_key = data[offset + 0x18];
        uint32_t slen = read_le32(data + offset + 0x1A);

        offset += 150;

        if (slen > 0 && (slen % 2 == 0) && range_fits(offset, slen, size)) {
            s.data.assign(data + offset, data + offset + slen);
            info.samples.push_back(s);
        }
        offset += safe_align_2048(slen);
    }

    return info;
}

AkaiS1000Disk AkaiS1000Disk::from_iso(const uint8_t* data, size_t size) {
    AkaiDiskInfo info = parse(data, size);
    AkaiS1000Disk disk(info.volume_name);
    for (const auto& p : info.programs) {
        disk.add_program(p.num, p.name, p.midi_channel, p.keygroups);
    }
    for (const auto& s : info.samples) {
        disk.add_sample(s.name, s.sample_rate, s.data, s.loop_start, s.loop_end, s.root_key);
    }
    return disk;
}

RolandS760Disk S760AkaiConverter::convert(const AkaiS1000Disk& akai_disk, const std::string& target_volume_name) {
    RolandS760Disk r_disk(target_volume_name);

    for (const auto& p : akai_disk.get_programs()) {
        std::vector<uint16_t> partials = {1, 2};
        r_disk.add_patch(p.num, p.name, partials, 127, 0);
    }

    uint16_t sid = 1;
    for (const auto& s : akai_disk.get_samples()) {
        r_disk.add_sample(sid++, s.name, s.sample_rate, s.data, s.loop_start, s.loop_end, s.root_key);
    }

    return r_disk;
}

} // namespace s760
