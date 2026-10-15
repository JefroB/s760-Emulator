#include "s760/s760_native_rate_converter.hpp"
#include "s760/s760_native_plugin_state.hpp"
#include "s760/s760_vst3_plugin.hpp"

#include <cstring>
#include <algorithm>
#include <iostream>
#include <cmath>
#include <cstdlib>
#include <chrono>
#include <fstream>
#include <rapidjson/document.h>
#include <rapidjson/writer.h>
#include <rapidjson/stringbuffer.h>
#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#endif

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

S760Vst3Plugin::S760Vst3Plugin(const NativeRuntimeConfig& config,const std::string& startup_error)
    : m_selected_host(std::make_unique<S760MameHost>()), m_bridge(m_selected_host.get()), m_native_mode(true),
      m_configuration_pending(!startup_error.empty()),m_startup_error(startup_error) {
    m_native_input_supported=config.experimental_adc;
    auto* host=native_host();
    if(!m_configuration_pending) {
        host->configure_native(config);
        if(!host->init()) throw std::runtime_error(host->native_error());
        if(!config.media_directory.empty() && !host->media_library().configure(config.media_directory.u8string()))
            throw std::runtime_error(host->media_library().error());
    }
    initialize_configuration(config);
    m_bridge.set_configuration_callbacks([this](const std::string& json){return configure_from_editor(json);},
                                        [this]{return configuration_snapshot();});
    // Per-instance URL: do not mutate process-wide environment or depend on
    // the DAW working directory. Percent-encode UTF-8 file path bytes.
    if(const auto* override_url=std::getenv("S760_UI_URL");override_url && *override_url)
        m_native_ui_url=override_url;
    else {
        m_native_ui_url="file:///";
        for(unsigned char c:(config.root/"google-ui/dist/index.html").generic_u8string()) {
            if((c>='a'&&c<='z') || (c>='A'&&c<='Z') || (c>='0'&&c<='9') ||
               c=='/' || c==':' || c=='-' || c=='_' || c=='.' || c=='~') m_native_ui_url+=char(c);
            else {m_native_ui_url+='%';m_native_ui_url+="0123456789ABCDEF"[c>>4];m_native_ui_url+="0123456789ABCDEF"[c&15];}
        }
    }
    m_scratch_left.resize(NativeStream::max_frames);
    m_scratch_right.resize(NativeStream::max_frames);
    for(unsigned channel=0;channel<16;++channel) m_midi_values[channel*129+128].store(8192.0/16383.0);
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
    m_bridge.set_configuration_callbacks({},{});
    m_native_stream.reset();
    if(!m_selected_host) m_host.get_drive_manager().flush_all();
}

// -----------------------------------------------------------------------------
//  S760Vst3PlugView â€” WebView-backed IPlugView (task 3.6).
//  Vended by S760Vst3Plugin::createView("editor"); binds the webview to the
//  plugin's in-process S760Bridge via S760EditorController.
// -----------------------------------------------------------------------------
static const TUID FUnknown_iid       = INLINE_UID(0x00000000, 0x00000000, 0xC0000000, 0x00000046);
static const TUID IComponent_iid     = INLINE_UID(0xE831FF31, 0xF2D54301, 0x928EBBEE, 0x25697802);
static const TUID IAudioProcessor_iid= INLINE_UID(0x42043F99, 0xB7DA453C, 0xA569E79D, 0x9AAEC33D);
static const TUID IEditController_iid = INLINE_UID(0xDCD7BBE3, 0x7742448D, 0xA874AACC, 0x979C759E);
static const TUID IMidiMapping_iid = INLINE_UID(0xDF0FF9F7, 0x49B74669, 0xB63AB732, 0x7ADBF5E5);
static const TUID IPlugView_iid       = INLINE_UID(0x5BC32507, 0xD06049EA, 0xA6151B52, 0x2B755B29);

class S760Vst3PlugView : public Steinberg::IPlugView {
public:
    explicit S760Vst3PlugView(S760Bridge* bridge, const std::string& url)
        : m_controller(bridge) { m_controller.set_frontend_url(url); }
    ~S760Vst3PlugView() { m_controller.close(); }

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
    if(m_native_mode && std::memcmp(_iid,IMidiMapping_iid,sizeof(TUID))==0) {
        *obj=static_cast<Steinberg::IMidiMapping*>(this);addRef();return kResultOk;
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
    m_terminated=true;
    m_is_processing=false;
    m_native_stream.reset();
    if(m_native_mode) native_host()->close_native();
    if(!m_selected_host) m_host.get_drive_manager().flush_all();
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
        if(m_selected_host && dir==kInput) return m_native_input_supported?1:0;
        return 1; // 1 Stereo Input bus (for live sampling / recording) + 1 Stereo Output bus
    } else if (type == kEvent) {
        return (dir == kInput) ? 1 : 0;
    }
    return 0;
}

tresult S760Vst3Plugin::getBusInfo(int32_t type, int32_t dir, int32_t index, void* bus) {
    if(!bus || index!=0 || (dir!=kInput && dir!=kOutput) || !getBusCount(type,dir)) return kInvalidArgument;
    auto& info=*static_cast<Steinberg::BusInfo*>(bus); info={};
    info.mediaType=type; info.direction=dir; info.channelCount=type==kAudio?2:16;
    const char16_t* name=type==kEvent?u"MIDI Input":dir==kOutput?u"Stereo Output":u"Stereo Input";
    std::copy(name,name+std::char_traits<char16_t>::length(name),info.name);
    info.busType=kMain; info.flags=(m_native_mode && type==kAudio && dir==kInput)?0:1; return kResultOk;
}

tresult S760Vst3Plugin::getRoutingInfo(void* inInfo, void* outInfo) {
    (void)inInfo; (void)outInfo;
    return kNotImplemented;
}

