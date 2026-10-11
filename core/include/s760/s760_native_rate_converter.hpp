#pragma once
#include <array>
#include <vector>
#include <functional>
#include <numeric>
#include <cmath>
#include <cstdint>
#include <stdexcept>

namespace s760 {
// Worker-side causal conversion. Host integer clock owns output; MAME remains
// 44100 Hz. No phase reset at callback/render boundaries. No allocations in pull.
class NativeRateConverter {
public:
    static constexpr unsigned native_rate=44100, taps=33, delay=16, max_frames=8192;
    struct Snapshot {
        unsigned version=1,rate=44100;
        std::uint64_t host_cursor=0,native_cursor=0;
        std::array<float,taps*2> history{};
    };
    using Render=std::function<bool(float*,std::size_t)>;
    static bool supported(double rate) { return rate==44100 || rate==48000 || rate==96000; }
    static std::uint64_t native_sample(std::uint64_t host_sample,unsigned rate) {
        return (host_sample*native_rate+rate-1)/rate; // never enqueue before requested time
    }
    static unsigned host_samples(unsigned native_samples,unsigned rate) {
        return unsigned((std::uint64_t(native_samples)*rate+native_rate-1)/native_rate);
    }
    static unsigned latency(unsigned rate) { return rate==native_rate ? 0 : unsigned((std::uint64_t(delay)*rate+native_rate-1)/native_rate); }
    NativeRateConverter(unsigned rate,Render render):rate_(rate),render_(std::move(render)) {
        if(!supported(rate)) throw std::invalid_argument("Unsupported native output rate");
        if(rate==native_rate) return;
        phases_=rate/std::gcd(rate,native_rate);
        coefficients_.resize(phases_*taps);
        constexpr double pi=3.14159265358979323846;
        for(unsigned phase=0;phase<phases_;++phase) {
            double sum=0,frac=double(phase)/phases_;
            for(unsigned k=0;k<taps;++k) {
                const double x=k+frac-delay;
                const double window=std::abs(x)>delay ? 0 : .42+.5*std::cos(pi*x/delay)+.08*std::cos(2*pi*x/delay);
                const double sinc=std::abs(x)<1e-12 ? 1 : std::sin(pi*x)/(pi*x);
                const double c=window*sinc;
                coefficients_[phase*taps+k]=c;sum+=c;
            }
            for(unsigned k=0;k<taps;++k) coefficients_[phase*taps+k]/=sum;
        }
    }
    NativeRateConverter(const Snapshot& s,Render render):NativeRateConverter(s.rate,std::move(render)) {
        if(s.version!=1 || s.host_cursor>UINT64_MAX/native_rate ||
           s.native_cursor!=(s.host_cursor ? (s.host_cursor-1)*native_rate/s.rate+1 : 0))
            throw std::invalid_argument("Invalid converter snapshot clocks");
        for(auto value:s.history) if(!std::isfinite(value)) throw std::invalid_argument("Invalid converter history");
        host_cursor_=s.host_cursor;native_cursor_=s.native_cursor;history_=s.history;
    }
    Snapshot snapshot() const { return {1,rate_,host_cursor_,native_cursor_,history_}; }
    bool pull(float* output,unsigned count) {
        if(!count || count>max_frames) return false;
        if(rate_==native_rate) { if(!render_(output,count)) return false; host_cursor_+=count;native_cursor_+=count;return true; }
        auto last=(host_cursor_+count-1)*native_rate/rate_;
        auto needed=last+1-native_cursor_;
        if(needed>max_frames || (needed && !render_(input_.data(),std::size_t(needed)))) return false;
        unsigned input_offset=0;
        for(unsigned i=0;i<count;++i) {
            const auto time=host_cursor_*native_rate;
            const auto index=time/rate_;
            const auto phase=unsigned((time%rate_)/(rate_/phases_));
            while(native_cursor_<=index) {
                const auto slot=native_cursor_%taps;
                history_[slot*2]=input_[input_offset*2];history_[slot*2+1]=input_[input_offset*2+1];
                ++native_cursor_;++input_offset;
            }
            double left=0,right=0;
            for(unsigned k=0;k<taps && k<=index;++k) {
                const auto slot=(index-k)%taps;const auto c=coefficients_[phase*taps+k];
                left+=history_[slot*2]*c;right+=history_[slot*2+1]*c;
            }
            output[i*2]=float(left);output[i*2+1]=float(right);++host_cursor_;
        }
        return true;
    }
    std::uint64_t host_frames() const { return host_cursor_; }
    std::uint64_t native_frames() const { return native_cursor_; }
private:
    unsigned rate_,phases_=0;
    Render render_;
    std::vector<double> coefficients_;
    std::array<float,max_frames*2> input_{};
    std::array<float,taps*2> history_{};
    std::uint64_t host_cursor_=0,native_cursor_=0;
};
}
