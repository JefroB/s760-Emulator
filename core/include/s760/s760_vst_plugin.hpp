#pragma once

#include "s760/vst_defs.h"
#include "s760/s760_libretro_host.hpp"
#include "s760/s760_backend_selector.hpp"
#include "s760/s760_bridge.hpp"
#include "s760/s760_webview_host.hpp"

#include <memory>
#include <vector>
#include <string>

namespace s760 {

class S760VstPlugin {
public:
    explicit S760VstPlugin(audioMasterCallback audioMaster, bool is_fx = false);
    ~S760VstPlugin();

    AEffect* get_aeffect() { return &m_effect; }

    intptr_t dispatcher(int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt);
    void process_replacing(float** inputs, float** outputs, int32_t sample_frames);
    void set_parameter(int32_t index, float value);
    float get_parameter(int32_t index);

    S760LibretroHost& get_host() { return m_host; }
    S760Bridge& get_bridge() { return m_bridge; }

private:
    AEffect m_effect;
    audioMasterCallback m_audio_master = nullptr;
    // Concrete Core backend. KEPT as a value member so all Core-specific
    // lifecycle/audio/savestate calls keep compiling and behaving exactly as
    // before (default Core path stays byte-for-byte identical on the wire).
    S760LibretroHost m_host;
    // Backend selector's chosen host (mame-live-backend task 9.3, R7.1).
    // Declared BEFORE m_bridge so it outlives the Bridge, which only borrows the
    // host pointer. Owns the MAME backend when selected; stays null for Core.
    std::unique_ptr<IS760Host> m_selected_host;
    S760Bridge m_bridge;                            // in-process UI bridge (3.2)
    std::unique_ptr<S760EditorController> m_editor; // WebView editor (3.6)
    ERect m_edit_rect{};                            // effEditGetRect storage
    bool m_is_fx = false;

    double m_sample_rate = 44100.0;
    int32_t m_block_size = 512;
    float m_master_gain = 1.0f;

    std::vector<float> m_scratch_left;
    std::vector<float> m_scratch_right;
    std::vector<uint8_t> m_chunk_data; // State chunk for effGetChunk

    void handle_vst_events(const VstEvents* events);
    void build_state_chunk();
    bool restore_state_chunk(const uint8_t* data, size_t size);

    // Run the backend selector and decide which IS760Host the Bridge is driven
    // from (mame-live-backend task 9.3). Called from the constructor's
    // initializer list BEFORE m_bridge. Returns the MAME host when selected+
    // available (owned by m_selected_host), otherwise &m_host (default Core).
    IS760Host* select_bridge_host();
};

} // namespace s760
