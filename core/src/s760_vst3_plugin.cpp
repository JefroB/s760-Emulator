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
static const TUID S760FXProcessorUID = INLINE_UID(0x53373630, 0x56535433, 0x46585052, 0x30303032);

S760Vst3Plugin::S760Vst3Plugin(bool is_fx)
    : m_bridge(select_bridge_host()), m_is_fx(is_fx) {
    m_scratch_left.resize(8192, 0.0f);
    m_scratch_right.resize(8192, 0.0f);
}

// -----------------------------------------------------------------------------
//  Backend selection (mame-live-backend task 9.3, Requirements 1.2/7.1/7.3).
//  Decides which IS760Host the Bridge is driven from. Only when the selector
//  resolves+inits the MAME backend does the Bridge get the MAME host; otherwise
//  the Bridge borrows the concrete &m_host (default Core, byte-for-byte identical).
// -----------------------------------------------------------------------------
IS760Host* S760Vst3Plugin::select_bridge_host() {
    BackendSelectionResult sel = select_backend();

    if (sel.active == BackendKind::Mame && sel.host) {
        m_selected_host = std::move(sel.host);
        return m_selected_host.get();
    }

    if (sel.bothUnavailable) {
        std::cerr << "[S760Vst3Plugin] backend selection failed: " << sel.error
                  << " (using Core host)" << std::endl;
    }
    return &m_host;
}

S760Vst3Plugin::~S760Vst3Plugin() {
    m_host.get_drive_manager().flush_all();
}

// -----------------------------------------------------------------------------
//  S760Vst3PlugView — WebView-backed IPlugView (task 3.6).
//  Vended by S760Vst3Plugin::createView("editor"); binds the webview to the
//  plugin's in-process S760Bridge via S760EditorController.
// -----------------------------------------------------------------------------
static const TUID FUnknown_iid       = INLINE_UID(0x00000000, 0x00000000, 0xC0000000, 0x00000046);
static const TUID IComponent_iid     = INLINE_UID(0xE8318227, 0x79A447F6, 0x8E6AEF5D, 0xDC202293);
static const TUID IAudioProcessor_iid= INLINE_UID(0x420423E5, 0x12DA4541, 0xA6190EB9, 0x99615A3B);
static const TUID IEditController_iid = INLINE_UID(0xDCD7BBE3, 0x7742448D, 0xA874AACC, 0x979C759E);
static const TUID IPlugView_iid       = INLINE_UID(0x5BC32507, 0xD06049EA, 0xA6151B52, 0x2B755B29);

class S760Vst3PlugView : public Steinberg::IPlugView {
public:
    explicit S760Vst3PlugView(S760Bridge* bridge)
        : m_controller(bridge) {}
    ~S760Vst3PlugView() override { m_controller.close(); }

    // FUnknown
    tresult queryInterface(const TUID _iid, void** obj) override {
        if (!obj) return kInvalidArgument;
        if (std::memcmp(_iid, FUnknown_iid, sizeof(TUID)) == 0 ||
            std::memcmp(_iid, IPlugView_iid, sizeof(TUID)) == 0) {
            *obj = static_cast<Steinberg::IPlugView*>(this);
            addRef();
            return kResultOk;
        }
        *obj = nullptr;
        return kResultFalse;
    }
    uint32_t addRef() override { return ++m_ref; }
    uint32_t release() override {
        uint32_t c = --m_ref;
        if (c == 0) { delete this; }
        return c;
    }

    tresult isPlatformTypeSupported(FIDString type) override {
        if (!type) return kResultFalse;
#if defined(_WIN32)
        return (std::strcmp(type, kPlatformTypeHWND) == 0) ? kResultOk : kResultFalse;
#elif defined(__APPLE__)
        return (std::strcmp(type, kPlatformTypeNSView) == 0) ? kResultOk : kResultFalse;
#else
        return (std::strcmp(type, kPlatformTypeX11EmbedWindowID) == 0) ? kResultOk : kResultFalse;
#endif
    }

