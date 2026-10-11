#include "s760/s760_native_runtime.hpp"
#include <stdexcept>
#include <mutex>
#include <cstring>
#include <map>
#include <random>
#include <sstream>
#include <chrono>
#include <algorithm>
#include <fstream>
#include <rapidjson/document.h>
#ifdef _WIN32
#define NOMINMAX
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#include <bcrypt.h>
#pragma comment(lib,"bcrypt.lib")
#endif

namespace s760 {
std::array<std::uint8_t,32> native_digest(const std::vector<std::uint8_t>& data) {
#ifdef _WIN32
    BCRYPT_ALG_HANDLE algorithm=nullptr;
    BCRYPT_HASH_HANDLE hash=nullptr;
    std::array<std::uint8_t,32> result{};
    if(BCryptOpenAlgorithmProvider(&algorithm,BCRYPT_SHA256_ALGORITHM,nullptr,0)<0)
        throw std::runtime_error("SHA256 provider unavailable");
    auto status=BCryptCreateHash(algorithm,&hash,nullptr,0,nullptr,0,0);
    if(status>=0) status=BCryptHashData(hash,const_cast<PUCHAR>(data.data()),ULONG(data.size()),0);
    if(status>=0) status=BCryptFinishHash(hash,result.data(),ULONG(result.size()),0);
    if(hash) BCryptDestroyHash(hash);
    BCryptCloseAlgorithmProvider(algorithm,0);
    if(status<0) throw std::runtime_error("SHA256 failed");
    return result;
#else
    throw std::runtime_error("Native state currently requires Windows");
#endif
}
namespace {
std::vector<std::uint8_t> read_state_file(const std::filesystem::path& path,std::size_t limit) {
    auto size=std::filesystem::file_size(path);
    if(!size || size>limit) throw std::runtime_error("Invalid native state/file size");
    std::vector<std::uint8_t> bytes(static_cast<std::size_t>(size));
    std::ifstream input(path,std::ios::binary);
    if(!input.read(reinterpret_cast<char*>(bytes.data()),bytes.size())) throw std::runtime_error("Native file read failed");
    return bytes;
}
std::array<std::uint8_t,32> scsi_identity(const std::filesystem::path& state) {
    const auto directory=state/"roms/SCSI";
    std::vector<std::filesystem::path> files;
    if(std::filesystem::exists(directory))
        for(const auto& file:std::filesystem::directory_iterator(directory)) {
            if(!file.is_regular_file() || file.is_symlink()) throw std::runtime_error("SCSI snapshot requires regular image files");
            files.push_back(file.path());
        }
    std::sort(files.begin(),files.end());
    std::vector<std::uint8_t> manifest;std::uintmax_t total=0;
    for(const auto& file:files) {
        auto size=std::filesystem::file_size(file);total+=size;
        if(total>64u*1024*1024) throw std::runtime_error("SCSI snapshot profile supports at most 64 MiB of external images");
        auto name=file.filename().u8string();manifest.insert(manifest.end(),name.begin(),name.end());manifest.push_back(0);
        auto sum=native_digest(size ? read_state_file(file,64u*1024*1024) : std::vector<std::uint8_t>{});
        manifest.insert(manifest.end(),sum.begin(),sum.end());
    }
    return native_digest(manifest);
}
rapidjson::Document parse(const std::string& text) {
    rapidjson::Document d;
    d.Parse(text.data(),text.size());
    if(d.HasParseError() || !d.IsObject()) throw std::runtime_error("Invalid native JSON response");
    return d;
}
#ifdef _WIN32
std::wstring quote(const std::wstring& text) {
    std::wstring result=L"\"";
    unsigned slashes=0;
    for(wchar_t c:text) {
        if(c==L'\\') { ++slashes; continue; }
        result.append(c==L'"' ? slashes*2+1 : slashes,L'\\');
        result+=c; slashes=0;
    }
    result.append(slashes*2,L'\\'); return result+L'"';
}
struct Socket {
    SOCKET value=INVALID_SOCKET;
    ~Socket() { if(value!=INVALID_SOCKET) closesocket(value); }
};
struct Handle {
    HANDLE value=INVALID_HANDLE_VALUE;
    ~Handle() { if(value!=INVALID_HANDLE_VALUE && value) CloseHandle(value); }
};
void transfer(SOCKET socket,void* data,std::size_t size,bool write) {
    auto* p=static_cast<char*>(data);
    while(size) {
        const int count=write ? send(socket,p,int(size),0) : recv(socket,p,int(size),0);
        if(count<=0) throw std::runtime_error("Native runtime disconnected or timed out");
        p+=count; size-=count;
    }
}
unsigned listen_local(Socket& socket) {
    socket.value=::socket(AF_INET,SOCK_STREAM,IPPROTO_TCP);
    sockaddr_in address{}; address.sin_family=AF_INET; address.sin_addr.s_addr=htonl(INADDR_LOOPBACK);
    if(socket.value==INVALID_SOCKET || bind(socket.value,reinterpret_cast<sockaddr*>(&address),sizeof(address)) || listen(socket.value,1))
        throw std::runtime_error("Cannot open native loopback listener");
    int size=sizeof(address); getsockname(socket.value,reinterpret_cast<sockaddr*>(&address),&size);
    return ntohs(address.sin_port);
}
void accept_local(Socket& result,Socket& listener,HANDLE process) {
    const auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(30);
    while(std::chrono::steady_clock::now()<deadline) {
        if(WaitForSingleObject(process,0)!=WAIT_TIMEOUT) throw std::runtime_error("Native process exited during startup");
        fd_set ready; FD_ZERO(&ready); FD_SET(listener.value,&ready); timeval timeout{0,100000};
        if(select(0,&ready,nullptr,nullptr,&timeout)>0) {
            result.value=accept(listener.value,nullptr,nullptr);
            if(result.value==INVALID_SOCKET) break;
            DWORD milliseconds=10000;
            BOOL no_delay=TRUE;
            setsockopt(result.value,IPPROTO_TCP,TCP_NODELAY,reinterpret_cast<char*>(&no_delay),sizeof(no_delay));
            setsockopt(result.value,SOL_SOCKET,SO_RCVTIMEO,reinterpret_cast<char*>(&milliseconds),sizeof(milliseconds));
            setsockopt(result.value,SOL_SOCKET,SO_SNDTIMEO,reinterpret_cast<char*>(&milliseconds),sizeof(milliseconds));
            return;
        }
    }
    throw std::runtime_error("Native connection timed out");
}
#endif
}
struct NativeRuntimeClient::Impl {
    std::array<std::uint8_t,32> scsi_hash{};
    std::mutex mutex;
    std::mutex media_mutex;
    std::filesystem::path state;
    NativeRuntimeConfig config;
#ifdef _WIN32
    Socket control,midi;
    Handle process,state_lock,log,job;
    bool wsa=false;
    ~Impl() {
        if(process.value!=INVALID_HANDLE_VALUE && WaitForSingleObject(process.value,0)==WAIT_TIMEOUT) {
            TerminateProcess(process.value,1); WaitForSingleObject(process.value,5000);
        }
        // Close sockets before matching the successful WSAStartup.
        if(control.value!=INVALID_SOCKET) { closesocket(control.value); control.value=INVALID_SOCKET; }
        if(midi.value!=INVALID_SOCKET) { closesocket(midi.value); midi.value=INVALID_SOCKET; }
        if(wsa) WSACleanup();
    }
    std::string receive_json() {
        std::uint32_t size=0; transfer(control.value,&size,4,false);
        if(!size || size>65536) throw std::runtime_error("Oversized native response");
        std::string text(size,'\0'); transfer(control.value,text.data(),size,false); return text;
    }
#endif
};
NativeRuntimeClient::NativeRuntimeClient(const NativeRuntimeConfig& supplied) : impl_(std::make_unique<Impl>()) {
#ifdef _WIN32
    auto cfg=supplied;
    if(cfg.root.empty() || cfg.state.empty()) throw std::runtime_error("Explicit native root and state directories are required");
    cfg.root=std::filesystem::absolute(cfg.root); cfg.state=std::filesystem::absolute(cfg.state);
    impl_->state=cfg.state;
    impl_->config=cfg;
    impl_->scsi_hash=scsi_identity(cfg.state);
    const auto exe=cfg.root/"mame-source/mames760.exe";
    if(!std::filesystem::is_regular_file(exe) || !std::filesystem::is_regular_file(cfg.boot_rom)
       || !std::filesystem::is_regular_file(cfg.system_disk) || std::filesystem::file_size(cfg.system_disk)!=1474560)
        throw std::runtime_error("Missing native executable/firmware or invalid system disk");
    std::filesystem::create_directories(cfg.state);
    impl_->state_lock.value=CreateFileW((cfg.state/"runtime.lock").c_str(),GENERIC_READ|GENERIC_WRITE,0,nullptr,OPEN_ALWAYS,0,nullptr);
    if(impl_->state_lock.value==INVALID_HANDLE_VALUE) throw std::runtime_error("Native state directory is in use");
    const auto roms=cfg.state/"roms/s760";
    std::filesystem::create_directories(roms);
    std::filesystem::copy_file(cfg.system_disk,roms/"s760224.img",std::filesystem::copy_options::overwrite_existing);
    if(!cfg.sample_disk.empty()) std::filesystem::copy_file(cfg.sample_disk,cfg.state/"inserted-floppy.img",std::filesystem::copy_options::overwrite_existing);
    WSADATA wsa{};
    if(WSAStartup(MAKEWORD(2,2),&wsa)) throw std::runtime_error("Winsock startup failed");
    impl_->wsa=true;
    impl_->job.value=CreateJobObjectW(nullptr,nullptr);
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION limits{};
    limits.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    if(!impl_->job.value || !SetInformationJobObject(impl_->job.value,JobObjectExtendedLimitInformation,&limits,sizeof(limits)))
        throw std::runtime_error("Cannot create native process lifetime job");
    Socket control_listener,midi_listener;
    const auto port=listen_local(control_listener), midi_port=listen_local(midi_listener);
    std::random_device random; std::string token;
    for(unsigned i=0;i<48;++i) token+="0123456789abcdef"[random()%16];
    std::map<std::wstring,std::wstring> env;
    wchar_t* inherited=GetEnvironmentStringsW();
    if(!inherited) throw std::runtime_error("Cannot read process environment");
    for(const wchar_t* p=inherited;*p;p+=wcslen(p)+1) {
        std::wstring entry=p; auto equals=entry.find(L'=',entry[0]==L'=' ? 1:0);
        if(equals==std::wstring::npos) continue;
        auto key=entry.substr(0,equals), upper=key;
        std::transform(upper.begin(),upper.end(),upper.begin(),::towupper);
        if(upper.rfind(L"S760_",0)!=0) env[key]=entry.substr(equals+1);
    }
    FreeEnvironmentStringsW(inherited);
    env[L"S760_RUNTIME_PORT"]=std::to_wstring(port);
    env[L"S760_RUNTIME_MIDI_PORT"]=std::to_wstring(midi_port);
    env[L"S760_RUNTIME_TOKEN"]=std::wstring(token.begin(),token.end());
    env[L"S760_ROM_BOOT"]=std::filesystem::absolute(cfg.boot_rom).wstring();
    env[L"S760_FLOPPY"]=std::filesystem::absolute(cfg.system_disk).wstring();
    env[L"S760_SAMPLE_FLOPPY"]=(cfg.state/"inserted-floppy.img").wstring();
    env[L"S760_MEDIA_EXPORT"]=(cfg.state/"media-export.img").wstring();
    env[L"S760_MEDIA_STATUS"]=(cfg.state/"media-status.json").wstring();
    env[L"S760_F00A"]=L"00"; env[L"S760_IC4_MIDI_EXPERIMENT"]=L"1"; env[L"S760_NATIVE_INTERPOLATION_MONITOR"]=L"1";
    std::vector<wchar_t> environment;
    for(const auto& item:env) { auto entry=item.first+L"="+item.second; environment.insert(environment.end(),entry.begin(),entry.end()); environment.push_back(0); }
    environment.push_back(0);
    std::wstring command=quote(exe.wstring())+L" s760 -video none -sound none -nothrottle -samplerate 44100 -skip_gameinfo -window -autoboot_delay 0";
    for(const auto& pair:std::vector<std::pair<std::wstring,std::filesystem::path>>{
        {L"-rompath",roms.parent_path()},{L"-pluginspath",cfg.root/"mame-source/plugins"},
        {L"-autoboot_script",cfg.root/"scripts/s760_runtime.lua"},{L"-cfg_directory",cfg.state/"cfg"},
        {L"-nvram_directory",cfg.state/"nvram"},{L"-snapshot_directory",cfg.state}})
        command+=L" "+pair.first+L" "+quote(pair.second.wstring());
    SECURITY_ATTRIBUTES attributes{sizeof(attributes),nullptr,TRUE};
    impl_->log.value=CreateFileW((cfg.state/"runtime.log").c_str(),GENERIC_WRITE,FILE_SHARE_READ,&attributes,CREATE_ALWAYS,0,nullptr);
    if(impl_->log.value==INVALID_HANDLE_VALUE) throw std::runtime_error("Cannot create native log");
    STARTUPINFOEXW startup{}; startup.StartupInfo.cb=sizeof(startup);
    startup.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
    startup.StartupInfo.hStdOutput=startup.StartupInfo.hStdError=impl_->log.value;
    startup.StartupInfo.hStdInput=impl_->log.value;
    SIZE_T attribute_size=0;
    InitializeProcThreadAttributeList(nullptr,1,0,&attribute_size);
    std::vector<unsigned char> attribute_storage(attribute_size);
    startup.lpAttributeList=reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(attribute_storage.data());
    if(!InitializeProcThreadAttributeList(startup.lpAttributeList,1,0,&attribute_size))
        throw std::runtime_error("Cannot initialize native process handle list");
    if(!UpdateProcThreadAttribute(startup.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,
        &impl_->log.value,sizeof(HANDLE),nullptr,nullptr)) {
        DeleteProcThreadAttributeList(startup.lpAttributeList);
        throw std::runtime_error("Cannot restrict native process inherited handles");
    }
    PROCESS_INFORMATION process{};
    const bool created=CreateProcessW(exe.c_str(),command.data(),nullptr,nullptr,TRUE,
        CREATE_NO_WINDOW|CREATE_UNICODE_ENVIRONMENT|EXTENDED_STARTUPINFO_PRESENT|CREATE_SUSPENDED,
        environment.data(),cfg.state.c_str(),&startup.StartupInfo,&process);
    DeleteProcThreadAttributeList(startup.lpAttributeList);
    if(!created)
        throw std::runtime_error("Cannot launch native machine");
    impl_->process.value=process.hProcess;
    if(!AssignProcessToJobObject(impl_->job.value,process.hProcess)) {
        CloseHandle(process.hThread);
        throw std::runtime_error("Cannot attach native process to lifetime job");
    }
    const auto resumed=ResumeThread(process.hThread); CloseHandle(process.hThread);
    if(resumed==DWORD(-1)) throw std::runtime_error("Cannot resume native process");
    accept_local(impl_->midi,midi_listener,process.hProcess);
    std::string actual(token.size(),'\0'); transfer(impl_->midi.value,actual.data(),actual.size(),false);
    if(actual!=token) throw std::runtime_error("Invalid native MIDI handshake");
    accept_local(impl_->control,control_listener,process.hProcess);
    auto hello=parse(impl_->receive_json());
    if(!hello.HasMember("protocol") || !hello["protocol"].IsInt() || hello["protocol"].GetInt()!=1
       || !hello.HasMember("token") || !hello["token"].IsString() || token!=hello["token"].GetString())
        throw std::runtime_error("Invalid native handshake");
#else
    throw std::runtime_error("Native process client currently requires Windows");
#endif
}
NativeRuntimeClient::~NativeRuntimeClient() {
#ifdef _WIN32
    if(impl_->control.value!=INVALID_SOCKET) {
        try { request("{\"op\":\"quit\"}"); WaitForSingleObject(impl_->process.value,5000); } catch(...) {}
    }
#endif
}
std::vector<std::uint8_t> NativeRuntimeClient::checkpoint_identity() const {
    auto scsi=scsi_identity(impl_->state);
    if(scsi!=impl_->scsi_hash) throw std::runtime_error("SCSI backing files changed since runtime startup");
    const auto& cfg=impl_->config;
    std::vector<std::filesystem::path> paths{cfg.root/"mame-source/mames760.exe",cfg.boot_rom,cfg.system_disk,cfg.root/"scripts/s760_runtime.lua"};
#ifdef _WIN32
    HMODULE module=nullptr;
    if(!GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCWSTR>(&native_digest),&module)) throw std::runtime_error("Cannot identify native host module");
    std::vector<wchar_t> filename(32768);
    auto length=GetModuleFileNameW(module,filename.data(),DWORD(filename.size()));
    if(!length || length>=filename.size()) throw std::runtime_error("Cannot identify native host filename");
    paths.emplace_back(std::wstring(filename.data(),length));
#endif
    std::vector<std::uint8_t> result;
    for(const auto& path:paths) {auto sum=native_digest(read_state_file(path,512u*1024*1024));result.insert(result.end(),sum.begin(),sum.end());}
    // Fold media identity into the host-module slot, retaining the 160-byte profile.
    std::vector<std::uint8_t> host_media(result.end()-32,result.end());
    host_media.insert(host_media.end(),scsi.begin(),scsi.end());auto combined=native_digest(host_media);
    std::copy(combined.begin(),combined.end(),result.end()-32);
    return result;
}
std::vector<std::uint8_t> NativeRuntimeClient::save_checkpoint() {
    std::lock_guard<std::mutex> lock(impl_->media_mutex);
    checkpoint_identity();
    request("{\"op\":\"checkpoint_save\"}");
    return read_state_file(impl_->state/"runtime-checkpoint.bin",257u*1024*1024);
}
void NativeRuntimeClient::load_checkpoint(const std::vector<std::uint8_t>& bytes) {
    std::lock_guard<std::mutex> lock(impl_->media_mutex);
    checkpoint_identity();
    if(bytes.empty() || bytes.size()>257u*1024*1024) throw std::runtime_error("Invalid native checkpoint size");
    { std::ofstream output(impl_->state/"runtime-checkpoint.bin",std::ios::binary|std::ios::trunc);
      output.write(reinterpret_cast<const char*>(bytes.data()),bytes.size()); output.close();
      if(!output) throw std::runtime_error("Native checkpoint write failed"); }
    request("{\"op\":\"checkpoint_load\"}");
}
NativeRuntimeReply NativeRuntimeClient::request(const std::string& command) {
    std::lock_guard<std::mutex> lock(impl_->mutex);
    NativeRuntimeReply result;
#ifdef _WIN32
    if(command.size()>65000 || command.find('\n')!=std::string::npos) throw std::runtime_error("Invalid native request size/framing");
    auto line=command+"\n"; transfer(impl_->control.value,line.data(),line.size(),true);
    result.json=impl_->receive_json(); auto d=parse(result.json);
    if(!d.HasMember("ok") || !d["ok"].IsBool() || !d["ok"].GetBool())
        throw std::runtime_error(d.HasMember("error") && d["error"].IsString() ? d["error"].GetString():"Native request failed");
    if(d.HasMember("seconds") && d["seconds"].IsNumber()) result.seconds=d["seconds"].GetDouble();
    if(d.HasMember("audio")) {
        const auto& a=d["audio"];
        if(!a.IsObject() || !a.HasMember("frames") || !a["frames"].IsUint() || a["frames"].GetUint()>44100
           || !a.HasMember("rate") || !a["rate"].IsUint() || a["rate"].GetUint()!=44100
           || !a.HasMember("channels") || !a["channels"].IsUint() || a["channels"].GetUint()!=2)
            throw std::runtime_error("Invalid native PCM descriptor");
        result.pcm.resize(a["frames"].GetUint()*8); transfer(impl_->control.value,result.pcm.data(),result.pcm.size(),false);
    }
    if(d.HasMember("surfaces")) {
        const auto& surfaces=d["surfaces"];
        if(!surfaces.IsArray() || surfaces.Size()!=2) throw std::runtime_error("Invalid native surfaces");
        for(unsigned i=0;i<2;++i) {
            const auto& s=surfaces[i]; const unsigned w=i?160:640,h=i?64:240;
            if(!s.IsArray() || s.Size()!=3 || !s[0].IsUint() || s[0].GetUint()!=i
               || !s[1].IsUint() || s[1].GetUint()!=w || !s[2].IsUint() || s[2].GetUint()!=h)
                throw std::runtime_error("Invalid native surface geometry");
            auto& bytes=i?result.lcd:result.crt; bytes.resize(w*h*4); transfer(impl_->control.value,bytes.data(),bytes.size(),false);
        }
    }
#else
    throw std::runtime_error("Native process client currently requires Windows");
#endif
    return result;
}
bool NativeRuntimeClient::render(float* output,std::size_t frames) {
    if(!frames || frames>8192) return false;
    auto response=request("{\"op\":\"render\",\"frames\":"+std::to_string(frames)+"}");
    if(response.pcm.size()!=frames*8) return false;
    std::memcpy(output,response.pcm.data(),response.pcm.size()); return true;
}
void NativeRuntimeClient::midi(const std::uint8_t* bytes,std::size_t count) {
    if(!bytes || !count || count>256) throw std::runtime_error("Invalid native MIDI packet");
    std::lock_guard<std::mutex> lock(impl_->mutex);
#ifdef _WIN32
    transfer(impl_->midi.value,const_cast<std::uint8_t*>(bytes),count,true);
#else
    throw std::runtime_error("Native process client currently requires Windows");
#endif
}
void NativeRuntimeClient::insert_media(const std::filesystem::path& source) {
    std::lock_guard<std::mutex> media_lock(impl_->media_mutex);
    const auto size=std::filesystem::file_size(source);
    if(size!=737280 && size!=1474560) throw std::runtime_error("Unsupported floppy size");
    const auto status=impl_->state/"media-status.json";
    auto control=[&](const std::string& name) {
        std::filesystem::remove(status);
        const auto base="{\"op\":\"button\",\"port\":\":NATIVE_MEDIA\",\"name\":\""+name+"\",\"down\":";
        try { request(base+"true}"); } catch(...) { try { request(base+"false}"); } catch(...) {} throw; }
        request(base+"false}");
        std::ifstream file(status); std::string text((std::istreambuf_iterator<char>(file)),{});
        auto result=parse(text);
        if(!result.HasMember("ok") || !result["ok"].IsBool() || !result["ok"].GetBool())
            throw std::runtime_error("Native media operation rejected");
        return result;
    };
    auto state=control("Floppy Media Status");
    if(!state.HasMember("dirty") || !state["dirty"].IsBool() || !state.HasMember("busy") || !state["busy"].IsBool()
       || state["dirty"].GetBool() || state["busy"].GetBool()) throw std::runtime_error("Media is busy or has unexported writes");
    const auto pending=impl_->state/"inserted-floppy.pending", slot=impl_->state/"inserted-floppy.img";
    std::filesystem::copy_file(source,pending,std::filesystem::copy_options::overwrite_existing);
#ifdef _WIN32
    if(!MoveFileExW(pending.c_str(),slot.c_str(),MOVEFILE_REPLACE_EXISTING|MOVEFILE_WRITE_THROUGH)) {
        std::filesystem::remove(pending); throw std::runtime_error("Cannot stage native floppy");
    }
#else
    std::filesystem::rename(pending,slot);
#endif
    control("Insert Sample Floppy");
}
std::uint32_t NativeRuntimeClient::process_id() const {
#ifdef _WIN32
    return GetProcessId(impl_->process.value);
#else
    return 0;
#endif
}
}
