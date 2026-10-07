#pragma once

#include "s760/clap_defs.h"
#include "s760/s760_libretro_host.hpp"

#include <memory>
#include <string>
#include <vector>

namespace s760 {

class S760ClapPlugin {
public:
    explicit S760ClapPlugin(const clap_host_t* host, bool is_fx = false);
    ~S760ClapPlugin();

    const clap_plugin_t* get_clap_plugin() const { return &m_plugin; }

    bool init();
    void destroy();
    bool activate(double sample_rate, uint32_t min_frames, uint32_t max_frames);
    void deactivate();
    bool start_processing();
    void stop_processing();
    void reset();
    clap_process_status process(const clap_process_t* process);
    const void* get_extension(const char* id);

    // State Serialization
    bool state_save(const clap_ostream_t* stream);
    bool state_load(const clap_istream_t* stream);

    S760LibretroHost& get_host() { return m_host; }
    bool is_fx() const { return m_is_fx; }

    static const clap_plugin_descriptor_t* get_descriptor(bool is_fx = false);

private:
    const clap_host_t* m_clap_host = nullptr;
    clap_plugin_t m_plugin;
    clap_plugin_state_t m_state_ext;
    clap_plugin_audio_ports_t m_audio_ports_ext;

    S760LibretroHost m_host;
    double m_sample_rate = 44100.0;
    bool m_is_active = false;
    bool m_is_processing = false;
    bool m_is_fx = false;

    // Temporary processing buffers
    std::vector<float> m_scratch_left;
    std::vector<float> m_scratch_right;

    void handle_events(const clap_input_events_t* in_events);
};

} // namespace s760
