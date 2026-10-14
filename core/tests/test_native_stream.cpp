#include "s760/s760_native_stream.hpp"
#include <stdexcept>
#include <iostream>
#include <chrono>
#include <thread>

static void check(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
int main() {
    try {
        std::uint64_t rendered=0, events=0;
        s760::NativeStream stream([&](const s760::NativeStream::Block& b,float* pcm) {
            check(b.first==rendered,"Worker block clock discontinuity");
            for (unsigned i=0;i<b.events;++i) {
                check(b.midi[i].offset==i*256+17 && b.midi[i].bytes[0]==0x80,"Lost note-off/offset");
                ++events;
            }
            for(unsigned i=0;i<b.frames;++i) { pcm[i*2]=float(rendered+i+1); pcm[i*2+1]=-pcm[i*2]; }
            rendered+=b.frames;
            return true;
        });
        stream.start();
        float left[256],right[256];
        s760::NativeStream::Midi note{17,{0x80,60,0}};
        for(unsigned block=0;block<128;++block) {
            check(stream.process(left,right,256,&note,1),"Stream process failed");
            for(unsigned i=0;i<256;++i) {
                auto t=block*256+i;
                float expected=t<s760::NativeStream::output_delay ? 0.f : float(t-s760::NativeStream::output_delay+1);
                check(left[i]==expected && right[i]==-expected,"PCM order/delay mismatch");
            }
            auto until=std::chrono::steady_clock::now()+std::chrono::seconds(2);
            while((block+1)%8==0 && stream.completed_frames()<(block+1)*256) {
                check(stream.fault()==s760::NativeStream::Fault::none,"Worker failure");
                check(std::chrono::steady_clock::now()<until,"Worker timeout");
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        }
        stream.stop(); check(events==128,"Lost events");
        s760::NativeStream blocked([](auto&,float*) { return false; });
        // No worker: finite queue must reject overload, including a note-off.
        unsigned accepted=0;
        while(blocked.process(left,right,1,&note,0)) ++accepted;
        check(accepted>0 && accepted<=s760::NativeStream::queue_blocks,"Unbounded producer");
        check(blocked.fault()==s760::NativeStream::Fault::input_overflow,"Overflow not reported");
        s760::NativeStream invalid([](auto&,float*) { return true; });
        check(!invalid.process(left,right,16,&note,1),"Out-of-block event accepted");
        check(invalid.fault()==s760::NativeStream::Fault::invalid_block,"Invalid block not reported");
        auto underrun=std::make_unique<s760::NativeStream>([](auto&,float*) { return true; });
        float l[1024],r[1024];
        for(unsigned i=0;i<8;++i) check(underrun->process(l,r,1024,nullptr,0),"Initial delay failed");
        check(!underrun->process(l,r,1024,nullptr,0),"Missing deadline not detected");
        check(underrun->fault()==s760::NativeStream::Fault::output_underrun,"Wrong underrun fault");
        for(auto value:l) check(value==0,"Underrun output not silent");
        auto offline=std::make_unique<s760::NativeStream>([](const auto& b,float* pcm) {
            std::this_thread::sleep_for(std::chrono::milliseconds(3));
            for(unsigned i=0;i<b.frames;++i) {pcm[i*2]=float(b.first+i+1);pcm[i*2+1]=-pcm[i*2];}
            return true;
        });
        offline->start();
        for(unsigned block=0;block<128;++block) {
            check(offline->process(l,r,1024,nullptr,0,true),"Unpaced offline block failed");
            for(unsigned i=0;i<1024;++i) {
                auto t=block*1024+i;
                const float expected=t<8192 ? 0.f : float(t-8192+1);
                check(l[i]==expected && r[i]==-expected,"Offline PCM clock changed");
            }
        }
        offline->stop();
        auto tiny=std::make_unique<s760::NativeStream>([](const auto& b,float* pcm) {
            std::fill_n(pcm,b.frames*2,.25f);return true;
        });
        tiny->start();
        for(unsigned i=0;i<9000;++i) {
            check(tiny->process(l,r,1,nullptr,0,true),"Tiny offline block backpressure failed");
            check(l[0]==(i<8192 ? 0.f : .25f),"Tiny offline output differs");
        }
        tiny->stop();
        auto failure=std::make_unique<s760::NativeStream>([](auto&,float*) { return false; });
        failure->start();
        check(failure->process(l,r,1024,nullptr,0) && failure->process(l,r,1024,nullptr,0),"Failure test enqueue");
        auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(2);
        while(failure->fault()==s760::NativeStream::Fault::none) {
            check(std::chrono::steady_clock::now()<deadline,"Failure was not reported");
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        check(failure->fault()==s760::NativeStream::Fault::renderer_failed,"Renderer failure hidden");
        check(!failure->process(l,r,1024,nullptr,0),"Failed renderer accepted more input");
        auto synth=[](const s760::NativeStream::Block& b,float* output) {
            for(unsigned i=0;i<b.frames;++i) {
                output[i*2]=float(b.first+i+1); output[i*2+1]=-output[i*2];
            }
            return true;
        };
        auto source=std::make_unique<s760::NativeStream>(synth);
        source->start();
        for(unsigned b=0;b<17;++b) {
            check(source->process(l,r,256,b==16 ? &note : nullptr,b==16 ? 1 : 0),"Snapshot setup");
            if((b+1)%8==0) {
                auto until=std::chrono::steady_clock::now()+std::chrono::seconds(2);
                while(source->completed_frames()<(b+1)*256) {
                    check(std::chrono::steady_clock::now()<until,"Snapshot setup timeout");
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                }
            }
        }
        source->stop();
        auto saved=source->snapshot();
        check(saved.clock==4352 && saved.completed==4096 && saved.pcm.size()==8192 && saved.pending.size()==1,
              "Snapshot omitted PCM or partial input block");
        std::uint64_t noteoffs=0;
        auto clone=std::make_unique<s760::NativeStream>([&](const auto& b,float* output) {
            for(unsigned i=0;i<b.events;++i) {
                check(b.first+b.midi[i].offset==4113 && b.midi[i].bytes[0]==0x80,"Restored note-off clock mismatch");
                ++noteoffs;
            }
            return synth(b,output);
        },saved);
        clone->start();
        for(unsigned b=17;b<128;++b) {
            check(clone->process(l,r,256,nullptr,0),"Restored stream callback failed");
            for(unsigned i=0;i<256;++i) {
                auto clock=b*256+i;
                auto expected=clock<8192 ? 0.f : float(clock-8192+1);
                check(l[i]==expected && r[i]==-expected,"Restored PCM or padding shifted");
            }
            if((b+1)%8==0) {
                auto until=std::chrono::steady_clock::now()+std::chrono::seconds(2);
                while(clone->completed_frames()<(b+1)*256) {
                    check(std::chrono::steady_clock::now()<until,"Restored worker timeout");
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                }
            }
        }
        clone->stop(); check(noteoffs==1,"Restored note-off lost or duplicated");
        saved.clock++;
        bool rejected=false;
        try { auto bad=std::make_unique<s760::NativeStream>(synth,saved); } catch(const std::invalid_argument&) { rejected=true; }
        check(rejected,"Inconsistent saved stream clock accepted");
        s760::NativeStream::InputRenderer capture=[](const auto& b,const float* input,float* pcm) {
            for(unsigned i=0;i<b.frames;++i) {
                check(input[i*2]==float(b.first+i)/32768.f && input[i*2+1]==-float(b.first+i)/32768.f,"Input copy/ordering changed");
                pcm[i*2]=input[i*2];pcm[i*2+1]=input[i*2+1];
            }
            return true;
        };
        auto input_source=std::make_unique<s760::NativeStream>(capture);
        float in_l[64],in_r[64];
        for(unsigned i=0;i<64;++i){in_l[i]=float(i)/32768.f;in_r[i]=-in_l[i];}
        check(input_source->process(l,r,64,nullptr,0,false,in_l,in_r),"Input enqueue failed");
        auto input_saved=input_source->snapshot();
        std::fill_n(in_l,64,99.f);std::fill_n(in_r,64,99.f);
        auto input_clone=std::make_unique<s760::NativeStream>(capture,input_saved);input_clone->start();
        for(unsigned block=1;block<160;++block) {
            for(unsigned i=0;i<64;++i){in_l[i]=float(block*64+i)/32768.f;in_r[i]=-in_l[i];}
            check(input_clone->process(l,r,64,nullptr,0,true,in_l,in_r),"Input snapshot replay failed");
            if(block*64>=8192)for(unsigned i=0;i<64;++i)check(l[i]==float(block*64+i-8192)/32768.f && r[i]==-l[i],"Recorded input output shifted");
        }
        input_clone->stop();
        auto bad_input=std::make_unique<s760::NativeStream>(capture);in_l[3]=NAN;
        check(!bad_input->process(l,r,64,nullptr,0,false,in_l,in_r),"Nonfinite input accepted");
        check(bad_input->fault()==s760::NativeStream::Fault::invalid_block,"Input format fault hidden");
        std::cout << "Native stream ordering, fixed delay, note-off offsets, backpressure and validation passed\n";
    } catch(const std::exception& e) { std::cerr << e.what()<<"\n"; return 1; }
}
