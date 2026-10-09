#include "s760/s760_clap_plugin.hpp"

#include <cstring>
#include <iostream>
#include <algorithm>

#if defined(_WIN32)
#define CLAP_EXPORT __declspec(dllexport)
#else
#define CLAP_EXPORT __attribute__((visibility("default")))
#endif

namespace s760 {

static const char* const s_plugin_features_inst[] = {
    "instrument",
    "sampler",
    "synthesizer",
    "stereo",
    nullptr
};

static const char* const s_plugin_features_fx[] = {
    "audio-effect",
    "sampler",
    "stereo",
    nullptr
};

static const clap_plugin_descriptor_t s_descriptor_inst = {
    CLAP_VERSION,
    "com.roland.s760.emulator",
    "Roland S-760 Sampler",
    "Roland Emulation Team",
    "https://github.com/JefroB/s760-Emulator",
    "",
    "",
    "2.24.0",
    "Hardware-accurate Roland S-760 16-bit sampler instrument with SCSI & floppy folder image persistence",
    s_plugin_features_inst
};

static const clap_plugin_descriptor_t s_descriptor_fx = {
    CLAP_VERSION,
    "com.roland.s760.emulator.fx",
    "Roland S-760 Live Sampler FX",
    "Roland Emulation Team",
    "https://github.com/JefroB/s760-Emulator",
    "",
    "",
    "2.24.0",
    "Roland S-760 Live Sampling FX processor for real-time track audio capture and sound shaping",
    s_plugin_features_fx
};

const clap_plugin_descriptor_t* S760ClapPlugin::get_descriptor(bool is_fx) {
    return is_fx ? &s_descriptor_fx : &s_descriptor_inst;
}

// -----------------------------------------------------------------------------
// CLAP C Thunks
// -----------------------------------------------------------------------------
extern "C" {

static bool clap_init_thunk(const struct clap_plugin *plugin) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->init() : false;
}

static void clap_destroy_thunk(const struct clap_plugin *plugin) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    if (p) delete p;
}

static bool clap_activate_thunk(const struct clap_plugin *plugin,
                               double sample_rate,
                               uint32_t min_frames_count,
                               uint32_t max_frames_count) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->activate(sample_rate, min_frames_count, max_frames_count) : false;
}

static void clap_deactivate_thunk(const struct clap_plugin *plugin) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    if (p) p->deactivate();
}

static bool clap_start_processing_thunk(const struct clap_plugin *plugin) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->start_processing() : false;
}

static void clap_stop_processing_thunk(const struct clap_plugin *plugin) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    if (p) p->stop_processing();
}

static void clap_reset_thunk(const struct clap_plugin *plugin) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    if (p) p->reset();
}

static clap_process_status clap_process_thunk(const struct clap_plugin *plugin, const clap_process_t *process) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->process(process) : CLAP_PROCESS_ERROR;
}

static const void *clap_get_extension_thunk(const struct clap_plugin *plugin, const char *id) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->get_extension(id) : nullptr;
}

static void clap_on_main_thread_thunk(const struct clap_plugin *plugin) {
    (void)plugin;
}

static bool clap_state_save_thunk(const clap_plugin_t *plugin, const clap_ostream_t *stream) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->state_save(stream) : false;
}

static bool clap_state_load_thunk(const clap_plugin_t *plugin, const clap_istream_t *stream) {
    auto* p = static_cast<S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->state_load(stream) : false;
}

static uint32_t clap_audio_ports_count_thunk(const clap_plugin_t *plugin, bool is_input) {
    (void)plugin; (void)is_input;
    return 1; // 1 stereo in, 1 stereo out
}

static bool clap_audio_ports_get_thunk(const clap_plugin_t *plugin, uint32_t index, bool is_input, clap_audio_port_info_t *info) {
    (void)plugin;
    if (index != 0 || !info) return false;
    info->id = is_input ? 0 : 1;
    info->flags = CLAP_AUDIO_PORT_IS_MAIN;
    info->channel_count = 2;
    info->port_type = CLAP_PORT_STEREO;
    info->in_place_pair = is_input ? 1 : 0;
    std::strncpy(info->name, is_input ? "Stereo In" : "Stereo Out", sizeof(info->name) - 1);
    return true;
}