tresult S760Vst3Plugin::activateBus(int32_t type, int32_t dir, int32_t index, bool state) {
    if(m_native_mode && type==kAudio && dir==kInput) {
        if(index!=0 || !m_native_input_supported || m_is_processing || (state && m_sample_rate!=44100))return kResultFalse;
        m_native_input_active=state;return kResultOk;
    }
    if(index!=0 || !getBusCount(type,dir))return kResultFalse;
    return kResultOk;
}

tresult S760Vst3Plugin::setActive(bool state) {
    m_is_active = state;
    if(!state && m_native_mode) m_is_processing=false;
    if (!state && !m_selected_host) {
        m_host.get_drive_manager().flush_all();
    }
    return kResultOk;
}

tresult S760Vst3Plugin::setBusArrangements(void* inputs, int32_t numIns, void* outputs, int32_t numOuts) {
    if(numIns<0 || numIns>getBusCount(kAudio,kInput) || (!m_native_mode && numIns!=getBusCount(kAudio,kInput)) || numOuts!=1 || !outputs ||
       *static_cast<uint64_t*>(outputs)!=3 || (numIns && (!inputs || *static_cast<uint64_t*>(inputs)!=3))) return kResultFalse;
    return kResultOk;
}

tresult S760Vst3Plugin::getBusArrangement(int32_t dir, int32_t index, void* arr) {
    if(!arr || index!=0 || (dir!=kInput && dir!=kOutput) || !getBusCount(kAudio,dir)) return kInvalidArgument;
    *static_cast<uint64_t*>(arr)=3; return kResultOk;
}

tresult S760Vst3Plugin::canProcessSampleSize(int32_t symbolicSampleSize) {
    return (symbolicSampleSize == 0) ? kResultOk : kResultFalse; // 32-bit float supported
}

uint32_t S760Vst3Plugin::getLatencySamples() {
    if(m_native_mode) return NativeRateConverter::host_samples(NativeStream::output_delay+NativeStream::midi_lead,unsigned(m_sample_rate))+NativeRateConverter::latency(unsigned(m_sample_rate));
    return 0;
}

tresult S760Vst3Plugin::setupProcessing(Steinberg::ProcessSetup& setup) {
    if(m_selected_host) {
        if(!m_native_mode || m_is_processing || setup.processMode<0 || setup.processMode>2 || !NativeRateConverter::supported(setup.sampleRate) || setup.symbolicSampleSize!=0 ||
           setup.maxSamplesPerBlock<1 || setup.maxSamplesPerBlock>NativeStream::max_frames || (m_native_input_active && setup.sampleRate!=44100))
            return kResultFalse;
        // Preserve queued PCM/note-offs. A started timeline cannot change its
        // rate without a stateful migration; require a fresh native instance.
        if(setup.sampleRate!=m_sample_rate && m_native_stream) return kResultFalse;
        m_sample_rate=setup.sampleRate; m_max_block_size=setup.maxSamplesPerBlock; m_process_mode=setup.processMode;
        return kResultOk;
    }
    m_sample_rate = setup.sampleRate;
    m_max_block_size = setup.maxSamplesPerBlock;
    m_host.set_target_sample_rate(setup.sampleRate);
    size_t alloc_size = std::max(size_t(8192), static_cast<size_t>(m_max_block_size));
    m_scratch_left.resize(alloc_size, 0.0f);
    m_scratch_right.resize(alloc_size, 0.0f);
    return kResultOk;
}

void S760Vst3Plugin::rebuild_native_stream(const NativeStream::Snapshot* saved) {
    auto* native=native_host()->native_runtime();
    auto origin=m_native_origin;auto rate=unsigned(m_sample_rate);auto converter=m_native_converter;auto input_supported=m_native_input_supported;
    auto input_context=std::make_shared<const float*>(nullptr);
    converter->set_renderer([native,rate,input_supported,input_context](float* pcm,std::size_t frames) {
        static const std::array<float,8192*2> silence{};
        return native->render(pcm,frames,input_supported?(rate==44100?*input_context:silence.data()):nullptr);
    });
    NativeStream::InputRenderer renderer=[native,origin,rate,converter,input_supported,input_context](const NativeStream::Block& b,const float* input,float* pcm) {
        if(b.events) {
            std::string json="{\"op\":\"schedule_midi\",\"append\":true,\"events\":[";
            for(unsigned i=0;i<b.events;++i) {
                if(i) json+=",";const auto& e=b.midi[i];
                json+="{\"sample\":"+std::to_string(origin+NativeRateConverter::native_sample(b.first+e.offset,rate)+NativeStream::midi_lead)+",\"bytes\":["+
                    std::to_string(e.bytes[0])+","+std::to_string(e.bytes[1])+","+std::to_string(e.bytes[2])+"]}";
            }
            native->request(json+"]}");
        }
        *input_context=input;
        return converter->host_frames()==b.first && converter->pull(pcm,b.frames);
    };
    if(saved) m_native_stream=std::make_unique<NativeStream>(renderer,*saved);
    else m_native_stream=std::make_unique<NativeStream>(renderer,NativeRateConverter::host_samples(NativeStream::output_delay,rate),NativeRateConverter::host_samples(2048,rate));
    m_native_stream->start();
}

tresult S760Vst3Plugin::setProcessing(bool state) {
    if(m_selected_host) {
        if(m_configuration_pending && !m_terminated) {m_is_processing=state;return kResultOk;}
        if(!m_native_mode || !native_host()->native_runtime()) return kResultFalse;
        if(state && m_native_state_failed) return kResultFalse;
        if(state && m_native_stream && m_native_stream->fault()!=NativeStream::Fault::none) return kResultFalse;
        if(state && !m_native_stream) {
            try {
                auto* native=native_host()->native_runtime();
                auto now=native->request("{\"op\":\"pause\"}").seconds;
                native->request("{\"op\":\"audio_capture\",\"enabled\":true}");
                m_native_origin=std::uint64_t(std::ceil(now*44100));
                auto rate=unsigned(m_sample_rate);
                m_native_converter=std::make_shared<NativeRateConverter>(rate,[native](float* pcm,std::size_t frames) { return native->render(pcm,frames); });
                if(m_native_input_supported) {
                    // ADC ingress shares the MIDI lead so video-frame surplus
                    // cannot consume host input before it has been submitted.
                    const std::array<float,NativeStream::midi_lead*2> silence{};
                    native->queue_input(silence.data(),NativeStream::midi_lead);
                }
                rebuild_native_stream();
            } catch(...) { m_native_stream.reset(); return kResultFalse; }
        }
        // Suspension retains queued PCM, pending serial events and the clock.
        // With no callback input the worker finishes its finite backlog and idles.
        native_host()->native_runtime()->set_audio_streaming(state);
        m_is_processing=state;
        return kResultOk;
    }
    m_is_processing = state;
    if (!state) {
        m_host.get_drive_manager().flush_all();
    }
    return kResultOk;
}

