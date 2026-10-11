#include "s760/s760_native_rate_converter.hpp"
#include <iostream>
#include <algorithm>
#include <memory>
static void check(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
static std::vector<float> tone(unsigned rate,double hz,bool varied) {
    std::uint64_t source=0;
    s760::NativeRateConverter converter(rate,[&](float* pcm,std::size_t n) {
        for(std::size_t i=0;i<n;++i,++source) {
            pcm[i*2]=float(std::sin(2*3.14159265358979323846*hz*double(source)/44100));
            pcm[i*2+1]=-pcm[i*2];
        }return true;
    });
    std::vector<float> output(rate*2);
    const unsigned sizes[]{1,63,127,256,511,1024,2048,3071};
    for(unsigned offset=0,b=0;offset<rate;++b) {
        auto count=std::min(rate-offset,varied?sizes[b%8]:2048u);
        check(converter.pull(output.data()+offset*2,count),"Conversion failed");offset+=count;
    }
    check(source==44100 && converter.native_frames()==44100,"Native clock drift");
    return output;
}
int main() {
    try {
        for(auto rate:{44100u,48000u,96000u}) {
            std::uint64_t cursor=0;
            auto render=[&](float* pcm,std::size_t n) {
                for(std::size_t i=0;i<n;++i,++cursor) {
                    pcm[2*i]=float(std::sin(double(cursor)*.131));
                    pcm[2*i+1]=float(std::cos(double(cursor)*.237));
                } return true;
            };
            s760::NativeRateConverter original(rate,render);
            std::vector<float> warm(777*2),expected(8192*2),actual(8192*2);
            check(original.pull(warm.data(),777),"Snapshot warmup failed");
            auto saved=original.snapshot(); auto saved_cursor=cursor;
            check(original.pull(expected.data(),8192),"Snapshot reference failed");
            cursor=saved_cursor;
            s760::NativeRateConverter restored(saved,render);
            check(restored.pull(actual.data(),8192) && actual==expected,"Converter history/phase not restored exactly");
            saved.native_cursor++;
            bool bad=false;
            try { s760::NativeRateConverter invalid(saved,render); }
            catch(const std::invalid_argument&) { bad=true; }
            check(bad,"Inconsistent converter clocks accepted");
        }
        for(auto rate:{44100u,48000u,96000u}) for(auto hz:{100.,1000.,10000.,18000.}) {
            auto a=tone(rate,hz,false), b=tone(rate,hz,true);
            check(a==b,"Rate converter depends on block partition");
            double error=0,energy=0;
            const auto delay=rate==44100?0.:16.;
            for(unsigned i=128;i<rate;++i) {
                check(a[i*2+1]==-a[i*2],"Channel crosstalk");
                auto expected=std::sin(2*3.14159265358979323846*hz*(double(i)/rate-delay/44100));
                error+=std::pow(a[i*2]-expected,2);energy+=expected*expected;
            }
            auto relative=std::sqrt(error/energy);
            std::cout<<"rate="<<rate<<" Hz="<<hz<<" relative_rms="<<relative<<"\n";
            check(relative<.005,"Rate conversion tone fidelity failed");
        }
        for(auto rate:{48000u,96000u}) {
            unsigned source=0;
            s760::NativeRateConverter impulse(rate,[&](float* pcm,std::size_t n) {
                for(std::size_t i=0;i<n;++i,++source) {pcm[i*2]=source==32 ? 1.f : 0.f;pcm[i*2+1]=0;}
                return true;
            });
            std::array<float,1024*2> out{};
            check(impulse.pull(out.data(),1024),"Impulse conversion failed");
            double energy=0,moment=0;
            for(unsigned i=0;i<1024;++i) {
                check(out[i*2+1]==0,"Impulse leaked to other channel");
                auto power=double(out[i*2])*out[i*2];energy+=power;moment+=i*power;
            }
            auto expected=48.*rate/44100;
            check(std::abs(moment/energy-expected)<.01,"Converter group delay differs");
            std::cout<<"rate="<<rate<<" impulse_center="<<moment/energy<<" expected="<<expected<<"\n";
            // Ten-minute event positions: ceil mapping stays within one native
            // sample without accumulating per-block rounding or phase errors.
            for(std::uint64_t host=0;host<std::uint64_t(rate)*600;host+=997) {
                auto mapped=s760::NativeRateConverter::native_sample(host,rate);
                check(mapped*rate>=host*44100 && mapped*rate-host*44100<rate,"Event clock drift");
            }
        }
        bool rejected=false;
        try { auto bad=std::make_unique<s760::NativeRateConverter>(32000,[](float*,auto){return true;}); }
        catch(const std::invalid_argument&) { rejected=true; }
        check(rejected,"Unsupported rate accepted");
        std::cout<<"Native conversion: phase continuity, clock, channel separation and tone fidelity passed\n";
    }catch(const std::exception& e) {std::cerr<<e.what()<<"\n";return 1;}
}
