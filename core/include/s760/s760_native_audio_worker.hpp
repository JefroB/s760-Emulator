#pragma once
#include "s760_native_audio_queue.hpp"
#include <functional>
#include <thread>
#include <chrono>
#include <stdexcept>

namespace s760 {
// Renderer runs on the worker, fills an exact interleaved PCM block and must
// bound/cancel its own I/O. No MAME connection is owned here. Callback uses only
// read(); setup, shutdown and telemetry belong off the realtime thread.
class NativeAudioWorker {
public:
    using Renderer=std::function<bool(float*,std::size_t)>;
    explicit NativeAudioWorker(Renderer render) : render_(std::move(render)) {}
    ~NativeAudioWorker() { stop(); }
    NativeAudioWorker(const NativeAudioWorker&)=delete;
    NativeAudioWorker& operator=(const NativeAudioWorker&)=delete;
    void start() {
        if (started_) throw std::logic_error("Audio worker is single-use");
        started_=true;
        thread_=std::thread([this] { run(); });
    }
    void stop() {
        stop_.store(true,std::memory_order_release);
        if (thread_.joinable()) thread_.join();
    }
    std::size_t read(float* left,float* right,std::size_t frames) noexcept {
        return queue_.read(left,right,frames);
    }
    bool failed() const noexcept { return failed_.load(std::memory_order_acquire); }
    std::uint64_t underrun_frames() const noexcept { return queue_.underrun_frames(); }
    std::size_t buffered_frames() const noexcept { return queue_.buffered_frames(); }
private:
    void run() noexcept {
        try {
            std::array<float,2048> block{};
            while (!stop_.load(std::memory_order_acquire)) {
                if (queue_.buffered_frames()>3072) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(1));
                    continue;
                }
                if (!render_(block.data(),1024)) {
                    failed_.store(true,std::memory_order_release);
                    return;
                }
                // Only this producer adds samples; consumption only frees space.
                if (queue_.write(block.data(),1024)!=1024)
                    throw std::logic_error("Native audio capacity invariant");
            }
        } catch (...) { failed_.store(true,std::memory_order_release); }
    }
    Renderer render_;
    NativeAudioQueue<4096> queue_;
    std::atomic<bool> stop_{false},failed_{false};
    bool started_=false;
    std::thread thread_;
};
}
