#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include <tuple>

namespace s760 {

struct MSDOSFileInfo {
    bool is_dos = false;
    std::string filename;
    uint32_t file_size = 0;
    bool is_wav = false;
    uint32_t sample_rate = 44100;
    std::vector<uint8_t> pcm_data;
};

struct SDSDumpInfo {
    bool valid_sds = false;
    uint8_t channel = 0;
    uint16_t sample_num = 0;
    uint8_t bits = 16;
    uint32_t sample_rate = 44100;
    uint32_t length = 0;
    uint32_t loop_start = 0;
    uint32_t loop_end = 0;
    uint8_t loop_type = 0;
};

class S760DSPTools {
public:
    static std::vector<uint8_t> crossfade_loop(const std::vector<uint8_t>& pcm_bytes,
                                               size_t loop_start, size_t loop_end,
                                               size_t xfade_samples = 500);

    static std::vector<uint8_t> time_stretch(const std::vector<uint8_t>& pcm_bytes,
                                             double stretch_factor = 1.25,
                                             uint32_t sample_rate = 44100);

    static std::vector<uint8_t> digital_filter(const std::vector<uint8_t>& pcm_bytes,
                                               double cutoff_hz = 1000.0,
                                               uint32_t sample_rate = 44100,
                                               const std::string& filter_type = "lpf");

    static std::vector<uint8_t> sample_rate_convert(const std::vector<uint8_t>& pcm_bytes,
                                                    uint32_t in_rate = 44100,
                                                    uint32_t out_rate = 22050);

    static std::vector<uint8_t> bit_convert(const std::vector<uint8_t>& pcm_bytes,
                                            int target_bits = 8);

    static std::tuple<std::vector<uint8_t>, size_t, size_t> auto_truncate_and_normalize(
        const std::vector<uint8_t>& pcm_bytes,
        double threshold_db = -48.0,
        double peak_target = 0.98);

    static std::vector<uint8_t> wave_edit(const std::vector<uint8_t>& pcm_a,
                                          const std::vector<uint8_t>& pcm_b,
                                          const std::string& operation,
                                          size_t start = 0, size_t length = 0);

    static std::vector<float> render_voice(const std::vector<uint8_t>& pcm_bytes,
                                           uint32_t sample_rate, uint8_t root_key,
                                           uint32_t loop_start, uint32_t loop_end,
                                           uint8_t note = 60,
                                           size_t num_output_samples = 44100,
                                           uint32_t output_rate = 44100);

    // MS-DOS FAT12 Sample Exchange
    static std::vector<uint8_t> build_msdos_sample_floppy(const std::string& wav_filename,
                                                          const std::vector<uint8_t>& pcm_bytes,
                                                          uint32_t sample_rate = 44100);
    static MSDOSFileInfo extract_wav_from_msdos(const std::vector<uint8_t>& disk_bytes);

    // MIDI Sample Dump Standard (SDS)
    static std::vector<uint8_t> build_sds_dump_header(uint16_t sample_num, uint32_t sample_rate,
                                                      uint32_t length, uint32_t loop_start, uint32_t loop_end,
                                                      uint8_t channel = 0);
    static SDSDumpInfo parse_sds_dump_header(const std::vector<uint8_t>& sysex);
};

} // namespace s760
