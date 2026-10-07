#include "s760/s760_vst_plugin.hpp"

#if defined(_WIN32)
#define VST_EXPORT __declspec(dllexport)
#else
#define VST_EXPORT __attribute__((visibility("default")))
#endif

extern "C" {

VST_EXPORT AEffect* VSTPluginMain(audioMasterCallback audioMaster) {
    auto* plugin = new s760::S760VstPlugin(audioMaster, false); // Instrument mode
    return plugin->get_aeffect();
}

} // extern "C"
