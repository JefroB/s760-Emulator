#include "s760/clap_defs.h"
#include "s760/s760_clap_plugin.hpp"
#include "s760/vst_defs.h"
#include "s760/s760_vst_plugin.hpp"
#include "s760/vst3_defs.h"
#include "s760/s760_vst3_plugin.hpp"
#include "s760/s760_disk.hpp"

#include <iostream>
#include <vector>
#include <cassert>
#include <cstring>
#include <filesystem>

namespace fs = std::filesystem;

// -----------------------------------------------------------------------------
// CLAP Memory Stream
// -----------------------------------------------------------------------------
struct MemoryStream {
    std::vector<uint8_t> buffer;
    size_t read_pos = 0;
};

static int64_t mem_write(const struct clap_ostream *stream, const void *buf, uint64_t size) {
    auto* ms = static_cast<MemoryStream*>(stream->ctx);
    const uint8_t* ptr = static_cast<const uint8_t*>(buf);
    ms->buffer.insert(ms->buffer.end(), ptr, ptr + size);
    return static_cast<int64_t>(size);
}

static int64_t mem_read(const struct clap_istream *stream, void *buf, uint64_t size) {
    auto* ms = static_cast<MemoryStream*>(stream->ctx);
    if (ms->read_pos >= ms->buffer.size()) return 0;
    size_t avail = ms->buffer.size() - ms->read_pos;
    size_t to_read = std::min<size_t>(avail, static_cast<size_t>(size));
    std::memcpy(buf, ms->buffer.data() + ms->read_pos, to_read);
    ms->read_pos += to_read;
    return static_cast<int64_t>(to_read);
}

// Minimal Host Event List for CLAP
struct EventList {
    std::vector<clap_event_header_t*> events;
};

static uint32_t event_list_size(const struct clap_input_events *list) {
    auto* el = static_cast<EventList*>(list->ctx);
    return static_cast<uint32_t>(el->events.size());
}

static const clap_event_header_t* event_list_get(const struct clap_input_events *list, uint32_t index) {
    auto* el = static_cast<EventList*>(list->ctx);
    return (index < el->events.size()) ? el->events[index] : nullptr;
}

void test_clap_plugin_lifecycle_and_audio() {
    std::cout << "[TEST] CLAP Plugin Instantiation & Audio Processing..." << std::endl;

    clap_host_t host_ctx;
    std::memset(&host_ctx, 0, sizeof(host_ctx));
    host_ctx.clap_version = CLAP_VERSION;
    host_ctx.name = "Test DAW Host";

    auto* plugin = new s760::S760ClapPlugin(&host_ctx);
    const auto* clap_plug = plugin->get_clap_plugin();

    assert(clap_plug->init(clap_plug));
    assert(clap_plug->activate(clap_plug, 44100.0, 64, 512));
    assert(clap_plug->start_processing(clap_plug));

    // Load mock core into host to generate audio
    std::string core_path = "build/Release/mock_core.dll";
    if (!fs::exists(core_path)) core_path = "Release/mock_core.dll";
    if (!fs::exists(core_path)) core_path = "mock_core.dll";

    if (fs::exists(core_path)) {
        plugin->get_host().load_core(core_path);
        plugin->get_host().load_system("s760_os");
    }

    // Set up Note-On Event
    clap_event_note_t note_on;
    std::memset(&note_on, 0, sizeof(note_on));
    note_on.header.size = sizeof(note_on);
    note_on.header.type = CLAP_EVENT_NOTE_ON;
    note_on.header.space_id = CLAP_CORE_EVENT_SPACE_ID;
    note_on.channel = 0;
    note_on.key = 60; // Middle C
    note_on.velocity = 0.95;

    EventList in_events;
    in_events.events.push_back(&note_on.header);

    clap_input_events_t input_events_iface = {
        &in_events,
        event_list_size,
        event_list_get
    };

    // Prepare Audio Output Buffers (512 frames, stereo)
    std::vector<float> out_l(512, 0.0f);
    std::vector<float> out_r(512, 0.0f);
    float* channel_ptrs[2] = {out_l.data(), out_r.data()};

    clap_audio_buffer_t audio_out;
    audio_out.data32 = channel_ptrs;
    audio_out.data64 = nullptr;
    audio_out.channel_count = 2;
    audio_out.latency = 0;
    audio_out.constant_mask = 0;

    clap_process_t proc;
    std::memset(&proc, 0, sizeof(proc));
    proc.frames_count = 512;
    proc.audio_outputs = &audio_out;
    proc.audio_outputs_count = 1;
    proc.in_events = &input_events_iface;

    clap_process_status status = clap_plug->process(clap_plug, &proc);
    assert(status == CLAP_PROCESS_CONTINUE);

    if (plugin->get_host().is_system_running()) {
        assert(out_l[0] != 0.0f || out_r[0] != 0.0f);
    }

    clap_plug->stop_processing(clap_plug);
    clap_plug->deactivate(clap_plug);
    clap_plug->destroy(clap_plug);

    std::cout << "  -> CLAP Plugin Audio & Event Processing Tests PASSED!" << std::endl;
}

