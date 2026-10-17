// SPDX-License-Identifier: BSD-3-Clause
// QA observer of a selected Windows endpoint; never supplies sampler audio.
#define NOMINMAX
#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <wrl/client.h>
#include <fstream>
#include <iostream>
#include <string>
#include <chrono>
#include <stdexcept>
using Microsoft::WRL::ComPtr;
void check(HRESULT hr){if(FAILED(hr))throw std::runtime_error("HRESULT="+std::to_string((unsigned long)hr));}
int wmain(int argc,wchar_t** argv){
 if(argc!=4)return 2;
 try{
 check(CoInitializeEx(nullptr,COINIT_MULTITHREADED));
 struct Cleanup{~Cleanup(){CoUninitialize();}} cleanup;
 ComPtr<IMMDeviceEnumerator> enumerator;check(CoCreateInstance(__uuidof(MMDeviceEnumerator),nullptr,CLSCTX_ALL,IID_PPV_ARGS(&enumerator)));
 ComPtr<IMMDevice> device;check(enumerator->GetDevice(argv[1],&device));
 ComPtr<IAudioClient> audio;check(device->Activate(__uuidof(IAudioClient),CLSCTX_ALL,nullptr,reinterpret_cast<void**>(audio.GetAddressOf())));
 WAVEFORMATEX* raw=nullptr;check(audio->GetMixFormat(&raw));
 struct FreeFormat{WAVEFORMATEX* p;~FreeFormat(){CoTaskMemFree(p);}} free_format{raw};
 bool floating=raw->wFormatTag==WAVE_FORMAT_IEEE_FLOAT;
 if(raw->wFormatTag==WAVE_FORMAT_EXTENSIBLE)floating=reinterpret_cast<WAVEFORMATEXTENSIBLE*>(raw)->SubFormat.Data1==WAVE_FORMAT_IEEE_FLOAT;
 if(!floating || raw->wBitsPerSample!=32 || raw->nChannels!=2)throw std::runtime_error("Fixture requires stereo float32 endpoint mix");
 check(audio->Initialize(AUDCLNT_SHAREMODE_SHARED,AUDCLNT_STREAMFLAGS_LOOPBACK,10000000,0,raw,nullptr));
 ComPtr<IAudioCaptureClient> capture;check(audio->GetService(IID_PPV_ARGS(&capture)));
 std::ofstream pcm(argv[2],std::ios::binary);
 check(audio->Start());
 std::wstring marker=std::wstring(argv[2])+L".ready";std::ofstream ready(marker);ready<<raw->nSamplesPerSec;ready.close();
 const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(_wtoi(argv[3]));
 unsigned long long frames=0,discontinuities=0,silent=0,packets=0;UINT64 first_qpc=0,last_qpc=0;
 while(std::chrono::steady_clock::now()<end){
  UINT32 available=0;check(capture->GetNextPacketSize(&available));
  while(available){BYTE* data=nullptr;UINT32 count=0;DWORD flags=0;UINT64 position=0,qpc=0;
   check(capture->GetBuffer(&data,&count,&flags,&position,&qpc));
   if(!packets)first_qpc=qpc;
   last_qpc=qpc;if(flags&AUDCLNT_BUFFERFLAGS_DATA_DISCONTINUITY)++discontinuities;
   if(flags&AUDCLNT_BUFFERFLAGS_SILENT){std::string zeros(count*raw->nBlockAlign,0);pcm.write(zeros.data(),zeros.size());silent+=count;}
   else pcm.write(reinterpret_cast<char*>(data),count*raw->nBlockAlign);
   frames+=count;++packets;check(capture->ReleaseBuffer(count));check(capture->GetNextPacketSize(&available));
  }
  Sleep(2);
 }
 check(audio->Stop());
 std::cout<<"{\"rate\":"<<raw->nSamplesPerSec<<",\"channels\":2,\"format\":\"float32\",\"frames\":"<<frames<<",\"packets\":"<<packets<<",\"discontinuity_flags\":"<<discontinuities<<",\"silent_frames\":"<<silent<<",\"first_qpc_100ns\":"<<first_qpc<<",\"last_qpc_100ns\":"<<last_qpc<<"}";
 return 0;
 }catch(const std::exception& e){std::cerr<<e.what();return 1;}
}
