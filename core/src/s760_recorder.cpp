#include "s760/s760_recorder.hpp"

#include <cmath>
#include <algorithm>
#include <cstring>
#include <iostream>

namespace s760 {

S760SampleRecorder::S760SampleRecorder() {
    set_config(RecordingConfig{});
}

void S760SampleRecorder::set_config(const RecordingConfig& config) {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_config = config;
    size_t pre_size = std::max<size_t>(256, config.pre_trigger_samples);
    m_pre_ring_l.assign(pre_size, 0.0f);
    m_pre_ring_r.assign(pre_size, 0.0f);
    m_pre_write_idx = 0;
    m_pre_filled = false;
}

RecordingConfig S760SampleRecorder::get_config() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_config;
}

void S760SampleRecorder::arm() {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_recorded_l.clear();
    m_recorded_r.clear();
    m_pre_write_idx = 0;
    m_pre_filled = false;
    std::fill(m_pre_ring_l.begin(), m_pre_ring_l.end(), 0.0f);
    std::fill(m_pre_ring_r.begin(), m_pre_ring_r.end(), 0.0f);
    m_state.store(RecordState::Armed);
}

void S760SampleRecorder::start_recording() {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_recorded_l.clear();
    m_recorded_r.clear();
    // Copy pre-trigger buffer if available
    if (m_pre_filled) {
        size_t cap = m_pre_ring_l.size();
        m_recorded_l.reserve(cap + 44100);
        m_recorded_r.reserve(cap + 44100);
        for (size_t i = 0; i < cap; ++i) {
            size_t idx = (m_pre_write_idx + i) % cap;
            m_recorded_l.push_back(m_pre_ring_l[idx]);
            m_recorded_r.push_back(m_pre_ring_r[idx]);
        }
    }
    m_state.store(RecordState::Recording);
}

void S760SampleRecorder::stop_recording() {
    if (m_state.load() == RecordState::Recording) {
        finalize_recording(m_config.target_sample_rate);
    } else {
        m_state.store(RecordState::Idle);
    }
}

void S760SampleRecorder::cancel() {
    std::lock_guard<std::mutex> lock(m_mutex);
    m_recorded_l.clear();
    m_recorded_r.clear();
    m_state.store(RecordState::Idle);
}

void S760SampleRecorder::reset() {
    cancel();
    m_last_result = RecordedSampleResult{};
}

void S760SampleRecorder::on_midi_note_on(uint8_t note, uint8_t velocity) {
    (void)note;
    if (velocity == 0) return;
    if (m_state.load() == RecordState::Armed && m_config.trigger_mode == RecordTriggerMode::MIDINote) {
        start_recording();
    }
}

void S760SampleRecorder::process_input(const float* left_in, const float* right_in, size_t num_frames, double host_sample_rate) {
    if (!left_in && !right_in) return;
    if (num_frames == 0) return;

    float max_l = 0.0f;
    float max_r = 0.0f;

    for (size_t i = 0; i < num_frames; ++i) {
        float l = left_in ? left_in[i] : 0.0f;
        float r = right_in ? right_in[i] : l;
        max_l = std::max(max_l, std::abs(l));
        max_r = std::max(max_r, std::abs(r));
    }

    m_peak_l.store(max_l);
    m_peak_r.store(max_r);

    RecordState st = m_state.load();

    if (st == RecordState::Armed) {
        // Feed into pre-trigger ring buffer
        size_t cap = m_pre_ring_l.size();
        for (size_t i = 0; i < num_frames; ++i) {
            float l = left_in ? left_in[i] : 0.0f;
            float r = right_in ? right_in[i] : l;
            m_pre_ring_l[m_pre_write_idx] = l;
            m_pre_ring_r[m_pre_write_idx] = r;
            m_pre_write_idx = (m_pre_write_idx + 1) % cap;
            if (m_pre_write_idx == 0) m_pre_filled = true;
        }

        // Check threshold trigger
        if (m_config.trigger_mode == RecordTriggerMode::Threshold) {
            double threshold_linear = std::pow(10.0, m_config.threshold_db / 20.0);
            if (max_l >= threshold_linear || max_r >= threshold_linear) {
                start_recording();
                st = RecordState::Recording;
            }
        }
    }

    if (st == RecordState::Recording) {
        std::lock_guard<std::mutex> lock(m_mutex);
        for (size_t i = 0; i < num_frames; ++i) {
            float l = left_in ? left_in[i] : 0.0f;
            float r = right_in ? right_in[i] : l;

            switch (m_config.channel_mode) {
                case RecordChannelMode::Stereo:
                    m_recorded_l.push_back(l);
                    m_recorded_r.push_back(r);
                    break;
                case RecordChannelMode::MonoLeft:
                    m_recorded_l.push_back(l);
                    m_recorded_r.push_back(l);
                    break;
                case RecordChannelMode::MonoRight:
                    m_recorded_l.push_back(r);
                    m_recorded_r.push_back(r);
                    break;
                case RecordChannelMode::MonoMix: {
                    float mix = (l + r) * 0.5f;
                    m_recorded_l.push_back(mix);
                    m_recorded_r.push_back(mix);
                    break;
                }
            }

            if (m_recorded_l.size() >= m_config.max_samples) {
                finalize_recording(host_sample_rate);
                break;
            }
        }
    }
}