    tresult attached(void* parent, FIDString type) override {
        if (isPlatformTypeSupported(type) != kResultOk) return kResultFalse;
        WebViewSize def{};
        WebViewSize sz{m_rect.getWidth()  > 0 ? static_cast<uint32_t>(m_rect.getWidth())  : def.width,
                       m_rect.getHeight() > 0 ? static_cast<uint32_t>(m_rect.getHeight()) : def.height};
        return m_controller.open(static_cast<NativeWindowHandle>(parent), sz) ? kResultOk : kResultFalse;
    }

    tresult removed() override { m_controller.close(); return kResultOk; }
    tresult onWheel(float) override { return kResultOk; }
    tresult onKeyDown(char16_t, int16_t, int16_t) override { return kResultOk; }
    tresult onKeyUp(char16_t, int16_t, int16_t) override { return kResultOk; }

    tresult getSize(Steinberg::ViewRect* size) override {
        if (!size) return kInvalidArgument;
        WebViewSize sz = m_controller.size();
        size->left = 0; size->top = 0;
        size->right = static_cast<int32_t>(sz.width);
        size->bottom = static_cast<int32_t>(sz.height);
        return kResultOk;
    }

    tresult onSize(Steinberg::ViewRect* newSize) override {
        if (!newSize) return kInvalidArgument;
        m_rect = *newSize;
        m_controller.set_size(WebViewSize{static_cast<uint32_t>(newSize->getWidth()),
                                          static_cast<uint32_t>(newSize->getHeight())});
        return kResultOk;
    }

    tresult onFocus(bool) override { return kResultOk; }
    tresult setFrame(Steinberg::IPlugFrame* frame) override { m_frame = frame; return kResultOk; }
    tresult canResize() override { return kResultOk; }
    tresult checkSizeConstraint(Steinberg::ViewRect*) override { return kResultOk; }

    // Pump the bridge (DAW UI timer / test harness drives this).
    void tick() { m_controller.tick(); }
    S760EditorController& controller() { return m_controller; }

private:
    std::atomic<uint32_t> m_ref{1};
    S760EditorController m_controller;
    Steinberg::IPlugFrame* m_frame = nullptr;
    Steinberg::ViewRect m_rect{};
};

