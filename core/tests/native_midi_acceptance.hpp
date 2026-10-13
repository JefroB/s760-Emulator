#pragma once
// Native reference bytes are explicit, independent of the processor's codec.
class ControllerTimeline : public Steinberg::IParameterChanges {
public:
 struct Item {unsigned time,channel,controller,value;};
 std::array<Item,10> items;
 class Queue : public Steinberg::IParamValueQueue {
 public:
  uint32_t id=0;int32_t offset=0;double value=0;
  tresult queryInterface(const TUID,void**) override{return kResultFalse;}
  uint32_t addRef() override{return 1;}uint32_t release() override{return 1;}
  uint32_t getParameterId() override{return id;}
  int32_t getPointCount() override{return 1;}
  tresult getPoint(int32_t i,int32_t& o,double& v) override{if(i)return kResultFalse;o=offset;v=value;return kResultOk;}
  tresult addPoint(int32_t,double,int32_t&) override{return kResultFalse;}
 };
 std::array<Queue,10> queues;int count=0;
 explicit ControllerTimeline(unsigned rate):items{{
  {2*rate+19,0,129,16383},{3*rate+19,0,129,8192},
  {4*rate+19,0,7,64},{5*rate+19,0,7,127},
  {6*rate+19,15,123,0},{7*rate+19,0,121,0},
  {8*rate+19,0,64,127},{10*rate+rate/4+19,0,64,0},
  {10*rate+rate/2+19,0,123,0},{11*rate+19,0,120,0}}} {}
 void bind(std::size_t first,unsigned frames) {
  count=0;
  for(const auto& item:items) if(item.time>=first && item.time<first+frames) {
   auto& q=queues[count++];q.id=s760::S760Vst3Plugin::midi_parameter_base+item.channel*129+(item.controller==129?128:item.controller);
   q.offset=int(item.time-first);q.value=double(item.value)/(item.controller==129?16383:127);
  }
 }
 tresult queryInterface(const TUID,void**) override{return kResultFalse;}
 uint32_t addRef() override{return 1;}uint32_t release() override{return 1;}
 int32_t getParameterCount() override{return count;}
 Steinberg::IParamValueQueue* getParameterData(int32_t i) override{return i>=0&&i<count?&queues[i]:nullptr;}
 Steinberg::IParamValueQueue* addParameterData(const uint32_t&,int32_t&) override{return nullptr;}
};
