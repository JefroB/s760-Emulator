#pragma once

#include "s760/s760_disk.hpp"
#include <cstdint>
#include <string>
#include <vector>

namespace s760 {

struct AkaiProgram {
    uint16_t num = 1;
    std::string name;
    uint8_t midi_channel = 1;
    uint8_t keygroups = 1;
};

struct AkaiSample {
    std::string name;
    uint32_t sample_rate = 44100;
    std::vector<uint8_t> data;
    uint32_t loop_start = 0;
    uint32_t loop_end = 0;
    uint8_t root_key = 60;
};

struct AkaiDiskInfo {
    bool is_akai = false;
    std::string volume_name;
    uint32_t num_programs = 0;
    uint32_t num_samples = 0;
    std::vector<AkaiProgram> programs;
    std::vector<AkaiSample> samples;
};

class AkaiS1000Disk {
public:
    static constexpr size_t SECTOR_SIZE = 1024;
    static constexpr size_t CD_BLOCK_SIZE = 2048;

    explicit AkaiS1000Disk(std::string volume_name = "AKAI S1000 VOL");

    void set_volume_name(const std::string& name);
    const std::string& get_volume_name() const;

    void add_program(uint16_t prog_num, const std::string& prog_name,
                     uint8_t midi_channel = 1, uint8_t keygroup_count = 1);

    void add_sample(const std::string& sample_name, uint32_t sample_rate,
                    const std::vector<uint8_t>& pcm_data,
                    uint32_t loop_start = 0, uint32_t loop_end = 0,
                    uint8_t root_key = 60);

    const std::vector<AkaiProgram>& get_programs() const { return m_programs; }
    const std::vector<AkaiSample>& get_samples() const { return m_samples; }

    std::vector<uint8_t> build_iso(size_t total_mb = 4) const;

    static AkaiDiskInfo parse(const uint8_t* data, size_t size);
    static AkaiS1000Disk from_iso(const uint8_t* data, size_t size);

private:
    std::string m_volume_name;
    std::vector<AkaiProgram> m_programs;
    std::vector<AkaiSample> m_samples;
};

class S760AkaiConverter {
public:
    static RolandS760Disk convert(const AkaiS1000Disk& akai_disk,
                                  const std::string& target_volume_name = "S760 CONVERT");
};

} // namespace s760
