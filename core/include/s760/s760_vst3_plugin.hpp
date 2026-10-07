#pragma once

#include "s760/vst3_defs.h"
#include "s760/s760_libretro_host.hpp"

#include <atomic>
#include <vector>
#include <string>

namespace s760 {

class S760Vst3Plugin : public Steinberg::IComponent, public Steinberg::IAudioProcessor {
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

    S760LibretroHost& get_host() { return m_host; }

private:
    std::atomic<uint32_t> m_ref_count{1};
    S760LibretroHost m_host;

    double m_sample_rate = 44100.0;
    int32_t m_max_block_size = 512;
    bool m_is_active = false;
    bool m_is_processing = false;
    bool m_is_fx = false;

    std::vector<float> m_scratch_left;
    std::vector<float> m_scratch_right;

    void process_events(Steinberg::IEventList* events);
};

} // namespace s760
