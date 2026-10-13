#pragma once
#include <filesystem>
#include <memory>
#include <string>
#include <vector>
#include <cstdint>
#include <array>

namespace s760 {
std::array<std::uint8_t,32> native_digest(const std::vector<std::uint8_t>& data);
struct NativeRuntimeConfig {
    std::filesystem::path root, state, boot_rom, system_disk, sample_disk;
    std::filesystem::path media_directory;
};
struct NativeRuntimeReply {
    std::string json;
    double seconds=0;
    int output_level=100;
    std::vector<std::uint8_t> crt, lcd, pcm;
};
// Blocking worker-side client of the SAME Lua/MAME protocol as the standalone.
// Windows process isolation; never call from a DAW audio callback.
class NativeRuntimeClient {
public:
    explicit NativeRuntimeClient(const NativeRuntimeConfig&);
    ~NativeRuntimeClient();
    NativeRuntimeClient(const NativeRuntimeClient&)=delete;
    NativeRuntimeClient& operator=(const NativeRuntimeClient&)=delete;
    NativeRuntimeReply request(const std::string& json);
    bool render(float* interleaved,std::size_t frames);
    void set_audio_streaming(bool enabled);
    NativeRuntimeReply display_frames();
    void midi(const std::uint8_t* bytes,std::size_t size);
    void insert_media(const std::filesystem::path& source);
    std::uint32_t process_id() const;
    // Worker/lifecycle thread only. Includes floppy and SCSI state; external
    // SCSI images must match the startup identity and supported size profile.
    std::vector<std::uint8_t> checkpoint_identity() const;
    std::vector<std::uint8_t> save_checkpoint();
    void load_checkpoint(const std::vector<std::uint8_t>&);
private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};
}