// --- clap.gui thunks (task 3.6) ---------------------------------------------
static bool clap_gui_is_api_supported_thunk(const clap_plugin_t *plugin, const char *api, bool is_floating) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_is_api_supported(api, is_floating) : false;
}
static bool clap_gui_get_preferred_api_thunk(const clap_plugin_t *plugin, const char **api, bool *is_floating) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_get_preferred_api(api, is_floating) : false;
}
static bool clap_gui_create_thunk(const clap_plugin_t *plugin, const char *api, bool is_floating) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_create(api, is_floating) : false;
}
static void clap_gui_destroy_thunk(const clap_plugin_t *plugin) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    if (p) p->gui_destroy();
}
static bool clap_gui_set_scale_thunk(const clap_plugin_t *plugin, double scale) {
    (void)plugin; (void)scale; return true;
}
static bool clap_gui_get_size_thunk(const clap_plugin_t *plugin, uint32_t *width, uint32_t *height) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_get_size(width, height) : false;
}
static bool clap_gui_can_resize_thunk(const clap_plugin_t *plugin) {
    (void)plugin; return true;
}
static bool clap_gui_get_resize_hints_thunk(const clap_plugin_t *plugin, clap_gui_resize_hints_t *hints) {
    (void)plugin;
    if (!hints) return false;
    hints->can_resize_horizontally = true;
    hints->can_resize_vertically = true;
    hints->preserve_aspect_ratio = false;
    hints->aspect_ratio_width = 0;
    hints->aspect_ratio_height = 0;
    return true;
}
static bool clap_gui_adjust_size_thunk(const clap_plugin_t *plugin, uint32_t *width, uint32_t *height) {
    (void)plugin; (void)width; (void)height; return true;
}
static bool clap_gui_set_size_thunk(const clap_plugin_t *plugin, uint32_t width, uint32_t height) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_set_size(width, height) : false;
}
static bool clap_gui_set_parent_thunk(const clap_plugin_t *plugin, const clap_window_t *window) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_set_parent(window) : false;
}
static bool clap_gui_set_transient_thunk(const clap_plugin_t *plugin, const clap_window_t *window) {
    (void)plugin; (void)window; return false; // embedded editor; not floating
}
static void clap_gui_suggest_title_thunk(const clap_plugin_t *plugin, const char *title) {
    (void)plugin; (void)title;
}
static bool clap_gui_show_thunk(const clap_plugin_t *plugin) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_show() : false;
}
static bool clap_gui_hide_thunk(const clap_plugin_t *plugin) {
    auto* p = static_cast<s760::S760ClapPlugin*>(plugin->plugin_data);
    return p ? p->gui_hide() : false;
}

} // extern "C"

// -----------------------------------------------------------------------------
// S760ClapPlugin Implementation
// -----------------------------------------------------------------------------

S760ClapPlugin::S760ClapPlugin(const clap_host_t* host, bool is_fx)
    : m_clap_host(host), m_is_fx(is_fx), m_bridge(select_bridge_host()) {
    m_plugin.desc = is_fx ? &s_descriptor_fx : &s_descriptor_inst;
    m_plugin.plugin_data = this;
    m_plugin.init = clap_init_thunk;
    m_plugin.destroy = clap_destroy_thunk;
    m_plugin.activate = clap_activate_thunk;
    m_plugin.deactivate = clap_deactivate_thunk;
    m_plugin.start_processing = clap_start_processing_thunk;
    m_plugin.stop_processing = clap_stop_processing_thunk;
    m_plugin.reset = clap_reset_thunk;
    m_plugin.process = clap_process_thunk;
    m_plugin.get_extension = clap_get_extension_thunk;
    m_plugin.on_main_thread = clap_on_main_thread_thunk;

    m_state_ext.save = clap_state_save_thunk;
    m_state_ext.load = clap_state_load_thunk;

    m_audio_ports_ext.count = clap_audio_ports_count_thunk;
    m_audio_ports_ext.get = clap_audio_ports_get_thunk;

    m_gui_ext.is_api_supported  = clap_gui_is_api_supported_thunk;
    m_gui_ext.get_preferred_api = clap_gui_get_preferred_api_thunk;
    m_gui_ext.create            = clap_gui_create_thunk;
    m_gui_ext.destroy           = clap_gui_destroy_thunk;
    m_gui_ext.set_scale         = clap_gui_set_scale_thunk;
    m_gui_ext.get_size          = clap_gui_get_size_thunk;
    m_gui_ext.can_resize        = clap_gui_can_resize_thunk;
    m_gui_ext.get_resize_hints  = clap_gui_get_resize_hints_thunk;
    m_gui_ext.adjust_size       = clap_gui_adjust_size_thunk;
    m_gui_ext.set_size          = clap_gui_set_size_thunk;
    m_gui_ext.set_parent        = clap_gui_set_parent_thunk;
    m_gui_ext.set_transient     = clap_gui_set_transient_thunk;
    m_gui_ext.suggest_title     = clap_gui_suggest_title_thunk;
    m_gui_ext.show              = clap_gui_show_thunk;
    m_gui_ext.hide              = clap_gui_hide_thunk;

    m_scratch_left.resize(2048, 0.0f);
    m_scratch_right.resize(2048, 0.0f);
}

