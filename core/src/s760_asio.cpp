// Standalone ASIO bridge. PortAudio owns device time; MAME owns emulated time.
// The native callback only copies bounded preallocated SPSC queues.
#define NOMINMAX
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <functiondiscoverykeys_devpkey.h>
#include <wrl/client.h>
#include <portaudio.h>
#include <pa_asio.h>
#include <array>
#include <atomic>
#include <algorithm>
#include <cmath>
#include <cstring>
#include <memory>
#include <stdexcept>
#include <string>

#define API extern "C" __declspec(dllexport)
namespace {
thread_local std::string error;
struct PortAudio {
    HMODULE dll=nullptr;
#define PA_FN(name) decltype(&name) name=nullptr
    PA_FN(Pa_Initialize); PA_FN(Pa_Terminate); PA_FN(Pa_GetDeviceCount);
    PA_FN(Pa_GetDeviceInfo); PA_FN(Pa_GetHostApiInfo); PA_FN(Pa_GetErrorText);
    PA_FN(Pa_OpenStream); PA_FN(Pa_StartStream); PA_FN(Pa_AbortStream);
    PA_FN(Pa_CloseStream); PA_FN(Pa_IsStreamActive); PA_FN(Pa_GetStreamInfo);
#undef PA_FN
    void check(PaError code) { if(code<0) throw std::runtime_error(Pa_GetErrorText(code)); }
    void load(const wchar_t* path) {
        if(dll)return;
        dll=LoadLibraryExW(path,nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
        if(!dll)throw std::runtime_error("ASIO PortAudio library is missing or cannot load");
        try {
#define LOAD(name) name=reinterpret_cast<decltype(name)>(GetProcAddress(dll,#name)); if(!name)throw std::runtime_error("ASIO library lacks " #name)
            LOAD(Pa_Initialize); LOAD(Pa_Terminate); LOAD(Pa_GetDeviceCount);
            LOAD(Pa_GetDeviceInfo); LOAD(Pa_GetHostApiInfo); LOAD(Pa_GetErrorText);
            LOAD(Pa_OpenStream); LOAD(Pa_StartStream); LOAD(Pa_AbortStream);
            LOAD(Pa_CloseStream); LOAD(Pa_IsStreamActive); LOAD(Pa_GetStreamInfo);
#undef LOAD
            check(Pa_Initialize());
        } catch(...) {FreeLibrary(dll);dll=nullptr;throw;}
    }
} pa;
unsigned open_hosts=0;
constexpr unsigned capacity=65536;
struct Ring {
    std::array<float,capacity*2> data{};
    alignas(64) std::atomic<unsigned long long> head{0},tail{0};
    unsigned available() const {const auto t=tail.load(std::memory_order_acquire);return std::min(capacity,unsigned(head.load(std::memory_order_acquire)-t));}
    unsigned write(const float* src,unsigned frames,bool sanitize=false) noexcept {
        const auto h=head.load(std::memory_order_relaxed),t=tail.load(std::memory_order_acquire);
        const auto n=std::min(frames,capacity-unsigned(h-t));
        for(unsigned i=0;i<n;++i)for(unsigned ch=0;ch<2;++ch){const float v=src[i*2+ch];data[((h+i)%capacity)*2+ch]=sanitize?(std::isfinite(v)?std::clamp(v,-1.0f,1.0f):0.0f):v;}
        head.store(h+n,std::memory_order_release);return n;
    }
    unsigned read(float* dst,unsigned frames) noexcept {
        const auto t=tail.load(std::memory_order_relaxed),h=head.load(std::memory_order_acquire);
        const auto n=std::min(frames,unsigned(h-t));
        for(unsigned i=0;i<n;++i){dst[i*2]=data[((t+i)%capacity)*2];dst[i*2+1]=data[((t+i)%capacity)*2+1];}
        tail.store(t+n,std::memory_order_release);return n;
    }
};
static_assert(std::atomic<unsigned long long>::is_always_lock_free);
struct Host {
    Ring output,input;
    PaStream* stream=nullptr;
    bool playback=false,recording=false,primed=false,started=false;
    unsigned prime=2048;
    std::atomic<unsigned long long> output_underflows{0},input_overflows{0},driver_flags{0},played{0},captured{0};
    static int callback(const void* in,void* out,unsigned long frames,const PaStreamCallbackTimeInfo*,PaStreamCallbackFlags flags,void* user) noexcept {
        auto& h=*static_cast<Host*>(user);
        if(flags)h.driver_flags.fetch_or(flags,std::memory_order_relaxed);
        if(in && h.recording){const auto n=h.input.write(static_cast<const float*>(in),unsigned(frames));h.captured.fetch_add(frames,std::memory_order_relaxed);h.input_overflows.fetch_add(frames-n,std::memory_order_relaxed);}
        if(out){
            auto* dst=static_cast<float*>(out);unsigned n=0;
            if(!h.primed && h.output.available()>=h.prime){h.primed=true;h.started=true;}
            if(h.playback && h.started && !h.primed)h.output_underflows.fetch_add(frames,std::memory_order_relaxed);
            if(h.playback && h.primed){n=h.output.read(dst,unsigned(frames));h.played.fetch_add(n,std::memory_order_relaxed);if(n<frames){h.output_underflows.fetch_add(frames-n,std::memory_order_relaxed);h.primed=false;}}
            std::fill(dst+n*2,dst+frames*2,0.0f);
        }
        return paContinue;
    }
    ~Host(){if(stream){pa.Pa_AbortStream(stream);pa.Pa_CloseStream(stream);}}
};
bool asio(int index){const auto* d=pa.Pa_GetDeviceInfo(index);return d && pa.Pa_GetHostApiInfo(d->hostApi)->type==paASIO;}
template<class F> int attempt(F fn){try{fn();error.clear();return 0;}catch(const std::exception& e){error=e.what();return -1;}}
}
API const char* s760_asio_error(){return error.c_str();}
// Control-thread inventory for MAME's existing WASAPI sound-map endpoint IDs.
API int s760_windows_output(int ordinal,char* id,unsigned id_size,char* name,unsigned name_size,unsigned* rate,unsigned* channels){return attempt([&]{
    const HRESULT init=CoInitializeEx(nullptr,COINIT_MULTITHREADED);
    if(FAILED(init) && init!=RPC_E_CHANGED_MODE)throw std::runtime_error("Windows audio COM initialization failed");
    struct Cleanup{bool initialized;~Cleanup(){if(initialized)CoUninitialize();}} cleanup{SUCCEEDED(init)};
    using Microsoft::WRL::ComPtr;
    ComPtr<IMMDeviceEnumerator> enumerator;ComPtr<IMMDeviceCollection> devices;
    if(FAILED(CoCreateInstance(__uuidof(MMDeviceEnumerator),nullptr,CLSCTX_ALL,IID_PPV_ARGS(&enumerator))) ||
       FAILED(enumerator->EnumAudioEndpoints(eRender,DEVICE_STATE_ACTIVE,&devices)))throw std::runtime_error("Windows output discovery failed");
    UINT count=0;devices->GetCount(&count);
    if(ordinal<0 || unsigned(ordinal)>=count)throw std::runtime_error("Windows output is unavailable");
    ComPtr<IMMDevice> device;ComPtr<IPropertyStore> properties;LPWSTR endpoint=nullptr;PROPVARIANT value;PropVariantInit(&value);
    if(FAILED(devices->Item(ordinal,&device)) || FAILED(device->GetId(&endpoint)))throw std::runtime_error("Windows endpoint identity failed");
    struct EndpointCleanup{LPWSTR id;PROPVARIANT* value;~EndpointCleanup(){CoTaskMemFree(id);PropVariantClear(value);}} release{endpoint,&value};
    if(FAILED(device->OpenPropertyStore(STGM_READ,&properties)) || FAILED(properties->GetValue(PKEY_Device_FriendlyName,&value)) || value.vt!=VT_LPWSTR)throw std::runtime_error("Windows endpoint name failed");
    auto copy=[](const wchar_t* src,char* dst,unsigned size){const int n=WideCharToMultiByte(CP_UTF8,0,src,-1,nullptr,0,nullptr,nullptr);if(n<=0 || unsigned(n)>size)throw std::runtime_error("Windows endpoint exceeds buffer");WideCharToMultiByte(CP_UTF8,0,src,-1,dst,size,nullptr,nullptr);};
    copy(endpoint,id,id_size);copy(value.pwszVal,name,name_size);
    *rate=0;*channels=0;ComPtr<IAudioClient> client;WAVEFORMATEX* format=nullptr;
    if(SUCCEEDED(device->Activate(__uuidof(IAudioClient),CLSCTX_ALL,nullptr,reinterpret_cast<void**>(client.GetAddressOf()))) && SUCCEEDED(client->GetMixFormat(&format))){*rate=format->nSamplesPerSec;*channels=format->nChannels;CoTaskMemFree(format);}
});}
API int s760_asio_initialize(const wchar_t* path){return attempt([&]{pa.load(path);});}
API int s760_asio_shutdown(){return attempt([]{if(open_hosts)throw std::runtime_error("ASIO streams remain open");if(pa.dll){pa.check(pa.Pa_Terminate());FreeLibrary(pa.dll);pa.dll=nullptr;}});}
API int s760_asio_device_count(){if(!pa.dll)return 0;int n=0;for(int i=0;i<pa.Pa_GetDeviceCount();++i)if(asio(i))++n;return n;}
API int s760_asio_device(int ordinal,char* name,unsigned size,int* inputs,int* outputs){return attempt([&]{
    for(int i=0;i<pa.Pa_GetDeviceCount();++i)if(asio(i) && ordinal--==0){const auto* d=pa.Pa_GetDeviceInfo(i);if(std::strlen(d->name)+1>size)throw std::runtime_error("ASIO driver name exceeds buffer");std::strcpy(name,d->name);*inputs=d->maxInputChannels;*outputs=d->maxOutputChannels;return;}
    throw std::runtime_error("ASIO driver is unavailable");
});}
API void* s760_asio_open(const char* name,int output_first,int input_first,unsigned block,int playback){
    Host* result=nullptr;
    attempt([&]{
        if(!pa.dll)throw std::runtime_error("ASIO is not initialized");
        if(block<64 || block>2048 || (block&(block-1)))throw std::runtime_error("ASIO buffer must be 64,128,256,512,1024 or2048 frames");
        int dev=paNoDevice;for(int i=0;i<pa.Pa_GetDeviceCount();++i)if(asio(i) && std::strcmp(pa.Pa_GetDeviceInfo(i)->name,name)==0){dev=i;break;}
        if(dev==paNoDevice)throw std::runtime_error("Selected ASIO driver is unavailable");
        const auto* d=pa.Pa_GetDeviceInfo(dev);
        if(output_first<1 || output_first+1>d->maxOutputChannels || input_first<0 || (input_first && input_first+1>d->maxInputChannels))throw std::runtime_error("Selected ASIO stereo channel pair is unavailable");
        auto h=std::make_unique<Host>();h->playback=playback!=0;h->recording=input_first!=0;h->prime=std::max(8192u,block*4);
        int outputs[2]={output_first-1,output_first},inputs[2]={input_first-1,input_first};
        PaAsioStreamInfo out_info{sizeof(PaAsioStreamInfo),paASIO,1,paAsioUseChannelSelectors,outputs};
        PaAsioStreamInfo in_info{sizeof(PaAsioStreamInfo),paASIO,1,paAsioUseChannelSelectors,inputs};
        PaStreamParameters out{dev,2,paFloat32,double(block)/44100,&out_info};
        PaStreamParameters in{dev,2,paFloat32,double(block)/44100,&in_info};
        pa.check(pa.Pa_OpenStream(&h->stream,h->recording?&in:nullptr,&out,44100,block,paClipOff,Host::callback,h.get()));
        pa.check(pa.Pa_StartStream(h->stream));result=h.release();++open_hosts;
    });return result;
}
API void s760_asio_close(void* host){if(host){delete static_cast<Host*>(host);--open_hosts;}}
API unsigned s760_asio_write(void* host,const float* pcm,unsigned frames){if(!host || frames>44100)return 0;return static_cast<Host*>(host)->output.write(pcm,frames,true);}
API unsigned s760_asio_read(void* host,short* pcm,unsigned frames){
    if(!host || frames>2048)return 0;
    auto& input=static_cast<Host*>(host)->input;
    if(input.available()<frames)return 0;
    std::array<float,4096> buffer;const auto n=input.read(buffer.data(),frames);
    for(unsigned i=0;i<n*2;++i){const auto v=std::isfinite(buffer[i])?std::clamp(buffer[i],-1.0f,1.0f):0.0f;pcm[i]=short(std::clamp(int(std::lrint(v*32768.0f)),-32768,32767));}
    return n;
}
struct Status {unsigned long long played,captured,output_underflows,input_overflows,driver_flags;unsigned output_queued,input_queued;double input_latency,output_latency,rate;int active;};
API int s760_asio_status(void* host,Status* result){return attempt([&]{
    if(!host)throw std::runtime_error("ASIO stream is closed");auto& h=*static_cast<Host*>(host);const auto* info=pa.Pa_GetStreamInfo(h.stream);
    *result={h.played.load(),h.captured.load(),h.output_underflows.load(),h.input_overflows.load(),h.driver_flags.load(),h.output.available(),h.input.available(),info?info->inputLatency:0,info?info->outputLatency:0,info?info->sampleRate:0,pa.Pa_IsStreamActive(h.stream)};
});}
