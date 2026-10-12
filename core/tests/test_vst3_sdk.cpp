// Deliberately includes ONLY Steinberg SDK interfaces, never project VST types.
#include "pluginterfaces/base/ipluginbase.h"
#include "pluginterfaces/vst/ivstcomponent.h"
#include "pluginterfaces/vst/ivstaudioprocessor.h"
#include "pluginterfaces/vst/ivsteditcontroller.h"
#include <windows.h>
#include <iostream>
#include <stdexcept>
#include <cstring>
static void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
int main(int argc,char** argv) {
 try {
  require(argc==2,"supply plugin DLL path");
  auto dll=LoadLibraryA(argv[1]); require(dll,"load module");
  auto entry=reinterpret_cast<Steinberg::IPluginFactory*(*)()>(GetProcAddress(dll,"GetPluginFactory"));
  require(entry,"factory export"); auto* factory=entry();
  Steinberg::PFactoryInfo info{};
  require(factory->getFactoryInfo(&info)==Steinberg::kResultOk && info.vendor[0],"factory metadata");
  void* unsupported=reinterpret_cast<void*>(1);
  Steinberg::TUID invalid{};
  require(factory->queryInterface(invalid,&unsupported)!=Steinberg::kResultOk && !unsupported,"unsupported factory interface");
  require(factory->countClasses()==1,"class count");
  Steinberg::PClassInfo cls{};
  require(factory->getClassInfo(0,&cls)==Steinberg::kResultOk && std::strcmp(cls.category,kVstAudioEffectClass)==0,"audio effect category");
  Steinberg::Vst::IComponent* component=nullptr;
  require(factory->createInstance(cls.cid,Steinberg::Vst::IComponent_iid,reinterpret_cast<void**>(&component))==Steinberg::kResultOk && component,"SDK component creation");
  require(component->initialize(nullptr)==Steinberg::kResultOk,"initialize");
  Steinberg::Vst::BusInfo bus{};
  require(component->getBusCount(Steinberg::Vst::kAudio,Steinberg::Vst::kOutput)==1,"output bus count");
  require(component->getBusInfo(Steinberg::Vst::kAudio,Steinberg::Vst::kOutput,0,bus)==Steinberg::kResultOk && bus.channelCount==2 && bus.name[0],"stereo bus metadata");
  Steinberg::Vst::IAudioProcessor* audio=nullptr;
  require(component->queryInterface(Steinberg::Vst::IAudioProcessor_iid,reinterpret_cast<void**>(&audio))==Steinberg::kResultOk && audio,"audio interface");
  Steinberg::Vst::SpeakerArrangement speakers=0;
  require(audio->getBusArrangement(Steinberg::Vst::kOutput,0,speakers)==Steinberg::kResultOk && speakers==3,"stereo arrangement");
  Steinberg::Vst::IEditController* controller=nullptr;
  require(component->queryInterface(Steinberg::Vst::IEditController_iid,reinterpret_cast<void**>(&controller))==Steinberg::kResultOk && controller,"controller interface");
  require(controller->getParameterCount()==0,"native parameters");
  controller->release(); audio->release(); component->terminate(); component->release();
  FreeLibrary(dll); std::cout<<"Independent SDK factory/component/bus/controller ABI passed\n"; return 0;
 } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
