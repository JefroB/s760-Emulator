#ifndef VST3_DEFS_H__
#define VST3_DEFS_H__

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef int32_t tresult;
#define kResultOk 0
#define kResultFalse 1
#if defined(_WIN32)
#define kNoInterface ((tresult)0x80004002L)
#define kInvalidArgument ((tresult)0x80070057L)
#define kNotImplemented ((tresult)0x80004001L)
#define kInternalError ((tresult)0x80004005L)
#define kNotInitialized ((tresult)0x8000FFFFL)
#else
#define kNoInterface -1
#define kInvalidArgument 2
#define kNotImplemented 3
#define kInternalError 4
#define kNotInitialized 5
#endif

typedef char FIDString[128];
typedef uint8_t TUID[16];

// SDK GUID byte layout: COM ordering on Windows, network order elsewhere.
#define S760_UID_BE(v) (uint8_t)((v)>>24), (uint8_t)((v)>>16), (uint8_t)((v)>>8), (uint8_t)(v)
#if defined(_WIN32)
#define INLINE_UID(a,b,c,d) { (uint8_t)(a), (uint8_t)((a)>>8), (uint8_t)((a)>>16), (uint8_t)((a)>>24), (uint8_t)((b)>>16), (uint8_t)((b)>>24), (uint8_t)(b), (uint8_t)((b)>>8), S760_UID_BE(c), S760_UID_BE(d) }
#else
#define INLINE_UID(a,b,c,d) { S760_UID_BE(a), S760_UID_BE(b), S760_UID_BE(c), S760_UID_BE(d) }
#endif

// Media types
enum MediaTypes {
    kAudio = 0,
    kEvent = 1
};

// Bus directions
enum BusDirections {
    kInput = 0,
    kOutput = 1
};

// Bus types
enum BusTypes {
    kMain = 0,
    kAux = 1
};

enum EventTypes {
    kNoteOnEvent = 0,
    kNoteOffEvent = 1,
    kDataEvent = 2,
    kPolyPressureEvent = 3,
    kNoteExpressionValueEvent = 4,
    kNoteExpressionTextEvent = 5,
    kChordEvent = 6,
    kScaleEvent = 7,
    kLegacyMIDICCOutEvent = 65535
};

struct NoteOnEvent {
    int16_t channel;
    int16_t pitch;
    float tuning;
    float velocity;
    int32_t length;
    int32_t noteId;
};

struct NoteOffEvent {
    int16_t channel;
    int16_t pitch;
    float velocity;
    int32_t noteId;
    float tuning;
};

struct DataEvent {
    uint32_t size;
    uint32_t type;
    const uint8_t* bytes;
};

struct Event {
    int32_t busIndex;
    int32_t sampleOffset;
    double ppqPosition;
    uint16_t flags;
    uint16_t type;
    union {
        NoteOnEvent noteOn;
        NoteOffEvent noteOff;
        DataEvent data;
    };
};

struct AudioBusBuffers {
    int32_t numChannels;
    uint64_t silenceFlags;
    union {
        float** channelBuffers32;
        double** channelBuffers64;
    };
};

struct ProcessSetup {
    int32_t processMode;
    int32_t symbolicSampleSize;
    int32_t maxSamplesPerBlock;
    double sampleRate;
};

#ifdef __cplusplus
}
#endif

#ifdef __cplusplus

