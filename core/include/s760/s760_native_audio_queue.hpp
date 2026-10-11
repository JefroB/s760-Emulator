#pragma once

#include <array>
#include <atomic>
#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <vector>
#include <stdexcept>

namespace s760 {

// Exactly one PCM worker producer and one audio-callback consumer. Construct
// before activation; never reset/destroy while either side is using the queue.
// No socket, lock, allocation or emulation work on the consumer path.
template <std::size_t Capacity = 32768>
class NativeAudioQueue {
    static_assert(Capacity > 0);
    static_assert(std::atomic<std::uint64_t>::is_always_lock_free);
public:
    // Accept a prefix; the worker retains/retries the remainder (no overwrite).
    std::size_t write(const float* interleaved, std::size_t count) noexcept {
        const auto head = head_.load(std::memory_order_relaxed);
        const auto tail = tail_.load(std::memory_order_acquire);
        const auto accepted = std::min(count, Capacity - std::size_t(head-tail));
        for (std::size_t i=0; i<accepted; ++i) {
            const auto slot = (head+i)%Capacity;
            data_[slot*2] = interleaved[i*2];
            data_[slot*2+1] = interleaved[i*2+1];
        }
        head_.store(head+accepted, std::memory_order_release);
        return accepted;
    }

    // Missing samples are explicit host underrun silence, never native PCM.
    std::size_t read(float* left, float* right, std::size_t count) noexcept {
        const auto tail = tail_.load(std::memory_order_relaxed);
        const auto head = head_.load(std::memory_order_acquire);
        const auto received = std::min(count, std::size_t(head-tail));
        for (std::size_t i=0; i<received; ++i) {
            const auto slot = (tail+i)%Capacity;
            left[i] = data_[slot*2];
            right[i] = data_[slot*2+1];
        }
        for (std::size_t i=received; i<count; ++i) left[i] = right[i] = 0.0f;
        tail_.store(tail+received, std::memory_order_release);
        if (received != count) underrun_frames_.fetch_add(count-received, std::memory_order_relaxed);
        return received;
    }
    std::uint64_t underrun_frames() const noexcept { return underrun_frames_.load(std::memory_order_relaxed); }
    std::size_t buffered_frames() const noexcept {
        const auto tail=tail_.load(std::memory_order_acquire);
        const auto head=head_.load(std::memory_order_acquire);
        return std::min(Capacity, std::size_t(head-tail));
    }
    // Control thread only, with producer and consumer stopped. Store chronological
    // unread PCM, not ring positions or padding. Float bits are preserved.
    std::vector<float> snapshot() const {
        const auto tail=tail_.load(), head=head_.load();
        std::vector<float> result(std::size_t(head-tail)*2);
        for(std::size_t i=0;i<head-tail;++i) {
            result[i*2]=data_[((tail+i)%Capacity)*2];
            result[i*2+1]=data_[((tail+i)%Capacity)*2+1];
        }
        return result;
    }
    void restore(const std::vector<float>& pcm) {
        if(pcm.size()%2 || pcm.size()>Capacity*2) throw std::invalid_argument("Invalid PCM queue snapshot");
        std::copy(pcm.begin(),pcm.end(),data_.begin());
        tail_.store(0); head_.store(pcm.size()/2); underrun_frames_.store(0);
    }
private:
    std::array<float, Capacity*2> data_{};
    alignas(64) std::atomic<std::uint64_t> head_{0};
    alignas(64) std::atomic<std::uint64_t> tail_{0};
    std::atomic<std::uint64_t> underrun_frames_{0};
};
}