// -----------------------------------------------------------------------------
//  Backend selection (mame-live-backend task 9.3, Requirements 1.2/7.1/7.3).
//  Called from the constructor's initializer list to decide which IS760Host the
//  Bridge is driven from. Keeps the Core path byte-for-byte identical: only when
//  the selector resolves+inits the MAME backend does the Bridge get the MAME
//  host; otherwise the Bridge borrows the concrete &m_host (default Core).
// -----------------------------------------------------------------------------
IS760Host* S760ClapPlugin::select_bridge_host() {
    // No runtime value supplied here -> use the CMake build default (Core unless
    // S760_BACKEND=mame). The selector constructs + init()'s the chosen backend.
    BackendSelectionResult sel = select_backend();

    if (sel.active == BackendKind::Mame && sel.host) {
        // MAME selected and available: own it and drive the Bridge from it. The
        // concrete m_host stays constructed (unused by the Bridge) so all
        // Core-specific plugin API still compiles.
        m_selected_host = std::move(sel.host);
        return m_selected_host.get();
    }

    if (sel.bothUnavailable) {
        // Neither backend available: surface the observable error (R7.5) but do
        // not crash. Fall back to the concrete Core host; the Bridge tolerates
        // even a null host.
        std::cerr << "[S760ClapPlugin] backend selection failed: " << sel.error
                  << " (using Core host)" << std::endl;
    }
    // Core selected/defaulted, or MAME fell back to Core: preserve the existing
    // behavior exactly by driving the Bridge from the concrete Core host.
    return &m_host;
}

S760ClapPlugin::~S760ClapPlugin() {
    if (m_editor) m_editor->close();
    deactivate();
}

bool S760ClapPlugin::init() {
    return true;
}

void S760ClapPlugin::destroy() {
    deactivate();
}

bool S760ClapPlugin::activate(double sample_rate, uint32_t min_frames, uint32_t max_frames) {
    (void)min_frames;
    m_sample_rate = sample_rate;
    m_host.set_target_sample_rate(sample_rate);
    size_t scratch_size = std::max<size_t>(2048, max_frames);
    m_scratch_left.resize(scratch_size, 0.0f);
    m_scratch_right.resize(scratch_size, 0.0f);
    m_is_active = true;
    return true;
}

void S760ClapPlugin::deactivate() {
    m_is_active = false;
    m_is_processing = false;
    m_host.get_drive_manager().flush_all();
}

bool S760ClapPlugin::start_processing() {
    m_is_processing = true;
    return true;
}

void S760ClapPlugin::stop_processing() {
    m_is_processing = false;
    m_host.get_drive_manager().flush_all();
}

void S760ClapPlugin::reset() {
    m_host.reset();
}

