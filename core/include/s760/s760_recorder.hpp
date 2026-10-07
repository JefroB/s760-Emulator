#pragma once

#include "s760/s760_disk.hpp"
#include "s760/s760_dsp.hpp"

#include <cstdint>
#include <vector>
#include <string>
#include <mutex>
#include <atomic>
#include <memory>

namespace s760 {

enum class RecordTriggerMode {
    Manual,
    Threshold,
    MIDINote
};

enum class RecordChannelMode {
    Stereo,
    MonoLeft,
    MonoRight,
    MonoMix
};

enum class RecordState {
    Idle,
    Armed,
    Recording,
    Finished
};

struct RecordingConfig {
    uint32_t target_sample_rate = 44100; // 48000, 44100, 32000, 22050
    RecordTriggerMode trigger_mode = RecordTriggerMode::Manual;
    RecordChannelMode channel_mode = RecordChannelMode::Stereo;
    double threshold_db = -36.0;         // For Threshold trigger
    size_t pre_trigger_samples = 2048;   // Pre-trigger buffer size (~45ms @ 44.1k)
    size_t max_samples = 44100 * 60;     // Default 60 seconds max
    bool auto_normalize = true;
    bool auto_truncate = true;
    bool monitor_input = true;           // Pass input to output (thru)
    float monitor_gain = 1.0f;
    std::string sample_name = "RECORDED";
    uint8_t root_key = 60;               // Middle C (C4)
};

struct RecordedSampleResult {
    bool valid = false;
    std::string sample_name;
    uint32_t sample_rate = 44100;
    uint32_t sample_length_words = 0;
    std::vector<uint8_t> left_pcm_bytes;
    std::vector<uint8_t> right_pcm_bytes;
    bool is_stereo = false;
};

class S760SampleRecorder {
public:
    S760SampleRecorder();
    ~S760SampleRecorder() = default;

    // Configuration
    void set_config(const RecordingConfig& config);
    RecordingConfig get_config() const;

    // State Control
    void arm();
    void start_recording();
    void stop_recording();
    void cancel();
    void reset();

    RecordState get_state() const { return m_state.load(); }
    bool is_recording() const { return m_state.load() == RecordState::Recording; }
    bool is_armed() const { return m_state.load() == RecordState::Armed; }

    // Live Audio Stream Processing (Called from DAW Audio Thread)
    void process_input(const float* left_in, const float* right_in, size_t num_frames, double host_sample_rate);

    // MIDI Trigger (Called from DAW Event Thread)
    void on_midi_note_on(uint8_t note, uint8_t velocity);

    // Monitoring (Thru)
    void apply_monitoring(float* left_out, float* right_out, size_t num_frames) const;

    // Metering
    float get_peak_level_left() const { return m_peak_l.load(); }
    float get_peak_level_right() const { return m_peak_r.load(); }

    // Retrieval & Disk Export
    RecordedSampleResult get_recorded_result();
    Sample export_sample(bool right_channel = false);

private:
    mutable std::mutex m_mutex;
    RecordingConfig m_config;
    std::atomic<RecordState> m_state{RecordState::Idle};

    std::atomic<float> m_peak_l{0.0f};
    std::atomic<float> m_peak_r{0.0f};

    // Pre-trigger circular ring buffers
    std::vector<float> m_pre_ring_l;
    std::vector<float> m_pre_ring_r;
    size_t m_pre_write_idx = 0;
    bool m_pre_filled = false;

    // Recorded raw float buffers (at host sample rate)
    std::vector<float> m_recorded_l;
    std::vector<float> m_recorded_r;

    // Output result
    RecordedSampleResult m_last_result;

    void finalize_recording(double host_sample_rate);
    static std::vector<uint8_t> floats_to_pcm16(const std::vector<float>& floats);
};

} // namespace s760