namespace Steinberg {

using ProcessSetup = ::ProcessSetup;
using Event = ::Event;
using AudioBusBuffers = ::AudioBusBuffers;

class FUnknown {
public:
    virtual tresult queryInterface(const TUID _iid, void** obj) = 0;
    virtual uint32_t addRef() = 0;
    virtual uint32_t release() = 0;
};

class IBStream : public FUnknown {
public:
    virtual tresult read(void* buffer, int32_t numBytes, int32_t* numBytesRead) = 0;
    virtual tresult write(void* buffer, int32_t numBytes, int32_t* numBytesWritten) = 0;
    virtual tresult seek(int64_t mode, int32_t mode_from, int64_t* result) = 0;
    virtual tresult tell(int64_t* result) = 0;
};

class IEventList : public FUnknown {
public:
    virtual int32_t getEventCount() = 0;
    virtual tresult getEvent(int32_t index, Event& e) = 0;
    virtual tresult addEvent(Event& e) = 0;
};

struct ProcessData {
    int32_t processMode;
    int32_t symbolicSampleSize;
    int32_t numSamples;
    int32_t numInputs;
    int32_t numOutputs;
    AudioBusBuffers* inputs;
    AudioBusBuffers* outputs;
    void* inputParameterChanges;
    void* outputParameterChanges;
    IEventList* inputEvents;
    IEventList* outputEvents;
    void* processContext;
};

class IPluginBase : public FUnknown {
public:
    virtual tresult initialize(FUnknown* context) = 0;
    virtual tresult terminate() = 0;
};

class IComponent : public IPluginBase {
public:
    virtual tresult getControllerClassId(TUID classId) = 0;
    virtual tresult setIoMode(int32_t mode) = 0;
    virtual tresult getBusCount(int32_t type, int32_t dir) = 0;
    virtual tresult getBusInfo(int32_t type, int32_t dir, int32_t index, void* bus) = 0;
    virtual tresult getRoutingInfo(void* inInfo, void* outInfo) = 0;
    virtual tresult activateBus(int32_t type, int32_t dir, int32_t index, bool state) = 0;
    virtual tresult setActive(bool state) = 0;
    virtual tresult setState(IBStream* state) = 0;
    virtual tresult getState(IBStream* state) = 0;
};

class IAudioProcessor : public FUnknown {
public:
    virtual tresult setBusArrangements(void* inputs, int32_t numIns, void* outputs, int32_t numOuts) = 0;
    virtual tresult getBusArrangement(int32_t dir, int32_t index, void* arr) = 0;
    virtual tresult canProcessSampleSize(int32_t symbolicSampleSize) = 0;
    virtual uint32_t getLatencySamples() = 0;
    virtual tresult setupProcessing(ProcessSetup& setup) = 0;
    virtual tresult setProcessing(bool state) = 0;
    virtual tresult process(ProcessData& data) = 0;
    virtual uint32_t getTailSamples() = 0;
};

// -----------------------------------------------------------------------------
//  Editor view interfaces (IPlugView / IPlugFrame / IEditController).
//  Minimal subset sufficient to host the WebView-backed React editor (task 3.6).
//  The platform window-type tokens match the VST3 SDK string constants.
// -----------------------------------------------------------------------------

// Platform UI type strings (VST3 SDK kPlatformType*).
#define kPlatformTypeHWND       "HWND"       // Windows
#define kPlatformTypeNSView     "NSView"     // macOS Cocoa
#define kPlatformTypeX11EmbedWindowID "X11EmbedWindowID" // Linux X11

struct ViewRect {
    int32_t left   = 0;
    int32_t top    = 0;
    int32_t right  = 0;
    int32_t bottom = 0;
    int32_t getWidth()  const { return right - left; }
    int32_t getHeight() const { return bottom - top; }
};

class IPlugFrame; // fwd

// IPlugView — the editor view the host attaches to its window (VST3 SDK).
class IPlugView : public FUnknown {
public:
    // Return kResultTrue (==kResultOk here) if the given platform type is
    // supported (e.g. "HWND" on Windows).
    virtual tresult isPlatformTypeSupported(FIDString type) = 0;
    // Attach the view to a parent platform window (HWND/NSView/X11 id).
    virtual tresult attached(void* parent, FIDString type) = 0;
    // Detach from the parent window.
    virtual tresult removed() = 0;
    virtual tresult onWheel(float distance) = 0;
    virtual tresult onKeyDown(char16_t key, int16_t keyCode, int16_t modifiers) = 0;
    virtual tresult onKeyUp(char16_t key, int16_t keyCode, int16_t modifiers) = 0;
    // Report the view's current size to the host.
    virtual tresult getSize(ViewRect* size) = 0;
    // Host asks the view to resize to the given rect.
    virtual tresult onSize(ViewRect* newSize) = 0;
    virtual tresult onFocus(bool state) = 0;
    // Host supplies a frame callback object (used for resize requests).
    virtual tresult setFrame(IPlugFrame* frame) = 0;
    virtual tresult canResize() = 0;
    // Constrain a proposed size (default: accept as-is).
    virtual tresult checkSizeConstraint(ViewRect* rect) = 0;
};

// IPlugFrame — host-provided callback for view-initiated resize.
class IPlugFrame : public FUnknown {
public:
    virtual tresult resizeView(IPlugView* view, ViewRect* newSize) = 0;
};

// IEditController — the controller half of a VST3 plugin. We implement just
// enough to vend the editor view via createView(ViewType::kEditor).
#define ViewType_kEditor "editor"

class IEditController : public IPluginBase {
public:
    virtual tresult setComponentState(IBStream* state) = 0;
    virtual tresult setState(IBStream* state) = 0;
    virtual tresult getState(IBStream* state) = 0;
    virtual int32_t getParameterCount() = 0;
    virtual tresult getParameterInfo(int32_t paramIndex, void* info) = 0;
    virtual tresult getParamStringByValue(uint32_t id, double valueNormalized, void* string) = 0;
    virtual tresult getParamValueByString(uint32_t id, char16_t* string, double* valueNormalized) = 0;
    virtual double normalizedParamToPlain(uint32_t id, double valueNormalized) = 0;
    virtual double plainParamToNormalized(uint32_t id, double plainValue) = 0;
    virtual double getParamNormalized(uint32_t id) = 0;
    virtual tresult setParamNormalized(uint32_t id, double value) = 0;
    virtual tresult setComponentHandler(void* handler) = 0;
    // Create a named view; for "editor" this returns our WebView-backed IPlugView.
    virtual IPlugView* createView(FIDString name) = 0;
};

struct PFactoryInfo { char vendor[64]; char url[256]; char email[128]; int32_t flags; };
struct BusInfo { int32_t mediaType, direction, channelCount; char16_t name[128]; int32_t busType; uint32_t flags; };

struct PClassInfo {
    TUID cid;
    int32_t cardinality;
    char category[32];
    char name[64];
};

class IPluginFactory : public FUnknown {
public:
    virtual tresult getFactoryInfo(void* info) = 0;
    virtual int32_t countClasses() = 0;
    virtual tresult getClassInfo(int32_t index, PClassInfo* info) = 0;
    virtual tresult createInstance(FIDString cid, FIDString _iid, void** obj) = 0;
};

} // namespace Steinberg

#endif

#endif
