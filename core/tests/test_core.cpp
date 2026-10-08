#include "s760/s760_disk.hpp"
#include "s760/s760_dsp.hpp"
#include "s760/akai_disk.hpp"
#include "s760/s760_drive_manager.hpp"
#include "s760/s760_libretro_host.hpp"

#include <iostream>
#include <cassert>
#include <cmath>
#include <filesystem>

namespace fs = std::filesystem;

void test_roland_disk() {
    std::cout << "[TEST] Roland S-760 Disk Builder & Parser..." << std::endl;

    s760::RolandS760Disk disk("S760 ACOUSTIC");
    disk.add_patch(1, "Ac. Bass", {1}, 127, 0);
    disk.add_patch(2, "Grand Piano", {2}, 120, -10);

    std::vector<uint8_t> dummy_pcm(4000, 0x12);
    disk.add_sample(1, "BassWave", 44100, dummy_pcm, 100, 1900, 28);
    disk.add_sample(2, "PianoWave", 44100, dummy_pcm, 200, 1800, 60);

    auto img = disk.build_image();
    assert(img.size() == s760::RolandS760Disk::FLOPPY_1440_SIZE);

    // Verify Sector 0 Header
    assert(std::memcmp(&img[0], "S770 MR25A", 10) == 0);
    assert(std::memcmp(&img[0x40], "S760 ACOUSTIC   ", 16) == 0);

    // Parse Back
    auto info = s760::RolandS760Disk::parse(img.data(), img.size());
    assert(info.is_roland == true);
    assert(info.volume_name == "S760 ACOUSTIC");
    assert(info.num_patches == 2);
    assert(info.num_samples == 2);
    assert(info.patches.size() == 2);
    assert(info.patches[0].id == 1);
    assert(info.patches[0].name == "Ac. Bass");
    assert(info.patches[1].id == 2);
    assert(info.patches[1].name == "Grand Piano");
    assert(info.samples.size() == 2);
    assert(info.samples[0].id == 1);
    assert(info.samples[0].name == "BassWave");
    assert(info.samples[0].loop_start == 100);
    assert(info.samples[0].loop_end == 1900);
    assert(info.samples[0].root_key == 28);
    assert(info.samples[0].pcm_data.size() == 4000);

    // SCSI Image
    auto scsi_img = disk.build_scsi_image_mb(10);
    assert(scsi_img.size() == 10 * 1024 * 1024);
    auto scsi_info = s760::RolandS760Disk::parse(scsi_img.data(), scsi_img.size());
    assert(scsi_info.is_roland == true);
    assert(scsi_info.num_patches == 2);

    std::cout << "  -> Roland S-760 Disk Tests PASSED!" << std::endl;
}

void test_akai_conversion() {
    std::cout << "[TEST] Akai S1000 ISO & Roland Conversion..." << std::endl;

    s760::AkaiS1000Disk akai("AKAI TEST");
    akai.add_program(1, "Prog Lead", 1, 1);
    akai.add_program(2, "Prog Pad", 2, 2);

    std::vector<uint8_t> pcm(2048, 0x33);
    akai.add_sample("SawWave", 44100, pcm, 50, 950, 60);

    auto iso = akai.build_iso(4);
    assert(iso.size() == 4 * 1024 * 1024);

    auto info = s760::AkaiS1000Disk::parse(iso.data(), iso.size());
    assert(info.is_akai == true);
    assert(info.volume_name == "AKAI TEST");
    assert(info.num_programs == 2);
    assert(info.num_samples == 1);
    assert(info.programs[0].name == "Prog Lead");
    assert(info.samples[0].name == "SawWave");

    // Convert Akai to Roland
    auto s760_disk = s760::S760AkaiConverter::convert(akai, "AKAI_CONV");
    assert(s760_disk.get_patches().size() == 2);
    assert(s760_disk.get_samples().size() == 1);
    assert(s760_disk.get_patches()[0].name.find("Prog Lead") != std::string::npos);
    assert(s760_disk.get_samples()[0].name.find("SawWave") != std::string::npos);

    std::cout << "  -> Akai S1000 & Converter Tests PASSED!" << std::endl;
}

