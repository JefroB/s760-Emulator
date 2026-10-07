#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>

namespace s760 {

#pragma pack(push, 1)
struct RolandPatchRecord {
    uint16_t id = 0;
    char name[16] = {0};
    uint8_t level = 127;
    int8_t pan = 0;
    uint8_t reserved[12] = {0};
    uint16_t partials[4] = {0, 0, 0, 0};
    uint8_t padding[216] = {0};
};
static_assert(sizeof(RolandPatchRecord) == 256, "RolandPatchRecord must be 256 bytes");

struct RolandSampleRecord {
    uint16_t id = 0;
    char name[16] = {0};
    uint32_t sample_rate = 44100;
    uint32_t loop_start = 0;
    uint32_t loop_end = 0;
    uint8_t root_key = 60;
    uint8_t reserved[1] = {0};
    uint32_t length_bytes = 0;
    uint8_t padding[220] = {0};
};
static_assert(sizeof(RolandSampleRecord) == 256, "RolandSampleRecord must be 256 bytes");
#pragma pack(pop)

struct Patch {
    uint16_t id = 1;
    std::string name;
    uint8_t level = 127;
    int8_t pan = 0;
    std::vector<uint16_t> partials;
};

struct Sample {
    uint16_t id = 1;
    std::string name;
    uint32_t sample_rate = 44100;
    uint32_t loop_start = 0;
    uint32_t loop_end = 0;
    uint8_t root_key = 60;
    std::vector<uint8_t> pcm_data; // 16-bit signed PCM little-endian
};

struct DiskInfo {
    bool is_roland = false;
    std::string volume_name;
    uint32_t num_patches = 0;
    uint32_t num_samples = 0;
    std::vector<Patch> patches;
    std::vector<Sample> samples;
};

class RolandS760Disk {
public:
    static constexpr size_t SECTOR_SIZE = 512;
    static constexpr size_t TOTAL_SECTORS = 2880;
    static constexpr size_t FLOPPY_1440_SIZE = TOTAL_SECTORS * SECTOR_SIZE; // 1,474,560 bytes

    explicit RolandS760Disk(std::string volume_name = "S-760 SOUND");

    void set_volume_name(const std::string& name);
    const std::string& get_volume_name() const;

    void add_patch(uint16_t patch_id, const std::string& patch_name, 
                   const std::vector<uint16_t>& partial_ids = {1, 2}, 
                   uint8_t level = 127, int8_t pan = 0);

    void add_sample(uint16_t sample_id, const std::string& sample_name,
                    uint32_t sample_rate, const std::vector<uint8_t>& pcm_data,
                    uint32_t loop_start = 0, uint32_t loop_end = 0, uint8_t root_key = 60);

    const std::vector<Patch>& get_patches() const { return m_patches; }
    const std::vector<Sample>& get_samples() const { return m_samples; }

    std::vector<uint8_t> build_image(size_t size_bytes = 0) const;
    std::vector<uint8_t> build_scsi_image_mb(size_t size_mb) const;

    static DiskInfo parse(const uint8_t* data, size_t size);
    static RolandS760Disk from_image(const uint8_t* data, size_t size);

    static std::vector<uint8_t> optimize_disk(const uint8_t* data, size_t size);

private:
    std::string m_volume_name;
    std::vector<Patch> m_patches;
    std::vector<Sample> m_samples;
};

} // namespace s760
