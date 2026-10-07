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

static const char* const s_plugin_features[] = {
    "instrument",
    "sampler",
    "synthesizer",
    "stereo",
    nullptr
};

static const clap_plugin_descriptor_t s_descriptor = {
    CLAP_VERSION,
    "com.roland.s760.emulator",
    "Roland S-760 Digital Sampler",
    "Roland Emulation Team",
    "https://github.com/JefroB/s760-Emulator",
    "",
    "",
    "2.24.0",
    "Hardware-accurate Roland S-760 16-bit sampler instrument with SCSI & floppy folder image persistence",
    s_plugin_features
};

const clap_plugin_descriptor_t* S760ClapPlugin::get_descriptor() {
    return &s_descriptor;
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

} // extern "C"

// -----------------------------------------------------------------------------
// S760ClapPlugin Implementation
// -----------------------------------------------------------------------------

S760ClapPlugin::S760ClapPlugin(const clap_host_t* host)
    : m_clap_host(host) {
    m_plugin.desc = &s_descriptor;
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

    m_scratch_left.resize(2048, 0.0f);
    m_scratch_right.resize(2048, 0.0f);
}

S760ClapPlugin::~S760ClapPlugin() {
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
            m_host.send_midi_message(ev->data, 3);
        }
    }
}

clap_process_status S760ClapPlugin::process(const clap_process_t* process) {
    if (!process || process->frames_count == 0) {
        return CLAP_PROCESS_CONTINUE;
    }

    // 1. Process MIDI & Note In Events
    handle_events(process->in_events);

    // 2. Ensure enough audio frames in host buffer
    uint32_t needed_frames = process->frames_count;
    while (m_host.is_system_running() && m_host.get_audio_stats().available_frames < needed_frames) {
        m_host.run_frame();
    }

    // 3. Read audio from S760 host into scratch buffers
    if (m_scratch_left.size() < needed_frames) {
        m_scratch_left.resize(needed_frames);
        m_scratch_right.resize(needed_frames);
    }

    m_host.read_audio_frames(m_scratch_left.data(), m_scratch_right.data(), needed_frames);

    // 4. Copy to DAW output buffers
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
    if (id && std::strcmp(id, CLAP_EXT_STATE) == 0) {
        return &m_state_ext;
    }
    return nullptr;
}

bool S760ClapPlugin::state_save(const clap_ostream_t* stream) {
    if (!stream || !stream->write) return false;

    // Header Tag
    const char magic[] = "S760CLAP";
    stream->write(stream, magic, sizeof(magic) - 1);

    // Write Floppy path
    auto f_stat = m_host.get_drive_manager().get_floppy_status();
    uint32_t f_len = static_cast<uint32_t>(f_stat.file_path.size());
    stream->write(stream, &f_len, 4);
    if (f_len > 0) {
        stream->write(stream, f_stat.file_path.data(), f_len);
    }

    // Write SCSI paths (IDs 0..6)
    for (int i = 0; i < 7; ++i) {
        auto scsi_stat = m_host.get_drive_manager().get_scsi_status(i);
        uint32_t s_len = static_cast<uint32_t>(scsi_stat.file_path.size());
        stream->write(stream, &s_len, 4);
        if (s_len > 0) {
            stream->write(stream, scsi_stat.file_path.data(), s_len);
        }
    }

    // Write Core Savestate
    auto state_data = m_host.save_state();
    uint32_t state_len = static_cast<uint32_t>(state_data.size());
    stream->write(stream, &state_len, 4);
    if (state_len > 0) {
        stream->write(stream, state_data.data(), state_len);
    }

    return true;
}

bool S760ClapPlugin::state_load(const clap_istream_t* stream) {
    if (!stream || !stream->read) return false;

    char magic[8] = {0};
    if (stream->read(stream, magic, 8) != 8 || std::memcmp(magic, "S760CLAP", 8) != 0) {
        return false;
    }

    // Read Floppy path
    uint32_t f_len = 0;
    if (stream->read(stream, &f_len, 4) != 4) return false;
    if (f_len > 0 && f_len < 4096) {
        std::string f_path(f_len, '\0');
        stream->read(stream, f_path.data(), f_len);
        m_host.get_drive_manager().mount_floppy(f_path);
    }

    // Read SCSI paths
    for (int i = 0; i < 7; ++i) {
        uint32_t s_len = 0;
        if (stream->read(stream, &s_len, 4) != 4) return false;
        if (s_len > 0 && s_len < 4096) {
            std::string s_path(s_len, '\0');
            stream->read(stream, s_path.data(), s_len);
            m_host.get_drive_manager().mount_scsi_device(i, s_path, DeviceType::HardDisk_SCSI);
        }
    }

    // Read Core Savestate
    uint32_t state_len = 0;
    if (stream->read(stream, &state_len, 4) != 4) return false;
    if (state_len > 0 && state_len < 64 * 1024 * 1024) {
        std::vector<uint8_t> state_data(state_len);
        stream->read(stream, state_data.data(), state_len);
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
    return 1;
}

static const clap_plugin_descriptor_t *clap_factory_get_plugin_descriptor(
    const struct clap_plugin_factory *factory, uint32_t index) {
    (void)factory;
    return (index == 0) ? s760::S760ClapPlugin::get_descriptor() : nullptr;
}

static const clap_plugin_t *clap_factory_create_plugin(
    const struct clap_plugin_factory *factory, const clap_host_t *host, const char *plugin_id) {
    (void)factory;
    if (plugin_id && std::strcmp(plugin_id, s760::S760ClapPlugin::get_descriptor()->id) == 0) {
        auto* plug = new s760::S760ClapPlugin(host);
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