void test_clap_plugin_state_serialization() {
    std::cout << "[TEST] CLAP Plugin State Serialization & Project Recall..." << std::endl;

    fs::create_directories("test_plugin_disks");
    std::string test_floppy = "test_plugin_disks/session_floppy.img";
    std::string test_scsi = "test_plugin_disks/session_scsi.hda";

    s760::RolandS760Disk disk("DAW PROJECT VOL");
    disk.add_patch(1, "Lead Synth", {1}, 127, 0);
    auto img = disk.build_image();
    {
        std::ofstream f(test_floppy, std::ios::binary);
        f.write(reinterpret_cast<const char*>(img.data()), img.size());
    }
    auto scsi_img = disk.build_scsi_image_mb(2);
    {
        std::ofstream f(test_scsi, std::ios::binary);
        f.write(reinterpret_cast<const char*>(scsi_img.data()), scsi_img.size());
    }

    clap_host_t host_ctx;
    std::memset(&host_ctx, 0, sizeof(host_ctx));

    // Plugin Instance 1
    s760::S760ClapPlugin plug1(&host_ctx);
    plug1.get_host().get_drive_manager().mount_floppy(test_floppy);
    plug1.get_host().get_drive_manager().mount_scsi_device(1, test_scsi, s760::DeviceType::HardDisk_SCSI);

    // Save state to MemoryStream
    MemoryStream ms;
    clap_ostream_t out_stream = { &ms, mem_write };
    assert(plug1.state_save(&out_stream));
    assert(!ms.buffer.empty());

    // Plugin Instance 2 (Recall Project)
    s760::S760ClapPlugin plug2(&host_ctx);
    clap_istream_t in_stream = { &ms, mem_read };
    assert(plug2.state_load(&in_stream));

    auto f_stat = plug2.get_host().get_drive_manager().get_floppy_status();
    assert(f_stat.is_mounted == true);
    assert(f_stat.image_name == "session_floppy.img");

    auto s_stat = plug2.get_host().get_drive_manager().get_scsi_status(1);
    assert(s_stat.is_mounted == true);
    assert(s_stat.image_name == "session_scsi.hda");

    fs::remove_all("test_plugin_disks");
    std::cout << "  -> CLAP Plugin State Serialization Tests PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
// VST2 Test
// -----------------------------------------------------------------------------
extern "C" AEffect* VSTPluginMain(audioMasterCallback audioMaster);

void test_vst_plugin_lifecycle_and_audio() {
    std::cout << "[TEST] VST2 Plugin Instantiation & Audio Processing..." << std::endl;

    auto* effect = VSTPluginMain(nullptr);
    assert(effect != nullptr);
    assert(effect->magic == VST_MAGIC);
    assert(effect->numOutputs == 2);

    // Dispatch effOpen, effSetSampleRate, effSetBlockSize
    assert(effect->dispatcher(effect, effOpen, 0, 0, nullptr, 0.0f) == 1);
    assert(effect->dispatcher(effect, effSetSampleRate, 0, 0, nullptr, 44100.0f) == 1);
    assert(effect->dispatcher(effect, effSetBlockSize, 0, 512, nullptr, 0.0f) == 1);

    // Audio Output Buffers
    std::vector<float> out_l(512, 0.0f);
    std::vector<float> out_r(512, 0.0f);
    float* channel_ptrs[2] = {out_l.data(), out_r.data()};

    // Process audio
    effect->processReplacing(effect, nullptr, channel_ptrs, 512);

    // Test Chunk Save & Restore (DAW project state)
    void* chunk_ptr = nullptr;
    intptr_t chunk_sz = effect->dispatcher(effect, effGetChunk, 0, 0, &chunk_ptr, 0.0f);
    assert(chunk_sz > 0 && chunk_ptr != nullptr);

    assert(effect->dispatcher(effect, effSetChunk, 0, chunk_sz, chunk_ptr, 0.0f) == 1);

    // Close effect
    assert(effect->dispatcher(effect, effClose, 0, 0, nullptr, 0.0f) == 1);

    std::cout << "  -> VST2 Plugin Tests PASSED!" << std::endl;
}

// -----------------------------------------------------------------------------
// VST3 Test
// -----------------------------------------------------------------------------
class Vst3MemoryStream : public Steinberg::IBStream {
public:
    std::vector<uint8_t> buffer;
    int64_t pos = 0;

    tresult queryInterface(const TUID _iid, void** obj) override {
        (void)_iid;
        *obj = this;
        return kResultOk;
    }
    uint32_t addRef() override { return 1; }
    uint32_t release() override { return 1; }

    tresult read(void* buf, int32_t numBytes, int32_t* numBytesRead) override {
        if (pos >= static_cast<int64_t>(buffer.size())) {
            if (numBytesRead) *numBytesRead = 0;
            return kResultOk;
        }
        size_t avail = buffer.size() - static_cast<size_t>(pos);
        size_t to_read = std::min<size_t>(avail, static_cast<size_t>(numBytes));
        std::memcpy(buf, buffer.data() + pos, to_read);
        pos += to_read;
        if (numBytesRead) *numBytesRead = static_cast<int32_t>(to_read);
        return kResultOk;
    }

    tresult write(void* buf, int32_t numBytes, int32_t* numBytesWritten) override {
        const uint8_t* ptr = static_cast<const uint8_t*>(buf);
        buffer.insert(buffer.end(), ptr, ptr + numBytes);
        pos += numBytes;
        if (numBytesWritten) *numBytesWritten = numBytes;
        return kResultOk;
    }

    tresult seek(int64_t mode, int32_t mode_from, int64_t* result) override {
        if (mode_from == 0) pos = mode; // beg
        else if (mode_from == 1) pos += mode; // cur
        else if (mode_from == 2) pos = static_cast<int64_t>(buffer.size()) + mode; // end
        if (result) *result = pos;
        return kResultOk;
    }

    tresult tell(int64_t* result) override {
        if (result) *result = pos;
        return kResultOk;
    }
};

extern "C" Steinberg::IPluginFactory* GetPluginFactory();

void test_vst3_plugin_lifecycle_and_audio() {
    std::cout << "[TEST] VST3 Factory, Processor & State Persistence..." << std::endl;

    std::cout << "  [VST3 Debug] Factory queried..." << std::endl;
    auto* factory = GetPluginFactory();
    assert(factory != nullptr);
    assert(factory->countClasses() == 1);

    Steinberg::PClassInfo info;
    assert(factory->getClassInfo(0, &info) == kResultOk);
    assert(std::string(info.name).find("S-760") != std::string::npos);

    std::cout << "  [VST3 Debug] Creating instance..." << std::endl;
    void* plugin_obj = nullptr;
    assert(factory->createInstance(nullptr, nullptr, &plugin_obj) == kResultOk);
    assert(plugin_obj != nullptr);

    auto* plugin = static_cast<s760::S760Vst3Plugin*>(plugin_obj);
    auto* comp = static_cast<Steinberg::IComponent*>(plugin);
    auto* proc = static_cast<Steinberg::IAudioProcessor*>(plugin);

    std::cout << "  [VST3 Debug] Initializing & setupProcessing..." << std::endl;
    assert(comp->initialize(nullptr) == kResultOk);
    Steinberg::ProcessSetup setup;
    setup.sampleRate = 44100.0;
    setup.maxSamplesPerBlock = 512;
    setup.processMode = 0;
    setup.symbolicSampleSize = 0;
    assert(proc->setupProcessing(setup) == kResultOk);
    assert(comp->setActive(true) == kResultOk);
    assert(proc->setProcessing(true) == kResultOk);

    std::cout << "  [VST3 Debug] Processing audio block..." << std::endl;
    std::vector<float> out_l(512, 0.0f);
    std::vector<float> out_r(512, 0.0f);
    float* channel_ptrs[2] = {out_l.data(), out_r.data()};

    AudioBusBuffers out_bus;
    out_bus.numChannels = 2;
    out_bus.silenceFlags = 0;
    out_bus.channelBuffers32 = channel_ptrs;

    Steinberg::ProcessData pdata;
    std::memset(&pdata, 0, sizeof(pdata));
    pdata.numSamples = 512;
    pdata.numOutputs = 1;
    pdata.outputs = &out_bus;

    assert(proc->process(pdata) == kResultOk);

    std::cout << "  [VST3 Debug] State saving & restoring..." << std::endl;
    Vst3MemoryStream stream;
    assert(comp->getState(&stream) == kResultOk);
    assert(!stream.buffer.empty());

    stream.seek(0, 0, nullptr);
    assert(comp->setState(&stream) == kResultOk);

    std::cout << "  [VST3 Debug] Terminating..." << std::endl;
    assert(proc->setProcessing(false) == kResultOk);
    assert(comp->setActive(false) == kResultOk);
    assert(comp->terminate() == kResultOk);
    delete plugin;

    std::cout << "  -> VST3 Plugin Tests PASSED!" << std::endl;
}

int main() {
    std::cout << "==========================================" << std::endl;
    std::cout << "  Roland S-760 VST3, VST2 & CLAP DAW Suite" << std::endl;
    std::cout << "==========================================" << std::endl;

    try {
        test_clap_plugin_lifecycle_and_audio();
        test_clap_plugin_state_serialization();
        test_vst_plugin_lifecycle_and_audio();
        test_vst3_plugin_lifecycle_and_audio();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL VST3, VST2 & CLAP PLUGIN TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