void test_dsp_tools() {
    std::cout << "[TEST] Offline DSP Algorithms..." << std::endl;

    // Create 1 second 440Hz sine wave
    size_t num_s = 44100;
    std::vector<uint8_t> pcm(num_s * 2);
    for (size_t i = 0; i < num_s; ++i) {
        int16_t s = static_cast<int16_t>(std::sin(2.0 * 3.14159265 * 440.0 * i / 44100.0) * 20000.0);
        std::memcpy(&pcm[i * 2], &s, 2);
    }

    // Crossfade
    auto xf = s760::S760DSPTools::crossfade_loop(pcm, 1000, 20000, 200);
    assert(xf.size() == pcm.size());

    // Time Stretch
    auto stretched = s760::S760DSPTools::time_stretch(pcm, 1.25, 44100);
    assert(stretched.size() == static_cast<size_t>(num_s * 1.25) * 2);

    // Filter
    auto filtered = s760::S760DSPTools::digital_filter(pcm, 1000.0, 44100, "lpf");
    assert(filtered.size() == pcm.size());

    // Resample 44.1k -> 22.05k
    auto resampled = s760::S760DSPTools::sample_rate_convert(pcm, 44100, 22050);
    assert(resampled.size() == (num_s / 2) * 2);

    // Bit depth 16 -> 8
    auto bit8 = s760::S760DSPTools::bit_convert(pcm, 8);
    assert(bit8.size() == pcm.size());

    // Auto Truncate & Normalize
    auto [norm_pcm, s_idx, e_idx] = s760::S760DSPTools::auto_truncate_and_normalize(pcm, -48.0, 0.98);
    assert(!norm_pcm.empty());

    // Voice render
    auto voice = s760::S760DSPTools::render_voice(pcm, 44100, 60, 1000, 20000, 60, 44100, 44100);
    assert(voice.size() == 44100);

    // MS-DOS Floppy exchange
    auto dos_floppy = s760::S760DSPTools::build_msdos_sample_floppy("TEST.WAV", pcm, 44100);
    assert(dos_floppy.size() == 1474560);
    auto extracted = s760::S760DSPTools::extract_wav_from_msdos(dos_floppy);
    assert(extracted.is_dos == true);
    assert(extracted.is_wav == true);
    assert(extracted.sample_rate == 44100);
    assert(extracted.pcm_data.size() == pcm.size());

    // MIDI SDS
    auto sds = s760::S760DSPTools::build_sds_dump_header(1, 44100, 1000, 100, 900, 0);
    auto sds_info = s760::S760DSPTools::parse_sds_dump_header(sds);
    assert(sds_info.valid_sds == true);
    assert(sds_info.sample_num == 1);
    assert(sds_info.length == 1000);
    assert(sds_info.loop_start == 100);
    assert(sds_info.loop_end == 900);

    std::cout << "  -> DSP Tools Tests PASSED!" << std::endl;
}

