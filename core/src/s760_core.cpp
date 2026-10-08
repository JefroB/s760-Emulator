#include "s760/s760_core.hpp"
#include <cmath>
#include <cstring>
#include <algorithm>

namespace s760 {

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

S760HardwareCore::S760HardwareCore() {
    m_wave_ram.resize(2 * 1024 * 1024, 0); // 4MB default wave RAM
    reset();
}

void S760HardwareCore::reset() {
    m_dsp_addr_latch = 0;
    m_dsp_data_latch = 0;

    for (int v = 0; v < 32; v++) {
        CoreVoice& voice = m_voices[v];
        voice.active = false;
        voice.start_addr = 0;
        voice.length = 44100;
        voice.loop_start = 0;
        voice.loop_end = 44100;
        voice.loop_mode = 0;
        voice.pos = 0.0;
        voice.step = 1.0;
        voice.volume = 1.0f;
        voice.pan_l = 1.0f;
        voice.pan_r = 1.0f;
        voice.env_level = 0.0f;
        voice.env_attack = 0.005f;
        voice.env_decay = 0.0002f;
        voice.env_sustain = 0.75f;
        voice.env_release = 0.001f;
        voice.env_stage = 0;
        voice.tvf_cutoff = 127;
        voice.tvf_resonance = 0;
        voice.tvf_mode = 0; // LPF
        voice.tvf_s1 = voice.tvf_s2 = voice.tvf_s3 = voice.tvf_s4 = 0.0;
        voice.tva_level = 127;
        voice.tva_pan = 0;
        voice.out_bus = 0;
    }
}

void S760HardwareCore::write_mmio_addr(uint8_t data) {
    m_dsp_addr_latch = data;
}

void S760HardwareCore::write_mmio_data(uint8_t data) {
    m_dsp_data_latch = data;
    uint8_t voice_idx = m_dsp_addr_latch & 0x1F;
    uint8_t reg_idx = (m_dsp_addr_latch >> 5) & 0x07;

    if (voice_idx >= 32) return;
    CoreVoice& voice = m_voices[voice_idx];

    switch (reg_idx) {
        case 0x00: // PITCH_STEP_L
            voice.step = (double)data / 128.0;
            if (voice.step <= 0.0) voice.step = 1.0;
            break;
        case 0x01: // PITCH_STEP_H
            voice.step = (double)(data + 1);
            break;
        case 0x02: // WAVE_START_ADDR
            voice.start_addr = (uint32_t)data * 4096;
            break;
        case 0x03: // WAVE_LOOP_START
            voice.loop_start = (uint32_t)data * 256;
            break;
        case 0x04: // WAVE_LOOP_END
            voice.loop_end = (uint32_t)data * 256;
            break;
        case 0x05: // VOICE_CTRL
            voice.active = (data & 0x01) != 0;
            voice.loop_mode = (data & 0x02) ? 1 : 0;
            voice.out_bus = (data >> 4) & 0x0F;
            if (voice.active) {
                voice.pos = 0.0;
                voice.env_level = 1.0f;
                voice.env_stage = 1;
                voice.tvf_s1 = voice.tvf_s2 = voice.tvf_s3 = voice.tvf_s4 = 0.0;
            }
            break;
        case 0x06: // TVF_CTRL
            voice.tvf_cutoff = data & 0x7F;
            voice.tvf_resonance = (data & 0x80) ? 64 : 0;
            break;
        case 0x07: // TVA_CTRL
            voice.tva_level = data & 0x7F;
            voice.volume = (float)voice.tva_level / 127.0f;
            break;
    }
}

uint8_t S760HardwareCore::read_mmio_data() const {
    uint8_t voice_idx = m_dsp_addr_latch & 0x1F;
    uint8_t reg_idx = (m_dsp_addr_latch >> 5) & 0x07;
    if (voice_idx >= 32) return 0;
    const CoreVoice& voice = m_voices[voice_idx];

    switch (reg_idx) {
        case 0x00: return (uint8_t)(voice.step * 128.0);
        case 0x05: return voice.active ? 0x01 : 0x00;
        case 0x06: return voice.tvf_cutoff;
        case 0x07: return voice.tva_level;
        default: return 0;
    }
}

void S760HardwareCore::note_on(int v, uint32_t wave_addr, uint32_t length,
                               uint32_t loop_s, uint32_t loop_e, uint8_t loop_m,
                               double sample_rate, int note, int root_key,
                               float vel, float pan) {
    if (v < 0 || v >= 32) return;

    CoreVoice& voice = m_voices[v];
    voice.start_addr = wave_addr;
    voice.length = length;
    voice.loop_start = loop_s;
    voice.loop_end = (loop_e > 0) ? loop_e : length;
    voice.loop_mode = loop_m;
    voice.pos = 0.0;
    voice.step = (sample_rate / 44100.0) * std::pow(2.0, (note - root_key) / 12.0);
    voice.volume = std::clamp(vel, 0.0f, 1.0f);
    voice.pan_l = std::clamp(1.0f - pan, 0.0f, 1.0f);
    voice.pan_r = std::clamp(1.0f + pan, 0.0f, 1.0f);
    voice.env_level = 0.0f;
    voice.env_attack = 0.005f;
    voice.env_decay = 0.0002f;
    voice.env_sustain = 0.75f;
    voice.env_release = 0.001f;
    voice.env_stage = 1;
    voice.tvf_s1 = voice.tvf_s2 = voice.tvf_s3 = voice.tvf_s4 = 0.0;
    voice.active = true;
}

void S760HardwareCore::note_off(int v) {
    if (v >= 0 && v < 32 && m_voices[v].active) {
        m_voices[v].env_stage = 4;
    }
}

double S760HardwareCore::cutoff_to_hz(uint8_t cutoff) {
    double fc = 20.0 * std::pow(10.0, (double)cutoff * 3.0 / 127.0);
    return std::clamp(fc, 20.0, 20000.0);
}

float S760HardwareCore::hermite_interpolate(float y0, float y1, float y2, float y3, float frac) {
    float c0 = y1;
    float c1 = 0.5f * (y2 - y0);
    float c2 = y0 - 2.5f * y1 + 2.0f * y2 - 0.5f * y3;
    float c3 = 0.5f * (y3 - y0) + 1.5f * (y1 - y2);
    return ((c3 * frac + c2) * frac + c1) * frac + c0;
}

void S760HardwareCore::render_audio(float* left_out, float* right_out, size_t num_frames, double sample_rate) {
    std::fill(left_out, left_out + num_frames, 0.0f);
    std::fill(right_out, right_out + num_frames, 0.0f);

    for (int v = 0; v < 32; v++) {
        CoreVoice& voice = m_voices[v];
        if (!voice.active) continue;

        for (size_t i = 0; i < num_frames; i++) {
            // Envelope generation
            if (voice.env_stage == 1) {
                voice.env_level += voice.env_attack;
                if (voice.env_level >= 1.0f) {
                    voice.env_level = 1.0f;
                    voice.env_stage = 2;
                }
            } else if (voice.env_stage == 2) {
                voice.env_level -= voice.env_decay;
                if (voice.env_level <= voice.env_sustain) {
                    voice.env_level = voice.env_sustain;
                    voice.env_stage = 3;
                }
            } else if (voice.env_stage == 4) {
                voice.env_level -= voice.env_release;
                if (voice.env_level <= 0.0f) {
                    voice.env_level = 0.0f;
                    voice.active = false;
                    break;
                }
            }

            uint32_t idx = voice.start_addr + (uint32_t)voice.pos;
            float frac = (float)(voice.pos - (uint32_t)voice.pos);

            // 4-Point Hermite Cubic Interpolation
            float s = 0.0f;
            if (idx >= 1 && idx + 2 < m_wave_ram.size()) {
                float y0 = (float)m_wave_ram[idx - 1] / 32768.0f;
                float y1 = (float)m_wave_ram[idx] / 32768.0f;
                float y2 = (float)m_wave_ram[idx + 1] / 32768.0f;
                float y3 = (float)m_wave_ram[idx + 2] / 32768.0f;
                s = hermite_interpolate(y0, y1, y2, y3, frac);
            } else if (idx + 1 < m_wave_ram.size()) {
                float s0 = (float)m_wave_ram[idx] / 32768.0f;
                float s1 = (float)m_wave_ram[idx + 1] / 32768.0f;
                s = s0 + frac * (s1 - s0);
            } else if (idx < m_wave_ram.size()) {
                s = (float)m_wave_ram[idx] / 32768.0f;
            }

            // Fujitsu MB87424 TVF 4-Pole 24dB Resonant Filter
            if (voice.tvf_cutoff < 127 || voice.tvf_resonance > 0) {
                double fc = cutoff_to_hz(voice.tvf_cutoff);
                double w = 2.0 * M_PI * fc / sample_rate;
                double g = std::tan(w * 0.5);
                double k = 3.98 * std::pow((double)voice.tvf_resonance / 127.0, 1.4);

                double g_over_1g = g / (1.0 + g);
                double u = s - k * std::tanh(voice.tvf_s4);

                double v1 = g_over_1g * (u - voice.tvf_s1);
                double y1 = v1 + voice.tvf_s1;
                voice.tvf_s1 = y1 + v1;

                double v2 = g_over_1g * (y1 - voice.tvf_s2);
                double y2 = v2 + voice.tvf_s2;
                voice.tvf_s2 = y2 + v2;

                double v3 = g_over_1g * (y2 - voice.tvf_s3);
                double y3 = v3 + voice.tvf_s3;
                voice.tvf_s3 = y3 + v3;

                double v4 = g_over_1g * (y3 - voice.tvf_s4);
                double y4 = v4 + voice.tvf_s4;
                voice.tvf_s4 = y4 + v4;

                if (voice.tvf_mode == 0) // LPF
                    s = (float)y4;
                else if (voice.tvf_mode == 1) // BPF
                    s = (float)(4.0 * (y2 - y3));
                else if (voice.tvf_mode == 2) // HPF
                    s = (float)(u - 4.0 * y1 + 6.0 * y2 - 4.0 * y3 + y4);
            }

            float gain = s * voice.volume * voice.env_level * 0.35f;
            left_out[i] += gain * voice.pan_l;
            right_out[i] += gain * voice.pan_r;

            voice.pos += voice.step;
            if (voice.loop_mode != 0 && voice.pos >= voice.loop_end) {
                double loop_len = (double)(voice.loop_end - voice.loop_start);
                if (loop_len > 1.0)
                    voice.pos = voice.loop_start + std::fmod(voice.pos - voice.loop_start, loop_len);
                else
                    voice.pos = voice.loop_start;
            } else if (voice.loop_mode == 0 && voice.pos >= voice.length) {
                voice.active = false;
                break;
            }
        }
    }
}

void S760HardwareCore::load_wave_data(const int16_t* pcm_samples, size_t num_samples, size_t dest_offset) {
    if (dest_offset + num_samples > m_wave_ram.size()) {
        m_wave_ram.resize(dest_offset + num_samples);
    }
    std::memcpy(&m_wave_ram[dest_offset], pcm_samples, num_samples * sizeof(int16_t));
}

size_t S760HardwareCore::active_voice_count() const {
    size_t count = 0;
    for (int v = 0; v < 32; v++) {
        if (m_voices[v].active) count++;
    }
    return count;
}

} // namespace s760
