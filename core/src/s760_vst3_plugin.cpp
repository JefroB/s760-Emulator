#include "s760/s760_vst3_plugin.hpp"

#include <cstring>
#include <algorithm>
#include <iostream>

#if defined(_WIN32)
#define VST3_EXPORT __declspec(dllexport)
#else
#define VST3_EXPORT __attribute__((visibility("default")))
#endif

namespace s760 {

static const TUID S760ProcessorUID = INLINE_UID(0x53373630, 0x56535433, 0x50524F43, 0x30303031);

S760Vst3Plugin::S760Vst3Plugin() {
    m_scratch_left.resize(2048, 0.0f);
    m_scratch_right.resize(2048, 0.0f);
}

S760Vst3Plugin::~S760Vst3Plugin() {
    m_host.get_drive_manager().flush_all();
}

tresult S760Vst3Plugin::queryInterface(const TUID _iid, void** obj) {
    if (!obj) return kInvalidArgument;

    // Check basic COM interfaces
    *obj = static_cast<Steinberg::IComponent*>(this);
    addRef();
    return kResultOk;
}

uint32_t S760Vst3Plugin::addRef() {
    return ++m_ref_count;
}

uint32_t S760Vst3Plugin::release() {
    uint32_t count = --m_ref_count;
    if (count == 0) {
        delete this;
    }
    return count;
}

tresult S760Vst3Plugin::initialize(Steinberg::FUnknown* context) {
    (void)context;
    return kResultOk;
}

tresult S760Vst3Plugin::terminate() {
    m_host.get_drive_manager().flush_all();
    return kResultOk;
}

tresult S760Vst3Plugin::getControllerClassId(TUID classId) {
    (void)classId;
    return kResultFalse;
}

tresult S760Vst3Plugin::setIoMode(int32_t mode) {
    (void)mode;
    return kResultOk;
}

tresult S760Vst3Plugin::getBusCount(int32_t type, int32_t dir) {
    if (type == kAudio) {
        return (dir == kOutput) ? 1 : 0;
    } else if (type == kEvent) {
        return (dir == kInput) ? 1 : 0;
    }
    return 0;
}

tresult S760Vst3Plugin::getBusInfo(int32_t type, int32_t dir, int32_t index, void* bus) {
    (void)type; (void)dir; (void)index; (void)bus;
    return kResultOk;
}

tresult S760Vst3Plugin::getRoutingInfo(void* inInfo, void* outInfo) {
    (void)inInfo; (void)outInfo;
    return kResultOk;
}

tresult S760Vst3Plugin::activateBus(int32_t type, int32_t dir, int32_t index, bool state) {
    (void)type; (void)dir; (void)index; (void)state;
    return kResultOk;
}

tresult S760Vst3Plugin::setActive(bool state) {
    m_is_active = state;
    if (!state) {
        m_host.get_drive_manager().flush_all();
    }
    return kResultOk;
}

tresult S760Vst3Plugin::setBusArrangements(void* inputs, int32_t numIns, void* outputs, int32_t numOuts) {
    (void)inputs; (void)numIns; (void)outputs; (void)numOuts;
    return kResultOk;
}

tresult S760Vst3Plugin::getBusArrangement(int32_t dir, int32_t index, void* arr) {
    (void)dir; (void)index; (void)arr;
    return kResultOk;
}

tresult S760Vst3Plugin::canProcessSampleSize(int32_t symbolicSampleSize) {
    return (symbolicSampleSize == 0) ? kResultOk : kResultFalse; // 32-bit float supported
}

uint32_t S760Vst3Plugin::getLatencySamples() {
    return 0;
}

tresult S760Vst3Plugin::setupProcessing(Steinberg::ProcessSetup& setup) {
    m_sample_rate = setup.sampleRate;
    m_max_block_size = setup.maxSamplesPerBlock;
    m_host.set_target_sample_rate(setup.sampleRate);
    m_scratch_left.resize(std::max(2048, m_max_block_size));
    m_scratch_right.resize(std::max(2048, m_max_block_size));
    return kResultOk;
}

tresult S760Vst3Plugin::setProcessing(bool state) {
    m_is_processing = state;
    if (!state) {
        m_host.get_drive_manager().flush_all();
    }
    return kResultOk;
}

uint32_t S760Vst3Plugin::getTailSamples() {
    return 0;
}

void S760Vst3Plugin::process_events(Steinberg::IEventList* events) {
    if (!events) return;

    int32_t num_events = events->getEventCount();
    for (int32_t i = 0; i < num_events; ++i) {
        Event e;
        if (events->getEvent(i, e) == kResultOk) {
            if (e.type == kNoteOnEvent) {
                uint8_t ch = static_cast<uint8_t>(e.noteOn.channel & 0x0F);
                uint8_t key = static_cast<uint8_t>(e.noteOn.pitch & 0x7F);
                uint8_t vel = static_cast<uint8_t>(std::clamp(static_cast<int>(e.noteOn.velocity * 127.0f), 0, 127));

                uint8_t msg[3] = { static_cast<uint8_t>(0x90 | ch), key, vel };
                m_host.send_midi_message(msg, 3);
            } else if (e.type == kNoteOffEvent) {
                uint8_t ch = static_cast<uint8_t>(e.noteOff.channel & 0x0F);
                uint8_t key = static_cast<uint8_t>(e.noteOff.pitch & 0x7F);
                uint8_t vel = static_cast<uint8_t>(std::clamp(static_cast<int>(e.noteOff.velocity * 127.0f), 0, 127));

                uint8_t msg[3] = { static_cast<uint8_t>(0x80 | ch), key, vel };
                m_host.send_midi_message(msg, 3);
            }
        }
    }
}

tresult S760Vst3Plugin::process(Steinberg::ProcessData& data) {
    if (data.numSamples <= 0) return kResultOk;

    // 1. Process MIDI Note Events
    process_events(data.inputEvents);

    // 2. Generate emulator audio
    uint32_t needed = static_cast<uint32_t>(data.numSamples);
    while (m_host.is_system_running() && m_host.get_audio_stats().available_frames < needed) {
        m_host.run_frame();
    }

    if (m_scratch_left.size() < needed) {
        m_scratch_left.resize(needed);
        m_scratch_right.resize(needed);
    }

    m_host.read_audio_frames(m_scratch_left.data(), m_scratch_right.data(), needed);

    // 3. Write to VST3 Output Buffers
    if (data.numOutputs > 0 && data.outputs) {
        auto& out_bus = data.outputs[0];
        if (out_bus.channelBuffers32 && out_bus.numChannels >= 2) {
            std::memcpy(out_bus.channelBuffers32[0], m_scratch_left.data(), needed * sizeof(float));
            std::memcpy(out_bus.channelBuffers32[1], m_scratch_right.data(), needed * sizeof(float));
        } else if (out_bus.channelBuffers32 && out_bus.numChannels == 1) {
            for (uint32_t i = 0; i < needed; ++i) {
                out_bus.channelBuffers32[0][i] = (m_scratch_left[i] + m_scratch_right[i]) * 0.5f;
            }
        }
    }

    return kResultOk;
}

tresult S760Vst3Plugin::getState(Steinberg::IBStream* state) {
    if (!state) return kInvalidArgument;

    int32_t written = 0;
    const char magic[] = "S760VST3";
    state->write((void*)magic, 8, &written);

    // Floppy path
    auto f_stat = m_host.get_drive_manager().get_floppy_status();
    uint32_t f_len = static_cast<uint32_t>(f_stat.file_path.size());
    state->write(&f_len, 4, &written);
    if (f_len > 0) {
        state->write((void*)f_stat.file_path.data(), f_len, &written);
    }

    // SCSI paths
    for (int i = 0; i < 7; ++i) {
        auto s_stat = m_host.get_drive_manager().get_scsi_status(i);
        uint32_t s_len = static_cast<uint32_t>(s_stat.file_path.size());
        state->write(&s_len, 4, &written);
        if (s_len > 0) {
            state->write((void*)s_stat.file_path.data(), s_len, &written);
        }
    }

    // Core savestate
    auto st = m_host.save_state();
    uint32_t st_len = static_cast<uint32_t>(st.size());
    state->write(&st_len, 4, &written);
    if (st_len > 0) {
        state->write(st.data(), st_len, &written);
    }

    return kResultOk;
}

tresult S760Vst3Plugin::setState(Steinberg::IBStream* state) {
    if (!state) return kInvalidArgument;

    int32_t bytes_read = 0;
    char magic[8] = {0};
    if (state->read(magic, 8, &bytes_read) != kResultOk || std::memcmp(magic, "S760VST3", 8) != 0) {
        return kResultFalse;
    }

    // Floppy path
    uint32_t f_len = 0;
    if (state->read(&f_len, 4, &bytes_read) == kResultOk && f_len > 0 && f_len < 4096) {
        std::string f_path(f_len, '\0');
        state->read(f_path.data(), f_len, &bytes_read);
        m_host.get_drive_manager().mount_floppy(f_path);
    }

    // SCSI paths
    for (int i = 0; i < 7; ++i) {
        uint32_t s_len = 0;
        if (state->read(&s_len, 4, &bytes_read) == kResultOk && s_len > 0 && s_len < 4096) {
            std::string s_path(s_len, '\0');
            state->read(s_path.data(), s_len, &bytes_read);
            m_host.get_drive_manager().mount_scsi_device(i, s_path, DeviceType::HardDisk_SCSI);
        }
    }

    // Core savestate
    uint32_t st_len = 0;
    if (state->read(&st_len, 4, &bytes_read) == kResultOk && st_len > 0 && st_len < 64 * 1024 * 1024) {
        std::vector<uint8_t> st_data(st_len);
        state->read(st_data.data(), st_len, &bytes_read);
        m_host.load_state(st_data);
    }

    return kResultOk;
}

// -----------------------------------------------------------------------------
// VST3 Factory Implementation
// -----------------------------------------------------------------------------

class S760Vst3Factory : public Steinberg::IPluginFactory {
public:
    tresult queryInterface(const TUID _iid, void** obj) override {
        (void)_iid;
        if (!obj) return kInvalidArgument;
        *obj = this;
        return kResultOk;
    }
    uint32_t addRef() override { return 1; }
    uint32_t release() override { return 1; }