void test_drive_manager() {
    std::cout << "[TEST] Folder-based Hardware-Accurate Drive Manager..." << std::endl;

    fs::create_directories("test_disks/floppy");
    fs::create_directories("test_disks/scsi");

    std::string test_floppy_path = "test_disks/floppy/test_sound.img";
    std::string test_scsi_path = "test_disks/scsi/test_hd.hda";

    // Create floppy image
    s760::RolandS760Disk disk("HARDWARE TEST");
    disk.add_patch(1, "Live Patch", {1}, 127, 0);
    auto f_data = disk.build_image();
    {
        std::ofstream f(test_floppy_path, std::ios::binary);
        f.write(reinterpret_cast<const char*>(f_data.data()), f_data.size());
    }

    // Create SCSI image (2MB)
    auto scsi_data = disk.build_scsi_image_mb(2);
    {
        std::ofstream f(test_scsi_path, std::ios::binary);
        f.write(reinterpret_cast<const char*>(scsi_data.data()), scsi_data.size());
    }

    s760::S760DriveManager mgr;
    assert(mgr.mount_floppy(test_floppy_path));
    auto f_status = mgr.get_floppy_status();
    assert(f_status.is_mounted == true);
    assert(f_status.image_name == "test_sound.img");
    assert(f_status.total_sectors == 2880);

    // Read Sector 0
    uint8_t sec0[512] = {0};
    assert(mgr.get_floppy_device()->read_sector(0, sec0));
    assert(std::memcmp(sec0, "S770 MR25A", 10) == 0);

    // Simulate S-760 hardware writing a new patch to floppy
    uint8_t modified_sec0[512];
    std::memcpy(modified_sec0, sec0, 512);
    std::memcpy(&modified_sec0[0x40], "MODIFIED VOL    ", 16);
    assert(mgr.get_floppy_device()->write_sector(0, modified_sec0));
    assert(mgr.get_floppy_status().is_dirty == true);

    // Flush to disk file
    assert(mgr.flush_floppy());
    assert(mgr.get_floppy_status().is_dirty == false);
    mgr.eject_floppy();

    // Verify written file directly on filesystem
    {
        std::ifstream f(test_floppy_path, std::ios::binary);
        std::vector<uint8_t> check_data(512);
        f.read(reinterpret_cast<char*>(check_data.data()), 512);
        assert(std::memcmp(&check_data[0x40], "MODIFIED VOL    ", 16) == 0);
    }

    // Test SCSI ID 1
    assert(mgr.mount_scsi_device(1, test_scsi_path, s760::DeviceType::HardDisk_SCSI));
    auto scsi_status = mgr.get_scsi_status(1);
    assert(scsi_status.is_mounted == true);
    assert(scsi_status.total_bytes == 2 * 1024 * 1024);
    mgr.eject_scsi_device(1);

    // Test Scan Image Folder
    auto found_floppies = s760::S760DriveManager::scan_image_folder("test_disks/floppy");
    assert(found_floppies.size() >= 1);
    auto found_scsi = s760::S760DriveManager::scan_image_folder("test_disks/scsi");
    assert(found_scsi.size() >= 1);

    // Clean up test files
    fs::remove_all("test_disks");

    std::cout << "  -> Folder-Based Hardware-Accurate Drive Manager Tests PASSED!" << std::endl;
}

void test_libretro_host() {
    std::cout << "[TEST] Libretro Host Dynamic Engine & DAW Audio Bridge..." << std::endl;

#if defined(_WIN32)
    std::string core_path = "build/Release/mock_core.dll";
    if (!fs::exists(core_path)) {
        core_path = "Release/mock_core.dll";
    }
    if (!fs::exists(core_path)) {
        core_path = "mock_core.dll";
    }
#else
    std::string core_path = "./libmock_core.so";
#endif

    if (!fs::exists(core_path)) {
        std::cout << "  (Skipping host test - mock_core not found at " << core_path << ")" << std::endl;
        return;
    }

    s760::S760LibretroHost host;
    assert(host.load_core(core_path));
    assert(host.is_core_loaded());

    assert(host.load_system("s760_os"));
    assert(host.is_system_running());

    // Run 5 emulator frames
    for (int i = 0; i < 5; ++i) {
        host.run_frame();
    }

    // Check Audio Stream (DAW buffer extraction)
    auto stats = host.get_audio_stats();
    assert(stats.available_frames >= 735 * 5);

    std::vector<float> daw_left(512);
    std::vector<float> daw_right(512);
    size_t read_frames = host.read_audio_frames(daw_left.data(), daw_right.data(), 512);
    assert(read_frames == 512);
    assert(daw_left[0] != 0.0f || daw_right[0] != 0.0f);

    // Check Video Frame (CRT display)
    auto frame = host.get_latest_video_frame();
    assert(frame.width == 320);
    assert(frame.height == 240);
    assert(frame.rgba_pixels.size() == 320 * 240);

    // Check Savestates (DAW project chunk serialization)
    size_t state_sz = host.get_state_size();
    assert(state_sz == 1024);
    auto state_data = host.save_state();
    assert(state_data.size() == 1024);
    assert(host.load_state(state_data));

    host.unload_system();
    host.unload_core();

    std::cout << "  -> Libretro Host & DAW Audio Bridge Tests PASSED!" << std::endl;
}

