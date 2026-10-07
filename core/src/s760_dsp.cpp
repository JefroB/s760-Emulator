#include "s760/s760_dsp.hpp"
#include <cmath>
#include <cstring>
#include <algorithm>

namespace s760 {

namespace {
    inline int16_t clamp16(int32_t val) {
        return static_cast<int16_t>(std::max(-32767, std::min(32767, val)));
    }
    
    inline int16_t clamp16(double val) {
        return static_cast<int16_t>(std::max(-32767.0, std::min(32767.0, val)));
    }

    std::vector<int16_t> unpack_samples(const std::vector<uint8_t>& pcm_bytes) {
        size_t n = pcm_bytes.size() / 2;
        std::vector<int16_t> s(n);
        for (size_t i = 0; i < n; ++i) {
            int16_t val;
            std::memcpy(&val, &pcm_bytes[i * 2], 2);
            s[i] = val;
        }
        return s;
    }

    std::vector<uint8_t> pack_samples(const std::vector<int16_t>& samples) {
        std::vector<uint8_t> out(samples.size() * 2);
        for (size_t i = 0; i < samples.size(); ++i) {
            std::memcpy(&out[i * 2], &samples[i], 2);
        }
        return out;
    }
}

std::vector<uint8_t> S760DSPTools::crossfade_loop(const std::vector<uint8_t>& pcm_bytes,
                                                  size_t loop_start, size_t loop_end,
                                                  size_t xfade_samples) {
    auto samples = unpack_samples(pcm_bytes);
    if (samples.empty() || loop_end <= loop_start || loop_end > samples.size()) {
        return pcm_bytes;
    }

    size_t max_xfade = std::min({
        xfade_samples,
        (loop_end - loop_start) / 3,
        loop_start,
        samples.size() - loop_end
    });

    if (max_xfade == 0) {
        return pcm_bytes;
    }

    auto out = samples;
    for (size_t i = 0; i < max_xfade; ++i) {
        double w_out = static_cast<double>(i) / static_cast<double>(max_xfade);
        double w_in = 1.0 - w_out;

        int16_t src_tail = samples[loop_end - max_xfade + i];
        int16_t src_head = samples[loop_start + i];
        int32_t blended = static_cast<int32_t>(w_in * src_tail + w_out * src_head);
        out[loop_end - max_xfade + i] = clamp16(blended);
    }

    return pack_samples(out);
}

std::vector<uint8_t> S760DSPTools::time_stretch(const std::vector<uint8_t>& pcm_bytes,
                                               double stretch_factor,
                                               uint32_t sample_rate) {
    auto samples = unpack_samples(pcm_bytes);
    if (stretch_factor <= 0.0 || samples.size() < 100) {
        return pcm_bytes;
    }

    size_t win_size = static_cast<size_t>(sample_rate * 0.030); // 30ms window
    if (win_size == 0) win_size = 1;
    size_t hop_in = win_size / 2;
    if (hop_in == 0) hop_in = 1;
    size_t hop_out = static_cast<size_t>(hop_in * stretch_factor);
    if (hop_out == 0) hop_out = 1;

    size_t out_len = static_cast<size_t>(samples.size() * stretch_factor);
    std::vector<double> out(out_len + win_size, 0.0);
    std::vector<double> norm(out_len + win_size, 0.0);

    const double PI = 3.14159265358979323846;
    std::vector<double> hann(win_size);
    for (size_t i = 0; i < win_size; ++i) {
        hann[i] = 0.5 * (1.0 - std::cos(2.0 * PI * i / static_cast<double>(win_size)));
    }

    size_t in_pos = 0;
    size_t out_pos = 0;
    while (in_pos + win_size <= samples.size() && out_pos + win_size <= out.size()) {
        for (size_t i = 0; i < win_size; ++i) {
            double w = hann[i];
            out[out_pos + i] += samples[in_pos + i] * w;
            norm[out_pos + i] += w;
        }
        in_pos += hop_in;
        out_pos += hop_out;
    }

    std::vector<int16_t> result(out_len);
    for (size_t i = 0; i < out_len; ++i) {
        double val = (norm[i] > 1e-4) ? (out[i] / (norm[i] + 1e-6)) : out[i];
        result[i] = clamp16(val);
    }

    return pack_samples(result);
}

std::vector<uint8_t> S760DSPTools::digital_filter(const std::vector<uint8_t>& pcm_bytes,
                                                 double cutoff_hz,
                                                 uint32_t sample_rate,
                                                 const std::string& filter_type) {
    auto samples = unpack_samples(pcm_bytes);
    if (samples.empty() || sample_rate == 0) return pcm_bytes;

    const double PI = 3.14159265358979323846;
    double omega = 2.0 * PI * cutoff_hz / static_cast<double>(sample_rate);
    double sn = std::sin(omega);
    double cs = std::cos(omega);
    double alpha = sn / (2.0 * 0.7071); // Q = 0.7071

    double b0 = 0.0, b1 = 0.0, b2 = 0.0;
    double a0 = 1.0 + alpha;
    double a1 = -2.0 * cs;
    double a2 = 1.0 - alpha;

    if (filter_type == "hpf" || filter_type == "HPF") {
        b0 = (1.0 + cs) / 2.0;
        b1 = -(1.0 + cs);
        b2 = (1.0 + cs) / 2.0;
    } else { // LPF
        b0 = (1.0 - cs) / 2.0;
        b1 = 1.0 - cs;
        b2 = (1.0 - cs) / 2.0;
    }

    b0 /= a0; b1 /= a0; b2 /= a0;
    a1 /= a0; a2 /= a0;

    std::vector<int16_t> out(samples.size());
    double x1 = 0.0, x2 = 0.0, y1 = 0.0, y2 = 0.0;

    for (size_t i = 0; i < samples.size(); ++i) {
        double x0 = static_cast<double>(samples[i]);
        double y0 = b0 * x0 + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2;
        x2 = x1; x1 = x0;
        y2 = y1; y1 = y0;
        out[i] = clamp16(y0);
    }

    return pack_samples(out);
}

std::vector<uint8_t> S760DSPTools::sample_rate_convert(const std::vector<uint8_t>& pcm_bytes,
                                                      uint32_t in_rate,
                                                      uint32_t out_rate) {
    auto samples = unpack_samples(pcm_bytes);
    if (samples.empty() || out_rate == 0 || in_rate == 0) return pcm_bytes;

    double ratio = static_cast<double>(in_rate) / static_cast<double>(out_rate);
    size_t num_out = static_cast<size_t>(samples.size() / ratio);

    std::vector<int16_t> out(num_out);
    for (size_t i = 0; i < num_out; ++i) {
        double src_pos = i * ratio;
        size_t idx = static_cast<size_t>(src_pos);
        double frac = src_pos - idx;

        if (idx + 1 < samples.size()) {
            double s0 = samples[idx];
            double s1 = samples[idx + 1];
            out[i] = clamp16(static_cast<int32_t>(s0 + frac * (s1 - s0)));
        } else if (idx < samples.size()) {
            out[i] = samples[idx];
        } else {
            out[i] = 0;
        }
    }

    return pack_samples(out);
}

std::vector<uint8_t> S760DSPTools::bit_convert(const std::vector<uint8_t>& pcm_bytes,
                                              int target_bits) {
    auto samples = unpack_samples(pcm_bytes);
    if (samples.empty() || target_bits <= 0 || target_bits >= 16) return pcm_bytes;

    int shift = 16 - target_bits;
    std::vector<int16_t> out(samples.size());
    for (size_t i = 0; i < samples.size(); ++i) {
        int32_t q = (samples[i] >> shift) << shift;
        out[i] = clamp16(q);
    }

    return pack_samples(out);
}

std::tuple<std::vector<uint8_t>, size_t, size_t> S760DSPTools::auto_truncate_and_normalize(
    const std::vector<uint8_t>& pcm_bytes,
    double threshold_db,
    double peak_target) {
    auto samples = unpack_samples(pcm_bytes);
    if (samples.empty()) {
        return {pcm_bytes, 0, 0};
    }

    double threshold_amp = 32768.0 * std::pow(10.0, threshold_db / 20.0);

    size_t start_idx = 0;
    for (size_t i = 0; i < samples.size(); ++i) {
        if (std::abs(samples[i]) >= threshold_amp) {
            start_idx = i;
            break;
        }
    }

    size_t end_idx = samples.size();
    for (size_t i = samples.size(); i > 0; --i) {
        if (std::abs(samples[i - 1]) >= threshold_amp) {
            end_idx = i;
            break;
        }
    }

    if (start_idx >= end_idx) {
        start_idx = 0;
        end_idx = samples.size();
    }

    std::vector<int16_t> trimmed(samples.begin() + start_idx, samples.begin() + end_idx);

    int32_t peak = 1;
    for (int16_t s : trimmed) {
        if (std::abs(s) > peak) peak = std::abs(s);
    }

    double gain = (32767.0 * peak_target) / static_cast<double>(peak);
    std::vector<int16_t> out(trimmed.size());
    for (size_t i = 0; i < trimmed.size(); ++i) {
        out[i] = clamp16(static_cast<int32_t>(trimmed[i] * gain));
    }

    return {pack_samples(out), start_idx, end_idx};
}

std::vector<uint8_t> S760DSPTools::wave_edit(const std::vector<uint8_t>& pcm_a,
                                            const std::vector<uint8_t>& pcm_b,
                                            const std::string& operation,
                                            size_t start, size_t length) {
    auto sa = unpack_samples(pcm_a);
    auto sb = unpack_samples(pcm_b);

    std::vector<int16_t> out_s;
    if (operation == "cut") {
        size_t end = std::min(start + length, sa.size());
        if (start < sa.size()) {
            out_s.insert(out_s.end(), sa.begin(), sa.begin() + start);
            out_s.insert(out_s.end(), sa.begin() + end, sa.end());
        } else {
            out_s = sa;
        }
    } else if (operation == "erase") {
        out_s = sa;
        size_t end = std::min(start + length, out_s.size());
        for (size_t i = start; i < end; ++i) {
            out_s[i] = 0;
        }
    } else if (operation == "splice") {
        size_t split = std::min(start, sa.size());
        out_s.insert(out_s.end(), sa.begin(), sa.begin() + split);
        out_s.insert(out_s.end(), sb.begin(), sb.end());
        out_s.insert(out_s.end(), sa.begin() + split, sa.end());
    } else if (operation == "mix") {
        size_t max_len = std::max(sa.size(), sb.size());
        out_s.resize(max_len, 0);
        for (size_t i = 0; i < max_len; ++i) {
            int32_t va = (i < sa.size()) ? sa[i] : 0;
            int32_t vb = (i < sb.size()) ? sb[i] : 0;
            out_s[i] = clamp16(static_cast<int32_t>((va + vb) * 0.5));
        }
    } else {
        out_s = sa;
    }

    return pack_samples(out_s);
}

std::vector<float> S760DSPTools::render_voice(const std::vector<uint8_t>& pcm_bytes,
                                             uint32_t sample_rate, uint8_t root_key,
                                             uint32_t loop_start, uint32_t loop_end,
                                             uint8_t note,
                                             size_t num_output_samples,
                                             uint32_t output_rate) {
    auto raw_samples = unpack_samples(pcm_bytes);
    if (raw_samples.empty() || output_rate == 0) {
        return std::vector<float>(num_output_samples, 0.0f);
    }

    if (loop_end == 0 || loop_end > raw_samples.size()) {
        loop_end = static_cast<uint32_t>(raw_samples.size());
    }
    bool loop_mode = (loop_end > loop_start && loop_end <= raw_samples.size());

    double step = (static_cast<double>(sample_rate) / static_cast<double>(output_rate)) *
                  std::pow(2.0, (static_cast<int>(note) - static_cast<int>(root_key)) / 12.0);

    double pos = 0.0;
    std::vector<float> output;
    output.reserve(num_output_samples);

    for (size_t s = 0; s < num_output_samples; ++s) {
        size_t idx = static_cast<size_t>(pos);
        double frac = pos - idx;
        float sample_val = 0.0f;

        if (idx + 1 < raw_samples.size()) {
            double s0 = raw_samples[idx];
            double s1 = raw_samples[idx + 1];
            sample_val = static_cast<float>((s0 + frac * (s1 - s0)) / 32768.0);
        } else if (idx < raw_samples.size()) {
            sample_val = static_cast<float>(raw_samples[idx] / 32768.0);
        }

        output.push_back(sample_val);
        pos += step;

        if (loop_mode && pos >= loop_end) {
            double loop_len = static_cast<double>(loop_end - loop_start);
            if (loop_len > 1.0) {
                pos = loop_start + std::fmod(pos - loop_start, loop_len);
            } else {
                pos = loop_start;
            }
        } else if (!loop_mode && pos >= raw_samples.size()) {
            break;
        }
    }

    while (output.size() < num_output_samples) {
        output.push_back(0.0f);
    }

    return output;
}

std::vector<uint8_t> S760DSPTools::build_msdos_sample_floppy(const std::string& wav_filename,
                                                            const std::vector<uint8_t>& pcm_bytes,
                                                            uint32_t sample_rate) {
    std::vector<uint8_t> disk(1474560, 0);

    // 1. FAT12 Boot Sector
    disk[0] = 0xEB; disk[1] = 0x3C; disk[2] = 0x90;
    std::memcpy(&disk[3], "MSDOS5.0", 8);
    uint16_t sector_size = 512;
    std::memcpy(&disk[11], &sector_size, 2);
    disk[13] = 1; // 1 sector per cluster
    uint16_t reserved_sectors = 1;
    std::memcpy(&disk[14], &reserved_sectors, 2);
    disk[16] = 2; // 2 FATs
    uint16_t root_entries = 224;
    std::memcpy(&disk[17], &root_entries, 2);
    uint16_t total_sectors = 2880;
    std::memcpy(&disk[19], &total_sectors, 2);
    disk[21] = 0xF0; // Media descriptor
    uint16_t sectors_per_fat = 9;
    std::memcpy(&disk[22], &sectors_per_fat, 2);
    uint16_t sectors_per_track = 18;
    std::memcpy(&disk[24], &sectors_per_track, 2);
    uint16_t heads = 2;
    std::memcpy(&disk[26], &heads, 2);
    disk[510] = 0x55; disk[511] = 0xAA;

    // 2. RIFF WAV Payload
    std::vector<uint8_t> wav_hdr(44, 0);
    std::memcpy(&wav_hdr[0], "RIFF", 4);
    uint32_t riff_len = static_cast<uint32_t>(36 + pcm_bytes.size());
    std::memcpy(&wav_hdr[4], &riff_len, 4);
    std::memcpy(&wav_hdr[8], "WAVEfmt ", 8);
    uint32_t fmt_len = 16;
    std::memcpy(&wav_hdr[16], &fmt_len, 4);
    uint16_t audio_fmt = 1; // PCM
    std::memcpy(&wav_hdr[20], &audio_fmt, 2);
    uint16_t num_ch = 1; // Mono
    std::memcpy(&wav_hdr[22], &num_ch, 2);
    std::memcpy(&wav_hdr[24], &sample_rate, 4);
    uint32_t byte_rate = sample_rate * 2;
    std::memcpy(&wav_hdr[28], &byte_rate, 4);
    uint16_t block_align = 2;
    std::memcpy(&wav_hdr[32], &block_align, 2);
    uint16_t bits = 16;
    std::memcpy(&wav_hdr[34], &bits, 2);
    std::memcpy(&wav_hdr[36], "data", 4);
    uint32_t data_len = static_cast<uint32_t>(pcm_bytes.size());
    std::memcpy(&wav_hdr[40], &data_len, 4);

    std::vector<uint8_t> wav_data = wav_hdr;
    wav_data.insert(wav_data.end(), pcm_bytes.begin(), pcm_bytes.end());

    // 3. Root Directory Entry (Sector 19 = offset 0x2600)
    size_t root_offset = 19 * 512;
    std::string base = wav_filename;
    std::string ext = "WAV";
    size_t dot_pos = wav_filename.find_last_of('.');
    if (dot_pos != std::string::npos) {
        base = wav_filename.substr(0, dot_pos);
        ext = wav_filename.substr(dot_pos + 1);
    }
    for (char& c : base) c = static_cast<char>(toupper(c));
    for (char& c : ext) c = static_cast<char>(toupper(c));

    base = base.substr(0, 8);
    while (base.size() < 8) base.push_back(' ');
    ext = ext.substr(0, 3);
    while (ext.size() < 3) ext.push_back(' ');

    std::memcpy(&disk[root_offset], base.data(), 8);
    std::memcpy(&disk[root_offset + 8], ext.data(), 3);
    disk[root_offset + 11] = 0x20; // Archive attribute
    uint16_t start_cluster = 2;
    std::memcpy(&disk[root_offset + 26], &start_cluster, 2);
    uint32_t file_sz = static_cast<uint32_t>(wav_data.size());
    std::memcpy(&disk[root_offset + 28], &file_sz, 4);

    // 4. Cluster 2 Data (Sector 33 = offset 0x4200)
    size_t data_offset = 33 * 512;
    if (data_offset + wav_data.size() <= disk.size()) {
        std::memcpy(&disk[data_offset], wav_data.data(), wav_data.size());
    }

    return disk;
}

MSDOSFileInfo S760DSPTools::extract_wav_from_msdos(const std::vector<uint8_t>& disk_bytes) {
    MSDOSFileInfo info;
    if (disk_bytes.size() < 1474560 || disk_bytes[510] != 0x55 || disk_bytes[511] != 0xAA) {
        return info;
    }

    size_t root_offset = 19 * 512;
    std::string fname(reinterpret_cast<const char*>(&disk_bytes[root_offset]), 8);
    std::string fext(reinterpret_cast<const char*>(&disk_bytes[root_offset + 8]), 3);

    size_t last = fname.find_last_not_of(" \t\r\n\0");
    if (last != std::string::npos) fname = fname.substr(0, last + 1);
    last = fext.find_last_not_of(" \t\r\n\0");
    if (last != std::string::npos) fext = fext.substr(0, last + 1);

    uint16_t start_cluster = 0;
    std::memcpy(&start_cluster, &disk_bytes[root_offset + 26], 2);
    uint32_t file_size = 0;
    std::memcpy(&file_size, &disk_bytes[root_offset + 28], 4);

    size_t data_offset = (33 + (start_cluster - 2)) * 512;
    if (data_offset + file_size > disk_bytes.size()) {
        return info;
    }

    info.is_dos = true;
    info.filename = fname + "." + fext;
    info.file_size = file_size;

    if (file_size >= 44 &&
        std::memcmp(&disk_bytes[data_offset], "RIFF", 4) == 0 &&
        std::memcmp(&disk_bytes[data_offset + 8], "WAVE", 4) == 0) {
        info.is_wav = true;
        std::memcpy(&info.sample_rate, &disk_bytes[data_offset + 24], 4);
        info.pcm_data.assign(&disk_bytes[data_offset + 44], &disk_bytes[data_offset + file_size]);
    }

    return info;
}

std::vector<uint8_t> S760DSPTools::build_sds_dump_header(uint16_t sample_num, uint32_t sample_rate,
                                                        uint32_t length, uint32_t loop_start, uint32_t loop_end,
                                                        uint8_t channel) {
    uint32_t period_ns = (sample_rate > 0) ? static_cast<uint32_t>(1e9 / static_cast<double>(sample_rate)) : 0;
    
    std::vector<uint8_t> msg = {
        0xF0, 0x7E, static_cast<uint8_t>(channel & 0x7F), 0x01,
        static_cast<uint8_t>(sample_num & 0x7F), static_cast<uint8_t>((sample_num >> 7) & 0x7F),
        16, // 16-bit
        static_cast<uint8_t>(period_ns & 0x7F),
        static_cast<uint8_t>((period_ns >> 7) & 0x7F),
        static_cast<uint8_t>((period_ns >> 14) & 0x7F),
        static_cast<uint8_t>(length & 0x7F),
        static_cast<uint8_t>((length >> 7) & 0x7F),
        static_cast<uint8_t>((length >> 14) & 0x7F),
        static_cast<uint8_t>(loop_start & 0x7F),
        static_cast<uint8_t>((loop_start >> 7) & 0x7F),
        static_cast<uint8_t>((loop_start >> 14) & 0x7F),
        static_cast<uint8_t>(loop_end & 0x7F),
        static_cast<uint8_t>((loop_end >> 7) & 0x7F),
        static_cast<uint8_t>((loop_end >> 14) & 0x7F),
        0x00, // Forward loop
        0xF7
    };
    return msg;
}

SDSDumpInfo S760DSPTools::parse_sds_dump_header(const std::vector<uint8_t>& sysex) {
    SDSDumpInfo info;
    if (sysex.size() < 21 || sysex[0] != 0xF0 || sysex[1] != 0x7E || sysex[3] != 0x01) {
        return info;
    }

    info.valid_sds = true;
    info.channel = sysex[2];
    info.sample_num = sysex[4] | (sysex[5] << 7);
    info.bits = sysex[6];
    uint32_t period_ns = sysex[7] | (sysex[8] << 7) | (sysex[9] << 14);
    info.sample_rate = (period_ns > 0) ? static_cast<uint32_t>(1e9 / period_ns) : 44100;
    info.length = sysex[10] | (sysex[11] << 7) | (sysex[12] << 14);
    info.loop_start = sysex[13] | (sysex[14] << 7) | (sysex[15] << 14);
    info.loop_end = sysex[16] | (sysex[17] << 7) | (sysex[18] << 14);
    info.loop_type = sysex[19];

    return info;
}

} // namespace s760