uint32_t S760Vst3Plugin::getTailSamples() {
    // SDK kInfiniteTail: a held or looped voice has no finite tail bound.
    return m_native_mode ? 0xffffffffu : 0;
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

tresult S760Vst3Plugin::process_native(Steinberg::ProcessData& data) {
    // VST hosts may alias input and output buffers. Capture ingress before
    // clearing output, using storage allocated during construction.
    bool input_valid=true;
    if(m_native_input_active) {
        input_valid=data.numSamples>=0 && data.numSamples<=m_max_block_size && data.numSamples<=int(m_scratch_left.size()) &&
            data.numInputs==1 && data.inputs && data.inputs[0].numChannels==2;
        if(input_valid) {
            const auto& bus=data.inputs[0];auto** channels=bus.channelBuffers32;
            input_valid=((bus.silenceFlags&1) || (channels && channels[0])) && ((bus.silenceFlags&2) || (channels && channels[1]));
            if(input_valid) {
                if(bus.silenceFlags&1)std::fill_n(m_scratch_left.data(),data.numSamples,0.f);
                else std::copy_n(channels[0],data.numSamples,m_scratch_left.data());
                if(bus.silenceFlags&2)std::fill_n(m_scratch_right.data(),data.numSamples,0.f);
                else std::copy_n(channels[1],data.numSamples,m_scratch_right.data());
            }
        }
    }
    // Clear even rejected blocks, including unsupported 64-bit host buffers.
    if(data.numSamples>0 && data.outputs) for(int b=0;b<data.numOutputs;++b) {
        auto& out=data.outputs[b];
        for(int ch=0;ch<out.numChannels;++ch) {
            if(data.symbolicSampleSize==0 && out.channelBuffers32 && out.channelBuffers32[ch])
                std::fill_n(out.channelBuffers32[ch],data.numSamples,0.f);
            else if(data.symbolicSampleSize==1 && out.channelBuffers64 && out.channelBuffers64[ch])
                std::fill_n(out.channelBuffers64[ch],data.numSamples,0.0);
        }
        out.silenceFlags=~std::uint64_t(0);
    }
    if(m_configuration_pending && !m_terminated && m_is_processing) {
        // A failed startup is a visible, silent native configuration state.
        // Never route it through the historical core or fabricate audio.
        return data.numSamples>=0 && data.numSamples<=m_max_block_size && data.processMode==m_process_mode &&
            data.symbolicSampleSize==0 && data.numInputs==0 && data.numOutputs==1 && data.outputs &&
            data.outputs[0].numChannels==2 && data.outputs[0].channelBuffers32 &&
            data.outputs[0].channelBuffers32[0] && data.outputs[0].channelBuffers32[1] ? kResultOk : kResultFalse;
    }
    if(!m_native_mode || !m_is_processing || !m_native_stream) return kResultFalse;
    auto reject=[this] { m_native_stream->fail(NativeStream::Fault::invalid_block); return kResultFalse; };
    auto* changes=static_cast<Steinberg::IParameterChanges*>(data.inputParameterChanges);
    if(data.numSamples==0 && (!data.inputEvents || data.inputEvents->getEventCount()==0) && (!changes || changes->getParameterCount()==0)) return kResultOk;
    if(data.processMode!=m_process_mode || data.numSamples<1 || data.numSamples>m_max_block_size || data.symbolicSampleSize!=0 ||
       data.numInputs<0 || data.numInputs>1 || (m_native_input_active && data.numInputs!=1) || data.numOutputs!=1 || !data.outputs || data.outputs[0].numChannels!=2 ||
       !data.outputs[0].channelBuffers32 || !data.outputs[0].channelBuffers32[0] || !data.outputs[0].channelBuffers32[1])
        return reject();
    const float* input_left=nullptr;const float* input_right=nullptr;
    if(m_native_input_active) {
        if(!input_valid)return reject();
        input_left=m_scratch_left.data();input_right=m_scratch_right.data();
    }
    std::array<NativeStream::Midi,NativeStream::max_events> events{};
    int count=data.inputEvents ? data.inputEvents->getEventCount() : 0;
    if(count<0 || count>NativeStream::max_events) return reject();
    for(int i=0;i<count;++i) {
        Event e{};
        if(data.inputEvents->getEvent(i,e)!=kResultOk || e.busIndex!=0 || e.sampleOffset<0 || e.sampleOffset>=data.numSamples)
            return reject();
        if(e.type!=kNoteOnEvent && e.type!=kNoteOffEvent) return reject();
        const auto channel=e.type==kNoteOnEvent ? e.noteOn.channel : e.noteOff.channel;
        const auto pitch=e.type==kNoteOnEvent ? e.noteOn.pitch : e.noteOff.pitch;
        const auto velocity=e.type==kNoteOnEvent ? e.noteOn.velocity : e.noteOff.velocity;
        if(channel<0 || channel>15 || pitch<0 || pitch>127 || !std::isfinite(velocity) || velocity<0 || velocity>1)
            return reject();
        events[i]={unsigned(e.sampleOffset),{std::uint8_t((e.type==kNoteOnEvent ? 0x90 : 0x80)|channel),
            std::uint8_t(pitch),std::uint8_t(velocity*127.f)}};
    }
    const int queues=changes ? changes->getParameterCount() : 0;
    if(queues<0 || queues>NativeStream::max_events) return reject();
    for(int q=0;q<queues;++q) {
        auto* queue=changes->getParameterData(q);
        if(!queue) return reject();
        const auto id=queue->getParameterId();
        if(id<midi_parameter_base || id>=midi_parameter_base+midi_parameters) return reject();
        const auto index=id-midi_parameter_base,channel=index/129,controller=index%129;
        const int points=queue->getPointCount();
        if(points<0 || points>NativeStream::max_events-count) return reject();
        int previous=-1;
        for(int p=0;p<points;++p) {
            int offset=0;double value=0;
            if(queue->getPoint(p,offset,value)!=kResultOk || offset<previous || offset<0 || offset>=data.numSamples || !std::isfinite(value) || value<0 || value>1) return reject();
            previous=offset;
            const unsigned discrete=unsigned(std::lround(value*(controller==128 ? 16383 : 127)));
            events[count++]={unsigned(offset),controller==128 ? std::array<std::uint8_t,3>{std::uint8_t(0xe0|channel),std::uint8_t(discrete&127),std::uint8_t(discrete>>7)} : std::array<std::uint8_t,3>{std::uint8_t(0xb0|channel),std::uint8_t(controller),std::uint8_t(discrete)}};
        }
    }
    // Stable bounded insertion sort: note events precede controller queues at
    // equal offsets; each queue retains host ordering. No callback allocations.
    for(int i=1;i<count;++i) {
        const auto event=events[i];int j=i;
        while(j>0 && events[j-1].offset>event.offset) {events[j]=events[j-1];--j;}
        events[j]=event;
    }
    auto& out=data.outputs[0];
    if(!m_native_stream->process(out.channelBuffers32[0],out.channelBuffers32[1],unsigned(data.numSamples),events.data(),unsigned(count),m_process_mode==2,input_left,input_right))
        return kResultFalse;
    out.silenceFlags=0;
    return kResultOk;
}

tresult S760Vst3Plugin::process(Steinberg::ProcessData& data) {
    if(m_selected_host) return process_native(data);
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

namespace {
bool state_transfer(Steinberg::IBStream* stream,void* data,std::size_t bytes,bool write) {
    auto* p=static_cast<std::uint8_t*>(data);
    while(bytes) {
        auto request=int32_t(std::min<std::size_t>(bytes,1024*1024));int32_t done=0;
        auto result=write ? stream->write(p,request,&done) : stream->read(p,request,&done);
        if(result!=kResultOk || done<=0 || done>request) return false;
        p+=done;bytes-=done;
    } return true;
}
}
tresult S760Vst3Plugin::get_native_state(Steinberg::IBStream* state) {
    // Hosts must quiesce process() before state operations. No serialization or
    // disk/network access is introduced into the realtime callback.
    if(!state || m_is_processing || m_native_state_failed || !native_host()->native_runtime()) return kResultFalse;
    NativePluginState saved;bool captured_stream=false,was_running=false;
    auto* native=native_host()->native_runtime();
    try {
        saved.rate=unsigned(m_sample_rate);saved.max_block=m_max_block_size;saved.origin=m_native_origin;
        saved.has_stream=bool(m_native_stream);
        if(saved.has_stream) {
            m_native_stream->stop();saved.stream=m_native_stream->snapshot();captured_stream=true;
            saved.converter=m_native_converter->snapshot();
        } else was_running=native->request("{\"op\":\"status\"}").json.find("\"running\"")!=std::string::npos;
        native->request("{\"op\":\"pause\"}");
        saved.identity=native->checkpoint_identity();saved.machine=native->save_checkpoint();
        saved.media=native_host()->media_library().state();
        auto bytes=saved.encode();
        if(captured_stream) {rebuild_native_stream(&saved.stream);captured_stream=false;}
        if(was_running) {native->request("{\"op\":\"resume\"}");was_running=false;}
        std::uint32_t size=std::uint32_t(bytes.size());
        return state_transfer(state,&size,4,true) && state_transfer(state,bytes.data(),bytes.size(),true) ? kResultOk : kResultFalse;
    } catch(...) {
        try {if(captured_stream) rebuild_native_stream(&saved.stream);if(was_running) native->request("{\"op\":\"resume\"}");} catch(...) {}
        return kResultFalse;
    }
}
tresult S760Vst3Plugin::set_native_state(Steinberg::IBStream* state) {
    if(!state || m_is_processing || !native_host()->native_runtime()) return kResultFalse;
    auto* native=native_host()->native_runtime();
    bool applying=false;
    const char* stage="decode/identity";
    try {
        std::uint32_t size=0;
        if(!state_transfer(state,&size,4,false) || size>NativePluginState::max_bytes || size<40) return kResultFalse;
        std::vector<std::uint8_t> bytes(size);
        if(!state_transfer(state,bytes.data(),size,false)) return kResultFalse;
        auto saved=NativePluginState::decode(bytes);
        if(saved.rate!=m_sample_rate || saved.max_block!=unsigned(m_max_block_size) || saved.identity!=native->checkpoint_identity()) return kResultFalse;
        // Allocate/validate replacement host objects before touching the machine.
        std::shared_ptr<NativeRateConverter> converter;
        if(saved.has_stream) converter=std::make_shared<NativeRateConverter>(saved.converter,[native](float* pcm,std::size_t n){return native->render(pcm,n);});
        applying=true; // Any failure after stopping the worker requires a successful reload.
        m_native_state_failed=true;
        if(m_native_stream) m_native_stream->stop();
        stage="pause";
        native->request("{\"op\":\"pause\"}");
        stage="load checkpoint";
        native->load_checkpoint(saved.machine);
        stage="restore host state";
        native_host()->restore_media(std::move(saved.media));
        m_native_stream.reset();m_native_converter=std::move(converter);m_native_origin=saved.origin;
        if(saved.has_stream) rebuild_native_stream(&saved.stream);
        m_native_state_failed=false;
        return kResultOk;
    } catch(const std::exception& error) {
        std::cerr<<"[S760 native state restore: "<<stage<<"] "<<error.what()<<'\n';
        if(applying && m_native_stream) m_native_stream->fail(NativeStream::Fault::renderer_failed);
        return kResultFalse;
    } catch(...) {
        // An apply failure must never run a partially restored timeline.
        if(applying && m_native_stream) m_native_stream->fail(NativeStream::Fault::renderer_failed);
        return kResultFalse;
    }
}

tresult S760Vst3Plugin::getState(Steinberg::IBStream* state) {
    if(m_native_mode) return get_native_state(state);
    if(m_selected_host) return kResultFalse; // Never serialize a different machine.
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
    if(m_native_mode) return set_native_state(state);
    if(m_selected_host) return kResultFalse;
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
// IEditController (editor half) â€” vends the WebView-backed editor view.
// -----------------------------------------------------------------------------
tresult S760Vst3Plugin::setComponentState(Steinberg::IBStream* state) {
    (void)state; // no automatable parameters mirrored into the editor yet
    return kResultOk;
}

int32_t S760Vst3Plugin::getParameterCount() { return m_native_mode ? midi_parameters : 0; }

tresult S760Vst3Plugin::getMidiControllerAssignment(int32_t bus,int16_t channel,int16_t controller,uint32_t& id) {
    if(!m_native_mode || bus!=0 || channel<0 || channel>15 || controller<0 || controller>129 || controller==128) return kResultFalse;
    id=midi_parameter_base+channel*129+(controller==129 ? 128 : controller);return kResultOk;
}

tresult S760Vst3Plugin::getParameterInfo(int32_t paramIndex, void* info) {
    if(!m_native_mode || !info || paramIndex<0 || paramIndex>=midi_parameters) return kResultFalse;
    auto& parameter=*static_cast<Steinberg::ParameterInfo*>(info);parameter={};
    parameter.id=midi_parameter_base+paramIndex;
    const auto controller=paramIndex%129;
    const std::string title="MIDI Ch "+std::to_string(paramIndex/129+1)+(controller==128 ? " Pitch Bend" : " CC "+std::to_string(controller));
    std::copy(title.begin(),title.end(),parameter.title);
    parameter.stepCount=controller==128 ? 16383 : 127;
    parameter.defaultNormalizedValue=controller==128 ? 8192.0/16383.0 : 0;
    parameter.flags=1|16; // automatable, hidden MIDI transport aliases
    return kResultOk;
}

tresult S760Vst3Plugin::getParamStringByValue(uint32_t id, double valueNormalized, void* string) {
    if(m_native_mode && string && id>=midi_parameter_base && id<midi_parameter_base+midi_parameters && std::isfinite(valueNormalized) && valueNormalized>=0 && valueNormalized<=1) {
        const auto text=std::to_string(std::lround(normalizedParamToPlain(id,valueNormalized)));
        auto* out=static_cast<char16_t*>(string);std::copy(text.begin(),text.end(),out);out[text.size()]=0;return kResultOk;
    }
    return kResultFalse;
}

tresult S760Vst3Plugin::getParamValueByString(uint32_t id, char16_t* string, double* valueNormalized) {
    if(m_native_mode && string && *string && valueNormalized && id>=midi_parameter_base && id<midi_parameter_base+midi_parameters) {
        unsigned value=0;
        for(unsigned i=0;string[i];++i) {
            if(i>=5 || string[i]<u'0' || string[i]>u'9') return kInvalidArgument;
            value=value*10+unsigned(string[i]-u'0');
        }
        const unsigned maximum=(id-midi_parameter_base)%129==128 ? 16383 : 127;
        if(value>maximum) return kInvalidArgument;
        *valueNormalized=double(value)/maximum;return kResultOk;
    }
    return kResultFalse;
}

double S760Vst3Plugin::normalizedParamToPlain(uint32_t id, double valueNormalized) {
    if(m_native_mode && id>=midi_parameter_base && id<midi_parameter_base+midi_parameters)
        return valueNormalized*((id-midi_parameter_base)%129==128 ? 16383 : 127);
    return valueNormalized;
}

double S760Vst3Plugin::plainParamToNormalized(uint32_t id, double plainValue) {
    if(m_native_mode && id>=midi_parameter_base && id<midi_parameter_base+midi_parameters)
        return plainValue/((id-midi_parameter_base)%129==128 ? 16383 : 127);
    return plainValue;
}

double S760Vst3Plugin::getParamNormalized(uint32_t id) {
    if(m_native_mode && id>=midi_parameter_base && id<midi_parameter_base+midi_parameters) return m_midi_values[id-midi_parameter_base].load();
    return 0.0;
}

tresult S760Vst3Plugin::setParamNormalized(uint32_t id, double value) {
    if(m_native_mode) {
        if(id<midi_parameter_base || id>=midi_parameter_base+midi_parameters || !std::isfinite(value) || value<0 || value>1) return kInvalidArgument;
        m_midi_values[id-midi_parameter_base].store(value);return kResultOk;
    }
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
    return new S760Vst3PlugView(&m_bridge,m_native_ui_url);
}

// -----------------------------------------------------------------------------
// VST3 Factory Implementation
// -----------------------------------------------------------------------------

static std::filesystem::path native_environment_path(const char* key) {
#if defined(_WIN32)
    const std::wstring wide_key(key,key+std::strlen(key));
    const auto* value=_wgetenv(wide_key.c_str());
#else
    const auto* value=std::getenv(key);
#endif
    return value ? std::filesystem::path(value) : std::filesystem::path{};
}

static std::filesystem::path native_settings_path() {
    auto explicit_path=native_environment_path("S760_PLUGIN_CONFIG");
    if(!explicit_path.empty()) {
        if(!explicit_path.is_absolute()) throw std::runtime_error("S760_PLUGIN_CONFIG must be an absolute path");
        return explicit_path;
    }
    auto appdata=native_environment_path("LOCALAPPDATA");
    return appdata.is_absolute()?appdata/"S760"/"plugin-settings.json":std::filesystem::path{};
}

static std::string configuration_json(const rapidjson::Value& value) {
    rapidjson::StringBuffer buffer;rapidjson::Writer<rapidjson::StringBuffer> writer(buffer);
    value.Accept(writer);return {buffer.GetString(),buffer.GetSize()};
}

void S760Vst3Plugin::initialize_configuration(const NativeRuntimeConfig& config) {
    rapidjson::Document d;d.SetObject();auto& a=d.GetAllocator();
    auto put=[&](const char* key,const std::filesystem::path& path) {
        const auto text=path.u8string();d.AddMember(rapidjson::Value(key,a),rapidjson::Value(text.c_str(),rapidjson::SizeType(text.size()),a),a);
    };
    d.AddMember("version",1,a);put("root",config.root);put("stateRoot",config.state.parent_path());
    put("bootRom",config.boot_rom);put("systemDisk",config.system_disk);
    d.AddMember("waveMemoryMb",config.wave_memory_mb,a);
    put("mediaDirectory",config.media_directory.empty()?config.root/"roms/FDD":config.media_directory);
    try {
        const auto path=native_settings_path();
        if(m_configuration_pending && std::filesystem::is_regular_file(path) && std::filesystem::file_size(path)<=32768) {
            std::ifstream file(path,std::ios::binary);std::string bytes((std::istreambuf_iterator<char>(file)),{});
            rapidjson::Document saved;saved.Parse<rapidjson::kParseValidateEncodingFlag>(bytes.data(),bytes.size());
            if(!saved.HasParseError() && saved.IsObject()) for(auto key:{"root","stateRoot","bootRom","systemDisk","mediaDirectory"})
                if(saved.HasMember(key) && saved[key].IsString()) d[key].CopyFrom(saved[key],a);
        }
    } catch(...) {} // Keep the startup error and editable defaults visible.
    m_configuration_json=configuration_json(d);
}

std::string S760Vst3Plugin::configuration_snapshot() const {
    rapidjson::Document d;d.Parse(m_configuration_json.c_str());auto& a=d.GetAllocator();
    d.AddMember("needsConfiguration",m_configuration_pending,a);
    d.AddMember("saved",m_configuration_saved,a);d.AddMember("revision",m_configuration_revision,a);
    d.AddMember("error",rapidjson::Value(m_configuration_error.c_str(),a),a);
    d.AddMember("startupError",rapidjson::Value(m_startup_error.c_str(),a),a);
    return configuration_json(d);
}

bool S760Vst3Plugin::configure_from_editor(const std::string& json) {
    if(json.size()>32768) {
        if(json.find("\"CONFIGURE_PLUGIN\"")>64) return false;
        ++m_configuration_revision;m_configuration_saved=false;m_configuration_error="Plugin settings exceed 32KB";return true;
    }
    rapidjson::Document request;request.Parse<rapidjson::kParseValidateEncodingFlag>(json.data(),json.size());
    if(request.HasParseError() || !request.IsObject() || !request.HasMember("type") || !request["type"].IsString() ||
       std::strcmp(request["type"].GetString(),"CONFIGURE_PLUGIN")) return false;
    ++m_configuration_revision;m_configuration_saved=false;
    try {
        if(!request.HasMember("payload") || !request["payload"].IsObject()) throw std::runtime_error("Missing plugin settings");
        const auto& p=request["payload"];
        if(!p.HasMember("confirmReload") || !p["confirmReload"].IsBool() || !p["confirmReload"].GetBool())
            throw std::runtime_error("Confirm applying settings after plugin reload");
        rapidjson::Document saved;saved.SetObject();auto& a=saved.GetAllocator();saved.AddMember("version",1,a);
        auto path=[&](const char* key) {
            if(!p.HasMember(key) || !p[key].IsString()) throw std::runtime_error(std::string("Missing ")+key);
            const auto& v=p[key];std::string text(v.GetString(),v.GetStringLength());
            if(text.empty() || text.size()>4096 || text.find('\0')!=std::string::npos) throw std::runtime_error(std::string("Invalid ")+key);
            auto result=std::filesystem::u8path(text);
            if(!result.is_absolute()) throw std::runtime_error(std::string(key)+" must be an absolute path");
            saved.AddMember(rapidjson::Value(key,a),rapidjson::Value(text.c_str(),a),a);return result;
        };
        unsigned memory=32;
        if(p.HasMember("waveMemoryMb")) {
            if(!p["waveMemoryMb"].IsUint()) throw std::runtime_error("Wave memory must be 8, 16 or 32 MB");
            memory=p["waveMemoryMb"].GetUint();
        }
        if(memory!=8 && memory!=16 && memory!=32) throw std::runtime_error("Wave memory must be 8, 16 or 32 MB");
        saved.AddMember("waveMemoryMb",memory,a);
        const auto root=path("root"),state=path("stateRoot"),boot=path("bootRom"),system=path("systemDisk"),media=path("mediaDirectory");
        for(auto file:{root/"mame-source/mames760.exe",root/"scripts/s760_runtime.lua",root/"google-ui/dist/index.html",boot,system}) {
            if(!std::filesystem::is_regular_file(file)) throw std::runtime_error("Missing runtime or firmware file: "+file.u8string());
            std::ifstream readable(file,std::ios::binary);if(!readable) throw std::runtime_error("Unreadable file: "+file.u8string());
        }
        if(std::filesystem::file_size(boot)!=32768 || std::filesystem::file_size(system)!=1474560)
            throw std::runtime_error("Boot ROM must be 32768 bytes and system disk must be 1474560 bytes");
        if(!std::filesystem::is_directory(media)) throw std::runtime_error("Media directory does not exist: "+media.u8string());
        if(std::filesystem::exists(state) && !std::filesystem::is_directory(state)) throw std::runtime_error("stateRoot must be a directory");
        const auto target=native_settings_path();if(!target.is_absolute()) throw std::runtime_error("No absolute plugin settings filename is configured");
        for(auto file:{boot,system,root/"mame-source/mames760.exe",root/"scripts/s760_runtime.lua",root/"google-ui/dist/index.html"})
            if(std::filesystem::weakly_canonical(target)==std::filesystem::weakly_canonical(file) ||
               (std::filesystem::exists(target) && std::filesystem::equivalent(target,file))) throw std::runtime_error("Settings filename must not overwrite firmware or runtime files");
        const auto bytes=configuration_json(saved);
        std::filesystem::create_directories(target.parent_path());
        auto temporary=target;temporary+="."+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+".tmp";
        try {
            {std::ofstream file(temporary,std::ios::binary|std::ios::trunc);file.write(bytes.data(),bytes.size());file.flush();if(!file) throw std::runtime_error("Cannot write plugin settings");}
#if defined(_WIN32)
            if(!MoveFileExW(temporary.c_str(),target.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)) throw std::runtime_error("Cannot replace plugin settings");
#else
            std::filesystem::rename(temporary,target);
#endif
        } catch(...) {std::error_code ignored;std::filesystem::remove(temporary,ignored);throw;}
        m_configuration_json=bytes;m_configuration_error.clear();m_configuration_saved=true;
    } catch(const std::exception& error) {m_configuration_error=error.what();}
    return true;
}

static void report_native_startup_error(const std::string& reason) noexcept {
    try {
        std::string message="S-760 plugin startup failed: "+reason+
            "\nRun python scripts/configure_vst3.py --help from the S-760 installation to validate and save paths; then reload the plugin.\n";
        const auto settings=native_settings_path();
        if(!settings.empty()) {
            message+="Settings: "+settings.u8string()+"\n";
            std::filesystem::create_directories(settings.parent_path());
            // Best-effort last failure, separate from configuration/session data.
            auto diagnostic=settings; diagnostic += ".last-error.txt";
            std::ofstream file(diagnostic,std::ios::trunc|std::ios::binary);
            file<<message;
            message+="Diagnostic: "+diagnostic.u8string()+"\n";
        }
        std::cerr<<message;
    } catch(...) { std::cerr<<"S-760 plugin startup failed: "<<reason<<'\n'; }
}

static NativeRuntimeConfig native_factory_config() {
    NativeRuntimeConfig config;config.experimental_adc=true;
    config.root=native_environment_path("S760_NATIVE_ROOT");
    auto state_root=native_environment_path("S760_NATIVE_STATE_ROOT");
    config.boot_rom=native_environment_path("S760_BOOT_ROM");
    config.system_disk=native_environment_path("S760_SYSTEM_DISK");
    // Complete explicit environment configuration remains supported for hosts
    // and isolated tests. Otherwise fill missing values from persistent UTF-8 JSON.
    if(config.root.empty() || state_root.empty() || config.boot_rom.empty() || config.system_disk.empty()) {
        auto settings=native_settings_path();
        if(!settings.empty() && std::filesystem::exists(settings)) {
            if(std::filesystem::file_size(settings)>32768) throw std::runtime_error("Plugin settings exceed 32KB");
            std::ifstream file(settings,std::ios::binary);
            if(!file) throw std::runtime_error("Cannot read plugin settings: "+settings.u8string());
            std::string bytes((std::istreambuf_iterator<char>(file)),{});
            rapidjson::Document document;
            document.Parse<rapidjson::kParseValidateEncodingFlag>(bytes.data(),bytes.size());
            if(document.HasParseError() || !document.IsObject() || !document.HasMember("version") ||
               !document["version"].IsInt() || document["version"].GetInt()!=1)
                throw std::runtime_error("Invalid plugin settings JSON/version");
            auto fill=[&](std::filesystem::path& path,const char* key) {
                if(!path.empty()) return;
                if(!document.HasMember(key) || !document[key].IsString())
                    throw std::runtime_error(std::string("Missing plugin setting: ")+key);
                const auto& value=document[key];
                std::string text(value.GetString(),value.GetStringLength());
                if(text.empty() || text.size()>4096 || text.find('\0')!=std::string::npos)
                    throw std::runtime_error(std::string("Invalid plugin setting: ")+key);
                path=std::filesystem::u8path(text);
            };
            if(document.HasMember("waveMemoryMb")) {
                if(!document["waveMemoryMb"].IsUint()) throw std::runtime_error("Wave memory must be 8, 16 or 32 MB");
                config.wave_memory_mb=document["waveMemoryMb"].GetUint();
                if(config.wave_memory_mb!=8 && config.wave_memory_mb!=16 && config.wave_memory_mb!=32)
                    throw std::runtime_error("Wave memory must be 8, 16 or 32 MB");
            }
            fill(config.root,"root"); fill(state_root,"stateRoot");
            fill(config.boot_rom,"bootRom"); fill(config.system_disk,"systemDisk");
            if(document.HasMember("mediaDirectory")) fill(config.media_directory,"mediaDirectory");
        }
    }
    // Explicit paths make scanner/host working directories irrelevant. Firmware
    // is user supplied; never fall back to the historical emulation backend.
    if(!config.root.is_absolute() || !state_root.is_absolute() ||
       !config.boot_rom.is_absolute() || !config.system_disk.is_absolute())
        throw std::runtime_error("Configure absolute root, stateRoot, bootRom and systemDisk paths (or the four S760 runtime environment overrides)");
    for(const auto& path:{config.root/"mame-source/mames760.exe",config.root/"scripts/s760_runtime.lua",config.boot_rom,config.system_disk})
        if(!std::filesystem::is_regular_file(path)) throw std::runtime_error("Missing native runtime or firmware file: "+path.string());
    if(!std::getenv("S760_UI_URL") && !std::filesystem::is_regular_file(config.root/"google-ui/dist/index.html"))
        throw std::runtime_error("Build the React editor with npm run build in google-ui before loading the plugin");
    if(std::filesystem::file_size(config.boot_rom)!=32768 || std::filesystem::file_size(config.system_disk)!=1474560)
        throw std::runtime_error("Boot ROM must be 32768 bytes and system disk must be 1474560 bytes");
    if(!config.media_directory.empty() && (!config.media_directory.is_absolute() || !std::filesystem::is_directory(config.media_directory)))
        throw std::runtime_error("Media directory must name an existing absolute directory");
    std::filesystem::create_directories(state_root);
    static std::atomic<unsigned long long> next{0};
    for(unsigned retry=0;retry<100;++retry) {
        config.state=state_root/("vst3-"+std::to_string(std::chrono::steady_clock::now().time_since_epoch().count())+"-"+std::to_string(next++));
        if(std::filesystem::create_directory(config.state)) return config;
    }
    throw std::runtime_error("Cannot allocate an independent native instance directory");
}

static NativeRuntimeConfig configuration_editor_defaults() {
    NativeRuntimeConfig config;config.experimental_adc=true;config.root=native_environment_path("S760_NATIVE_ROOT");
#if defined(_WIN32)
    HMODULE module=nullptr;wchar_t path[32768]{};
    if(GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&configuration_editor_defaults),&module) && GetModuleFileNameW(module,path,32768)) {
        auto folder=std::filesystem::path(path).parent_path();
        for(unsigned i=0;i<10 && !folder.empty();++i,folder=folder.parent_path())
            if(std::filesystem::is_regular_file(folder/"google-ui/dist/index.html")) {config.root=folder;break;}
    }
#endif
    if(!std::getenv("S760_UI_URL") && !std::filesystem::is_regular_file(config.root/"google-ui/dist/index.html"))
        throw std::runtime_error("Plugin editor files are missing; repair the S-760 installation");
    auto state=native_environment_path("S760_NATIVE_STATE_ROOT");
    if(state.empty()) state=native_environment_path("LOCALAPPDATA")/"S760/runtime";
    config.state=state/"unconfigured";
    config.boot_rom=native_environment_path("S760_BOOT_ROM");config.system_disk=native_environment_path("S760_SYSTEM_DISK");
    return config;
}

class S760Vst3Factory : public Steinberg::IPluginFactory2 {
public:
    tresult queryInterface(const TUID _iid, void** obj) override {
        if (!obj) return kInvalidArgument;
        *obj=nullptr;
        static const TUID factoryId=INLINE_UID(0x7A4D811C,0x52114A1F,0xAED9D2EE,0x0B43BF9F);
        static const TUID factory2Id=INLINE_UID(0x0007B650,0xF24B4C0B,0xA464EDB9,0xF00B2ABB);
        if(std::memcmp(_iid,FUnknown_iid,16) && std::memcmp(_iid,factoryId,16) && std::memcmp(_iid,factory2Id,16)) return kResultFalse;
        *obj=static_cast<Steinberg::IPluginFactory*>(this); addRef(); return kResultOk;
    }
    uint32_t addRef() override { return 1; }
    uint32_t release() override { return 1; }

    tresult getFactoryInfo(void* info) override {
        if(!info) return kInvalidArgument;
        auto& value=*static_cast<Steinberg::PFactoryInfo*>(info); value={};
        std::strcpy(value.vendor,"S-760 Emulator Contributors");
        std::strcpy(value.url,"https://github.com/JefroB/s760-Emulator");
        return kResultOk;
    }

    int32_t countClasses() override {
        return 1; // Native instrument. Live-sampling FX requires native ADC.
    }

    tresult getClassInfo(int32_t index, Steinberg::PClassInfo* info) override {
        if (!info) return kInvalidArgument;
        if (index == 0) {
            *info={};
            std::memcpy(info->cid, S760ProcessorUID, 16);
            info->cardinality = 0x7fffffff;
            std::strncpy(info->category, "Audio Module Class", sizeof(info->category) - 1);
            std::strncpy(info->name, "Roland S-760 Sampler", sizeof(info->name) - 1);
            return kResultOk;
        }
        return kInvalidArgument;
    }

    tresult getClassInfo2(int32_t index, Steinberg::PClassInfo2* info) override {
        if(!info || index!=0) return kInvalidArgument;
        *info={};
        std::memcpy(info->cid,S760ProcessorUID,16);
        info->cardinality=0x7fffffff;
        std::strcpy(info->category,"Audio Module Class");
        std::strcpy(info->name,"Roland S-760 Sampler");
        std::strcpy(info->subCategories,"Instrument|Sampler");
        std::strcpy(info->vendor,"S-760 Emulator Contributors");
        std::strcpy(info->version,"1.0.0");
        std::strcpy(info->sdkVersion,"VST 3");
        return kResultOk;
    }

    tresult createInstance(FIDString cid, FIDString _iid, void** obj) override {
        if (!obj) return kInvalidArgument;
        *obj=nullptr;
        if(!cid || !_iid || std::memcmp(cid,S760ProcessorUID,16)!=0) return kInvalidArgument;
        if(std::memcmp(_iid,FUnknown_iid,16) && std::memcmp(_iid,IComponent_iid,16) &&
           std::memcmp(_iid,IAudioProcessor_iid,16) && std::memcmp(_iid,IEditController_iid,16)) return kResultFalse;
        try {
            auto* plugin = new S760Vst3Plugin(native_factory_config());
            auto result=plugin->queryInterface(reinterpret_cast<const std::uint8_t*>(_iid),obj);
            plugin->release(); // queryInterface owns the returned reference.
            return result;
        } catch(const std::exception& error) {
            report_native_startup_error(error.what());
            try {
                auto* plugin=new S760Vst3Plugin(configuration_editor_defaults(),error.what());
                auto result=plugin->queryInterface(reinterpret_cast<const std::uint8_t*>(_iid),obj);
                plugin->release();return result;
            } catch(...) {return kResultFalse;}
        } catch(...) {
            return kInternalError; // Never unwind through a host/plugin ABI.
        }
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