void test_sample_recorder() {
    std::cout << "[TEST] S-760 Sample Recorder (Live Audio Sampling, Triggers & Metering)..." << std::endl;

    s760::S760SampleRecorder recorder;
    s760::RecordingConfig cfg;
    cfg.target_sample_rate = 44100;
    cfg.trigger_mode = s760::RecordTriggerMode::Threshold;
    cfg.threshold_db = -20.0;
    cfg.pre_trigger_samples = 512;
    cfg.sample_name = "LIVE_SAMP";
    cfg.root_key = 60;
    recorder.set_config(cfg);

    recorder.arm();
    assert(recorder.is_armed());
    assert(!recorder.is_recording());

    // 1. Feed silence - should remain armed and not trigger
    std::vector<float> silence(256, 0.0f);
    recorder.process_input(silence.data(), silence.data(), silence.size(), 44100.0);
    assert(recorder.is_armed());

    // 2. Feed audio burst exceeding -20dB (e.g. 0.5f = ~ -6dB) -> should auto-trigger threshold!
    std::vector<float> burst(1024);
    for (size_t i = 0; i < burst.size(); ++i) {
        burst[i] = static_cast<float>(std::sin(2.0 * 3.14159265 * 440.0 * i / 44100.0) * 0.5);
    }
    recorder.process_input(burst.data(), burst.data(), burst.size(), 44100.0);
    assert(recorder.is_recording());
    assert(recorder.get_peak_level_left() > 0.4f);

    // Stop recording and retrieve sample
    recorder.stop_recording();
    assert(recorder.get_state() == s760::RecordState::Finished);

    auto res = recorder.get_recorded_result();
    assert(res.valid);
    assert(res.sample_name == "LIVE_SAMP");
    assert(res.sample_rate == 44100);
    assert(!res.left_pcm_bytes.empty());

    // Export as Roland Sample block
    auto sample_l = recorder.export_sample(false);
    assert(sample_l.name == "LIVE_SAMP_L");
    assert(sample_l.sample_rate == 44100);
    assert(sample_l.root_key == 60);
    assert(!sample_l.pcm_data.empty());

    // 3. Test MIDI Note-On Trigger
    cfg.trigger_mode = s760::RecordTriggerMode::MIDINote;
    recorder.set_config(cfg);
    recorder.arm();
    assert(recorder.is_armed());

    recorder.on_midi_note_on(60, 100);
    assert(recorder.is_recording());
    recorder.stop_recording();

    std::cout << "  -> S-760 Sample Recorder & Live Sampling Tests PASSED!" << std::endl;
}

