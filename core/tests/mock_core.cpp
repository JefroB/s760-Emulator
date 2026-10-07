#include "s760/libretro.h"
#include <cstring>
#include <cmath>

#if defined(_WIN32)
#define RETRO_EXPORT __declspec(dllexport)
#else
#define RETRO_EXPORT __attribute__((visibility("default")))
#endif

static retro_environment_t s_environ_cb = nullptr;
static retro_video_refresh_t s_video_cb = nullptr;
static retro_audio_sample_batch_t s_audio_batch_cb = nullptr;
static bool s_game_loaded = false;
static uint32_t s_frame_count = 0;

extern "C" {

RETRO_EXPORT void retro_init(void) {
    s_frame_count = 0;
}

RETRO_EXPORT void retro_deinit(void) {
    s_game_loaded = false;
}

RETRO_EXPORT unsigned retro_api_version(void) {
    return RETRO_API_VERSION;
}

RETRO_EXPORT void retro_get_system_info(struct retro_system_info* info) {
    if (!info) return;
    info->library_name = "Mock Roland S-760";
    info->library_version = "2.24";
    info->valid_extensions = "img|hda|iso";
    info->need_fullpath = false;
    info->block_extract = false;
}

RETRO_EXPORT void retro_get_system_av_info(struct retro_system_av_info* info) {
    if (!info) return;
    info->geometry.base_width = 320;
    info->geometry.base_height = 240;
    info->geometry.max_width = 640;
    info->geometry.max_height = 480;
    info->geometry.aspect_ratio = 4.0f / 3.0f;
    info->timing.fps = 60.0;
    info->timing.sample_rate = 44100.0;
}

RETRO_EXPORT void retro_set_environment(retro_environment_t cb) {
    s_environ_cb = cb;
    if (s_environ_cb) {
        enum retro_pixel_format fmt = RETRO_PIXEL_FORMAT_XRGB8888;
        s_environ_cb(RETRO_ENVIRONMENT_SET_PIXEL_FORMAT, &fmt);
    }
}

RETRO_EXPORT void retro_set_video_refresh(retro_video_refresh_t cb) { s_video_cb = cb; }
RETRO_EXPORT void retro_set_audio_sample(retro_audio_sample_t cb) { (void)cb; }
RETRO_EXPORT void retro_set_audio_sample_batch(retro_audio_sample_batch_t cb) { s_audio_batch_cb = cb; }
RETRO_EXPORT void retro_set_input_poll(retro_input_poll_t cb) { (void)cb; }
RETRO_EXPORT void retro_set_input_state(retro_input_state_t cb) { (void)cb; }

RETRO_EXPORT bool retro_load_game(const struct retro_game_info* game) {
    (void)game;
    s_game_loaded = true;
    return true;
}

RETRO_EXPORT void retro_unload_game(void) {
    s_game_loaded = false;
}

RETRO_EXPORT void retro_run(void) {
    if (!s_game_loaded) return;
    s_frame_count++;

    // Generate 735 audio frames (44100 / 60) of a 440Hz test tone
    int16_t audio_buf[735 * 2];
    for (int i = 0; i < 735; ++i) {
        double phase = 2.0 * 3.14159265 * 440.0 * (s_frame_count * 735 + i) / 44100.0;
        int16_t val = static_cast<int16_t>(std::sin(phase) * 16384.0);
        audio_buf[i * 2] = val;     // Left
        audio_buf[i * 2 + 1] = val; // Right
    }
    if (s_audio_batch_cb) {
        s_audio_batch_cb(audio_buf, 735);
    }

    // Generate 320x240 video test pattern (XRGB8888)
    uint32_t video_buf[320 * 240];
    for (int y = 0; y < 240; ++y) {
        for (int x = 0; x < 320; ++x) {
            video_buf[y * 320 + x] = 0x00112233; // Dark Roland S-760 LCD blue
        }
    }
    if (s_video_cb) {
        s_video_cb(video_buf, 320, 240, 320 * sizeof(uint32_t));
    }
}

RETRO_EXPORT size_t retro_serialize_size(void) {
    return 1024;
}

RETRO_EXPORT bool retro_serialize(void* data, size_t size) {
    if (!data || size < 1024) return false;
    std::memset(data, 0xAA, size);
    std::memcpy(data, &s_frame_count, sizeof(s_frame_count));
    return true;
}

RETRO_EXPORT bool retro_unserialize(const void* data, size_t size) {
    if (!data || size < 1024) return false;
    std::memcpy(&s_frame_count, data, sizeof(s_frame_count));
    return true;
}

RETRO_EXPORT void retro_reset(void) {
    s_frame_count = 0;
}

} // extern "C"