void S760ClapPlugin::handle_events(const clap_input_events_t* in_events) {
    if (!in_events || !in_events->size) return;

    uint32_t num_events = in_events->size(in_events);
    for (uint32_t i = 0; i < num_events; ++i) {
        const auto* hdr = in_events->get(in_events, i);
        if (!hdr || hdr->space_id != CLAP_CORE_EVENT_SPACE_ID) continue;

        if (hdr->type == CLAP_EVENT_NOTE_ON) {
            const auto* ev = reinterpret_cast<const clap_event_note_t*>(hdr);
            uint8_t ch = static_cast<uint8_t>(ev->channel & 0x0F);
            uint8_t key = static_cast<uint8_t>(ev->key & 0x7F);
            uint8_t vel = static_cast<uint8_t>(std::clamp(static_cast<int>(ev->velocity * 127.0), 0, 127));

            uint8_t midi_msg[3] = { static_cast<uint8_t>(0x90 | ch), key, vel };
            m_host.send_midi_message(midi_msg, 3);
        } else if (hdr->type == CLAP_EVENT_NOTE_OFF) {
            const auto* ev = reinterpret_cast<const clap_event_note_t*>(hdr);
            uint8_t ch = static_cast<uint8_t>(ev->channel & 0x0F);
            uint8_t key = static_cast<uint8_t>(ev->key & 0x7F);
            uint8_t vel = static_cast<uint8_t>(std::clamp(static_cast<int>(ev->velocity * 127.0), 0, 127));

            uint8_t midi_msg[3] = { static_cast<uint8_t>(0x80 | ch), key, vel };
            m_host.send_midi_message(midi_msg, 3);
        } else if (hdr->type == CLAP_EVENT_MIDI) {
            const auto* ev = reinterpret_cast<const clap_event_midi_t*>(hdr);
            uint8_t status = ev->data[0];
            size_t msg_len = 3;
            if ((status & 0xF0) == 0xC0 || (status & 0xF0) == 0xD0) {
                msg_len = 2; // Program Change / Channel Pressure
            } else if (status >= 0xF8) {
                msg_len = 1; // Realtime system message
            }
            m_host.send_midi_message(ev->data, msg_len);
        }
    }
}

clap_process_status S760ClapPlugin::process(const clap_process_t* process) {
    if (!process || process->frames_count == 0) {
        return CLAP_PROCESS_CONTINUE;
    }

    // 1. Process MIDI & Note In Events
    handle_events(process->in_events);

    uint32_t needed_frames = process->frames_count;

    // 2. Feed Audio Inputs to Live Sampler Recorder
    if (process->audio_inputs_count > 0 && process->audio_inputs) {
        const auto& in_buf = process->audio_inputs[0];
        if (in_buf.data32) {
            const float* in_l = in_buf.data32[0];
            const float* in_r = (in_buf.channel_count >= 2 && in_buf.data32[1]) ? in_buf.data32[1] : in_l;
            m_host.feed_audio_input(in_l, in_r, needed_frames);
        }
    }

    // 3. Ensure enough audio frames in host buffer with bounded iteration loop
    constexpr int MAX_EMULATOR_FRAMES_PER_BLOCK = 4;
    int emu_ticks = 0;
    while (m_host.is_system_running() && 
           m_host.get_audio_stats().available_frames < needed_frames &&
           emu_ticks < MAX_EMULATOR_FRAMES_PER_BLOCK) {
        m_host.run_frame();
        emu_ticks++;
    }

    // 4. Read audio from S760 host into scratch buffers
    if (m_scratch_left.size() < needed_frames) {
        needed_frames = static_cast<uint32_t>(m_scratch_left.size());
    }

    m_host.read_audio_frames(m_scratch_left.data(), m_scratch_right.data(), needed_frames);

    // 5. Apply pass-through monitoring if FX or recording/armed
    if (m_is_fx || m_host.get_recorder().is_recording() || m_host.get_recorder().is_armed()) {
        if (process->audio_inputs_count > 0 && process->audio_inputs) {
            const auto& in_buf = process->audio_inputs[0];
            if (in_buf.data32) {
                const float* in_l = in_buf.data32[0];
                const float* in_r = (in_buf.channel_count >= 2 && in_buf.data32[1]) ? in_buf.data32[1] : in_l;
                if (in_l) {
                    for (uint32_t i = 0; i < needed_frames; ++i) {
                        m_scratch_left[i] += in_l[i];
                    }
                }
                if (in_r) {
                    for (uint32_t i = 0; i < needed_frames; ++i) {
                        m_scratch_right[i] += in_r[i];
                    }
                }
            }
        }
    }

    // 6. Copy to DAW output buffers
    if (process->audio_outputs_count > 0 && process->audio_outputs) {
        auto& out_buf = process->audio_outputs[0];
        if (out_buf.data32 && out_buf.channel_count >= 2) {
            std::memcpy(out_buf.data32[0], m_scratch_left.data(), needed_frames * sizeof(float));
            std::memcpy(out_buf.data32[1], m_scratch_right.data(), needed_frames * sizeof(float));
        } else if (out_buf.data32 && out_buf.channel_count == 1) {
            // Mono mixdown
            for (uint32_t i = 0; i < needed_frames; ++i) {
                out_buf.data32[0][i] = (m_scratch_left[i] + m_scratch_right[i]) * 0.5f;
            }
        }
    }

    return CLAP_PROCESS_CONTINUE;
}