void test_adversarial_remediation() {
    std::cout << "[TEST] Adversarial Code Review Regression & Hardening Tests..." << std::endl;

    // 1. Finding 1 & 3: Mount replacement over dirty image without self-deadlock & LBA bounds
    fs::create_directories("test_adversarial");
    std::string path_a = "test_adversarial/disk_a.img";
    std::string path_b = "test_adversarial/disk_b.img";
    {
        std::ofstream fa(path_a, std::ios::binary);
        std::vector<uint8_t> buf_a(512 * 10, 0xAA);
        fa.write(reinterpret_cast<const char*>(buf_a.data()), buf_a.size());

        std::ofstream fb(path_b, std::ios::binary);
        std::vector<uint8_t> buf_b(512 * 10, 0xBB);
        fb.write(reinterpret_cast<const char*>(buf_b.data()), buf_b.size());
    }

    s760::FileBackedBlockDevice dev(s760::DeviceType::Floppy_35_HD, 512);
    assert(dev.mount_file(path_a));
    assert(dev.get_status().is_mounted);

    // Modify sector 0 to make it dirty
    uint8_t mod_sec[512] = {0x12, 0x34};
    assert(dev.write_sector(0, mod_sec));
    assert(dev.get_status().is_dirty);

    // Mount disk_b over disk_a: must not deadlock and must flush disk_a cleanly
    assert(dev.mount_file(path_b));
    assert(dev.get_status().is_mounted);
    assert(dev.get_status().image_name == "disk_b.img");
    assert(!dev.get_status().is_dirty);

    // Verify disk_a was flushed
    {
        std::ifstream fa(path_a, std::ios::binary);
        uint8_t check[2];
        fa.read(reinterpret_cast<char*>(check), 2);
        assert(check[0] == 0x12 && check[1] == 0x34);
    }

    // Overflow LBA bounds test (UINT64_MAX, extreme values)
    uint8_t lba_buf[512];
    assert(!dev.read_sector(UINT64_MAX, lba_buf));
    assert(!dev.write_sector(UINT64_MAX, lba_buf));
    assert(!dev.read_sector(0x1000000000ULL, lba_buf));

    // Reject empty file (0 bytes) and sub-sector file (128 bytes)
    std::string empty_path = "test_adversarial/empty.img";
    std::string sub_path = "test_adversarial/sub.img";
    {
        std::ofstream fe(empty_path, std::ios::binary);
        std::ofstream fs_sub(sub_path, std::ios::binary);
        std::vector<uint8_t> sub_buf(128, 0xFF);
        fs_sub.write(reinterpret_cast<const char*>(sub_buf.data()), sub_buf.size());
    }
    assert(!dev.mount_file(empty_path));
    assert(!dev.mount_file(sub_path));

    // 2. Finding 4 & 5: Roland & Akai parser and builder hardening
    // Akai build_iso(0) must reject safely
    bool akai_zero_threw = false;
    try {
        s760::AkaiS1000Disk akai_disk;
        auto iso = akai_disk.build_iso(0);
    } catch (const std::invalid_argument&) {
        akai_zero_threw = true;
    }
    assert(akai_zero_threw);

    // Roland build_image(100) must reject safely
    bool roland_small_threw = false;
    try {
        s760::RolandS760Disk r_disk;
        auto img = r_disk.build_image(100);
    } catch (const std::invalid_argument&) {
        roland_small_threw = true;
    }
    assert(roland_small_threw);

    // Malformed counts 0xFFFFFFFF in Roland header
    std::vector<uint8_t> malformed_img(512, 0);
    std::memcpy(&malformed_img[0], "S770 MR25A", 10);
    uint32_t bad_count = 0xFFFFFFFF;
    std::memcpy(&malformed_img[0x60], &bad_count, 4);
    std::memcpy(&malformed_img[0x64], &bad_count, 4);
    auto malformed_info = s760::RolandS760Disk::parse(malformed_img.data(), malformed_img.size());
    assert(malformed_info.patches.empty());
    assert(malformed_info.samples.empty());

    // 3. Finding 24: Audio underrun telemetry tracking
    s760::S760LibretroHost host;
    std::vector<float> dummy_out_l(500, 0.0f);
    std::vector<float> dummy_out_r(500, 0.0f);
    size_t read_frames = host.read_audio_frames(dummy_out_l.data(), dummy_out_r.data(), 500);
    assert(read_frames == 0); // Nothing in ring buffer yet
    auto stats = host.get_audio_stats();
    assert(stats.underrun_count == 1);
    assert(stats.underrun_frames == 500);

    // Clean up
    fs::remove_all("test_adversarial");
    std::cout << "  -> Adversarial Code Review Regression Tests PASSED!" << std::endl;
}

int main() {
    std::cout << "========================================" << std::endl;
    std::cout << "  Roland S-760 C++ Core Test Suite      " << std::endl;
    std::cout << "========================================" << std::endl;

    try {
        test_roland_disk();
        test_akai_conversion();
        test_dsp_tools();
        test_drive_manager();
        test_libretro_host();
        test_sample_recorder();
        test_adversarial_remediation();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL C++ CORE TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
