#include "s760/s760_vst_plugin.hpp"

#include <cstring>
#include <algorithm>
#include <iostream>

#if defined(_WIN32)
#define VST_EXPORT __declspec(dllexport)
#else
#define VST_EXPORT __attribute__((visibility("default")))
#endif

namespace s760 {

// -----------------------------------------------------------------------------
// VST C Thunks
// -----------------------------------------------------------------------------
extern "C" {

static intptr_t vst_dispatcher_thunk(AEffect* effect, int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt) {
    if (!effect || !effect->user) return 0;
    auto* plugin = static_cast<S760VstPlugin*>(effect->user);
    return plugin->dispatcher(opcode, index, value, ptr, opt);
}

static void vst_process_replacing_thunk(AEffect* effect, float** inputs, float** outputs, int32_t sample_frames) {
    if (!effect || !effect->user) return;
    auto* plugin = static_cast<S760VstPlugin*>(effect->user);
    plugin->process_replacing(inputs, outputs, sample_frames);
}

static void vst_set_param_thunk(AEffect* effect, int32_t index, float parameter) {
    if (!effect || !effect->user) return;
    auto* plugin = static_cast<S760VstPlugin*>(effect->user);
    plugin->set_parameter(index, parameter);
}

static float vst_get_param_thunk(AEffect* effect, int32_t index) {
    if (!effect || !effect->user) return 0.0f;
    auto* plugin = static_cast<S760VstPlugin*>(effect->user);
    return plugin->get_parameter(index);
}

} // extern "C"

// -----------------------------------------------------------------------------
// S760VstPlugin Implementation
// -----------------------------------------------------------------------------

S760VstPlugin::S760VstPlugin(audioMasterCallback audioMaster)
    : m_audio_master(audioMaster) {
    std::memset(&m_effect, 0, sizeof(m_effect));

    m_effect.magic = VST_MAGIC;
    m_effect.dispatcher = vst_dispatcher_thunk;
    m_effect.process = vst_process_replacing_thunk;
    m_effect.processReplacing = vst_process_replacing_thunk;
    m_effect.setParameter = vst_set_param_thunk;
    m_effect.getParameter = vst_get_param_thunk;

    m_effect.numPrograms = 1;
    m_effect.numParams = 1; // Param 0: Master Gain
    m_effect.numInputs = 0;  // Instrument (no audio in)
    m_effect.numOutputs = 2; // Stereo audio out
    m_effect.flags = effFlagsCanReplacing | effFlagsProgramChunks | effFlagsIsSynth;
    m_effect.uniqueID = 0x53373630; // 'S760'
    m_effect.version = 2240;
    m_effect.user = this;

    m_scratch_left.resize(2048, 0.0f);
    m_scratch_right.resize(2048, 0.0f);
}

S760VstPlugin::~S760VstPlugin() {
    m_host.get_drive_manager().flush_all();
}

void S760VstPlugin::set_parameter(int32_t index, float value) {
    if (index == 0) {
        m_master_gain = std::clamp(value, 0.0f, 1.0f);
    }
}

float S760VstPlugin::get_parameter(int32_t index) {
    if (index == 0) {
        return m_master_gain;
    }
    return 0.0f;
}

void S760VstPlugin::handle_vst_events(const VstEvents* events) {
    if (!events || events->numEvents <= 0) return;

    for (int32_t i = 0; i < events->numEvents; ++i) {
        const auto* ev = events->events[i];
        if (!ev) continue;

        if (ev->type == kVstMidiType) {
            const auto* midi_ev = reinterpret_cast<const VstMidiEvent*>(ev);
            const uint8_t* bytes = reinterpret_cast<const uint8_t*>(midi_ev->midiData);
            m_host.send_midi_message(bytes, 3);
        }
    }
}

void S760VstPlugin::process_replacing(float** inputs, float** outputs, int32_t sample_frames) {
    (void)inputs;
    if (!outputs || sample_frames <= 0) return;

    uint32_t needed = static_cast<uint32_t>(sample_frames);

    // Run emulator frames to maintain audio generation
    while (m_host.is_system_running() && m_host.get_audio_stats().available_frames < needed) {
        m_host.run_frame();
    }

    if (m_scratch_left.size() < needed) {
        m_scratch_left.resize(needed);
        m_scratch_right.resize(needed);
    }

    m_host.read_audio_frames(m_scratch_left.data(), m_scratch_right.data(), needed);

    float* out_l = outputs[0];
    float* out_r = (outputs[1] != nullptr) ? outputs[1] : outputs[0];

    for (uint32_t i = 0; i < needed; ++i) {
        if (out_l) out_l[i] = m_scratch_left[i] * m_master_gain;
        if (out_r) out_r[i] = m_scratch_right[i] * m_master_gain;
    }
}

void S760VstPlugin::build_state_chunk() {
    m_chunk_data.clear();

    const char magic[] = "S760VSTP";
    m_chunk_data.insert(m_chunk_data.end(), magic, magic + 8);

    // Floppy path
    auto f_stat = m_host.get_drive_manager().get_floppy_status();
    uint32_t f_len = static_cast<uint32_t>(f_stat.file_path.size());
    const uint8_t* fl_ptr = reinterpret_cast<const uint8_t*>(&f_len);
    m_chunk_data.insert(m_chunk_data.end(), fl_ptr, fl_ptr + 4);
    if (f_len > 0) {
        m_chunk_data.insert(m_chunk_data.end(), f_stat.file_path.begin(), f_stat.file_path.end());
    }

    // SCSI paths (IDs 0..6)
    for (int i = 0; i < 7; ++i) {
        auto scsi_stat = m_host.get_drive_manager().get_scsi_status(i);
        uint32_t s_len = static_cast<uint32_t>(scsi_stat.file_path.size());
        const uint8_t* sl_ptr = reinterpret_cast<const uint8_t*>(&s_len);
        m_chunk_data.insert(m_chunk_data.end(), sl_ptr, sl_ptr + 4);
        if (s_len > 0) {
            m_chunk_data.insert(m_chunk_data.end(), scsi_stat.file_path.begin(), scsi_stat.file_path.end());
        }
    }

    // Core savestate
    auto state = m_host.save_state();
    uint32_t state_len = static_cast<uint32_t>(state.size());
    const uint8_t* st_ptr = reinterpret_cast<const uint8_t*>(&state_len);
    m_chunk_data.insert(m_chunk_data.end(), st_ptr, st_ptr + 4);
    if (state_len > 0) {
        m_chunk_data.insert(m_chunk_data.end(), state.begin(), state.end());
    }
}

bool S760VstPlugin::restore_state_chunk(const uint8_t* data, size_t size) {
    if (!data || size < 8 || std::memcmp(data, "S760VSTP", 8) != 0) {
        return false;
    }

    size_t offset = 8;
    if (offset + 4 > size) return false;

    // Floppy path
    uint32_t f_len = 0;
    std::memcpy(&f_len, data + offset, 4);
    offset += 4;
    if (f_len > 0 && offset + f_len <= size) {
        std::string f_path(reinterpret_cast<const char*>(data + offset), f_len);
        offset += f_len;
        m_host.get_drive_manager().mount_floppy(f_path);
    }

    // SCSI paths
    for (int i = 0; i < 7; ++i) {
        if (offset + 4 > size) return false;
        uint32_t s_len = 0;
        std::memcpy(&s_len, data + offset, 4);
        offset += 4;
        if (s_len > 0 && offset + s_len <= size) {
            std::string s_path(reinterpret_cast<const char*>(data + offset), s_len);
            offset += s_len;
            m_host.get_drive_manager().mount_scsi_device(i, s_path, DeviceType::HardDisk_SCSI);
        }
    }

    // Core savestate
    if (offset + 4 <= size) {
        uint32_t state_len = 0;
        std::memcpy(&state_len, data + offset, 4);
        offset += 4;
        if (state_len > 0 && offset + state_len <= size) {
            std::vector<uint8_t> st(data + offset, data + offset + state_len);
            m_host.load_state(st);
        }
    }

    return true;
}

intptr_t S760VstPlugin::dispatcher(int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt) {
    (void)index; (void)value; (void)opt;

    switch (opcode) {
        case effOpen:
            return 1;

        case effClose:
            delete this;
            return 1;

        case effSetSampleRate:
            m_sample_rate = opt;
            m_host.set_target_sample_rate(opt);
            return 1;

        case effSetBlockSize:
            m_block_size = static_cast<int32_t>(value);
            m_scratch_left.resize(std::max(2048, m_block_size));
            m_scratch_right.resize(std::max(2048, m_block_size));
            return 1;

        case effProcessEvents:
            if (ptr) {
                handle_vst_events(reinterpret_cast<const VstEvents*>(ptr));
            }
            return 1;

        case effGetChunk:
            build_state_chunk();
            if (ptr) {
                *reinterpret_cast<void**>(ptr) = m_chunk_data.data();
            }
            return static_cast<intptr_t>(m_chunk_data.size());

        case effSetChunk:
            if (ptr && value > 0) {
                return restore_state_chunk(reinterpret_cast<const uint8_t*>(ptr), static_cast<size_t>(value)) ? 1 : 0;
            }
            return 0;

        case effGetEffectName:
            if (ptr) {
                std::strncpy(reinterpret_cast<char*>(ptr), "Roland S-760 Sampler", 31);
                return 1;
            }
            break;

        case effGetVendorString:
            if (ptr) {
                std::strncpy(reinterpret_cast<char*>(ptr), "Roland Emulation Team", 31);
                return 1;
            }
            break;

        case effGetProductString:
            if (ptr) {
                std::strncpy(reinterpret_cast<char*>(ptr), "Roland S-760 VST", 31);
                return 1;
            }
            break;

        case effGetVendorVersion:
            return 2240;

        case effGetVstVersion:
            return 2400; // VST 2.4

        case effCanDo:
            if (ptr) {
                const char* can_do = reinterpret_cast<const char*>(ptr);
                if (std::strcmp(can_do, "sendVstEvents") == 0 ||
                    std::strcmp(can_do, "sendVstMidiEvent") == 0 ||
                    std::strcmp(can_do, "receiveVstEvents") == 0 ||
                    std::strcmp(can_do, "receiveVstMidiEvent") == 0) {
                    return 1;
                }
            }
            return 0;

        default:
            break;
    }
    return 0;
}

} // namespace s760

// -----------------------------------------------------------------------------
// VST Export Entry Points
// -----------------------------------------------------------------------------
extern "C" {

VST_EXPORT AEffect* VSTPluginMain(audioMasterCallback audioMaster) {
    auto* plugin = new s760::S760VstPlugin(audioMaster);
    return plugin->get_aeffect();
}

} // extern "C"
