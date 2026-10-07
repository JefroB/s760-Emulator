#ifndef CLAP_DEFS_H__
#define CLAP_DEFS_H__

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

#define CLAP_VERSION_MAJOR 1
#define CLAP_VERSION_MINOR 2
#define CLAP_VERSION_REVISION 0

typedef struct clap_version {
    uint32_t major;
    uint32_t minor;
    uint32_t revision;
} clap_version_t;

static const clap_version_t CLAP_VERSION = {CLAP_VERSION_MAJOR, CLAP_VERSION_MINOR, CLAP_VERSION_REVISION};

typedef uint32_t clap_id;
#define CLAP_INVALID_ID UINT32_MAX

typedef struct clap_host {
    clap_version_t clap_version;
    void *host_data;
    const char *name;
    const char *vendor;
    const char *url;
    const char *version;

    const void *(*get_extension)(const struct clap_host *host, const char *extension_id);
    void (*request_restart)(const struct clap_host *host);
    void (*request_process)(const struct clap_host *host);
    void (*request_callback)(const struct clap_host *host);
} clap_host_t;

typedef struct clap_plugin_descriptor {
    clap_version_t clap_version;
    const char *id;
    const char *name;
    const char *vendor;
    const char *url;
    const char *manual_url;
    const char *support_url;
    const char *version;
    const char *description;
    const char *const *features;
} clap_plugin_descriptor_t;

struct clap_plugin;

typedef struct clap_audio_buffer {
    float **data32;
    double **data64;
    uint32_t channel_count;
    uint32_t latency;
    uint64_t constant_mask;
} clap_audio_buffer_t;

typedef struct clap_event_header {
    size_t size;
    uint32_t time;
    uint16_t space_id;
    uint16_t type;
    uint32_t flags;
} clap_event_header_t;

#define CLAP_CORE_EVENT_SPACE_ID 0

enum {
    CLAP_EVENT_NOTE_ON = 0,
    CLAP_EVENT_NOTE_OFF = 1,
    CLAP_EVENT_NOTE_CHOKE = 2,
    CLAP_EVENT_NOTE_END = 3,
    CLAP_EVENT_NOTE_EXPRESSION = 4,
    CLAP_EVENT_PARAM_VALUE = 5,
    CLAP_EVENT_PARAM_MOD = 6,
    CLAP_EVENT_PARAM_GESTURE_BEGIN = 7,
    CLAP_EVENT_PARAM_GESTURE_END = 8,
    CLAP_EVENT_TRANSPORT = 9,
    CLAP_EVENT_MIDI = 10,
    CLAP_EVENT_MIDI_SYSEX = 11,
    CLAP_EVENT_MIDI2 = 12,
};

typedef struct clap_event_note {
    clap_event_header_t header;
    int16_t note_id;
    int16_t port_index;
    int16_t channel;
    int16_t key;
    double velocity;
} clap_event_note_t;

typedef struct clap_event_midi {
    clap_event_header_t header;
    uint16_t port_index;
    uint8_t data[3];
} clap_event_midi_t;

typedef struct clap_input_events {
    void *ctx;
    uint32_t (*size)(const struct clap_input_events *list);
    const clap_event_header_t *(*get)(const struct clap_input_events *list, uint32_t index);
} clap_input_events_t;

typedef struct clap_output_events {
    void *ctx;
    bool (*try_push)(const struct clap_output_events *list, const clap_event_header_t *event);
} clap_output_events_t;

typedef struct clap_process {
    int64_t steady_time;
    uint32_t frames_count;
    const void *transport;
    const clap_audio_buffer_t *audio_inputs;
    clap_audio_buffer_t *audio_outputs;
    uint32_t audio_inputs_count;
    uint32_t audio_outputs_count;
    const clap_input_events_t *in_events;
    const clap_output_events_t *out_events;
} clap_process_t;

enum {
    CLAP_PROCESS_ERROR = 0,
    CLAP_PROCESS_CONTINUE = 1,
    CLAP_PROCESS_CONTINUE_IF_NOT_QUIET = 2,
    CLAP_PROCESS_TAIL = 3,
    CLAP_PROCESS_SLEEP = 4,
};
typedef int32_t clap_process_status;

typedef struct clap_plugin {
    const clap_plugin_descriptor_t *desc;
    void *plugin_data;

    bool (*init)(const struct clap_plugin *plugin);
    void (*destroy)(const struct clap_plugin *plugin);
    bool (*activate)(const struct clap_plugin *plugin,
                     double sample_rate,
                     uint32_t min_frames_count,
                     uint32_t max_frames_count);
    void (*deactivate)(const struct clap_plugin *plugin);
    bool (*start_processing)(const struct clap_plugin *plugin);
    void (*stop_processing)(const struct clap_plugin *plugin);
    void (*reset)(const struct clap_plugin *plugin);
    clap_process_status (*process)(const struct clap_plugin *plugin, const clap_process_t *process);
    const void *(*get_extension)(const struct clap_plugin *plugin, const char *id);
    void (*on_main_thread)(const struct clap_plugin *plugin);
} clap_plugin_t;

// State Extension
#define CLAP_EXT_STATE "clap.state"

typedef struct clap_istream {
    void *ctx;
    int64_t (*read)(const struct clap_istream *stream, void *buffer, uint64_t size);
} clap_istream_t;

typedef struct clap_ostream {
    void *ctx;
    int64_t (*write)(const struct clap_ostream *stream, const void *buffer, uint64_t size);
} clap_ostream_t;

typedef struct clap_plugin_state {
    bool (*save)(const clap_plugin_t *plugin, const clap_ostream_t *stream);
    bool (*load)(const clap_plugin_t *plugin, const clap_istream_t *stream);
} clap_plugin_state_t;

// Audio Ports Extension
#define CLAP_EXT_AUDIO_PORTS "clap.audio-ports"

typedef struct clap_audio_port_info {
    clap_id id;
    char name[256];
    uint32_t flags;
    uint32_t channel_count;
    const char *port_type;
    clap_id in_place_pair;
} clap_audio_port_info_t;

#define CLAP_AUDIO_PORT_IS_MAIN (1 << 0)
#define CLAP_PORT_STEREO "stereo"

typedef struct clap_plugin_audio_ports {
    uint32_t (*count)(const clap_plugin_t *plugin, bool is_input);
    bool (*get)(const clap_plugin_t *plugin, uint32_t index, bool is_input, clap_audio_port_info_t *info);
} clap_plugin_audio_ports_t;

// Factory
typedef struct clap_plugin_factory {
    uint32_t (*get_plugin_count)(const struct clap_plugin_factory *factory);
    const clap_plugin_descriptor_t *(*get_plugin_descriptor)(const struct clap_plugin_factory *factory, uint32_t index);
    const clap_plugin_t *(*create_plugin)(const struct clap_plugin_factory *factory,
                                          const clap_host_t *host,
                                          const char *plugin_id);
} clap_plugin_factory_t;

#define CLAP_PLUGIN_FACTORY_ID "clap.plugin-factory"

typedef struct clap_plugin_entry {
    clap_version_t clap_version;
    bool (*init)(const char *plugin_path);
    void (*deinit)(void);
    const void *(*get_factory)(const char *factory_id);
} clap_plugin_entry_t;

#ifdef __cplusplus
}
#endif

#endif
