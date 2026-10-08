#pragma once

#include <cstdint>
#include <vector>
#include <string>
#include <cmath>
#include <memory>
#include <algorithm>

namespace s760 {

struct CoreVoice {
    bool active = false;
    uint32_t start_addr = 0;
    uint32_t length = 44100;
    uint32_t loop_start = 0;
    uint32_t loop_end = 44100;
    uint8_t loop_mode = 0; // 0=One-shot, 1=Forward, 2=Alternating
    double pos = 0.0;
    double step = 1.0;
    float volume = 1.0f;
    float pan_l = 1.0f;
    float pan_r = 1.0f;
    float env_level = 0.0f;
    float env_attack = 0.005f;
    float env_decay = 0.0002f;
    float env_sustain = 0.75f;
    float env_release = 0.001f;
    int env_stage = 0; // 0=Idle, 1=Attack, 2=Decay, 3=Sustain, 4=Release

    // Fujitsu MB87424 TVF 4-Pole 24dB Resonant Filter
    uint8_t tvf_cutoff = 127;    // 0..127 (20 Hz - 20 kHz)
    uint8_t tvf_resonance = 0;   // 0..127
    uint8_t tvf_mode = 0;        // 0=LPF, 1=BPF, 2=HPF
    double tvf_s1 = 0.0, tvf_s2 = 0.0, tvf_s3 = 0.0, tvf_s4 = 0.0;

    // TVA & Routing
    uint8_t tva_level = 127;
    int8_t tva_pan = 0;
    uint8_t out_bus = 0; // 0=Stereo, 1..8=Individual Outs
};

class S760HardwareCore {
public:
    S760HardwareCore();
    ~S760HardwareCore() = default;

    void reset();

    // Gate Array MMIO Streaming Protocol (0xF006 Data / 0xF008 Addr)
    void write_mmio_addr(uint8_t data);
    void write_mmio_data(uint8_t data);
    uint8_t read_mmio_data() const;

    // Voice Lifecycle & Direct Triggering
    void note_on(int voice_idx, uint32_t wave_addr, uint32_t length,
                 uint32_t loop_s, uint32_t loop_e, uint8_t loop_m,
                 double sample_rate, int note, int root_key,
                 float vel = 1.0f, float pan = 0.0f);
    void note_off(int voice_idx);

    // Audio Rendering for DAW Plugins & MAME
    void render_audio(float* left_out, float* right_out, size_t num_frames, double sample_rate = 44100.0);

    // Wave RAM Management (Up to 32MB / 16M 16-Bit Words)
    void load_wave_data(const int16_t* pcm_samples, size_t num_samples, size_t dest_offset = 0);
    const std::vector<int16_t>& wave_ram() const { return m_wave_ram; }
    std::vector<int16_t>& wave_ram() { return m_wave_ram; }

    const CoreVoice& get_voice(int idx) const { return m_voices[idx & 31]; }
    size_t active_voice_count() const;

    static double cutoff_to_hz(uint8_t cutoff);
    static float hermite_interpolate(float y0, float y1, float y2, float y3, float frac);

private:
    std::vector<int16_t> m_wave_ram;
    CoreVoice m_voices[32];
    uint8_t m_dsp_addr_latch = 0;
    uint8_t m_dsp_data_latch = 0;
};

} // namespace s760
