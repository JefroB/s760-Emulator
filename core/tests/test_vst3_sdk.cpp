// Deliberately includes ONLY Steinberg SDK interfaces, never project VST types.
#include "pluginterfaces/base/ipluginbase.h"
#include "pluginterfaces/vst/ivstcomponent.h"
#include "pluginterfaces/vst/ivstaudioprocessor.h"
#include "pluginterfaces/vst/ivsteditcontroller.h"
#include "pluginterfaces/gui/iplugview.h"
#include "pluginterfaces/vst/ivstparameterchanges.h"
#include <windows.h>
#include <iostream>
#include <stdexcept>
#include <cstring>
static void require(bool ok,const char* message) { if(!ok) throw std::runtime_error(message); }
class ControllerQueue : public Steinberg::Vst::IParamValueQueue {
public:
 Steinberg::Vst::ParamID id=0; int count=2;double value=.5;
 Steinberg::tresult PLUGIN_API queryInterface(const Steinberg::TUID,void** out) override{*out=nullptr;return Steinberg::kNoInterface;}
 Steinberg::uint32 PLUGIN_API addRef() override{return 1;}
 Steinberg::uint32 PLUGIN_API release() override{return 1;}
 Steinberg::Vst::ParamID PLUGIN_API getParameterId() override{return id;}
 Steinberg::int32 PLUGIN_API getPointCount() override{return count;}
 Steinberg::tresult PLUGIN_API getPoint(Steinberg::int32 i,Steinberg::int32& offset,Steinberg::Vst::ParamValue& v) override{offset=17+i*31;v=value;return Steinberg::kResultOk;}
 Steinberg::tresult PLUGIN_API addPoint(Steinberg::int32,Steinberg::Vst::ParamValue,Steinberg::int32&) override{return Steinberg::kNotImplemented;}
};
class ControllerChanges : public Steinberg::Vst::IParameterChanges {
public:
 ControllerQueue queue;
 Steinberg::tresult PLUGIN_API queryInterface(const Steinberg::TUID,void** out) override{*out=nullptr;return Steinberg::kNoInterface;}
 Steinberg::uint32 PLUGIN_API addRef() override{return 1;}
 Steinberg::uint32 PLUGIN_API release() override{return 1;}
 Steinberg::int32 PLUGIN_API getParameterCount() override{return 1;}
 Steinberg::Vst::IParamValueQueue* PLUGIN_API getParameterData(Steinberg::int32 i) override{return i==0 ? &queue : nullptr;}
 Steinberg::Vst::IParamValueQueue* PLUGIN_API addParameterData(const Steinberg::Vst::ParamID&,Steinberg::int32&) override{return nullptr;}
};
int main(int argc,char** argv) {
 try {
  require(argc==2 || (argc==3 && std::strcmp(argv[2],"--editor")==0),"supply plugin DLL path [--editor]");
  auto dll=LoadLibraryA(argv[1]); require(dll,"load module");
  auto entry=reinterpret_cast<Steinberg::IPluginFactory*(*)()>(GetProcAddress(dll,"GetPluginFactory"));
  require(entry,"factory export"); auto* factory=entry();
  Steinberg::PFactoryInfo info{};
  require(factory->getFactoryInfo(&info)==Steinberg::kResultOk && info.vendor[0],"factory metadata");
  void* unsupported=reinterpret_cast<void*>(1);
  Steinberg::TUID invalid{};
  require(factory->queryInterface(invalid,&unsupported)!=Steinberg::kResultOk && !unsupported,"unsupported factory interface");
  require(factory->countClasses()==1,"class count");
  Steinberg::IPluginFactory2* factory2=nullptr;
  require(factory->queryInterface(Steinberg::IPluginFactory2_iid,reinterpret_cast<void**>(&factory2))==Steinberg::kResultOk && factory2,"extended factory metadata interface");
  Steinberg::PClassInfo2 info2{};
  require(factory2->getClassInfo2(0,&info2)==Steinberg::kResultOk && std::strcmp(info2.subCategories,"Instrument|Sampler")==0 && info2.version[0],"instrument sampling subcategory");factory2->release();
  Steinberg::PClassInfo cls{};
  require(factory->getClassInfo(0,&cls)==Steinberg::kResultOk && std::strcmp(cls.category,kVstAudioEffectClass)==0,"audio effect category");
  Steinberg::Vst::IComponent* component=nullptr;
  require(factory->createInstance(cls.cid,Steinberg::Vst::IComponent_iid,reinterpret_cast<void**>(&component))==Steinberg::kResultOk && component,"SDK component creation");
  require(component->initialize(nullptr)==Steinberg::kResultOk,"initialize");
  Steinberg::Vst::BusInfo bus{};
  require(component->getBusCount(Steinberg::Vst::kAudio,Steinberg::Vst::kOutput)==1,"output bus count");
  require(component->getBusInfo(Steinberg::Vst::kAudio,Steinberg::Vst::kOutput,0,bus)==Steinberg::kResultOk && bus.channelCount==2 && bus.name[0],"stereo bus metadata");
  require(bus.mediaType==Steinberg::Vst::kAudio && bus.direction==Steinberg::Vst::kOutput && bus.busType==Steinberg::Vst::kMain,"output bus description");
  require(component->getBusCount(Steinberg::Vst::kAudio,Steinberg::Vst::kInput)==1,"optional native input bus");
  require(component->getBusInfo(Steinberg::Vst::kAudio,Steinberg::Vst::kInput,0,bus)==Steinberg::kResultOk && bus.channelCount==2 && !(bus.flags & Steinberg::Vst::BusInfo::kDefaultActive),"optional stereo input metadata");
  require(component->getBusCount(Steinberg::Vst::kEvent,Steinberg::Vst::kInput)==1 && component->getBusCount(Steinberg::Vst::kEvent,Steinberg::Vst::kOutput)==0,"MIDI bus counts");
  require(component->getBusInfo(Steinberg::Vst::kEvent,Steinberg::Vst::kInput,0,bus)==Steinberg::kResultOk && bus.mediaType==Steinberg::Vst::kEvent && bus.direction==Steinberg::Vst::kInput && bus.channelCount==16 && bus.name[0],"MIDI bus description");
  require(component->getBusInfo(Steinberg::Vst::kAudio,Steinberg::Vst::kOutput,1,bus)!=Steinberg::kResultOk,"nonexistent bus rejected");
  Steinberg::Vst::IAudioProcessor* audio=nullptr;
  require(component->queryInterface(Steinberg::Vst::IAudioProcessor_iid,reinterpret_cast<void**>(&audio))==Steinberg::kResultOk && audio,"audio interface");
  require(audio->getTailSamples()==Steinberg::Vst::kInfiniteTail,"sampler must report potentially infinite voice tail");
  Steinberg::Vst::SpeakerArrangement speakers=0;
  require(audio->getBusArrangement(Steinberg::Vst::kOutput,0,speakers)==Steinberg::kResultOk && speakers==3,"stereo arrangement");
  Steinberg::Vst::IEditController* controller=nullptr;
  require(component->queryInterface(Steinberg::Vst::IEditController_iid,reinterpret_cast<void**>(&controller))==Steinberg::kResultOk && controller,"controller interface");
  Steinberg::Vst::IMidiMapping* mapping=nullptr;
  require(controller->queryInterface(Steinberg::Vst::IMidiMapping_iid,reinterpret_cast<void**>(&mapping))==Steinberg::kResultOk && mapping,"native MIDI mapping interface");
  Steinberg::Vst::ParamID sustain=0,bend=0,other=0;
  require(mapping->getMidiControllerAssignment(0,0,64,sustain)==Steinberg::kResultOk && mapping->getMidiControllerAssignment(0,15,129,bend)==Steinberg::kResultOk && sustain!=bend,"MIDI sustain/bend assignments");
  require(mapping->getMidiControllerAssignment(0,16,64,other)!=Steinberg::kResultOk && mapping->getMidiControllerAssignment(1,0,64,other)!=Steinberg::kResultOk,"invalid MIDI mapping rejected");
  require(controller->getParameterCount()==16*129,"native MIDI parameter count");
  Steinberg::Vst::ParameterInfo parameter{};
  require(controller->getParameterInfo(64,parameter)==Steinberg::kResultOk && parameter.id==sustain && parameter.stepCount==127,"SDK MIDI parameter ABI");
  require(controller->normalizedParamToPlain(sustain,1)==127 && controller->plainParamToNormalized(bend,16383)==1,"MIDI parameter units");
  Steinberg::Vst::String128 text{};
  require(controller->getParamStringByValue(sustain,1,text)==Steinberg::kResultOk && text[0]==u'1' && text[1]==u'2' && text[2]==u'7',"MIDI parameter string");
  for(int channel=0;channel<16;++channel) {
   Steinberg::Vst::ParamID cc=0,pitch=0;
   require(mapping->getMidiControllerAssignment(0,channel,120,cc)==Steinberg::kResultOk && mapping->getMidiControllerAssignment(0,channel,129,pitch)==Steinberg::kResultOk && cc!=pitch,"channel panic/bend mapping");
  }
  mapping->release();
  if(argc==3) {
   auto* view=controller->createView("editor");require(view,"SDK editor creation");
   auto window=CreateWindowExW(0,L"STATIC",L"S-760 SDK editor qualification",WS_OVERLAPPEDWINDOW,
       0,0,1440,1100,nullptr,nullptr,GetModuleHandleW(nullptr),nullptr);
   require(window,"editor parent window");
   auto pump=[] {
    const auto until=GetTickCount64()+1500;
    do {MSG msg;while(PeekMessageW(&msg,nullptr,0,0,PM_REMOVE)){TranslateMessage(&msg);DispatchMessageW(&msg);}Sleep(5);}while(GetTickCount64()<until);
   };
   require(view->attached(window,Steinberg::kPlatformTypeHWND)==Steinberg::kResultOk,"SDK editor attach");pump();
   require(view->canResize()==Steinberg::kResultOk,"SDK editor resize support");
   for(auto dimensions : {std::pair<int,int>{1200,900},{1600,1200},{1440,1100}}) {
    Steinberg::ViewRect target(0,0,dimensions.first,dimensions.second),actual;
    require(view->checkSizeConstraint(&target)==Steinberg::kResultOk && view->onSize(&target)==Steinberg::kResultOk,"SDK editor resize");pump();
    require(view->getSize(&actual)==Steinberg::kResultOk && actual.getWidth()==dimensions.first && actual.getHeight()==dimensions.second,"SDK editor size readback");
   }
   require(view->removed()==Steinberg::kResultOk,"SDK editor detach");
   require(view->attached(window,Steinberg::kPlatformTypeHWND)==Steinberg::kResultOk,"SDK editor reattach");pump();
   require(view->removed()==Steinberg::kResultOk,"SDK reopened editor detach");
   view->release();DestroyWindow(window);
   std::cout<<"Independent SDK editor attach/resize/readback/reopen passed\n";
  }
  Steinberg::Vst::ProcessSetup setup{};setup.sampleRate=44100;setup.maxSamplesPerBlock=512;
  for(auto rate:{44100,48000,96000}) {
   setup.sampleRate=rate;
   require(audio->setupProcessing(setup)==Steinberg::kResultOk,"latency rate setup");
   const auto expected=rate==44100 ? 12288u : rate==48000 ? 13393u : 26785u;
   require(audio->getLatencySamples()==expected,"negotiated SDK latency report");
  }
  setup.sampleRate=44100;setup.processMode=3;
  require(audio->setupProcessing(setup)!=Steinberg::kResultOk,"unknown process mode rejected");
  setup.processMode=Steinberg::Vst::kRealtime;
  require(audio->setupProcessing(setup)==Steinberg::kResultOk && component->setActive(true)==Steinberg::kResultOk && audio->setProcessing(true)==Steinberg::kResultOk,"SDK controller test setup");
  float left[512]{},right[512]{};float* channels[]{left,right};
  Steinberg::Vst::AudioBusBuffers output{};output.numChannels=2;output.channelBuffers32=channels;
  ControllerChanges changes;changes.queue.id=sustain;
  Steinberg::Vst::ProcessData data{};data.numSamples=512;data.numOutputs=1;data.outputs=&output;data.inputParameterChanges=&changes;
  require(audio->process(data)==Steinberg::kResultOk,"SDK controller point queue ABI");
  changes.queue.id=bend;
  require(audio->process(data)==Steinberg::kResultOk,"SDK bend queue ABI");
  changes.queue.count=65;
  std::fill_n(left,512,1.f);std::fill_n(right,512,1.f);
  require(audio->process(data)!=Steinberg::kResultOk,"controller overflow rejected");
  require(left[0]==0 && right[511]==0,"rejected controller block cleared");
  require(audio->setProcessing(false)==Steinberg::kResultOk,"controller test suspend");
  controller->release(); audio->release(); component->terminate(); component->release();
  component=nullptr;audio=nullptr;
  require(factory->createInstance(cls.cid,Steinberg::Vst::IComponent_iid,reinterpret_cast<void**>(&component))==Steinberg::kResultOk && component,"fresh input component");
  require(component->initialize(nullptr)==Steinberg::kResultOk,"input initialize");
  require(component->queryInterface(Steinberg::Vst::IAudioProcessor_iid,reinterpret_cast<void**>(&audio))==Steinberg::kResultOk && audio,"input audio interface");
  setup.sampleRate=44100;
  require(audio->setupProcessing(setup)==Steinberg::kResultOk && component->activateBus(Steinberg::Vst::kAudio,Steinberg::Vst::kInput,0,true)==Steinberg::kResultOk,"activate optional input");
  auto invalid_input_setup=setup;invalid_input_setup.sampleRate=48000;
  require(audio->setupProcessing(invalid_input_setup)!=Steinberg::kResultOk,"active input rejects unsupported clock");
  require(component->setActive(true)==Steinberg::kResultOk && audio->setProcessing(true)==Steinberg::kResultOk,"start input");
  Steinberg::Vst::AudioBusBuffers input{};input.numChannels=2;input.silenceFlags=3;
  data.inputParameterChanges=nullptr;data.numInputs=1;data.inputs=&input;
  require(audio->process(data)==Steinberg::kResultOk,"silent input permits null buffers");
  data.numInputs=0;data.inputs=nullptr;
  std::fill_n(left,512,1.f);std::fill_n(right,512,1.f);
  require(audio->process(data)!=Steinberg::kResultOk && left[0]==0 && right[511]==0,"disconnected active input rejects silently");
  require(audio->setProcessing(false)==Steinberg::kResultOk && audio->setProcessing(true)!=Steinberg::kResultOk,"input disconnection latches visible processing failure");
  audio->release();component->terminate();component->release();
  FreeLibrary(dll); std::cout<<"Independent SDK factory/component/bus/controller/input ABI passed\n"; return 0;
 } catch(const std::exception& e) { std::cerr<<e.what()<<'\n'; return 1; }
}
