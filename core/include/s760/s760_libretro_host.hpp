#pragma once

#include "s760/libretro.h"
#include "s760/s760_drive_manager.hpp"
#include "s760/s760_recorder.hpp"

#include <cstddef>
#include <string>
#include <vector>
#include <memory>
#include <mutex>
#include <queue>
#include <functional>

#include <atomic>

namespace s760 {

struct AudioBufferStats {
    size_t available_frames = 0;
    size_t capacity_frames = 0;
    double sample_rate = 44100.0;
    uint64_t underrun_count = 0;
    uint64_t underrun_frames = 0;
};

struct VideoFrame {
    uint32_t width = 0;
    uint32_t height = 0;
    std::vector<uint32_t> rgba_pixels; // 32-bit RGBA
};

} // namespace s760

// VideoFrame (above) is the shared surface struct the IS760Host contract uses.
// It must be fully defined before including the interface header, which depends
// on it. The interface header also includes this file; the #pragma once guard
// plus this ordering keeps the mutual include well-formed.
#include "s760/s760_host_interface.hpp"

namespace s760 {

class S760LibretroHost : public IS760Host {
public:
    S760LibretroHost();
    ~S760LibretroHost();

    // Core Lifecycle
    bool load_core(const std::string& core_path);
    void unload_core();
    bool is_core_loaded() const { return m_core_loaded; }

    bool load_system(const std::string& system_name = "s760",
                     const std::string& system_dir = "roms/s760",
                     const std::string& save_dir = "saves");
    void unload_system();
    bool is_system_running() const { return m_game_loaded; }

    // IS760Host: load / initialize the backend. For the Core backend the core
    // and system are brought up via load_core()/load_system(); init() reports
    // whether a system is running so the Bridge can treat a non-running host as
    // an initialization failure (Requirement 1.4) without changing any existing
    // behavior. No process is spawned and the host is never terminated here.
    bool init() override { return is_system_running(); }

    // IS760Host: advance exactly one emulated frame. Returns true when a frame
    // was advanced. Behavior is otherwise identical to the previous void
    // run_frame() (the Bridge already ignores the result).
    bool run_frame() override;
    void reset();

    // Audio Processing for DAW Audio Thread
    size_t read_audio_frames(float* left_out, float* right_out, size_t num_frames);
    void feed_audio_input(const float* left_in, const float* right_in, size_t num_frames);
    AudioBufferStats get_audio_stats() const;
    void set_target_sample_rate(double rate) { m_target_sample_rate = rate; }

    // Sample Recorder (Live Sampling Ingestion & Triggers)
    S760SampleRecorder& get_recorder() override { return m_recorder; }
    const S760SampleRecorder& get_recorder() const override { return m_recorder; }

    // Video CRT Frame for DAW UI
    VideoFrame get_latest_video_frame() const override;

    // IS760Host: the Core backend exposes no SED1335/OLED LCD raster, so this
    // returns false and the Bridge keeps its authentic-blank LCD behavior,
    // preserving byte-for-byte parity on the wire for this backend.
    bool get_lcd_surface(uint8_t* out, std::size_t len) const override {
        (void)out;
        (void)len;
        return false;
    }

    // MIDI Input for DAW MIDI Thread
    void send_midi_byte(uint8_t byte);
    void send_midi_message(const uint8_t* msg, size_t len) override;

    // Hardware Drive Manager (FDD & SCSI ZuluSCSI/Gotek)
    S760DriveManager& get_drive_manager() override { return m_drive_manager; }
    const S760DriveManager& get_drive_manager() const { return m_drive_manager; }

    // Savestates (DAW Project Chunk Serialization)
    size_t get_state_size();
    std::vector<uint8_t> save_state();
    bool load_state(const std::vector<uint8_t>& state_data);

    // Callbacks hooked from Libretro Core
    bool handle_environment(unsigned cmd, void* data);
    void handle_video_refresh(const void* data, unsigned width, unsigned height, size_t pitch);
    void handle_audio_sample(int16_t left, int16_t right);
    size_t handle_audio_sample_batch(const int16_t* data, size_t frames);
    int16_t handle_input_state(unsigned port, unsigned device, unsigned index, unsigned id) override;

    static S760LibretroHost* get_active_instance() { return s_active_instance; }

private:
    void* m_module_handle = nullptr;
    bool m_core_loaded = false;
    bool m_game_loaded = false;

    // Core function pointers
    void (*m_retro_init)(void) = nullptr;
    void (*m_retro_deinit)(void) = nullptr;
    unsigned (*m_retro_api_version)(void) = nullptr;
    void (*m_retro_get_system_info)(struct retro_system_info* info) = nullptr;
    void (*m_retro_get_system_av_info)(struct retro_system_av_info* info) = nullptr;
    void (*m_retro_set_environment)(retro_environment_t) = nullptr;
    void (*m_retro_set_video_refresh)(retro_video_refresh_t) = nullptr;
    void (*m_retro_set_audio_sample)(retro_audio_sample_t) = nullptr;
    void (*m_retro_set_audio_sample_batch)(retro_audio_sample_batch_t) = nullptr;
    void (*m_retro_set_input_poll)(retro_input_poll_t) = nullptr;
    void (*m_retro_set_input_state)(retro_input_state_t) = nullptr;
    bool (*m_retro_load_game)(const struct retro_game_info* game) = nullptr;
    void (*m_retro_unload_game)(void) = nullptr;
    void (*m_retro_run)(void) = nullptr;
    size_t (*m_retro_serialize_size)(void) = nullptr;
    bool (*m_retro_serialize)(void* data, size_t size) = nullptr;
    bool (*m_retro_unserialize)(const void* data, size_t size) = nullptr;
    void (*m_retro_reset)(void) = nullptr;

    // Environment & paths
    std::string m_system_dir;
    std::string m_save_dir;
    enum retro_pixel_format m_pixel_format = RETRO_PIXEL_FORMAT_0RGB1555;
    double m_target_sample_rate = 44100.0;
    double m_core_sample_rate = 44100.0;

    // Audio Ring Buffer (interleaved stereo float)
    mutable std::mutex m_audio_mutex;
    std::vector<float> m_audio_ring;
    size_t m_audio_read_pos = 0;
    size_t m_audio_write_pos = 0;
    size_t m_audio_frames_available = 0;
    static constexpr size_t AUDIO_BUFFER_FRAMES = 65536;

    std::atomic<uint64_t> m_underrun_count{0};
    std::atomic<uint64_t> m_underrun_frames{0};

    // Video Frame
    mutable std::mutex m_video_mutex;
    VideoFrame m_video_frame;

    // MIDI In Queue
    mutable std::mutex m_midi_mutex;
    std::queue<uint8_t> m_midi_in_queue;

    // Hardware Drive Manager
    S760DriveManager m_drive_manager;

    // Live Sample Recorder
    S760SampleRecorder m_recorder;

    static S760LibretroHost* s_active_instance;
};

} // namespace s760