tresult S760Vst3Plugin::queryInterface(const TUID _iid, void** obj) {
    if (!obj) return kInvalidArgument;

    if (std::memcmp(_iid, FUnknown_iid, sizeof(TUID)) == 0 ||
        std::memcmp(_iid, IComponent_iid, sizeof(TUID)) == 0) {
        *obj = static_cast<Steinberg::IComponent*>(this);
        addRef();
        return kResultOk;
    }
    if (std::memcmp(_iid, IAudioProcessor_iid, sizeof(TUID)) == 0) {
        *obj = static_cast<Steinberg::IAudioProcessor*>(this);
        addRef();
        return kResultOk;
    }
    if (std::memcmp(_iid, IEditController_iid, sizeof(TUID)) == 0) {
        *obj = static_cast<Steinberg::IEditController*>(this);
        addRef();
        return kResultOk;
    }

    *obj = nullptr;
    return kResultFalse;
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
        return 1; // 1 Stereo Input bus (for live sampling / recording) + 1 Stereo Output bus
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
    size_t alloc_size = std::max(size_t(8192), static_cast<size_t>(m_max_block_size));
    m_scratch_left.resize(alloc_size, 0.0f);
    m_scratch_right.resize(alloc_size, 0.0f);
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

    // 2. Feed Audio Inputs to Live Sampler Recorder
    uint32_t needed = static_cast<uint32_t>(data.numSamples);
    if (data.numInputs > 0 && data.inputs && data.inputs[0].channelBuffers32) {
        const float* in_l = data.inputs[0].channelBuffers32[0];
        const float* in_r = (data.inputs[0].numChannels >= 2) ? data.inputs[0].channelBuffers32[1] : in_l;
        m_host.feed_audio_input(in_l, in_r, needed);
    }

    // 3. Generate emulator audio with bounded loop to prevent audio deadline dropouts
    constexpr int MAX_EMULATOR_FRAMES_PER_BLOCK = 4;
    int emu_ticks = 0;
    while (m_host.is_system_running() && 
           m_host.get_audio_stats().available_frames < needed && 
           emu_ticks < MAX_EMULATOR_FRAMES_PER_BLOCK) {
        m_host.run_frame();
        emu_ticks++;
    }

    if (m_scratch_left.size() < needed) {
        needed = static_cast<uint32_t>(m_scratch_left.size());
    }

    m_host.read_audio_frames(m_scratch_left.data(), m_scratch_right.data(), needed);

    // 4. Apply input pass-through monitoring if active
    if (m_is_fx || m_host.get_recorder().is_recording() || m_host.get_recorder().is_armed()) {
        if (data.numInputs > 0 && data.inputs && data.inputs[0].channelBuffers32) {
            const float* in_l = data.inputs[0].channelBuffers32[0];
            const float* in_r = (data.inputs[0].numChannels >= 2) ? data.inputs[0].channelBuffers32[1] : in_l;
            if (in_l) {
                for (uint32_t i = 0; i < needed; ++i) {
                    m_scratch_left[i] += in_l[i];
                }
            }
            if (in_r) {
                for (uint32_t i = 0; i < needed; ++i) {
                    m_scratch_right[i] += in_r[i];
                }
            }
        }
    }

    // 5. Write to VST3 Output Buffers
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
    if (state->write((void*)magic, 8, &written) != kResultOk || written != 8) return kResultFalse;

    // Floppy path
    auto f_stat = m_host.get_drive_manager().get_floppy_status();
    uint32_t f_len = static_cast<uint32_t>(f_stat.file_path.size());
    if (state->write(&f_len, 4, &written) != kResultOk || written != 4) return kResultFalse;
    if (f_len > 0) {
        if (state->write((void*)f_stat.file_path.data(), f_len, &written) != kResultOk || written != static_cast<int32_t>(f_len)) return kResultFalse;
    }

    // SCSI paths
    for (int i = 0; i < 7; ++i) {
        auto s_stat = m_host.get_drive_manager().get_scsi_status(i);
        uint32_t s_len = static_cast<uint32_t>(s_stat.file_path.size());
        if (state->write(&s_len, 4, &written) != kResultOk || written != 4) return kResultFalse;
        if (s_len > 0) {
            if (state->write((void*)s_stat.file_path.data(), s_len, &written) != kResultOk || written != static_cast<int32_t>(s_len)) return kResultFalse;
        }
    }

    // Core savestate
    auto st = m_host.save_state();
    uint32_t st_len = static_cast<uint32_t>(st.size());
    if (state->write(&st_len, 4, &written) != kResultOk || written != 4) return kResultFalse;
    if (st_len > 0) {
        if (state->write(st.data(), st_len, &written) != kResultOk || written != static_cast<int32_t>(st_len)) return kResultFalse;
    }

    return kResultOk;
}

tresult S760Vst3Plugin::setState(Steinberg::IBStream* state) {
    if (!state) return kInvalidArgument;

    int32_t bytes_read = 0;
    char magic[8] = {0};
    if (state->read(magic, 8, &bytes_read) != kResultOk || bytes_read != 8 || std::memcmp(magic, "S760VST3", 8) != 0) {
        return kResultFalse;
    }

    // Parse into temporary state to ensure transactionality
    std::string f_path;
    uint32_t f_len = 0;
    if (state->read(&f_len, 4, &bytes_read) != kResultOk || bytes_read != 4 || f_len > 4096) {
        return kResultFalse;
    }
    if (f_len > 0) {
        f_path.resize(f_len);
        if (state->read(f_path.data(), f_len, &bytes_read) != kResultOk || bytes_read != static_cast<int32_t>(f_len)) {
            return kResultFalse;
        }
    }

    // SCSI paths
    std::string s_paths[7];
    for (int i = 0; i < 7; ++i) {
        uint32_t s_len = 0;
        if (state->read(&s_len, 4, &bytes_read) != kResultOk || bytes_read != 4 || s_len > 4096) {
            return kResultFalse;
        }
        if (s_len > 0) {
            s_paths[i].resize(s_len);
            if (state->read(s_paths[i].data(), s_len, &bytes_read) != kResultOk || bytes_read != static_cast<int32_t>(s_len)) {
                return kResultFalse;
            }
        }
    }

    // Core savestate
    std::vector<uint8_t> st_data;
    uint32_t st_len = 0;
    if (state->read(&st_len, 4, &bytes_read) != kResultOk || bytes_read != 4 || st_len > 64 * 1024 * 1024) {
        return kResultFalse;
    }
    if (st_len > 0) {
        st_data.resize(st_len);
        if (state->read(st_data.data(), st_len, &bytes_read) != kResultOk || bytes_read != static_cast<int32_t>(st_len)) {
            return kResultFalse;
        }
    }

    // All validation passed - atomically apply to live instance
    if (!f_path.empty()) {
        m_host.get_drive_manager().mount_floppy(f_path);
    }
    for (int i = 0; i < 7; ++i) {
        if (!s_paths[i].empty()) {
            m_host.get_drive_manager().mount_scsi_device(i, s_paths[i], DeviceType::HardDisk_SCSI);
        }
    }
    if (!st_data.empty()) {
        m_host.load_state(st_data);
    }

    return kResultOk;
}