const void* S760ClapPlugin::get_extension(const char* id) {
    if (!id) return nullptr;
    if (std::strcmp(id, CLAP_EXT_STATE) == 0) {
        return &m_state_ext;
    }
    if (std::strcmp(id, CLAP_EXT_AUDIO_PORTS) == 0) {
        return &m_audio_ports_ext;
    }
    if (std::strcmp(id, CLAP_EXT_GUI) == 0) {
        return &m_gui_ext;
    }
    return nullptr;
}

// -----------------------------------------------------------------------------
//  clap.gui editor (task 3.6) — WebView-backed React editor on m_bridge.
// -----------------------------------------------------------------------------
static const char* clap_native_window_api() {
#if defined(_WIN32)
    return CLAP_WINDOW_API_WIN32;
#elif defined(__APPLE__)
    return CLAP_WINDOW_API_COCOA;
#else
    return CLAP_WINDOW_API_X11;
#endif
}

bool S760ClapPlugin::gui_is_api_supported(const char* api, bool is_floating) {
    if (is_floating || !api) return false; // embedded editor only
    return std::strcmp(api, clap_native_window_api()) == 0;
}

bool S760ClapPlugin::gui_get_preferred_api(const char** api, bool* is_floating) {
    if (!api || !is_floating) return false;
    *api = clap_native_window_api();
    *is_floating = false;
    return true;
}

bool S760ClapPlugin::gui_create(const char* api, bool is_floating) {
    if (!gui_is_api_supported(api, is_floating)) return false;
    if (!m_editor) m_editor = std::make_unique<S760EditorController>(&m_bridge);
    m_gui_created = true;
    return true;
}

void S760ClapPlugin::gui_destroy() {
    if (m_editor) m_editor->close();
    m_gui_created = false;
}

bool S760ClapPlugin::gui_get_size(uint32_t* width, uint32_t* height) {
    if (!width || !height) return false;
    WebViewSize sz = m_editor ? m_editor->size() : WebViewSize{};
    *width = sz.width;
    *height = sz.height;
    return true;
}

bool S760ClapPlugin::gui_set_size(uint32_t width, uint32_t height) {
    if (m_editor) m_editor->set_size(WebViewSize{width, height});
    return true;
}

bool S760ClapPlugin::gui_set_parent(const clap_window_t* window) {
    if (!m_gui_created || !window) return false;
    if (!m_editor) m_editor = std::make_unique<S760EditorController>(&m_bridge);
    uint32_t w = 0, h = 0;
    gui_get_size(&w, &h);
    return m_editor->open(window->ptr, WebViewSize{w, h});
}

bool S760ClapPlugin::gui_show() {
    // The embedded view is shown by the DAW once parented; nothing extra needed
    // for the WebView host. Return true if the editor exists.
    return m_editor != nullptr;
}

bool S760ClapPlugin::gui_hide() {
    return m_editor != nullptr;
}

bool S760ClapPlugin::state_save(const clap_ostream_t* stream) {
    if (!stream || !stream->write) return false;

    // Header Tag
    const char magic[] = "S760CLAP";
    if (stream->write(stream, magic, 8) != 8) return false;

    // Write Floppy path
    auto f_stat = m_host.get_drive_manager().get_floppy_status();
    uint32_t f_len = static_cast<uint32_t>(f_stat.file_path.size());
    if (stream->write(stream, &f_len, 4) != 4) return false;
    if (f_len > 0) {
        if (stream->write(stream, f_stat.file_path.data(), f_len) != static_cast<int64_t>(f_len)) return false;
    }

    // Write SCSI paths (IDs 0..6)
    for (int i = 0; i < 7; ++i) {
        auto scsi_stat = m_host.get_drive_manager().get_scsi_status(i);
        uint32_t s_len = static_cast<uint32_t>(scsi_stat.file_path.size());
        if (stream->write(stream, &s_len, 4) != 4) return false;
        if (s_len > 0) {
            if (stream->write(stream, scsi_stat.file_path.data(), s_len) != static_cast<int64_t>(s_len)) return false;
        }
    }

    // Write Core Savestate
    auto state_data = m_host.save_state();
    uint32_t state_len = static_cast<uint32_t>(state_data.size());
    if (stream->write(stream, &state_len, 4) != 4) return false;
    if (state_len > 0) {
        if (stream->write(stream, state_data.data(), state_len) != static_cast<int64_t>(state_len)) return false;
    }

    return true;
}