void S760SampleRecorder::apply_monitoring(float* left_out, float* right_out, size_t num_frames) const {
    if (!m_config.monitor_input) return;
    float gain = m_config.monitor_gain;
    if (gain <= 0.0001f) return;

    if (m_state.load() == RecordState::Recording || m_state.load() == RecordState::Armed) {
        if (left_out) {
            for (size_t i = 0; i < num_frames; ++i) {
                left_out[i] *= gain;
            }
        }
        if (right_out) {
            for (size_t i = 0; i < num_frames; ++i) {
                right_out[i] *= gain;
            }
        }
    }
}

std::vector<uint8_t> S760SampleRecorder::floats_to_pcm16(const std::vector<float>& floats) {
    std::vector<uint8_t> pcm(floats.size() * 2);
    for (size_t i = 0; i < floats.size(); ++i) {
        float clamped = std::clamp(floats[i], -1.0f, 1.0f);
        int16_t sample16 = static_cast<int16_t>(clamped * 32767.0f);
        pcm[i * 2 + 0] = static_cast<uint8_t>(sample16 & 0xFF);
        pcm[i * 2 + 1] = static_cast<uint8_t>((sample16 >> 8) & 0xFF);
    }
    return pcm;
}

void S760SampleRecorder::finalize_recording(double host_sample_rate) {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (m_recorded_l.empty()) {
        m_state.store(RecordState::Finished);
        return;
    }

    uint32_t target_rate = m_config.target_sample_rate;
    if (target_rate == 0) target_rate = 44100;

    std::vector<float> resampled_l;
    std::vector<float> resampled_r;

    if (std::abs(host_sample_rate - target_rate) > 1.0 && host_sample_rate > 1000.0) {
        // Resample to target rate
        double ratio = static_cast<double>(target_rate) / host_sample_rate;
        size_t target_len = static_cast<size_t>(m_recorded_l.size() * ratio);
        resampled_l.resize(target_len);
        resampled_r.resize(target_len);

        for (size_t i = 0; i < target_len; ++i) {
            double src_idx = static_cast<double>(i) / ratio;
            size_t idx0 = static_cast<size_t>(src_idx);
            size_t idx1 = std::min(idx0 + 1, m_recorded_l.size() - 1);
            double frac = src_idx - idx0;

            resampled_l[i] = static_cast<float>(m_recorded_l[idx0] * (1.0 - frac) + m_recorded_l[idx1] * frac);
            resampled_r[i] = static_cast<float>(m_recorded_r[idx0] * (1.0 - frac) + m_recorded_r[idx1] * frac);
        }
    } else {
        resampled_l = std::move(m_recorded_l);
        resampled_r = std::move(m_recorded_r);
    }

    auto pcm_l = floats_to_pcm16(resampled_l);
    auto pcm_r = floats_to_pcm16(resampled_r);

    if (m_config.auto_truncate || m_config.auto_normalize) {
        auto [norm_l, s_l, e_l] = S760DSPTools::auto_truncate_and_normalize(pcm_l, m_config.threshold_db, 0.98);
        auto [norm_r, s_r, e_r] = S760DSPTools::auto_truncate_and_normalize(pcm_r, m_config.threshold_db, 0.98);
        (void)s_l; (void)e_l; (void)s_r; (void)e_r;
        pcm_l = std::move(norm_l);
        pcm_r = std::move(norm_r);
    }

    m_last_result.valid = !pcm_l.empty();
    m_last_result.sample_name = m_config.sample_name;
    m_last_result.sample_rate = target_rate;
    m_last_result.sample_length_words = static_cast<uint32_t>(pcm_l.size() / 2);
    m_last_result.left_pcm_bytes = std::move(pcm_l);
    m_last_result.right_pcm_bytes = std::move(pcm_r);
    m_last_result.is_stereo = (m_config.channel_mode == RecordChannelMode::Stereo);

    m_state.store(RecordState::Finished);
}

RecordedSampleResult S760SampleRecorder::get_recorded_result() {
    std::lock_guard<std::mutex> lock(m_mutex);
    return m_last_result;
}

Sample S760SampleRecorder::export_sample(bool right_channel) {
    std::lock_guard<std::mutex> lock(m_mutex);
    Sample smp{};
    if (!m_last_result.valid) return smp;

    std::string name = m_last_result.sample_name;
    if (m_last_result.is_stereo) {
        name += right_channel ? "_R" : "_L";
    }
    smp.name = name;
    smp.sample_rate = m_last_result.sample_rate;
    smp.root_key = m_config.root_key;
    smp.loop_start = 0;
    smp.loop_end = (m_last_result.sample_length_words > 0) ? (m_last_result.sample_length_words - 1) : 0;
    smp.pcm_data = right_channel ? m_last_result.right_pcm_bytes : m_last_result.left_pcm_bytes;

    return smp;
}

} // namespace s760
