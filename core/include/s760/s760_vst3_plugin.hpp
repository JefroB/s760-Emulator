#pragma once

#include "s760/vst3_defs.h"
#include "s760/s760_libretro_host.hpp"
#include "s760/s760_backend_selector.hpp"
#include "s760/s760_bridge.hpp"
#include "s760/s760_webview_host.hpp"

#include <atomic>
#include <memory>
#include <vector>
#include <string>

namespace s760 {

class S760Vst3PlugView; // WebView-backed IPlugView (defined in the .cpp)

// Single-component VST3 effect: implements IComponent + IAudioProcessor (audio)
// AND IEditController (editor) so one object vends both the processor and the
// WebView-backed editor view (task 3.6). The editor is bound to the plugin's
// in-process S760Bridge.
class S760Vst3Plugin : public Steinberg::IComponent,
                       public Steinberg::IAudioProcessor,
                       public Steinberg::IEditController {
public:
    explicit S760Vst3Plugin(bool is_fx = false);
    virtual ~S760Vst3Plugin();

    // FUnknown
    tresult queryInterface(const TUID _iid, void** obj) override;
    uint32_t addRef() override;
    uint32_t release() override;

    // IPluginBase
    tresult initialize(Steinberg::FUnknown* context) override;
    tresult terminate() override;

    // IComponent
    tresult getControllerClassId(TUID classId) override;
    tresult setIoMode(int32_t mode) override;
    tresult getBusCount(int32_t type, int32_t dir) override;
    tresult getBusInfo(int32_t type, int32_t dir, int32_t index, void* bus) override;
    tresult getRoutingInfo(void* inInfo, void* outInfo) override;
    tresult activateBus(int32_t type, int32_t dir, int32_t index, bool state) override;
    tresult setActive(bool state) override;
    tresult setState(Steinberg::IBStream* state) override;
    tresult getState(Steinberg::IBStream* state) override;

    // IAudioProcessor
    tresult setBusArrangements(void* inputs, int32_t numIns, void* outputs, int32_t numOuts) override;
    tresult getBusArrangement(int32_t dir, int32_t index, void* arr) override;
    tresult canProcessSampleSize(int32_t symbolicSampleSize) override;
    uint32_t getLatencySamples() override;
    tresult setupProcessing(Steinberg::ProcessSetup& setup) override;
    tresult setProcessing(bool state) override;
    tresult process(Steinberg::ProcessData& data) override;
    uint32_t getTailSamples() override;

    // IEditController (editor half). initialize/terminate/setState/getState are
    // shared with IComponent (same signatures via IPluginBase) and implemented
    // once above.
    tresult setComponentState(Steinberg::IBStream* state) override;
    int32_t getParameterCount() override;
    tresult getParameterInfo(int32_t paramIndex, void* info) override;
    tresult getParamStringByValue(uint32_t id, double valueNormalized, void* string) override;
    tresult getParamValueByString(uint32_t id, char16_t* string, double* valueNormalized) override;
    double normalizedParamToPlain(uint32_t id, double valueNormalized) override;
    double plainParamToNormalized(uint32_t id, double plainValue) override;
    double getParamNormalized(uint32_t id) override;
    tresult setParamNormalized(uint32_t id, double value) override;
    tresult setComponentHandler(void* handler) override;
    Steinberg::IPlugView* createView(FIDString name) override;

    S760LibretroHost& get_host() { return m_host; }
    S760Bridge& get_bridge() { return m_bridge; }

private:
    std::atomic<uint32_t> m_ref_count{1};
    // Concrete Core backend. KEPT as a value member so all Core-specific
    // lifecycle/audio/savestate calls keep compiling and behaving exactly as
    // before (default Core path stays byte-for-byte identical on the wire).
    S760LibretroHost m_host;
    // Backend selector's chosen host (mame-live-backend task 9.3, R7.1).
    // Declared BEFORE m_bridge so it outlives the Bridge, which only borrows the
    // host pointer. Owns the MAME backend when selected; stays null for Core.
    std::unique_ptr<IS760Host> m_selected_host;
    S760Bridge m_bridge; // in-process UI bridge (3.2); editor view binds to it

    double m_sample_rate = 44100.0;
    int32_t m_max_block_size = 512;
    bool m_is_active = false;
    bool m_is_processing = false;
    bool m_is_fx = false;

    std::vector<float> m_scratch_left;
    std::vector<float> m_scratch_right;

    void process_events(Steinberg::IEventList* events);

    // Run the backend selector and decide which IS760Host the Bridge is driven
    // from (mame-live-backend task 9.3). Called from the constructor's
    // initializer list BEFORE m_bridge. Returns the MAME host when selected+
    // available (owned by m_selected_host), otherwise &m_host (default Core).
    IS760Host* select_bridge_host();
};

} // namespace s760
