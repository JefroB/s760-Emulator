#include "s760/s760_media_library.hpp"
#include "s760/s760_native_plugin_state.hpp"
#include <fstream>
#include <iostream>
static void check(bool ok,const char* message){if(!ok)throw std::runtime_error(message);}
int main(int argc,char** argv) {
 try {
  check(argc==2,"Supply private fixture directory");
  auto root=std::filesystem::absolute(argv[1]);std::filesystem::create_directories(root/"nested");
  std::ofstream(root/"first.IMG").put('a');std::ofstream(root/"nested"/"second.img").put('b');std::ofstream(root/"ignore.txt").put('c');
  s760::MediaLibrary library;check(library.configure(root.u8string()),"Configure failed");
  check(library.state().paths.size()==2,"Recursive discovery did not filter images");
  auto selected=library.state().paths.back();check(library.select(selected),"Selection failed");
  auto snapshot=library.state();check(!library.configure((root/"missing").u8string()),"Missing folder accepted");
  check(library.state().paths==snapshot.paths && library.state().selected==selected,"Failed scan destroyed library");
  check(!library.select((root/"ignore.txt").u8string()),"Unknown selection accepted");
  library.inserted(snapshot.paths.front());library.select(selected);snapshot=library.state();
  s760::NativePluginState state;state.identity.resize(160);state.machine={1};state.media=snapshot;
  auto decoded=s760::NativePluginState::decode(state.encode());
  check(decoded.media.selected==selected && decoded.media.inserted==snapshot.inserted,"State conflates selected and inserted media");
  s760::MediaLibrary restored;restored.restore(decoded.media);
  check(restored.state().folder==root.u8string() && restored.state().paths==snapshot.paths,"Library state lost");
  auto old=state;old.version=1;auto legacy=s760::NativePluginState::decode(old.encode());
  check(legacy.media.inserted.empty() && legacy.media.paths.empty(),"Legacy state invents media identity");
  auto input_state=state;input_state.has_stream=true;input_state.stream.clock=64;
  input_state.stream.pending.resize(1);auto& block=input_state.stream.pending[0];block.frames=64;
  for(unsigned i=0;i<128;++i)block.input[i]=float(int(i)-64)/128.f;
  auto input_recall=s760::NativePluginState::decode(input_state.encode());
  check(input_recall.version==3 && input_recall.stream.pending[0].input==block.input,"Pending stereo input lost in state");
  auto downgrade=input_state;downgrade.version=2;bool refused=false;
  try{downgrade.encode();}catch(const std::invalid_argument&){refused=true;}
  check(refused,"Legacy encoding silently discarded queued input");
  downgrade.stream.pending[0].input.fill(0.f);
  check(s760::NativePluginState::decode(downgrade.encode()).version==2,"Legacy v2 decode rejected");
  auto broken=snapshot;broken.selected="not-in-inventory";
  bool rejected=false;try{restored.restore(broken);}catch(...){rejected=true;}
  check(rejected && restored.state().selected==selected,"Malformed metadata was applied");
  std::cout<<"Recursive media, transactional errors, selection, v2 state and v1 compatibility passed\n";
 }catch(const std::exception& e){std::cerr<<e.what()<<'\n';return 1;}
}
