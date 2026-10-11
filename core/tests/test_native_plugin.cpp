#include "s760/s760_native_rate_converter.hpp"
#include "s760/s760_vst3_plugin.hpp"
#include "s760/s760_native_audio_worker.hpp"
#include "s760/s760_mame_host.hpp"
#include <iostream>
#include <cmath>
#include <thread>
#include <stdexcept>
#include <fstream>
#include <cstdlib>
#ifdef S760_TEST_EXPORTED_FACTORY
#define NOMINMAX
#include <windows.h>
#endif

class Events : public Steinberg::IEventList {
public:
    Event event{}; bool present=false;
    tresult queryInterface(const TUID,void**) override { return kResultFalse; }
    uint32_t addRef() override { return 1; }
    uint32_t release() override { return 1; }
    int32_t getEventCount() override { return present ? 1 : 0; }
    tresult getEvent(int32_t i,Event& e) override { if(i || !present) return kResultFalse; e=event; return kResultOk; }
    tresult addEvent(Event&) override { return kResultFalse; }
};
static void check(bool ok,const char* text) { if(!ok) throw std::runtime_error(text); }
#include "native_state_acceptance.hpp"
int main(int argc,char** argv) {
    try {
        if(argc<3 || argc>6) throw std::runtime_error("Usage: s760_native_runtime_tests ROOT PRIVATE_STATE [--paced|--paced-var] [44100|48000|96000] [seconds]");
        std::filesystem::path root=std::filesystem::absolute(argv[1]);
        s760::NativeRuntimeConfig cfg{root,argv[2],root/"roms/BOOT/Roland_S-760_v1.11.BIN",
            root/"roms/System/S760224.IMG",root/"roms/FDD/ROBOFULL.IMG"};
#ifdef S760_TEST_EXPORTED_FACTORY
        struct Module {
            HMODULE handle;
            ~Module() { if(handle) FreeLibrary(handle); }
        } module{LoadLibraryW((root/"build/Release/Roland_S760.vst3").c_str())};
        check(module.handle!=nullptr,"Cannot load exported VST3 module");
        auto entry=reinterpret_cast<Steinberg::IPluginFactory*(*)()>(GetProcAddress(module.handle,"GetPluginFactory"));
        check(entry!=nullptr,"Missing factory export");
        auto* factory=entry();
        check(factory->countClasses()==1,"Factory advertises unimplemented ADC/FX");
        Steinberg::PClassInfo info{};
        check(factory->getClassInfo(0,&info)==kResultOk,"Missing instrument class");
        TUID iid=INLINE_UID(0xE8318227,0x79A447F6,0x8E6AEF5D,0xDC202293);
        void* object=reinterpret_cast<void*>(1);
        _wputenv_s(L"S760_NATIVE_ROOT",L"");
        check(factory->createInstance(reinterpret_cast<char*>(info.cid),reinterpret_cast<char*>(iid),&object)==kResultFalse && !object,"Missing configuration fell through to legacy core");
        _wputenv_s(L"S760_NATIVE_ROOT",cfg.root.c_str());
        _wputenv_s(L"S760_NATIVE_STATE_ROOT",std::filesystem::absolute(cfg.state).c_str());
        _wputenv_s(L"S760_BOOT_ROM",cfg.boot_rom.c_str());
        _wputenv_s(L"S760_SYSTEM_DISK",cfg.system_disk.c_str());
        _wputenv_s(L"S760_BACKEND",L"core"); // Historical selector cannot redirect production.
        check(factory->createInstance(reinterpret_cast<char*>(info.cid),reinterpret_cast<char*>(iid),&object)==kResultOk && object,"Native exported factory failed");
        auto* concrete=dynamic_cast<s760::S760Vst3Plugin*>(static_cast<Steinberg::IComponent*>(object));
        check(concrete!=nullptr,"Unexpected factory component");
        std::unique_ptr<s760::S760Vst3Plugin,void(*)(s760::S760Vst3Plugin*)> owner(concrete,[](auto* p){p->release();});
        auto& plugin=*owner;
        check(plugin.native_host() && plugin.native_host()->native_runtime(),"Factory selected historical host");
        // First instance must get its own child directory, never the shared root.
        unsigned directories=0;
        auto state_root=cfg.state;
        for(const auto& entry:std::filesystem::directory_iterator(state_root))
            if(entry.is_directory()) {cfg.state=entry.path();++directories;}
        check(directories==1,"Factory test requires a fresh private state root");
        object=nullptr;
        TUID processor_iid=INLINE_UID(0x420423E5,0x12DA4541,0xA6190EB9,0x99615A3B);
        check(factory->createInstance(reinterpret_cast<char*>(info.cid),reinterpret_cast<char*>(processor_iid),&object)==kResultOk && object,"Factory processor IID failed");
        auto* second=static_cast<Steinberg::IAudioProcessor*>(object);
        auto* second_plugin=dynamic_cast<s760::S760Vst3Plugin*>(second);
        check(second_plugin && second_plugin->native_host()->native_runtime()->process_id()!=plugin.native_host()->native_runtime()->process_id(),"Factory reused native child");
        second->release();
        std::cout<<"Exported factory: native-only selection, independent children and requested interfaces passed\n";
#else
        s760::S760Vst3Plugin plugin(cfg);
#endif
        auto& host=*plugin.native_host();
        auto& native=*host.native_runtime();
        const bool varied=argc>=4 && std::string(argv[3])=="--paced-var";
        const bool paced=varied || (argc>=4 && std::string(argv[3])=="--paced");
        const bool state_test=argc>=4 && std::string(argv[3])=="--state";
        check(argc==3 || paced || state_test,"Unknown option");
        const unsigned host_rate=argc>=5 ? unsigned(std::stoul(argv[4])) : 44100;
        const unsigned seconds=argc>=6 ? unsigned(std::stoul(argv[5])) : 10;
        check(seconds>=3 && seconds<=600,"Duration must be 3..600 seconds");
        bool rejected=false;
        try { s760::NativeRuntimeClient duplicate(cfg); } catch(const std::exception&) { rejected=true; }
        check(rejected,"Shared state was accepted");
        {
            auto other=cfg; other.state=cfg.state.string()+"-second";
            s760::NativeRuntimeClient independent(other);
            independent.request("{\"op\":\"pause\"}");
            check(native.request("{\"op\":\"status\"}").json.find("running")!=std::string::npos,
                  "Pausing another instance affected the first");
        }
        auto wait=[&](double duration) {
            auto target=native.request("{\"op\":\"status\"}").seconds+duration;
            auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);
            while(native.request("{\"op\":\"status\"}").seconds<target) {
                check(std::chrono::steady_clock::now()<deadline,"Native time stalled");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        };
        auto button=[&](const char* port,const char* name,bool down) {
            native.request(std::string("{\"op\":\"button\",\"port\":\"")+port+"\",\"name\":\""+name+"\",\"down\":"+(down?"true":"false")+"}");
        };
        auto click=[&](unsigned x,unsigned y) {
            native.request("{\"op\":\"pointer\",\"x\":"+std::to_string(x)+",\"y\":"+std::to_string(y)+"}");
            wait(.2); button(":NATIVE_MOUSE_BUTTONS","Mouse Left",true); wait(.1);
            button(":NATIVE_MOUSE_BUTTONS","Mouse Left",false); wait(.2);
        };
        wait(20);
        auto screens=native.request("{\"op\":\"frames\"}");
        check(screens.crt.size()==640*240*4 && screens.lcd.size()==160*64*4,"Missing native frames");
        bool pixels=false;
        for(std::size_t i=0;i<screens.crt.size();i+=4) pixels|=(screens.crt[i] || screens.crt[i+1] || screens.crt[i+2]);
        check(pixels,"Blank native CRT");
        check(host.run_frame(),"Native adapter display refresh failed");
        check(host.get_latest_video_frame().rgba_pixels.size()==640*480,"Native adapter CRT geometry");
        std::uint8_t lcd[1280]; check(host.get_lcd_surface(lcd,sizeof(lcd)),"Native adapter LCD");
        check(host.mount_disk(cfg.sample_disk.string()),"Native adapter floppy insertion failed");
        click(118,5); wait(2); click(80,22); wait(8); click(50,34); wait(2); click(76,98); wait(35);
        click(10,5); click(15,22); wait(3);
        auto now=native.request("{\"op\":\"pause\"}").seconds;
        auto raw=native.request("{\"op\":\"frames\"}");
        check(host.run_frame(),"Paused native display refresh failed");
        auto converted=host.get_latest_video_frame();
        for(std::size_t y=0;y<240;++y) for(std::size_t x=0;x<640;++x) {
            auto src=(y*640+x)*4;
            auto expected=std::uint32_t(raw.crt[src+2]) | (std::uint32_t(raw.crt[src+1])<<8)
                | (std::uint32_t(raw.crt[src])<<16) | 0xff000000u;
            check(converted.rgba_pixels[y*2*640+x]==expected && converted.rgba_pixels[(y*2+1)*640+x]==expected,
                  "Adapter CRT differs from native pixels");
        }
        check(host.get_lcd_surface(lcd,sizeof(lcd)),"Paused native LCD failed");
        for(std::size_t i=0;i<160*64;++i)
            check(bool(lcd[i/8] & (0x80>>(i%8)))==bool(raw.lcd[i*4] || raw.lcd[i*4+1] || raw.lcd[i*4+2]),
                  "Adapter LCD differs from native pixels");
        Steinberg::ProcessSetup setup{0,0,1024,32000};
        check(plugin.setupProcessing(setup)==kResultFalse,"Unsupported rate accepted");
        setup.sampleRate=host_rate;
        check(plugin.setupProcessing(setup)==kResultOk,"Native plugin setup failed");
        check(plugin.getBusCount(kAudio,kInput)==0,"Native ADC falsely advertised");
        check(plugin.getState(nullptr)==kResultFalse && plugin.setState(nullptr)==kResultFalse,"Legacy state used for native machine");
        if(state_test) {
            unsigned instance=0;
            state_acceptance(plugin,setup,[&]() -> std::shared_ptr<s760::S760Vst3Plugin> {
#ifdef S760_TEST_EXPORTED_FACTORY
                void* result=nullptr;
                check(factory->createInstance(reinterpret_cast<char*>(info.cid),reinterpret_cast<char*>(iid),&result)==kResultOk,"Fresh factory state instance failed");
                auto* p=dynamic_cast<s760::S760Vst3Plugin*>(static_cast<Steinberg::IComponent*>(result));
                check(p!=nullptr,"Wrong cold factory type");
                return {p,[](auto* q){q->release();}};
#else
                auto next=cfg;next.sample_disk.clear();next.state=cfg.state.string()+"-cold-"+std::to_string(instance++);
                return std::make_shared<s760::S760Vst3Plugin>(next);
#endif
            });
            return 0;
        }
        const auto padding=s760::NativeRateConverter::host_samples(s760::NativeStream::output_delay,host_rate);
        const auto total=std::size_t(host_rate)*(paced ? seconds : 3);
        const auto note_off=std::size_t(host_rate)*((paced ? seconds : 3)-2)+23;
        const auto origin=std::uint64_t(std::ceil(now*44100));
        auto event_time=[&](std::uint64_t host) { return origin+s760::NativeRateConverter::native_sample(host,host_rate)+s760::NativeStream::midi_lead; };
        // Same native machine checkpoint in a fresh reference child, then
        // the real processor's callback/worker stream at wall-clock deadlines.
        native.request("{\"op\":\"checkpoint_save\"}");
        std::vector<float> reference((total-padding)*2);
        {
            auto reference_cfg=cfg;reference_cfg.state=cfg.state.string()+"-reference";reference_cfg.sample_disk.clear();
            s760::NativeRuntimeClient reference_native(reference_cfg);
            reference_native.request("{\"op\":\"pause\"}");
            std::filesystem::copy_file(cfg.state/"runtime-checkpoint.bin",reference_cfg.state/"runtime-checkpoint.bin",std::filesystem::copy_options::overwrite_existing);
            reference_native.request("{\"op\":\"checkpoint_load\"}");
            reference_native.request("{\"op\":\"audio_capture\",\"enabled\":true}");
            auto send=[&](std::uint64_t sample,unsigned status) {
                reference_native.request("{\"op\":\"schedule_midi\",\"append\":true,\"events\":[{\"sample\":"+std::to_string(sample)+",\"bytes\":["+std::to_string(status)+",60,"+(status==144 ? "127" : "0")+"]}]}");
            };
            send(event_time(17),144);
            s760::NativeRateConverter reference_converter(host_rate,[&](float* pcm,std::size_t frames) {return reference_native.render(pcm,frames);});
            bool off_sent=false;
            for(std::size_t offset=0;offset<reference.size()/2;) {
                if(!off_sent && offset+host_rate>=note_off) {send(event_time(note_off),128);off_sent=true;}
                auto count=unsigned(std::min<std::size_t>(2048,reference.size()/2-offset));
                check(reference_converter.pull(reference.data()+offset*2,count),"Offline reference render failed");offset+=count;
            }
        }
        check(plugin.setActive(true)==kResultOk && plugin.setProcessing(true)==kResultOk,"Native processing start failed");
        check(plugin.setupProcessing(setup)==kResultFalse,"Reconfiguration during processing accepted");
        float left[1024],right[1024],peak=0,tail=0;
        float* channels[]{left,right};
        AudioBusBuffers output{2,0}; output.channelBuffers32=channels;
        Steinberg::ProcessData data{}; data.numSamples=256; data.numOutputs=1; data.outputs=&output;
        Events events; data.inputEvents=&events;
        std::size_t consumed=0,first_audible=0;
        bool note_on_verified=false;
        auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(90);
        auto clock_start=std::chrono::steady_clock::now();
        double max_callback_us=0,max_deadline_fraction=0;
        unsigned missed_deadlines=0;
        for(unsigned block=0;consumed<total;++block) {
            const unsigned sizes[]{64,127,256,511,1024};
            unsigned count=varied ? sizes[block%5] : 256;
            count=unsigned(std::min<std::size_t>(count,total-consumed));
            data.numSamples=int(count);
            events.present=(block==0 || (consumed<=note_off && consumed+count>note_off));
            events.event={}; events.event.sampleOffset=block==0 ? 17 : int(note_off-consumed);
            events.event.type=block==0 ? kNoteOnEvent : kNoteOffEvent;
            if(block==0) { events.event.noteOn.pitch=60; events.event.noteOn.velocity=1; }
            else { events.event.noteOff.pitch=60; }
            auto callback_start=std::chrono::steady_clock::now();
            auto result=plugin.process(data);
            auto callback_us=std::chrono::duration<double,std::micro>(std::chrono::steady_clock::now()-callback_start).count();
            max_callback_us=std::max(max_callback_us,callback_us);
            auto deadline_fraction=callback_us*host_rate/(1e6*count);
            max_deadline_fraction=std::max(max_deadline_fraction,deadline_fraction);
            if(deadline_fraction>=1) ++missed_deadlines;
            if(result!=kResultOk) std::cerr << "Stream fault=" << int(plugin.native_stream()->fault()) << " block=" << block << " started=" << plugin.native_stream()->started_frames() << " completed=" << plugin.native_stream()->completed_frames() << "\n";
            check(result==kResultOk,"Native VST3 process failed");
            for(unsigned i=0;i<count;++i) {
                check(std::isfinite(left[i]) && std::isfinite(right[i]),"Nonfinite native PCM");
                auto level=std::max(std::abs(left[i]),std::abs(right[i]));
                peak=std::max(peak,level);
                if(!first_audible && level>.0001f) first_audible=consumed+i;
                const auto position=consumed+i;
                if(position>total-host_rate/2) tail=std::max(tail,level);
                if(position>=padding) {
                    auto expected=(position-padding)*2;
                    check(left[i]==reference[expected] && right[i]==reference[expected+1],"Native PCM differs from offline reference");
                } else check(left[i]==0 && right[i]==0,"Initial padding differs");
            }
            consumed+=count;
            if(!note_on_verified && consumed>=host_rate/2) {
                auto status=native.request("{\"op\":\"status\"}").json;
                check(status.find(std::to_string(event_time(17)))!=std::string::npos,"Native note-on offset differs");
                note_on_verified=true;
            }
            // Accelerated functional test: this wait is OUTSIDE process().
            while(!paced && (block+1)%8==0 && plugin.native_stream()->completed_frames()<consumed) {
                check(plugin.native_stream()->fault()==s760::NativeStream::Fault::none,"Native plugin worker fault");
                check(std::chrono::steady_clock::now()<deadline,"Native plugin worker stalled");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
            if(block==103 && !paced) {
                check(plugin.setProcessing(false)==kResultOk,"Suspend failed");
                auto before=native.request("{\"op\":\"status\"}").seconds;
                std::this_thread::sleep_for(std::chrono::milliseconds(25));
                check(native.request("{\"op\":\"status\"}").seconds==before,"Suspended clock advanced");
                check(plugin.setProcessing(true)==kResultOk,"Resume failed");
            }
            if(paced) std::this_thread::sleep_until(clock_start+std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::duration<double>(double(consumed)/host_rate)));
        }
        auto delivered=native.request("{\"op\":\"status\"}").json;
        std::cout << "Expected MIDI " << event_time(17) << "," << event_time(note_off) << "; status=" << delivered << "\n";
        check(note_on_verified && delivered.find(std::to_string(event_time(note_off)))!=std::string::npos,"Native note-off offset differs");
        check(peak>.001f && tail==0 && first_audible>=padding,"Native plugin note/release failed");
        check(plugin.native_stream()->fault()==s760::NativeStream::Fault::none,"Native plugin fault");
        check(missed_deadlines==0,"Callback exceeded its block deadline");
        check(plugin.setProcessing(false)==kResultOk,"Final suspend failed");
        std::cout << "Native VST3 boot/load/display/offsets/audio/suspend passed; frames=" << consumed
                  << " rate=" << host_rate << " reference_exact=1 peak=" << peak << " tail=" << tail << " first_audible=" << first_audible
                  << " reported_latency=" << plugin.getLatencySamples() << " paced=" << paced << " varied=" << varied << " max_callback_us=" << max_callback_us << " max_deadline_fraction=" << max_deadline_fraction << " missed_deadlines=" << missed_deadlines << "\n";
        auto* original_stream=plugin.native_stream();
        setup.sampleRate=host_rate==96000 ? 48000 : 96000;
        check(plugin.setupProcessing(setup)==kResultFalse && plugin.native_stream()==original_stream,"Started rate change lost queued state");
        setup.sampleRate=host_rate;
        check(plugin.setupProcessing(setup)==kResultOk && plugin.setProcessing(true)==kResultOk,"Same-rate resume failed");
        plugin.terminate();
        check(!host.native_runtime(),"Terminate retained native child");
        check(plugin.setProcessing(true)==kResultFalse,"Restart after termination accepted");
        return 0;
    } catch(const std::exception& error) { std::cerr << error.what() << "\n"; return 1; }
}
