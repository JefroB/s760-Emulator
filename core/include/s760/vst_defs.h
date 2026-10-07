#ifndef VST_DEFS_H__
#define VST_DEFS_H__

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

#define VST_MAGIC 0x56737450 // 'VstP'

// Opcode constants
enum {
    effOpen = 0,
    effClose = 1,
    effSetProgram = 2,
    effGetProgram = 3,
    effSetProgramName = 4,
    effGetProgramName = 5,
    effGetParamLabel = 6,
    effGetParamDisplay = 7,
    effGetParamName = 8,
    effSetSampleRate = 10,
    effSetBlockSize = 11,
    effMainsChanged = 12,
    effEditGetRect = 13,
    effEditOpen = 14,
    effEditClose = 15,
    effGetChunk = 23,
    effSetChunk = 24,
    effProcessEvents = 25,
    effCanBeAutomated = 26,
    effGetPlugCategory = 35,
    effGetEffectName = 45,
    effGetVendorString = 47,
    effGetProductString = 48,
    effGetVendorVersion = 49,
    effVendorSpecific = 50,
    effCanDo = 51,
    effGetVstVersion = 58,
};

enum VstPlugCategory {
    kPlugCategUnknown = 0,
    kPlugCategEffect = 1,
    kPlugCategSynth = 2,
    kPlugCategAnalysis = 3,
    kPlugCategMastering = 4,
    kPlugCategSpacializer = 5,
    kPlugCategRoomFx = 6,
    kPlugSurroundFx = 7,
    kPlugCategRestoration = 8,
    kPlugCategOfflineProcess = 9,
    kPlugCategShell = 10,
    kPlugCategGenerator = 11,
    kPlugCategMaxCount
};

// Effect Flags
enum {
    effFlagsHasEditor = 1 << 0,
    effFlagsCanReplacing = 1 << 4,
    effFlagsProgramChunks = 1 << 5,
    effFlagsIsSynth = 1 << 8,
};

// Events
enum {
    kVstMidiType = 1,
    kVstSysExType = 6,
};

struct VstEvent {
    int32_t type;
    int32_t byteSize;
    int32_t deltaFrames;
    int32_t flags;
    char data[16];
};

struct VstMidiEvent {
    int32_t type;
    int32_t byteSize;
    int32_t deltaFrames;
    int32_t flags;
    int32_t noteLength;
    int32_t noteOffset;
    char midiData[4];
    char detune;
    char noteOffVelocity;
    char reserved1;
    char reserved2;
};

struct VstEvents {
    int32_t numEvents;
    intptr_t reserved;
    VstEvent* events[2];
};

struct AEffect;

typedef intptr_t (*audioMasterCallback)(struct AEffect* effect, int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt);
typedef intptr_t (*AEffectDispatcherProc)(struct AEffect* effect, int32_t opcode, int32_t index, intptr_t value, void* ptr, float opt);
typedef void (*AEffectProcessProc)(struct AEffect* effect, float** inputs, float** outputs, int32_t sampleFrames);
typedef void (*AEffectSetParameterProc)(struct AEffect* effect, int32_t index, float parameter);
typedef float (*AEffectGetParameterProc)(struct AEffect* effect, int32_t index);

struct AEffect {
    int32_t magic;
    AEffectDispatcherProc dispatcher;
    AEffectProcessProc process;
    AEffectSetParameterProc setParameter;
    AEffectGetParameterProc getParameter;

    int32_t numPrograms;
    int32_t numParams;
    int32_t numInputs;
    int32_t numOutputs;

    int32_t flags;

    intptr_t resvd1;
    intptr_t resvd2;

    int32_t initialDelay;
    int32_t realQualities;
    int32_t offQualities;
    float ioRatio;

    void* object;
    void* user;

    int32_t uniqueID;
    int32_t version;

    AEffectProcessProc processReplacing;
    AEffectProcessProc processDoubleReplacing;

    char future[56];
};

#ifdef __cplusplus
}
#endif

#endif
