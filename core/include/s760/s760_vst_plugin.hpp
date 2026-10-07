#pragma once

#include "s760/vst_defs.h"
#include "s760/s760_libretro_host.hpp"

#include <vector>
#include <string>

namespace s760 {

class S760VstPlugin {
public:
    explicit S760VstPlugin(audioMasterCallback audioMaster);
    ~S760VstPlugin();

    AEffect* get_aeffect() { return &m_effect; }

    intptr_t dispatcher(int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt);
    void process_replacing(float** inputs, float** outputs, int32_t sample_frames);
    void set_parameter(int32_t index, float value);
    float get_parameter(int32_t index);

    S760LibretroHost& get_host() { return m_host; }

private:
    AEffect m_effect;
    audioMasterCallback m_audio_master = nullptr;
    S760LibretroHost m_host;

    double m_sample_rate = 44100.0;
    int32_t m_block_size = 512;
    float m_master_gain = 1.0f;

    std::vector<float> m_scratch_left;
    std::vector<float> m_scratch_right;
    std::vector<uint8_t> m_chunk_data; // State chunk for effGetChunk

    void handle_vst_events(const VstEvents* events);
    void build_state_chunk();
    bool restore_state_chunk(const uint8_t* data, size_t size);
};

} // namespace s760
