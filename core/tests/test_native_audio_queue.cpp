#include "s760/s760_native_audio_queue.hpp"
#include "s760/s760_native_audio_worker.hpp"
#include <stdexcept>
#include <thread>
#include <iostream>
#include <fstream>
#include <vector>

static void check(bool value) { if (!value) throw std::runtime_error("Native PCM queue regression"); }
int main(int argc, char** argv) {
    s760::NativeAudioQueue<4> q;
    float input[] = {1,-1,2,-2,3,-3,4,-4,5,-5};
    float l[8], r[8];
    check(q.write(input,5)==4);
    check(q.write(input,1)==0);
    check(q.read(l,r,3)==3 && l[2]==3 && r[2]==-3);
    check(q.write(input+8,1)==1);
    auto saved=q.snapshot();
    check(saved==std::vector<float>({4,-4,5,-5}));
    s760::NativeAudioQueue<4> restored;
    restored.restore(saved);
    check(restored.read(l,r,2)==2 && l[0]==4 && r[1]==-5);
    for(const auto& invalid: {std::vector<float>(3),std::vector<float>(10)}) {
        bool rejected=false;
        try { restored.restore(invalid); } catch(const std::invalid_argument&) { rejected=true; }
        check(rejected);
    }
    check(q.read(l,r,4)==2 && l[0]==4 && r[1]==-5 && l[2]==0 && r[3]==0);
    check(q.underrun_frames()==2);
    s760::NativeAudioQueue<257> concurrent;
    constexpr unsigned total=200000;
    std::thread producer([&] {
        for (unsigned i=1;i<=total;++i) {
            float pair[] = {float(i),-float(i)};
            while (!concurrent.write(pair,1)) std::this_thread::yield();
        }
    });
    unsigned next=1;
    while (next<=total) {
        const auto count=concurrent.read(l,r,8);
        for (std::size_t i=0;i<count;++i,++next) check(l[i]==float(next) && r[i]==-float(next));
        if (!count) std::this_thread::yield();
    }
    producer.join();
    unsigned rendered=0;
    s760::NativeAudioWorker audio([&](float* pcm,std::size_t frames) {
        for(std::size_t i=0;i<frames;++i) {
            pcm[i*2]=float(++rendered); pcm[i*2+1]=-float(rendered);
        }
        return true;
    });
    audio.start();
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    while(audio.buffered_frames()!=4096 && std::chrono::steady_clock::now()<deadline)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    check(audio.buffered_frames()==4096);
    check(audio.read(l,r,8)==8 && l[0]==1 && r[7]==-8);
    audio.stop();
    check(!audio.failed() && audio.underrun_frames()==0);
    s760::NativeAudioWorker failing([](float*,std::size_t) { return false; });
    failing.start();
    while(!failing.failed() && std::chrono::steady_clock::now()<deadline)
        std::this_thread::sleep_for(std::chrono::milliseconds(1));
    check(failing.failed() && failing.read(l,r,8)==0 && failing.underrun_frames()==8);
    failing.stop();
    std::cout << "Native PCM queue: wrap, backpressure, underrun and 200000 concurrent frames passed\n";
    if (argc == 2) {
        std::ifstream file(argv[1], std::ios::binary | std::ios::ate);
        check(bool(file));
        const auto bytes = file.tellg();
        check(bytes > 0 && bytes % 8 == 0);
        std::vector<float> native(std::size_t(bytes)/4);
        file.seekg(0);
        file.read(reinterpret_cast<char*>(native.data()), bytes);
        check(bool(file));
        s760::NativeAudioQueue<4096> stream;
        const auto frames = native.size()/2;
        std::thread worker([&] {
            std::size_t offset=0;
            while (offset<frames) {
                offset += stream.write(native.data()+offset*2, std::min(std::size_t(735), frames-offset));
                std::this_thread::yield();
            }
        });
        std::size_t offset=0;
        while (offset<frames) {
            const auto received=stream.read(l,r,std::min(std::size_t(8),frames-offset));
            for (std::size_t i=0;i<received;++i,++offset)
                check(l[i]==native[offset*2] && r[i]==native[offset*2+1]);
            std::this_thread::yield();
        }
        worker.join();
        std::cout << "Native captured PCM preserved exactly through worker queue: " << frames << " frames\n";
    }
}
