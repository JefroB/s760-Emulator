#include "s760/s760_libretro_host.hpp"

#include <iostream>
#include <cstring>
#include <algorithm>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#else
#include <dlfcn.h>
#endif

namespace s760 {

S760LibretroHost* S760LibretroHost::s_active_instance = nullptr;

// -----------------------------------------------------------------------------
// Libretro C Thunk Callbacks
// -----------------------------------------------------------------------------
extern "C" {

static bool env_thunk(unsigned cmd, void* data) {
    if (auto* host = S760LibretroHost::get_active_instance()) {
        return host->handle_environment(cmd, data);
    }
    return false;
}

static void video_thunk(const void* data, unsigned width, unsigned height, size_t pitch) {
    if (auto* host = S760LibretroHost::get_active_instance()) {
        host->handle_video_refresh(data, width, height, pitch);
    }
}

static void audio_sample_thunk(int16_t left, int16_t right) {
    if (auto* host = S760LibretroHost::get_active_instance()) {
        host->handle_audio_sample(left, right);
    }
}

static size_t audio_sample_batch_thunk(const int16_t* data, size_t frames) {
    if (auto* host = S760LibretroHost::get_active_instance()) {
        return host->handle_audio_sample_batch(data, frames);
    }
    return 0;
}

static void input_poll_thunk(void) {
    // Input polled on demand
}

static int16_t input_state_thunk(unsigned port, unsigned device, unsigned index, unsigned id) {
    if (auto* host = S760LibretroHost::get_active_instance()) {
        return host->handle_input_state(port, device, index, id);
    }
    return 0;
}

// MIDI interface thunks
static bool midi_input_enabled(void) { return true; }
static bool midi_output_enabled(void) { return true; }
static bool midi_read(uint8_t* byte) {
    if (!byte) return false;
    // Handled in host MIDI queue
    return false;
}
static bool midi_write(uint8_t byte, uint32_t delta_time) {
    (void)byte; (void)delta_time;
    return true;
}
static bool midi_flush(void) { return true; }

static struct retro_midi_interface s_midi_iface = {
    midi_input_enabled,
    midi_output_enabled,
    midi_read,
    midi_write,
    midi_flush
};

} // extern "C"

// -----------------------------------------------------------------------------
// S760LibretroHost Implementation
// -----------------------------------------------------------------------------

S760LibretroHost::S760LibretroHost() {
    m_audio_ring.resize(AUDIO_BUFFER_FRAMES * 2, 0.0f);
    s_active_instance = this;
}

S760LibretroHost::~S760LibretroHost() {
    unload_system();
    unload_core();
    if (s_active_instance == this) {
        s_active_instance = nullptr;
    }
}

#if defined(_WIN32)
template<typename T>
static bool load_sym(HMODULE mod, const char* name, T& func) {
    func = reinterpret_cast<T>(GetProcAddress(mod, name));
    return (func != nullptr);
}
#else
template<typename T>
static bool load_sym(void* mod, const char* name, T& func) {
    func = reinterpret_cast<T>(dlsym(mod, name));
    return (func != nullptr);
}
#endif

bool S760LibretroHost::load_core(const std::string& core_path) {
    unload_system();
    unload_core();

#if defined(_WIN32)
    HMODULE mod = LoadLibraryA(core_path.c_str());
    if (!mod) {
        return false;
    }
    m_module_handle = mod;
#else
    void* mod = dlopen(core_path.c_str(), RTLD_NOW);
    if (!mod) {
        return false;
    }
    m_module_handle = mod;
#endif

    bool ok = true;
    ok &= load_sym(mod, "retro_init", m_retro_init);
    ok &= load_sym(mod, "retro_deinit", m_retro_deinit);
    ok &= load_sym(mod, "retro_api_version", m_retro_api_version);
    ok &= load_sym(mod, "retro_get_system_info", m_retro_get_system_info);
    ok &= load_sym(mod, "retro_get_system_av_info", m_retro_get_system_av_info);
    ok &= load_sym(mod, "retro_set_environment", m_retro_set_environment);
    ok &= load_sym(mod, "retro_set_video_refresh", m_retro_set_video_refresh);
    ok &= load_sym(mod, "retro_set_audio_sample", m_retro_set_audio_sample);
    ok &= load_sym(mod, "retro_set_audio_sample_batch", m_retro_set_audio_sample_batch);
    ok &= load_sym(mod, "retro_set_input_poll", m_retro_set_input_poll);
    ok &= load_sym(mod, "retro_set_input_state", m_retro_set_input_state);
    ok &= load_sym(mod, "retro_load_game", m_retro_load_game);
    ok &= load_sym(mod, "retro_unload_game", m_retro_unload_game);
    ok &= load_sym(mod, "retro_run", m_retro_run);
    ok &= load_sym(mod, "retro_serialize_size", m_retro_serialize_size);
    ok &= load_sym(mod, "retro_serialize", m_retro_serialize);
    ok &= load_sym(mod, "retro_unserialize", m_retro_unserialize);
    ok &= load_sym(mod, "retro_reset", m_retro_reset);

    if (!ok) {
        unload_core();
        return false;
    }

    s_active_instance = this;
    m_retro_set_environment(env_thunk);
    m_retro_set_video_refresh(video_thunk);
    m_retro_set_audio_sample(audio_sample_thunk);
    m_retro_set_audio_sample_batch(audio_sample_batch_thunk);
    m_retro_set_input_poll(input_poll_thunk);
    m_retro_set_input_state(input_state_thunk);

    m_retro_init();
    m_core_loaded = true;
    return true;
}

void S760LibretroHost::unload_core() {
    if (m_core_loaded && m_retro_deinit) {
        m_retro_deinit();
    }

#if defined(_WIN32)
    if (m_module_handle) {
        FreeLibrary(static_cast<HMODULE>(m_module_handle));
        m_module_handle = nullptr;
    }
#else
    if (m_module_handle) {
        dlclose(m_module_handle);
        m_module_handle = nullptr;
    }
#endif

    m_retro_init = nullptr;
    m_retro_deinit = nullptr;
    m_retro_api_version = nullptr;
    m_retro_get_system_info = nullptr;
    m_retro_get_system_av_info = nullptr;
    m_retro_set_environment = nullptr;
    m_retro_set_video_refresh = nullptr;
    m_retro_set_audio_sample = nullptr;
    m_retro_set_audio_sample_batch = nullptr;
    m_retro_set_input_poll = nullptr;
    m_retro_set_input_state = nullptr;
    m_retro_load_game = nullptr;
    m_retro_unload_game = nullptr;
    m_retro_run = nullptr;
    m_retro_serialize_size = nullptr;
    m_retro_serialize = nullptr;
    m_retro_unserialize = nullptr;
    m_retro_reset = nullptr;

    m_core_loaded = false;
}

bool S760LibretroHost::load_system(const std::string& system_name,
                                   const std::string& system_dir,
                                   const std::string& save_dir) {
    if (!m_core_loaded) return false;
    unload_system();

    m_system_dir = system_dir;
    m_save_dir = save_dir;

    struct retro_game_info game;
    std::memset(&game, 0, sizeof(game));
    game.path = system_name.c_str();

    if (!m_retro_load_game(&game)) {
        return false;
    }

    struct retro_system_av_info av_info;
    std::memset(&av_info, 0, sizeof(av_info));
    m_retro_get_system_av_info(&av_info);
    m_core_sample_rate = av_info.timing.sample_rate;
    if (m_core_sample_rate <= 0.0) m_core_sample_rate = 44100.0;

    m_game_loaded = true;
    return true;
}

void S760LibretroHost::unload_system() {
    if (m_game_loaded && m_retro_unload_game) {
        m_drive_manager.flush_all();
        m_retro_unload_game();
        m_game_loaded = false;
    }
}

bool S760LibretroHost::run_frame() {
    if (m_game_loaded && m_retro_run) {
        s_active_instance = this;
        m_retro_run();
        return true;
    }
    return false;
}

void S760LibretroHost::reset() {
    if (m_game_loaded && m_retro_reset) {
        m_retro_reset();
    }
}

size_t S760LibretroHost::read_audio_frames(float* left_out, float* right_out, size_t num_frames) {
    std::lock_guard<std::mutex> lock(m_audio_mutex);
    size_t to_read = std::min(num_frames, m_audio_frames_available);

    for (size_t i = 0; i < to_read; ++i) {
        size_t idx = (m_audio_read_pos + i) % AUDIO_BUFFER_FRAMES;
        if (left_out) left_out[i] = m_audio_ring[idx * 2];
        if (right_out) right_out[i] = m_audio_ring[idx * 2 + 1];
    }

    // Fill remaining requested frames with silence and track underruns
    if (to_read < num_frames) {
        m_underrun_count.fetch_add(1, std::memory_order_relaxed);
        m_underrun_frames.fetch_add(num_frames - to_read, std::memory_order_relaxed);
        for (size_t i = to_read; i < num_frames; ++i) {
            if (left_out) left_out[i] = 0.0f;
            if (right_out) right_out[i] = 0.0f;
        }
    }

    m_audio_read_pos = (m_audio_read_pos + to_read) % AUDIO_BUFFER_FRAMES;
    m_audio_frames_available -= to_read;
    return to_read;
}

void S760LibretroHost::feed_audio_input(const float* left_in, const float* right_in, size_t num_frames) {
    m_recorder.process_input(left_in, right_in, num_frames, m_target_sample_rate);
}

AudioBufferStats S760LibretroHost::get_audio_stats() const {
    std::lock_guard<std::mutex> lock(m_audio_mutex);
    AudioBufferStats s;
    s.available_frames = m_audio_frames_available;
    s.capacity_frames = AUDIO_BUFFER_FRAMES;
    s.sample_rate = m_core_sample_rate;
    s.underrun_count = m_underrun_count.load(std::memory_order_relaxed);
    s.underrun_frames = m_underrun_frames.load(std::memory_order_relaxed);
    return s;
}

VideoFrame S760LibretroHost::get_latest_video_frame() const {
    std::lock_guard<std::mutex> lock(m_video_mutex);
    return m_video_frame;
}

void S760LibretroHost::send_midi_byte(uint8_t byte) {
    std::lock_guard<std::mutex> lock(m_midi_mutex);
    m_midi_in_queue.push(byte);
}

void S760LibretroHost::send_midi_message(const uint8_t* msg, size_t len) {
    if (!msg || len == 0) return;

    // Check MIDI Note On for sample recording trigger
    if (len >= 3 && (msg[0] & 0xF0) == 0x90 && msg[2] > 0) {
        m_recorder.on_midi_note_on(msg[1], msg[2]);
    }

    std::lock_guard<std::mutex> lock(m_midi_mutex);
    for (size_t i = 0; i < len; ++i) {
        m_midi_in_queue.push(msg[i]);
    }
}

size_t S760LibretroHost::get_state_size() {
    if (!m_game_loaded || !m_retro_serialize_size) return 0;
    return m_retro_serialize_size();
}

std::vector<uint8_t> S760LibretroHost::save_state() {
    size_t sz = get_state_size();
    if (sz == 0) return {};

    std::vector<uint8_t> buf(sz);
    if (!m_retro_serialize(buf.data(), sz)) {
        return {};
    }
    m_drive_manager.flush_all();
    return buf;
}

bool S760LibretroHost::load_state(const std::vector<uint8_t>& state_data) {
    if (!m_game_loaded || !m_retro_unserialize || state_data.empty()) return false;
    return m_retro_unserialize(state_data.data(), state_data.size());
}

bool S760LibretroHost::handle_environment(unsigned cmd, void* data) {
    switch (cmd) {
        case RETRO_ENVIRONMENT_GET_SYSTEM_DIRECTORY:
        case RETRO_ENVIRONMENT_GET_LIBRETRO_PATH: {
            if (data) {
                *reinterpret_cast<const char**>(data) = m_system_dir.c_str();
                return true;
            }
            break;
        }
        case RETRO_ENVIRONMENT_GET_SAVE_DIRECTORY: {
            if (data) {
                *reinterpret_cast<const char**>(data) = m_save_dir.c_str();
                return true;
            }
            break;
        }
        case RETRO_ENVIRONMENT_SET_PIXEL_FORMAT: {
            if (data) {
                m_pixel_format = *reinterpret_cast<const enum retro_pixel_format*>(data);
                return true;
            }
            break;
        }
        case RETRO_ENVIRONMENT_GET_VARIABLE: {
            if (data) {
                auto* var = reinterpret_cast<struct retro_variable*>(data);
                var->value = nullptr;
                return true;
            }
            break;
        }
        case RETRO_ENVIRONMENT_GET_CAN_DUPE: {
            if (data) {
                *reinterpret_cast<bool*>(data) = true;
                return true;
            }
            break;
        }
        case RETRO_ENVIRONMENT_SET_SUPPORT_NO_GAME: {
            return true;
        }
        case RETRO_ENVIRONMENT_GET_MIDI_INTERFACE: {
            if (data) {
                *reinterpret_cast<struct retro_midi_interface**>(data) = &s_midi_iface;
                return true;
            }
            break;
        }
        default:
            break;
    }
    return false;
}

void S760LibretroHost::handle_video_refresh(const void* data, unsigned width, unsigned height, size_t pitch) {
    if (!data || width == 0 || height == 0) return;

    std::lock_guard<std::mutex> lock(m_video_mutex);
    m_video_frame.width = width;
    m_video_frame.height = height;
    m_video_frame.rgba_pixels.resize(width * height);

    const uint8_t* src_row = reinterpret_cast<const uint8_t*>(data);
    uint32_t* dst = m_video_frame.rgba_pixels.data();

    if (m_pixel_format == RETRO_PIXEL_FORMAT_XRGB8888) {
        for (unsigned y = 0; y < height; ++y) {
            const uint32_t* src_pixels = reinterpret_cast<const uint32_t*>(src_row);
            for (unsigned x = 0; x < width; ++x) {
                uint32_t px = src_pixels[x];
                uint8_t r = (px >> 16) & 0xFF;
                uint8_t g = (px >> 8) & 0xFF;
                uint8_t b = px & 0xFF;
                dst[y * width + x] = 0xFF000000 | (r << 0) | (g << 8) | (b << 16);
            }
            src_row += pitch;
        }
    } else if (m_pixel_format == RETRO_PIXEL_FORMAT_RGB565) {
        for (unsigned y = 0; y < height; ++y) {
            const uint16_t* src_pixels = reinterpret_cast<const uint16_t*>(src_row);
            for (unsigned x = 0; x < width; ++x) {
                uint16_t px = src_pixels[x];
                uint8_t r = ((px >> 11) & 0x1F) * 255 / 31;
                uint8_t g = ((px >> 5) & 0x3F) * 255 / 63;
                uint8_t b = (px & 0x1F) * 255 / 31;
                dst[y * width + x] = 0xFF000000 | (r << 0) | (g << 8) | (b << 16);
            }
            src_row += pitch;
        }
    } else { // 0RGB1555
        for (unsigned y = 0; y < height; ++y) {
            const uint16_t* src_pixels = reinterpret_cast<const uint16_t*>(src_row);
            for (unsigned x = 0; x < width; ++x) {
                uint16_t px = src_pixels[x];
                uint8_t r = ((px >> 10) & 0x1F) * 255 / 31;
                uint8_t g = ((px >> 5) & 0x1F) * 255 / 31;
                uint8_t b = (px & 0x1F) * 255 / 31;
                dst[y * width + x] = 0xFF000000 | (r << 0) | (g << 8) | (b << 16);
            }
            src_row += pitch;
        }
    }
}

void S760LibretroHost::handle_audio_sample(int16_t left, int16_t right) {
    int16_t buf[2] = {left, right};
    handle_audio_sample_batch(buf, 1);
}

size_t S760LibretroHost::handle_audio_sample_batch(const int16_t* data, size_t frames) {
    if (!data || frames == 0) return 0;

    std::lock_guard<std::mutex> lock(m_audio_mutex);
    for (size_t f = 0; f < frames; ++f) {
        size_t idx = (m_audio_write_pos + f) % AUDIO_BUFFER_FRAMES;
        m_audio_ring[idx * 2] = data[f * 2] / 32768.0f;
        m_audio_ring[idx * 2 + 1] = data[f * 2 + 1] / 32768.0f;
    }

    m_audio_write_pos = (m_audio_write_pos + frames) % AUDIO_BUFFER_FRAMES;
    m_audio_frames_available = std::min(AUDIO_BUFFER_FRAMES, m_audio_frames_available + frames);
    return frames;
}

int16_t S760LibretroHost::handle_input_state(unsigned port, unsigned device, unsigned index, unsigned id) {
    (void)port; (void)device; (void)index; (void)id;
    return 0;
}

} // namespace s760