bool S760ClapPlugin::state_load(const clap_istream_t* stream) {
    if (!stream || !stream->read) return false;

    char magic[8] = {0};
    if (stream->read(stream, magic, 8) != 8 || std::memcmp(magic, "S760CLAP", 8) != 0) {
        return false;
    }

    // Read Floppy path into temporary
    std::string f_path;
    uint32_t f_len = 0;
    if (stream->read(stream, &f_len, 4) != 4 || f_len > 4096) return false;
    if (f_len > 0) {
        f_path.resize(f_len);
        if (stream->read(stream, f_path.data(), f_len) != static_cast<int64_t>(f_len)) return false;
    }

    // Read SCSI paths into temporaries
    std::string s_paths[7];
    for (int i = 0; i < 7; ++i) {
        uint32_t s_len = 0;
        if (stream->read(stream, &s_len, 4) != 4 || s_len > 4096) return false;
        if (s_len > 0) {
            s_paths[i].resize(s_len);
            if (stream->read(stream, s_paths[i].data(), s_len) != static_cast<int64_t>(s_len)) return false;
        }
    }

    // Read Core Savestate into temporary
    std::vector<uint8_t> state_data;
    uint32_t state_len = 0;
    if (stream->read(stream, &state_len, 4) != 4 || state_len > 64 * 1024 * 1024) return false;
    if (state_len > 0) {
        state_data.resize(state_len);
        if (stream->read(stream, state_data.data(), state_len) != static_cast<int64_t>(state_len)) return false;
    }

    // All chunks read and verified successfully - apply atomically
    if (!f_path.empty()) {
        m_host.get_drive_manager().mount_floppy(f_path);
    }
    for (int i = 0; i < 7; ++i) {
        if (!s_paths[i].empty()) {
            m_host.get_drive_manager().mount_scsi_device(i, s_paths[i], DeviceType::HardDisk_SCSI);
        }
    }
    if (!state_data.empty()) {
        m_host.load_state(state_data);
    }

    return true;
}

} // namespace s760

// -----------------------------------------------------------------------------
// CLAP Plugin Entry & Factory
// -----------------------------------------------------------------------------
extern "C" {

static uint32_t clap_factory_get_plugin_count(const struct clap_plugin_factory *factory) {
    (void)factory;
    return 2;
}

static const clap_plugin_descriptor_t *clap_factory_get_plugin_descriptor(
    const struct clap_plugin_factory *factory, uint32_t index) {
    (void)factory;
    if (index == 0) return s760::S760ClapPlugin::get_descriptor(false);
    if (index == 1) return s760::S760ClapPlugin::get_descriptor(true);
    return nullptr;
}

static const clap_plugin_t *clap_factory_create_plugin(
    const struct clap_plugin_factory *factory, const clap_host_t *host, const char *plugin_id) {
    (void)factory;
    if (!plugin_id) return nullptr;
    if (std::strcmp(plugin_id, s760::S760ClapPlugin::get_descriptor(false)->id) == 0) {
        auto* plug = new s760::S760ClapPlugin(host, false);
        return plug->get_clap_plugin();
    }
    if (std::strcmp(plugin_id, s760::S760ClapPlugin::get_descriptor(true)->id) == 0) {
        auto* plug = new s760::S760ClapPlugin(host, true);
        return plug->get_clap_plugin();
    }
    return nullptr;
}

static const clap_plugin_factory_t s_clap_factory = {
    clap_factory_get_plugin_count,
    clap_factory_get_plugin_descriptor,
    clap_factory_create_plugin
};

static bool clap_entry_init(const char *plugin_path) {
    (void)plugin_path;
    return true;
}

static void clap_entry_deinit(void) {}

static const void *clap_entry_get_factory(const char *factory_id) {
    if (factory_id && std::strcmp(factory_id, CLAP_PLUGIN_FACTORY_ID) == 0) {
        return &s_clap_factory;
    }
    return nullptr;
}

CLAP_EXPORT const clap_plugin_entry_t clap_entry = {
    CLAP_VERSION,
    clap_entry_init,
    clap_entry_deinit,
    clap_entry_get_factory
};

} // extern "C"
