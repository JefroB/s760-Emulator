#pragma once
#include "s760/s760_native_plugin_state.hpp"
#include <functional>

class StateMemory : public Steinberg::IBStream {
public:
    std::vector<std::uint8_t> data;std::size_t offset=0;bool fail_write=false;
    tresult queryInterface(const TUID,void**) override{return kResultFalse;}
    uint32_t addRef() override{return 1;} uint32_t release() override{return 1;}
    tresult read(void* buffer,int32_t count,int32_t* actual) override {
        if(count<0 || offset>data.size()) return kResultFalse;
        auto n=std::min<std::size_t>({std::size_t(count),data.size()-offset,65521});
        std::memcpy(buffer,data.data()+offset,n);offset+=n;*actual=int32_t(n);return kResultOk;
    }
    tresult write(void* buffer,int32_t count,int32_t* actual) override {
        if(fail_write || count<0) return kResultFalse;
        auto n=std::min<std::size_t>(count,65521);auto* p=static_cast<std::uint8_t*>(buffer);
        data.insert(data.end(),p,p+n);offset=data.size();*actual=int32_t(n);return kResultOk;
    }
    tresult seek(int64_t position,int32_t from,int64_t* result) override {
        if(from || position<0 || std::size_t(position)>data.size()) return kResultFalse;
        offset=std::size_t(position);if(result)*result=position;return kResultOk;
    }
    tresult tell(int64_t* result) override{*result=offset;return kResultOk;}
};

