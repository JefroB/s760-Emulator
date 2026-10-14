#pragma once
#include "s760_native_audio_queue.hpp"
#include <thread>
#include <chrono>
#include <functional>
#include <stdexcept>
#include <memory>
#include <cmath>
#include <cstdio>

namespace s760 {
// Single callback producer/consumer and one worker. Fixed input/output clocks:
// on a missed deadline, latch a fault rather than replaying stale audio later.
// Lifecycle calls require the callback to be quiescent. Rendering stays on the
// worker; only explicitly offline callers may wait. No speculative rendering.
class NativeStream {
public:
    static constexpr unsigned max_frames=1024, max_events=64, queue_blocks=128;
    static constexpr unsigned output_delay=8192, midi_lead=4096;
    struct Midi { unsigned offset=0; std::array<std::uint8_t,3> bytes{}; };
    struct Block {
        std::uint64_t first=0;
        unsigned frames=0,events=0;
        std::array<Midi,max_events> midi{};
        std::array<float,max_frames*2> input{};
    };
    enum class Fault { none, invalid_block, input_overflow, output_underrun, renderer_failed };
    using Renderer=std::function<bool(const Block&,float*)>;
    using InputRenderer=std::function<bool(const Block&,const float*,float*)>;
    struct Snapshot {
        unsigned version=3;
        unsigned delay_frames=output_delay,batch_frames=2048;
        std::uint64_t clock=0,completed=0;
        std::vector<Block> pending;
        std::vector<float> pcm;
    };
    explicit NativeStream(Renderer render,unsigned delay_frames=output_delay,unsigned batch_frames=2048)
        :NativeStream(InputRenderer([render](const Block& b,const float*,float* pcm){return render(b,pcm);}),delay_frames,batch_frames) {}
    explicit NativeStream(InputRenderer render,unsigned delay_frames=output_delay,unsigned batch_frames=2048)
        :render_(std::move(render)),delay_frames_(delay_frames),batch_frames_(batch_frames) {
        if(!delay_frames || delay_frames>32768-8192 || batch_frames<max_frames || batch_frames>8192-max_frames)
            throw std::invalid_argument("Invalid native stream timing budget");
    }
    NativeStream(Renderer render,const Snapshot& saved):NativeStream(InputRenderer([render](const Block& b,const float*,float* pcm){return render(b,pcm);}),saved) {}
    NativeStream(InputRenderer render,const Snapshot& saved):NativeStream(std::move(render),saved.delay_frames,saved.batch_frames) {
        if((saved.version!=2 && saved.version!=3) || saved.pending.size()>queue_blocks || saved.completed>saved.clock)
            throw std::invalid_argument("Invalid stream snapshot header");
        auto cursor=saved.completed;
        for(const auto& block:saved.pending) {
            if(block.first!=cursor || cursor>saved.clock || block.frames>saved.clock-cursor ||
               !block.frames || block.frames>max_frames || block.events>max_events)
                throw std::invalid_argument("Invalid pending stream block");
            for(unsigned i=0;i<block.events;++i)
                if(block.midi[i].offset>=block.frames || (i && block.midi[i].offset<block.midi[i-1].offset))
                    throw std::invalid_argument("Invalid pending event offset");
            for(unsigned i=0;i<block.frames*2;++i) if(!std::isfinite(block.input[i])) throw std::invalid_argument("Invalid saved input PCM");
            cursor+=block.frames;
        }
        const auto consumed=saved.clock>delay_frames_ ? saved.clock-delay_frames_ : 0;
        if(cursor!=saved.clock || saved.completed<consumed || saved.pcm.size()%2 ||
           saved.pcm.size()/2!=saved.completed-consumed)
            throw std::invalid_argument("Stream snapshot clock/PCM mismatch");
        pcm_.restore(saved.pcm);
        std::copy(saved.pending.begin(),saved.pending.end(),blocks_->begin());
        head_.store(saved.pending.size()); completed_.store(saved.completed); clock_=saved.clock;
    }
    ~NativeStream() { stop(); }
    void start() {
        if(started_) throw std::logic_error("Stream is single-use");
        started_=true; thread_=std::thread([this] { run(); });
    }
    void stop() { stop_.store(true); if(thread_.joinable()) thread_.join(); }
    // Callback must be quiescent and worker joined before capturing. The native
    // machine and its MIDI-clock origin must be captured at this same boundary.
    Snapshot snapshot() const {
        if(thread_.joinable() || fault()!=Fault::none)
            throw std::logic_error("Snapshot requires stopped, healthy stream");
        Snapshot result; result.delay_frames=delay_frames_; result.batch_frames=batch_frames_; result.clock=clock_; result.completed=completed_.load();
        for(auto i=tail_.load();i<head_.load();++i) result.pending.push_back((*blocks_)[i%queue_blocks]);
        result.pcm=pcm_.snapshot();
        return result;
    }
    Fault fault() const noexcept { return fault_.load(); }
    void fail(Fault value) noexcept {
        auto expected=Fault::none; fault_.compare_exchange_strong(expected,value);
    }
    std::uint64_t completed_frames() const noexcept { return completed_.load(std::memory_order_acquire); }
    std::uint64_t started_frames() const noexcept { return started_frames_.load(std::memory_order_acquire); }
    bool process(float* left,float* right,unsigned frames,const Midi* midi,unsigned events,bool offline=false,const float* input_left=nullptr,const float* input_right=nullptr) noexcept {
        // The plugin validates writable output buffers before entering here.
        std::fill_n(left,frames,0.f); std::fill_n(right,frames,0.f);
        if(fault()!=Fault::none) return false;
        if(!frames || frames>max_frames || events>max_events || (events && !midi)) {
            fail(Fault::invalid_block); return false;
        }
        for(unsigned i=0;i<events;++i) if(midi[i].offset>=frames || (i && midi[i].offset<midi[i-1].offset)) {
            fail(Fault::invalid_block); return false;
        }
        if((input_left==nullptr)!=(input_right==nullptr)) {fail(Fault::invalid_block);return false;}
        if(input_left)for(unsigned i=0;i<frames;++i)if(!std::isfinite(input_left[i]) || !std::isfinite(input_right[i])) {fail(Fault::invalid_block);return false;}
        auto head=head_.load(std::memory_order_relaxed);
        if(offline && head-tail_.load(std::memory_order_acquire)==queue_blocks) {
            // Tiny blocks may fill the packet queue before reaching a render
            // batch. Request a partial batch before waiting for producer space.
            flush_until_.store(clock_,std::memory_order_release);
            const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);
            while(head-tail_.load(std::memory_order_acquire)==queue_blocks) {
                if(fault()!=Fault::none || stop_.load()) return false;
                if(std::chrono::steady_clock::now()>=deadline) {fail(Fault::input_overflow);return false;}
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        }
        if(head-tail_.load(std::memory_order_acquire)==queue_blocks) {
            fail(Fault::input_overflow); return false;
        }
        auto& b=(*blocks_)[head%queue_blocks]; b.first=clock_; b.frames=frames; b.events=events;
        std::copy_n(midi,events,b.midi.begin());
        for(unsigned i=0;i<frames;++i){b.input[i*2]=input_left?input_left[i]:0.f;b.input[i*2+1]=input_right?input_right[i]:0.f;}
        head_.store(head+1,std::memory_order_release);
        auto silence=unsigned(std::min<std::uint64_t>(frames,clock_<delay_frames_ ? delay_frames_-clock_ : 0));
        clock_+=frames;
        // Offline hosts need not observe wall-clock callback pacing. Wait only
        // on that explicitly negotiated path; realtime remains nonblocking.
        if(offline && silence<frames) {
            const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10);
            while(pcm_.buffered_frames()<frames-silence) {
                if(fault()!=Fault::none || stop_.load()) return false;
                if(std::chrono::steady_clock::now()>=deadline) {
                    fail(Fault::output_underrun); return false;
                }
                std::this_thread::sleep_for(std::chrono::milliseconds(1));
            }
        }
        if(silence<frames && pcm_.read(left+silence,right+silence,frames-silence)!=frames-silence) {
            fail(Fault::output_underrun);
            std::fill_n(left,frames,0.f); std::fill_n(right,frames,0.f); return false;
        }
        return true;
    }
private:
    void run() noexcept {
        try {
            std::array<float,8192*2> pcm{},input{};
            while(!stop_.load() && fault()==Fault::none) {
                auto tail=tail_.load(std::memory_order_relaxed);
                auto head=head_.load(std::memory_order_acquire);
                if(tail==head || pcm_.buffered_frames()>32768-8192) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(1)); continue;
                }
                // Amortize paused-runtime control polling over a configured number of host samples.
                // Callback packets retain their exact offsets when concatenated.
                Block b{}; b.first=(*blocks_)[tail%queue_blocks].first;
                auto end=tail;
                while(end<head && b.frames<batch_frames_) {
                    const auto& next=(*blocks_)[end%queue_blocks];
                    if(b.events+next.events>max_events) break;
                    for(unsigned i=0;i<next.events;++i) {
                        b.midi[b.events]=next.midi[i]; b.midi[b.events++].offset+=b.frames;
                    }
                    std::copy_n(next.input.data(),next.frames*2,input.data()+b.frames*2);
                    b.frames+=next.frames; ++end;
                }
                if(b.frames<batch_frames_ && end==head && b.events<max_events && b.first>=flush_until_.load(std::memory_order_acquire)) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(1)); continue;
                }
                started_frames_.store(b.first+b.frames,std::memory_order_release);
                if(!render_(b,input.data(),pcm.data()) || pcm_.write(pcm.data(),b.frames)!=b.frames) {
                    fail(Fault::renderer_failed); return;
                }
                completed_.store(b.first+b.frames,std::memory_order_release);
                tail_.store(end,std::memory_order_release);
            }
        } catch(const std::exception& error) { std::fprintf(stderr,"Native stream worker failed: %s\n",error.what());fail(Fault::renderer_failed); }
        catch(...) { fail(Fault::renderer_failed); }
    }
    InputRenderer render_;
    unsigned delay_frames_,batch_frames_;
    std::unique_ptr<std::array<Block,queue_blocks>> blocks_=std::make_unique<std::array<Block,queue_blocks>>();
    NativeAudioQueue<> pcm_;
    alignas(64) std::atomic<std::uint64_t> head_{0},tail_{0};
    std::atomic<std::uint64_t> completed_{0};
    std::atomic<std::uint64_t> started_frames_{0};
    std::atomic<std::uint64_t> flush_until_{0};
    std::atomic<Fault> fault_{Fault::none};
    std::atomic<bool> stop_{false};
    std::uint64_t clock_=0;
    bool started_=false;
    std::thread thread_;
};
}
