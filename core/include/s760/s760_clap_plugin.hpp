#pragma once

#include "s760/clap_defs.h"
#include "s760/s760_libretro_host.hpp"
#include "s760/s760_backend_selector.hpp"
#include "s760/s760_bridge.hpp"
#include "s760/s760_webview_host.hpp"

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

    // --- clap.gui editor (task 3.6) -----------------------------------------
    // The WebView-backed React editor, wired to this plugin's in-process bridge.
    bool gui_is_api_supported(const char* api, bool is_floating);
    bool gui_get_preferred_api(const char** api, bool* is_floating);
    bool gui_create(const char* api, bool is_floating);
    void gui_destroy();
    bool gui_get_size(uint32_t* width, uint32_t* height);
    bool gui_set_size(uint32_t width, uint32_t height);
    bool gui_set_parent(const clap_window_t* window);
    bool gui_show();
    bool gui_hide();

    S760LibretroHost& get_host() { return m_host; }
    S760Bridge& get_bridge() { return m_bridge; }
    bool is_fx() const { return m_is_fx; }

    static const clap_plugin_descriptor_t* get_descriptor(bool is_fx = false);

private:
    const clap_host_t* m_clap_host = nullptr;
    clap_plugin_t m_plugin;
    clap_plugin_state_t m_state_ext;
    clap_plugin_audio_ports_t m_audio_ports_ext;
    clap_plugin_gui_t m_gui_ext;

    // The concrete Core backend. KEPT as a value member so all Core-specific
    // lifecycle/audio/savestate calls the plugin makes (load_core/load_system,
    // run_frame, feed_audio_input, read_audio_frames, save_state/load_state,
    // reset, set_target_sample_rate, is_system_running, get_audio_stats,
    // get_recorder, get_drive_manager) keep compiling and behaving EXACTLY as
    // before — the default Core path stays byte-for-byte identical on the wire.
    S760LibretroHost m_host;
    // The backend selector's chosen host (mame-live-backend task 9.3,
    // Requirement 7.1). Declared BEFORE m_bridge so it is constructed first and
    // outlives the Bridge, which only BORROWS the host pointer. When the
    // selector resolves+inits the MAME backend, this owns it and the Bridge is
    // driven from it; when the selection is Core (the default when S760_BACKEND
    // is unset/core), this stays null and the Bridge is driven from &m_host.
    std::unique_ptr<IS760Host> m_selected_host;
    S760Bridge m_bridge;                            // in-process UI bridge (3.2)
    std::unique_ptr<S760EditorController> m_editor; // WebView editor (3.6)
    bool m_gui_created = false;
    double m_sample_rate = 44100.0;
    bool m_is_active = false;
    bool m_is_processing = false;
    bool m_is_fx = false;

    // Temporary processing buffers
    std::vector<float> m_scratch_left;
    std::vector<float> m_scratch_right;

    void handle_events(const clap_input_events_t* in_events);

    // Run the backend selector and decide which IS760Host the Bridge is driven
    // from (mame-live-backend task 9.3). Called from the constructor's
    // initializer list BEFORE m_bridge is constructed. When the selector
    // resolves+inits the MAME backend, this moves it into m_selected_host and
    // returns m_selected_host.get(); otherwise (Core selected/defaulted, or MAME
    // unavailable and falling back to Core) it returns &m_host so the default
    // Core path is preserved byte-for-byte. If the selector reports BOTH
    // backends unavailable (host null), the failure is surfaced to stderr and
    // &m_host is still used (the Bridge also tolerates a null host) so the
    // plugin never crashes (Requirement 7.5).
    IS760Host* select_bridge_host();
};

} // namespace s760