// -----------------------------------------------------------------------------
// IEditController (editor half) — vends the WebView-backed editor view.
// -----------------------------------------------------------------------------
tresult S760Vst3Plugin::setComponentState(Steinberg::IBStream* state) {
    (void)state; // no automatable parameters mirrored into the editor yet
    return kResultOk;
}

int32_t S760Vst3Plugin::getParameterCount() { return 0; }

tresult S760Vst3Plugin::getParameterInfo(int32_t paramIndex, void* info) {
    (void)paramIndex; (void)info;
    return kResultFalse;
}

tresult S760Vst3Plugin::getParamStringByValue(uint32_t id, double valueNormalized, void* string) {
    (void)id; (void)valueNormalized; (void)string;
    return kResultFalse;
}

tresult S760Vst3Plugin::getParamValueByString(uint32_t id, char16_t* string, double* valueNormalized) {
    (void)id; (void)string; (void)valueNormalized;
    return kResultFalse;
}

double S760Vst3Plugin::normalizedParamToPlain(uint32_t id, double valueNormalized) {
    (void)id;
    return valueNormalized;
}

double S760Vst3Plugin::plainParamToNormalized(uint32_t id, double plainValue) {
    (void)id;
    return plainValue;
}

double S760Vst3Plugin::getParamNormalized(uint32_t id) {
    (void)id;
    return 0.0;
}

tresult S760Vst3Plugin::setParamNormalized(uint32_t id, double value) {
    (void)id; (void)value;
    return kResultOk;
}

tresult S760Vst3Plugin::setComponentHandler(void* handler) {
    (void)handler;
    return kResultOk;
}

Steinberg::IPlugView* S760Vst3Plugin::createView(FIDString name) {
    // Only the "editor" view is vended; it is the WebView-backed React editor
    // bound to this plugin's in-process bridge.
    if (!name || std::strcmp(name, ViewType_kEditor) != 0) {
        return nullptr;
    }
    return new S760Vst3PlugView(&m_bridge);
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
        return 2; // Class 0: Instrument, Class 1: Live Sampler FX
    }

    tresult getClassInfo(int32_t index, Steinberg::PClassInfo* info) override {
        if (!info) return kInvalidArgument;
        if (index == 0) {
            std::memcpy(info->cid, S760ProcessorUID, 16);
            info->cardinality = 0;
            std::strncpy(info->category, "Instrument|Synth", sizeof(info->category) - 1);
            std::strncpy(info->name, "Roland S-760 Sampler", sizeof(info->name) - 1);
            return kResultOk;
        } else if (index == 1) {
            std::memcpy(info->cid, S760FXProcessorUID, 16);
            info->cardinality = 0;
            std::strncpy(info->category, "Fx|Sampler", sizeof(info->category) - 1);
            std::strncpy(info->name, "Roland S-760 Live Sampler FX", sizeof(info->name) - 1);
            return kResultOk;
        }
        return kInvalidArgument;
    }

    tresult createInstance(FIDString cid, FIDString _iid, void** obj) override {
        (void)_iid;
        if (!obj) return kInvalidArgument;
        if (cid && std::memcmp(cid, S760FXProcessorUID, 16) == 0) {
            auto* plugin = new S760Vst3Plugin(true);
            *obj = static_cast<Steinberg::IComponent*>(plugin);
            return kResultOk;
        }
        auto* plugin = new S760Vst3Plugin(false);
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