static void state_acceptance(s760::S760Vst3Plugin& plugin,Steinberg::ProcessSetup setup,const std::filesystem::path& fixture,
        const std::function<std::shared_ptr<s760::S760Vst3Plugin>()>& create) {
    unsigned rate=unsigned(setup.sampleRate);
    auto& library=plugin.native_host()->media_library();
    auto mounted=library.state().inserted;
    check(!mounted.empty(),"Native media identity missing before save");
    // Browse a different image without changing the disk whose bytes are captured.
    auto source=std::filesystem::u8path(mounted);
    auto configured=std::filesystem::absolute(fixture);
    std::filesystem::create_directories(configured/"nested");
    std::filesystem::copy_file(source,configured/"first.img",std::filesystem::copy_options::overwrite_existing);
    std::filesystem::copy_file(source,configured/"nested"/"second.img",std::filesystem::copy_options::overwrite_existing);
    check(library.configure(configured.u8string()),"Recursive native media configure failed");
    auto paths=library.state().paths;
    auto other=std::find_if(paths.begin(),paths.end(),[&](const auto& p){return p!=mounted;});
    check(other!=paths.end() && library.select(*other),"Distinct browse selection unavailable");
    const auto media=library.state();
    const auto padding=s760::NativeRateConverter::host_samples(s760::NativeStream::output_delay,rate);
    auto render=[&](s760::S760Vst3Plugin& p,std::uint64_t first,unsigned frames,bool on,bool off) {
        std::vector<float> result;float left[1024],right[1024];float* channels[]{left,right};
        AudioBusBuffers output{2,0};output.channelBuffers32=channels;
        Steinberg::ProcessData data{};data.numOutputs=1;data.outputs=&output;
        Events events;data.inputEvents=&events;
        for(unsigned used=0;used<frames;) {
            auto count=std::min(1024u,frames-used);auto required=first+used+count>padding ? first+used+count-padding : 0;
            auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);
            while(p.native_stream()->completed_frames()<required) {
                check(p.native_stream()->fault()==s760::NativeStream::Fault::none,"State replay worker failed");
                check(std::chrono::steady_clock::now()<deadline,"State replay worker stalled");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
            events.present=used==0 && (on||off);events.event={};events.event.sampleOffset=17;
            events.event.type=on?kNoteOnEvent:kNoteOffEvent;
            if(on){events.event.noteOn.pitch=60;events.event.noteOn.velocity=1;}
            else {events.event.noteOff.pitch=60;}
            data.numSamples=count;check(p.process(data)==kResultOk,"State replay process failed");
            for(unsigned i=0;i<count;++i){result.push_back(left[i]);result.push_back(right[i]);}used+=count;
        } return result;
    };
    check(plugin.setActive(true)==kResultOk && plugin.setProcessing(true)==kResultOk,"State start failed");
    StateMemory rejected;
    check(plugin.getState(&rejected)==kResultFalse && rejected.data.empty(),"Running state operation accepted");
    render(plugin,0,64,true,false);
    check(plugin.setProcessing(false)==kResultOk,"State suspend failed");
    StateMemory early;
    check(plugin.getState(&early)==kResultOk,"Pending host-event save failed");
    auto inspect=s760::NativePluginState::decode({early.data.begin()+4,early.data.end()});
    check(inspect.stream.pending.size()==1 && inspect.stream.pending[0].events==1,"Pending host MIDI missing from archive");
    check(plugin.setProcessing(true)==kResultOk,"State resume failed");
    auto expected=render(plugin,64,rate,false,false);
    check(plugin.setProcessing(false)==kResultOk,"State reference suspend failed");
    // Restore must use captured media bytes even when the browse library has moved.
    auto relocated=configured;relocated+="-relocated";
    check(configured.parent_path()==relocated.parent_path(),"Fixture move escaped private parent");
    std::filesystem::rename(configured,relocated);
    check(source.parent_path()==configured.parent_path(),"Mounted fixture source is not private");
    auto moved_source=source;moved_source+=".relocated";
    std::filesystem::rename(source,moved_source);
    auto cold=create();check(cold->setupProcessing(setup)==kResultOk,"Cold state setup failed");
    auto invalid=inspect;invalid.machine={0};auto invalid_bytes=invalid.encode();
    StateMemory invalid_state;auto invalid_size=std::uint32_t(invalid_bytes.size());
    invalid_state.data.resize(4);std::memcpy(invalid_state.data.data(),&invalid_size,4);
    invalid_state.data.insert(invalid_state.data.end(),invalid_bytes.begin(),invalid_bytes.end());
    check(cold->setState(&invalid_state)==kResultFalse,"Invalid native checkpoint accepted");
    check(cold->setProcessing(true)==kResultFalse,"Failed native restore allowed processing");
    early.offset=0;check(cold->setState(&early)==kResultOk,"Fresh-instance pending state restore failed");
    auto restored_media=cold->native_host()->media_library().state();
    check(restored_media.folder==media.folder && restored_media.selected==media.selected && restored_media.inserted==media.inserted && restored_media.paths==media.paths,"Cold state lost media metadata");
    check(cold->setActive(true)==kResultOk && cold->setProcessing(true)==kResultOk,"Cold state start failed");
    check(render(*cold,64,rate,false,false)==expected,"Cold pending-event PCM differs");
    check(cold->setProcessing(false)==kResultOk,"Cold suspend failed");
    cold.reset();
    // The voice is now active, and converter phase/history plus queued PCM are
    // nontrivial. Save a pending host note-off and replay it in another child.
    auto first=std::uint64_t(rate)+64;
    check(plugin.setProcessing(true)==kResultOk,"Active resume failed");
    render(plugin,first,64,false,true);first+=64;
    check(plugin.setProcessing(false)==kResultOk,"Active suspend failed");
    StateMemory active;check(plugin.getState(&active)==kResultOk,"Active save failed");
    StateMemory broken=active;broken.data.back()^=1;broken.offset=0;
    check(plugin.setState(&broken)==kResultFalse,"Corrupt archive accepted");
    // Capture re-arms a finite saved backlog; compare only after it has settled.
    StateMemory failed;failed.fail_write=true;check(plugin.getState(&failed)==kResultFalse,"Failed host write accepted");
    check(plugin.setProcessing(true)==kResultOk,"Failed save lost resumability");
    expected=render(plugin,first,rate*2,false,false);
    check(plugin.setProcessing(false)==kResultOk,"Active reference suspend failed");
    check(std::any_of(expected.begin(),expected.end(),[](float f){return std::abs(f)>.001f;}),"Active replay is silent");
    check(std::all_of(expected.end()-rate/2,expected.end(),[](float f){return f==0;}),"Reference note-off tail not silent");
    cold=create();check(cold->setupProcessing(setup)==kResultOk,"Active cold setup failed");
    active.offset=0;check(cold->setState(&active)==kResultOk,"Active cold restore failed");
    check(cold->setActive(true)==kResultOk && cold->setProcessing(true)==kResultOk,"Active cold start failed");
    check(render(*cold,first,rate*2,false,false)==expected,"Active cold PCM differs");
    check(cold->setProcessing(false)==kResultOk,"Active cold suspend failed");
    active.offset=0;check(cold->setState(&active)==kResultOk,"Repeated recall failed");
    check(cold->setProcessing(true)==kResultOk,"Repeated resume failed");
    check(render(*cold,first,rate*2,false,false)==expected,"Repeated recall PCM differs");
    cold->terminate();plugin.terminate();
    std::cout<<"Native plugin state passed rate="<<rate<<" exact_frames="<<rate*5
             <<" pending_host_note=1 cold_active_note=1 repeated_recall=1 silent_tail=1 corrupt_rejected=1 failed_write_recoverable=1\n";
}