    tresult getFactoryInfo(void* info) override {
        (void)info;
        return kResultOk;
    }

    int32_t countClasses() override {
        return 1;
    }

    tresult getClassInfo(int32_t index, Steinberg::PClassInfo* info) override {
        if (index != 0 || !info) return kInvalidArgument;
        std::memcpy(info->cid, S760ProcessorUID, 16);
        info->cardinality = 0;
        std::strncpy(info->category, "Audio Module", sizeof(info->category) - 1);
        std::strncpy(info->name, "Roland S-760 Sampler VST3", sizeof(info->name) - 1);
        return kResultOk;
    }

    tresult createInstance(FIDString cid, FIDString _iid, void** obj) override {
        (void)cid; (void)_iid;
        if (!obj) return kInvalidArgument;
        auto* plugin = new S760Vst3Plugin();
        *obj = static_cast<Steinberg::IComponent*>(plugin);
        return kResultOk;
    }
};

static S760Vst3Factory s_factory;

} // namespace s760

// -----------------------------------------------------------------------------
// VST3 Export Entry Points
// -----------------------------------------------------------------------------
extern "C" {

VST3_EXPORT bool InitDll() {
    return true;
}

VST3_EXPORT bool ExitDll() {
    return true;
}

VST3_EXPORT Steinberg::IPluginFactory* GetPluginFactory() {
    return &s760::s_factory;
}

} // extern "C"
