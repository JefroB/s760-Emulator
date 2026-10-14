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
#include "native_midi_acceptance.hpp"
#ifdef S760_TEST_NATIVE_EDITOR
#include "native_editor_acceptance.hpp"
#endif
int main(int argc,char** argv) {
    try {
        if(argc<3 || argc>6) throw std::runtime_error("Usage: s760_native_runtime_tests ROOT PRIVATE_STATE [--paced|--paced-var|--controllers|--input|--offline] [44100|48000|96000] [seconds]");
        std::filesystem::path root=std::filesystem::absolute(argv[1]);
        s760::NativeRuntimeConfig cfg{root,argv[2],root/"roms/BOOT/Roland_S-760_v1.11.BIN",
            root/"roms/System/S760224.IMG",root/"roms/FDD/ROBOFULL.IMG"};
#ifdef S760_TEST_EXPORTED_FACTORY
        cfg.experimental_adc=true;
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
        TUID iid=INLINE_UID(0xE831FF31,0xF2D54301,0x928EBBEE,0x25697802);
        void* object=reinterpret_cast<void*>(1);
        _wputenv_s(L"S760_NATIVE_ROOT",L"");
        _wputenv_s(L"S760_PLUGIN_CONFIG",std::filesystem::absolute(cfg.state/"plugin-settings.json").c_str());
        check(factory->createInstance(reinterpret_cast<char*>(info.cid),reinterpret_cast<char*>(iid),&object)==kResultOk && object,"Missing configuration did not open recovery editor");
        auto* pending=dynamic_cast<s760::S760Vst3Plugin*>(static_cast<Steinberg::IComponent*>(object));
        check(pending && pending->native_host() && !pending->native_host()->native_runtime(),"Unconfigured instance fell through to legacy core");
        check(pending->get_bridge().current_telemetry().pluginConfiguration.find("\"needsConfiguration\":true")!=std::string::npos,"Startup error not visible to editor");
        Steinberg::ProcessSetup silent_setup{0,0,512,44100};
        check(pending->setupProcessing(silent_setup)==kResultOk && pending->setProcessing(true)==kResultOk,"Recovery processing setup rejected");
        float l[512],r[512];std::fill_n(l,512,1.f);std::fill_n(r,512,1.f);float* ch[]{l,r};
        AudioBusBuffers out{2,0};out.channelBuffers32=ch;
        Steinberg::ProcessData silent{};silent.numSamples=512;silent.numOutputs=1;silent.outputs=&out;
        check(pending->process(silent)==kResultOk && l[0]==0 && r[511]==0,"Unconfigured processor did not remain silent");
        auto message=std::string("{\"type\":\"CONFIGURE_PLUGIN\",\"payload\":{\"confirmReload\":true,\"root\":\"")+root.generic_u8string()+
            "\",\"stateRoot\":\""+std::filesystem::absolute(cfg.state).generic_u8string()+"\",\"bootRom\":\""+cfg.boot_rom.generic_u8string()+
            "\",\"systemDisk\":\""+cfg.system_disk.generic_u8string()+"\",\"mediaDirectory\":\""+(root/"roms/FDD").generic_u8string()+"\"}}";
        check(pending->get_bridge().on_input(message),"Editor configuration rejected");
        check(pending->get_bridge().current_telemetry().pluginConfiguration.find("\"saved\":true")!=std::string::npos,"Valid settings not persisted");
        auto settings_file=cfg.state/"plugin-settings.json";
        std::ifstream before_file(settings_file);std::string before((std::istreambuf_iterator<char>(before_file)),{});before_file.close();
        auto bad=message;const auto at=bad.find(cfg.boot_rom.generic_u8string());bad.replace(at,cfg.boot_rom.generic_u8string().size(),"relative.bin");
        check(pending->get_bridge().on_input(bad),"Invalid configuration not handled");
        std::ifstream after_file(settings_file);std::string after((std::istreambuf_iterator<char>(after_file)),{});after_file.close();
        check(before==after && pending->get_bridge().current_telemetry().pluginConfiguration.find("must be an absolute path")!=std::string::npos,"Rejected change replaced previous settings");
        check(!pending->native_host()->native_runtime(),"Saving settings started or replaced a machine during processing");
        pending->terminate();pending->release();object=nullptr;
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
        TUID processor_iid=INLINE_UID(0x42043F99,0xB7DA453C,0xA569E79D,0x9AAEC33D);
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
        const bool controller_test=argc>=4 && std::string(argv[3])=="--controllers";
        const bool offline=argc>=4 && std::string(argv[3])=="--offline";
        const bool input_test=argc>=4 && std::string(argv[3])=="--input";
        const bool varied=offline || controller_test || input_test || (argc>=4 && std::string(argv[3])=="--paced-var");
        const bool paced=!offline && (varied || (argc>=4 && std::string(argv[3])=="--paced"));
        const bool state_test=argc>=4 && std::string(argv[3])=="--state";
        check(argc==3 || paced || offline || state_test,"Unknown option");
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
#ifdef S760_TEST_NATIVE_EDITOR
        // Exercise the embedded bridge route, not the Python standalone route.
        check(!plugin.get_bridge().on_input(R"({"type":"DIAL_DELTA","payload":{"id":"VALUE","delta":1}})"),"Unverified native dial accepted");
        check(!plugin.get_bridge().on_input(R"({"type":"MOUSE_CLICK","payload":{"x":0.5,"y":0.5,"button":0}})"),"Legacy click pulse accepted for native mode");
        check(!plugin.get_bridge().on_input(R"({"type":"BUTTON_PRESS","payload":{"id":"UNKNOWN"}})"),"Unknown native panel control accepted");
        check(!plugin.get_bridge().on_input(R"({"type":"MOUSE_MOVE","payload":{"x":2,"y":0.5}})"),"Invalid native pointer accepted");
        check(plugin.get_bridge().on_input(R"({"type":"MOUSE_MOVE","payload":{"x":0.5,"y":0.5}})"),"Native pointer rejected");
        wait(.3);
        const auto before_panel=native.request("{\"op\":\"frames\"}").crt;
        check(plugin.get_bridge().on_input(R"({"type":"BUTTON_PRESS","payload":{"id":"MODE"}})"),"Bridge rejected MODE");
        wait(.2);
        plugin.get_bridge().on_input(R"({"type":"BUTTON_RELEASE","payload":{"id":"MODE"}})");
        check(native.request("{\"op\":\"frames\"}").crt!=before_panel,"Bridge MODE did not change firmware pixels");
        plugin.get_bridge().on_input(R"({"type":"BUTTON_PRESS","payload":{"id":"EXIT"}})");
        wait(.2);
        plugin.get_bridge().on_input(R"({"type":"BUTTON_RELEASE","payload":{"id":"EXIT"}})");
#endif
        auto screens=native.request("{\"op\":\"frames\"}");
        check(screens.crt.size()==640*240*4 && screens.lcd.size()==160*64*4,"Missing native frames");
        bool pixels=false;
        for(std::size_t i=0;i<screens.crt.size();i+=4) pixels|=(screens.crt[i] || screens.crt[i+1] || screens.crt[i+2]);
        check(pixels,"Blank native CRT");
        check(host.run_frame(),"Native adapter display refresh failed");
        check(host.get_latest_video_frame().rgba_pixels.size()==640*480,"Native adapter CRT geometry");
        std::uint8_t lcd[1280]; check(host.get_lcd_surface(lcd,sizeof(lcd)),"Native adapter LCD");
        auto mount_source=cfg.sample_disk;
        if(state_test) {
            mount_source=std::filesystem::absolute(cfg.state/"mounted-source.img");
            std::filesystem::copy_file(cfg.sample_disk,mount_source,std::filesystem::copy_options::overwrite_existing);
        }
        check(host.mount_disk(mount_source.u8string()),"Native adapter floppy insertion failed");
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
        setup.sampleRate=host_rate;setup.processMode=offline ? 2 : 0;
        auto invalid_setup=setup;
        invalid_setup.sampleRate=32000;
        check(plugin.setupProcessing(invalid_setup)==kResultFalse,"Unsupported native host rate accepted");
        invalid_setup=setup;invalid_setup.maxSamplesPerBlock=1025;
        check(plugin.setupProcessing(invalid_setup)==kResultFalse,"Oversized native callback accepted");
        invalid_setup=setup;invalid_setup.maxSamplesPerBlock=0;
        check(plugin.setupProcessing(invalid_setup)==kResultFalse,"Zero native block limit accepted");
        invalid_setup=setup;invalid_setup.symbolicSampleSize=1;
        check(plugin.setupProcessing(invalid_setup)==kResultFalse,"Unsupported float64 native buffers accepted");
        check(plugin.setupProcessing(setup)==kResultOk,"Native plugin setup failed");
        check(plugin.getBusCount(kAudio,kInput)==(cfg.experimental_adc?1:0),"Native input topology mismatch");
        if(cfg.experimental_adc) {
            auto input_setup=setup;input_setup.sampleRate=44100;
            check(plugin.setupProcessing(input_setup)==kResultOk,"Input clock setup failed");
            check(plugin.activateBus(kAudio,kInput,0,true)==kResultOk,"Native stereo input activation failed");
            auto unsupported=input_setup;unsupported.sampleRate=48000;
            check(plugin.setupProcessing(unsupported)==kResultFalse,"Unsupported active-input rate accepted");
            check(plugin.activateBus(kAudio,kInput,0,false)==kResultOk,"Native input deactivation failed");
            check(plugin.setupProcessing(setup)==kResultOk,"Output-only rate setup failed");
        }
        check(plugin.getState(nullptr)==kResultFalse && plugin.setState(nullptr)==kResultFalse,"Legacy state used for native machine");
        if(state_test) {
            unsigned instance=0;
            state_acceptance(plugin,setup,cfg.state/"media-library-fixture",[&]() -> std::shared_ptr<s760::S760Vst3Plugin> {
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
        if(input_test)check(cfg.experimental_adc && host_rate==44100 && plugin.activateBus(kAudio,kInput,0,true)==kResultOk,"Input acceptance requires native 44.1kHz ADC profile");
        const auto padding=s760::NativeRateConverter::host_samples(s760::NativeStream::output_delay,host_rate);
        ControllerTimeline controllers(host_rate);
        check(!controller_test || seconds==12,"Controller timeline requires12 seconds");
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
            bool reference_off_sent=false;
            if(controller_test) for(const auto& item:controllers.items) {
                if(!reference_off_sent && item.time>note_off) {send(event_time(note_off),128);reference_off_sent=true;}
                const bool bend=item.controller==129;
                const unsigned status=(bend?0xe0:0xb0)|item.channel;
                const unsigned first=bend?item.value&127:item.controller,second=bend?item.value>>7:item.value;
                reference_native.request("{\"op\":\"schedule_midi\",\"append\":true,\"events\":[{\"sample\":"+std::to_string(event_time(item.time))+",\"bytes\":["+std::to_string(status)+","+std::to_string(first)+","+std::to_string(second)+"]}]}");
            }
            s760::NativeRateConverter reference_converter(host_rate,[&](float* pcm,std::size_t frames) {return reference_native.render(pcm,frames);});
            bool off_sent=reference_off_sent;
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
        Steinberg::ProcessData data{}; data.processMode=setup.processMode; data.numSamples=256; data.numOutputs=1; data.outputs=&output;
        float input_left[1024]{},input_right[1024]{};float* input_channels[]{input_left,input_right};
        AudioBusBuffers input_bus{2,0};input_bus.channelBuffers32=input_channels;
        if(input_test){data.numInputs=1;data.inputs=&input_bus;}
        Events events; data.inputEvents=&events;
        std::size_t consumed=0,first_audible=0;
        bool note_on_verified=false;
        auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(90);
#ifdef S760_TEST_NATIVE_EDITOR
        check(paced && seconds>=10,"Editor acceptance requires paced playback >=10 seconds");
        const auto editor_pid=native.process_id();
        NativeEditorAcceptance editor(plugin.get_bridge(),root,cfg.state);
#endif
        auto clock_start=std::chrono::steady_clock::now();
        double max_callback_us=0,max_deadline_fraction=0;
        unsigned missed_deadlines=0;
        for(unsigned block=0;consumed<total;++block) {
            const unsigned sizes[]{64,127,256,511,1024};
            unsigned count=varied ? sizes[block%5] : 256;
            count=unsigned(std::min<std::size_t>(count,total-consumed));
            data.numSamples=int(count);
            if(input_test)for(unsigned i=0;i<count;++i) {
                input_left[i]=float((int((consumed+i)%257)-128)*64)/32768.f;
                input_right[i]=float((int((consumed+i)%509)-254)*32)/32768.f;
            }
            controllers.bind(consumed,count);
            data.inputParameterChanges=controller_test ? &controllers : nullptr;
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
#ifdef S760_TEST_NATIVE_EDITOR
            editor.phase=consumed<total/3?0:consumed<total/2?1:2;
            check(!editor.failed,"Native editor could not open");
#endif
            if(!note_on_verified && consumed>=host_rate/2) {
                auto status=native.request("{\"op\":\"status\"}").json;
                check(status.find(std::to_string(event_time(17)))!=std::string::npos,"Native note-on offset differs");
                note_on_verified=true;
            }
            // Accelerated functional test: this wait is OUTSIDE process().
            while(!paced && !offline && (block+1)%8==0 && plugin.native_stream()->completed_frames()<consumed) {
                check(plugin.native_stream()->fault()==s760::NativeStream::Fault::none,"Native plugin worker fault");
                check(std::chrono::steady_clock::now()<deadline,"Native plugin worker stalled");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
            if(block==103 && !paced && !offline) {
                check(plugin.setProcessing(false)==kResultOk,"Suspend failed");
                auto before=native.request("{\"op\":\"status\"}").seconds;
                std::this_thread::sleep_for(std::chrono::milliseconds(25));
                check(native.request("{\"op\":\"status\"}").seconds==before,"Suspended clock advanced");
                check(plugin.setProcessing(true)==kResultOk,"Resume failed");
            }
            if(paced) std::this_thread::sleep_until(clock_start+std::chrono::duration_cast<std::chrono::steady_clock::duration>(std::chrono::duration<double>(double(consumed)/host_rate)));
        }
#ifdef S760_TEST_NATIVE_EDITOR
        editor.finish();
        check(editor.verified==3,"React did not paint native pixels before and after reopen");
        check(native.process_id()==editor_pid,"Editor lifecycle replaced native child");
        check(native.display_frames().seconds>now+seconds/2,"Editor display cache stopped advancing during audio");
        std::cout<<"Native editor: React pixel agreement before/after reopen, same child, concurrent exact PCM\n";
#endif
        auto delivered=native.request("{\"op\":\"status\"}").json;
        std::cout << "Expected MIDI " << event_time(17) << "," << event_time(note_off) << "; status=" << delivered << "\n";
        const auto last_midi_time=controller_test ? controllers.items.back().time : note_off;
        check(note_on_verified && delivered.find(std::to_string(event_time(last_midi_time)))!=std::string::npos,"Native final MIDI offset differs");
        check(peak>.001f && tail==0 && first_audible>=padding,"Native plugin note/release failed");
        check(plugin.native_stream()->fault()==s760::NativeStream::Fault::none,"Native plugin fault");
        check(offline || missed_deadlines==0,"Callback exceeded its block deadline");
        check(plugin.setProcessing(false)==kResultOk,"Final suspend failed");
        std::cout << "Native VST3 boot/load/display/offsets/audio/suspend passed; frames=" << consumed
                  << " rate=" << host_rate << " input_active=" << input_test << " reference_exact=1 peak=" << peak << " tail=" << tail << " first_audible=" << first_audible
                  << " offline=" << offline << " reported_tail=" << plugin.getTailSamples() << " reported_latency=" << plugin.getLatencySamples() << " paced=" << paced << " varied=" << varied << " max_callback_us=" << max_callback_us << " max_deadline_fraction=" << max_deadline_fraction << " missed_deadlines=" << missed_deadlines << "\n";
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
