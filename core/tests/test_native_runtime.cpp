#include "s760/s760_native_runtime.hpp"
#include "s760/s760_native_audio_worker.hpp"
#include "s760/s760_mame_host.hpp"
#include <iostream>
#include <cmath>
#include <thread>
#include <stdexcept>
#include <fstream>
#include <cstdlib>

static void check(bool ok,const char* text) { if(!ok) throw std::runtime_error(text); }
int main(int argc,char** argv) {
    try {
        if(argc!=3 && argc!=4) throw std::runtime_error("Usage: s760_native_runtime_tests ROOT PRIVATE_STATE [--crash-probe]");
        std::filesystem::path root=std::filesystem::absolute(argv[1]);
        s760::NativeRuntimeConfig cfg{root,argv[2],root/"roms/BOOT/Roland_S-760_v1.11.BIN",
            root/"roms/System/S760224.IMG",root/"roms/FDD/ROBOFULL.IMG"};
        s760::S760MameHost host;
        host.configure_native(cfg);
        check(host.init(),host.native_error().c_str());
        auto& native=*host.native_runtime();
        if(argc==4) {
            check(std::string(argv[3])=="--crash-probe","Unknown test option");
            { std::ofstream pid(cfg.state/"child.pid"); pid << native.process_id(); }
            std::_Exit(73); // Deliberately bypass all C++ destructors.
        }
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
        native.request("{\"op\":\"audio_capture\",\"enabled\":true}");
        auto first=std::uint64_t(std::ceil(now*44100))+1000;
        native.request("{\"op\":\"schedule_midi\",\"events\":[{\"sample\":"+std::to_string(first)+
            ",\"bytes\":[144,60,127]},{\"sample\":"+std::to_string(first+44100)+",\"bytes\":[128,60,0]}]}");
        s760::NativeAudioWorker worker([&](float* pcm,std::size_t count) { return host.render_native_audio(pcm,count); });
        worker.start();
        float left[256],right[256],peak=0,tail=0;
        std::size_t consumed=0;
        const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(45);
        while(consumed<88200) {
            const auto count=std::min(std::size_t(256),88200-consumed);
            while(worker.buffered_frames()<count) {
                check(!worker.failed(),"Native render worker failed");
                check(std::chrono::steady_clock::now()<deadline,"Native worker stalled");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
            check(worker.read(left,right,count)==count,"Unexpected underrun after prefill");
            for(std::size_t i=0;i<count;++i) {
                check(std::isfinite(left[i]) && std::isfinite(right[i]),"Nonfinite native PCM");
                peak=std::max(peak,std::max(std::abs(left[i]),std::abs(right[i])));
                if(consumed+i>80000) tail=std::max(tail,std::max(std::abs(left[i]),std::abs(right[i])));
            }
            consumed+=count;
        }
        worker.stop();
        check(peak>.001f && tail==0 && !worker.failed(),"Native note/release failed");
        std::cout << "C++ native boot/load/frames/scheduled MIDI/worker PCM passed; frames=" << consumed
                  << " peak=" << peak << " tail=" << tail << " underruns=" << worker.underrun_frames() << "\n";
        return 0;
    } catch(const std::exception& error) { std::cerr << error.what() << "\n"; return 1; }
}
