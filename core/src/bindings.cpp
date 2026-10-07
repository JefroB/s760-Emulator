#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "s760/s760_disk.hpp"
#include "s760/s760_dsp.hpp"
#include "s760/akai_disk.hpp"
#include "s760/s760_drive_manager.hpp"
#include "s760/s760_libretro_host.hpp"

namespace py = pybind11;
using namespace s760;

PYBIND11_MODULE(s760_cpp, m) {
    m.doc() = "Native C++ Roland S-760 & Akai S1000 Core Engine";

    // -------------------------------------------------------------------------
    // Roland S-760 Disk
    // -------------------------------------------------------------------------
    py::class_<Patch>(m, "Patch")
        .def_readwrite("id", &Patch::id)
        .def_readwrite("name", &Patch::name)
        .def_readwrite("level", &Patch::level)
        .def_readwrite("pan", &Patch::pan)
        .def_readwrite("partials", &Patch::partials);

    py::class_<Sample>(m, "Sample")
        .def_readwrite("id", &Sample::id)
        .def_readwrite("name", &Sample::name)
        .def_readwrite("sample_rate", &Sample::sample_rate)
        .def_readwrite("loop_start", &Sample::loop_start)
        .def_readwrite("loop_end", &Sample::loop_end)
        .def_readwrite("root_key", &Sample::root_key)
        .def_property("data",
            [](const Sample& s) {
                return py::bytes(reinterpret_cast<const char*>(s.pcm_data.data()), s.pcm_data.size());
            },
            [](Sample& s, py::bytes b) {
                std::string str = b;
                s.pcm_data.assign(str.begin(), str.end());
            }
        );

    py::class_<DiskInfo>(m, "DiskInfo")
        .def_readwrite("is_roland", &DiskInfo::is_roland)
        .def_readwrite("volume_name", &DiskInfo::volume_name)
        .def_readwrite("num_patches", &DiskInfo::num_patches)
        .def_readwrite("num_samples", &DiskInfo::num_samples)
        .def_readwrite("patches", &DiskInfo::patches)
        .def_readwrite("samples", &DiskInfo::samples);

    py::class_<RolandS760Disk>(m, "RolandS760Disk")
        .def(py::init<std::string>(), py::arg("volume_name") = "S-760 SOUND")
        .def("set_volume_name", &RolandS760Disk::set_volume_name)
        .def("get_volume_name", &RolandS760Disk::get_volume_name)
        .def("add_patch", &RolandS760Disk::add_patch,
             py::arg("patch_id"), py::arg("patch_name"),
             py::arg("partial_ids") = std::vector<uint16_t>{1, 2},
             py::arg("level") = 127, py::arg("pan") = 0)
        .def("add_sample", [](RolandS760Disk& disk, uint16_t sample_id, const std::string& name,
                              uint32_t sample_rate, py::bytes pcm_data,
                              uint32_t loop_start, uint32_t loop_end, uint8_t root_key) {
            std::string s = pcm_data;
            std::vector<uint8_t> vec(s.begin(), s.end());
            disk.add_sample(sample_id, name, sample_rate, vec, loop_start, loop_end, root_key);
        }, py::arg("sample_id"), py::arg("sample_name"), py::arg("sample_rate"),
           py::arg("pcm_data"), py::arg("loop_start") = 0, py::arg("loop_end") = 0, py::arg("root_key") = 60)
        .def("build_image", [](const RolandS760Disk& disk, size_t size_bytes) {
            auto data = disk.build_image(size_bytes);
            return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        }, py::arg("size_bytes") = 0)
        .def("build_scsi_image_mb", [](const RolandS760Disk& disk, size_t size_mb) {
            auto data = disk.build_scsi_image_mb(size_mb);
            return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        }, py::arg("size_mb"))
        .def_static("parse", [](py::bytes b) {
            std::string s = b;
            return RolandS760Disk::parse(reinterpret_cast<const uint8_t*>(s.data()), s.size());
        })
        .def_static("optimize_disk", [](py::bytes b) {
            std::string s = b;
            auto out = RolandS760Disk::optimize_disk(reinterpret_cast<const uint8_t*>(s.data()), s.size());
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        });

    // -------------------------------------------------------------------------
    // Akai S1000 Disk & Converter
    // -------------------------------------------------------------------------
    py::class_<AkaiProgram>(m, "AkaiProgram")
        .def_readwrite("num", &AkaiProgram::num)
        .def_readwrite("name", &AkaiProgram::name)
        .def_readwrite("midi_channel", &AkaiProgram::midi_channel)
        .def_readwrite("keygroups", &AkaiProgram::keygroups);

    py::class_<AkaiSample>(m, "AkaiSample")
        .def_readwrite("name", &AkaiSample::name)
        .def_readwrite("sample_rate", &AkaiSample::sample_rate)
        .def_readwrite("loop_start", &AkaiSample::loop_start)
        .def_readwrite("loop_end", &AkaiSample::loop_end)
        .def_readwrite("root_key", &AkaiSample::root_key)
        .def_property("data",
            [](const AkaiSample& s) {
                return py::bytes(reinterpret_cast<const char*>(s.data.data()), s.data.size());
            },
            [](AkaiSample& s, py::bytes b) {
                std::string str = b;
                s.data.assign(str.begin(), str.end());
            }
        );

    py::class_<AkaiDiskInfo>(m, "AkaiDiskInfo")
        .def_readwrite("is_akai", &AkaiDiskInfo::is_akai)
        .def_readwrite("volume_name", &AkaiDiskInfo::volume_name)
        .def_readwrite("num_programs", &AkaiDiskInfo::num_programs)
        .def_readwrite("num_samples", &AkaiDiskInfo::num_samples)
        .def_readwrite("programs", &AkaiDiskInfo::programs)
        .def_readwrite("samples", &AkaiDiskInfo::samples);

    py::class_<AkaiS1000Disk>(m, "AkaiS1000Disk")
        .def(py::init<std::string>(), py::arg("volume_name") = "AKAI S1000 VOL")
        .def("add_program", &AkaiS1000Disk::add_program,
             py::arg("prog_num"), py::arg("prog_name"),
             py::arg("midi_channel") = 1, py::arg("keygroup_count") = 1)
        .def("add_sample", [](AkaiS1000Disk& disk, const std::string& name,
                              uint32_t sample_rate, py::bytes pcm_data,
                              uint32_t loop_start, uint32_t loop_end, uint8_t root_key) {
            std::string s = pcm_data;
            std::vector<uint8_t> vec(s.begin(), s.end());
            disk.add_sample(name, sample_rate, vec, loop_start, loop_end, root_key);
        }, py::arg("sample_name"), py::arg("sample_rate"), py::arg("pcm_data"),
           py::arg("loop_start") = 0, py::arg("loop_end") = 0, py::arg("root_key") = 60)
        .def("build_iso", [](const AkaiS1000Disk& disk, size_t total_mb) {
            auto data = disk.build_iso(total_mb);
            return py::bytes(reinterpret_cast<const char*>(data.data()), data.size());
        }, py::arg("total_mb") = 4)
        .def_static("parse", [](py::bytes b) {
            std::string s = b;
            return AkaiS1000Disk::parse(reinterpret_cast<const uint8_t*>(s.data()), s.size());
        });

    py::class_<S760AkaiConverter>(m, "S760AkaiConverter")
        .def_static("convert", &S760AkaiConverter::convert,
                    py::arg("akai_disk"), py::arg("target_volume_name") = "S760 CONVERT");

    // -------------------------------------------------------------------------
    // S760 DSP Tools
    // -------------------------------------------------------------------------
    py::class_<MSDOSFileInfo>(m, "MSDOSFileInfo")
        .def_readwrite("is_dos", &MSDOSFileInfo::is_dos)
        .def_readwrite("filename", &MSDOSFileInfo::filename)
        .def_readwrite("file_size", &MSDOSFileInfo::file_size)
        .def_readwrite("is_wav", &MSDOSFileInfo::is_wav)
        .def_readwrite("sample_rate", &MSDOSFileInfo::sample_rate)
        .def_property_readonly("pcm_data", [](const MSDOSFileInfo& info) {
            return py::bytes(reinterpret_cast<const char*>(info.pcm_data.data()), info.pcm_data.size());
        });

    py::class_<SDSDumpInfo>(m, "SDSDumpInfo")
        .def_readwrite("valid_sds", &SDSDumpInfo::valid_sds)
        .def_readwrite("channel", &SDSDumpInfo::channel)
        .def_readwrite("sample_num", &SDSDumpInfo::sample_num)
        .def_readwrite("bits", &SDSDumpInfo::bits)
        .def_readwrite("sample_rate", &SDSDumpInfo::sample_rate)
        .def_readwrite("length", &SDSDumpInfo::length)
        .def_readwrite("loop_start", &SDSDumpInfo::loop_start)
        .def_readwrite("loop_end", &SDSDumpInfo::loop_end)
        .def_readwrite("loop_type", &SDSDumpInfo::loop_type);

    py::class_<S760DSPTools>(m, "S760DSPTools")
        .def_static("crossfade_loop", [](py::bytes pcm_bytes, size_t loop_start, size_t loop_end, size_t xfade_samples) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto out = S760DSPTools::crossfade_loop(vec, loop_start, loop_end, xfade_samples);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("pcm_bytes"), py::arg("loop_start"), py::arg("loop_end"), py::arg("xfade_samples") = 500)
        .def_static("time_stretch", [](py::bytes pcm_bytes, double stretch_factor, uint32_t sample_rate) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto out = S760DSPTools::time_stretch(vec, stretch_factor, sample_rate);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("pcm_bytes"), py::arg("stretch_factor") = 1.25, py::arg("sample_rate") = 44100)
        .def_static("digital_filter", [](py::bytes pcm_bytes, double cutoff_hz, uint32_t sample_rate, const std::string& filter_type) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto out = S760DSPTools::digital_filter(vec, cutoff_hz, sample_rate, filter_type);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("pcm_bytes"), py::arg("cutoff_hz") = 1000.0, py::arg("sample_rate") = 44100, py::arg("filter_type") = "lpf")
        .def_static("sample_rate_convert", [](py::bytes pcm_bytes, uint32_t in_rate, uint32_t out_rate) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto out = S760DSPTools::sample_rate_convert(vec, in_rate, out_rate);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("pcm_bytes"), py::arg("in_rate") = 44100, py::arg("out_rate") = 22050)
        .def_static("bit_convert", [](py::bytes pcm_bytes, int target_bits) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto out = S760DSPTools::bit_convert(vec, target_bits);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("pcm_bytes"), py::arg("target_bits") = 8)
        .def_static("auto_truncate_and_normalize", [](py::bytes pcm_bytes, double threshold_db, double peak_target) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto [out, start_idx, end_idx] = S760DSPTools::auto_truncate_and_normalize(vec, threshold_db, peak_target);
            return py::make_tuple(py::bytes(reinterpret_cast<const char*>(out.data()), out.size()), start_idx, end_idx);
        }, py::arg("pcm_bytes"), py::arg("threshold_db") = -48.0, py::arg("peak_target") = 0.98)
        .def_static("wave_edit", [](py::bytes pcm_a, py::bytes pcm_b, const std::string& operation, size_t start, size_t length) {
            std::string sa = pcm_a;
            std::string sb = pcm_b;
            std::vector<uint8_t> va(sa.begin(), sa.end());
            std::vector<uint8_t> vb(sb.begin(), sb.end());
            auto out = S760DSPTools::wave_edit(va, vb, operation, start, length);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("pcm_a"), py::arg("pcm_b") = py::bytes(), py::arg("operation") = "mix", py::arg("start") = 0, py::arg("length") = 0)
        .def_static("render_voice", [](py::bytes pcm_bytes, uint32_t sample_rate, uint8_t root_key,
                                       uint32_t loop_start, uint32_t loop_end, uint8_t note,
                                       size_t num_output_samples, uint32_t output_rate) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            return S760DSPTools::render_voice(vec, sample_rate, root_key, loop_start, loop_end, note, num_output_samples, output_rate);
        }, py::arg("pcm_bytes"), py::arg("sample_rate"), py::arg("root_key"),
           py::arg("loop_start"), py::arg("loop_end"), py::arg("note") = 60,
           py::arg("num_output_samples") = 44100, py::arg("output_rate") = 44100)
        .def_static("build_msdos_sample_floppy", [](const std::string& fname, py::bytes pcm_bytes, uint32_t sample_rate) {
            std::string s = pcm_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            auto out = S760DSPTools::build_msdos_sample_floppy(fname, vec, sample_rate);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("wav_filename"), py::arg("pcm_bytes"), py::arg("sample_rate") = 44100)
        .def_static("extract_wav_from_msdos", [](py::bytes disk_bytes) {
            std::string s = disk_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            return S760DSPTools::extract_wav_from_msdos(vec);
        })
        .def_static("build_sds_dump_header", [](uint16_t sample_num, uint32_t sample_rate,
                                                uint32_t length, uint32_t loop_start, uint32_t loop_end, uint8_t channel) {
            auto out = S760DSPTools::build_sds_dump_header(sample_num, sample_rate, length, loop_start, loop_end, channel);
            return py::bytes(reinterpret_cast<const char*>(out.data()), out.size());
        }, py::arg("sample_num"), py::arg("sample_rate"), py::arg("length"),
           py::arg("loop_start"), py::arg("loop_end"), py::arg("channel") = 0)
        .def_static("parse_sds_dump_header", [](py::bytes sysex) {
            std::string s = sysex;
            std::vector<uint8_t> vec(s.begin(), s.end());
            return S760DSPTools::parse_sds_dump_header(vec);
        });

    // -------------------------------------------------------------------------
    // Drive Manager (Folder-Based FDD & SCSI)
    // -------------------------------------------------------------------------
    py::enum_<DeviceType>(m, "DeviceType")
        .value("None", DeviceType::None)
        .value("Floppy_35_HD", DeviceType::Floppy_35_HD)
        .value("HardDisk_SCSI", DeviceType::HardDisk_SCSI)
        .value("CDROM_SCSI", DeviceType::CDROM_SCSI)
        .value("MODrive_SCSI", DeviceType::MODrive_SCSI);

    py::class_<DriveStatus>(m, "DriveStatus")
        .def_readwrite("type", &DriveStatus::type)
        .def_readwrite("is_mounted", &DriveStatus::is_mounted)
        .def_readwrite("is_write_protected", &DriveStatus::is_write_protected)
        .def_readwrite("is_dirty", &DriveStatus::is_dirty)
        .def_readwrite("file_path", &DriveStatus::file_path)
        .def_readwrite("image_name", &DriveStatus::image_name)
        .def_readwrite("total_bytes", &DriveStatus::total_bytes)
        .def_readwrite("sector_size", &DriveStatus::sector_size)
        .def_readwrite("total_sectors", &DriveStatus::total_sectors);

    py::class_<S760DriveManager>(m, "S760DriveManager")
        .def(py::init<>())
        .def("mount_floppy", &S760DriveManager::mount_floppy, py::arg("filepath"), py::arg("read_only") = false)
        .def("eject_floppy", &S760DriveManager::eject_floppy)
        .def("flush_floppy", &S760DriveManager::flush_floppy)
        .def("get_floppy_status", &S760DriveManager::get_floppy_status)
        .def("mount_scsi_device", &S760DriveManager::mount_scsi_device,
             py::arg("scsi_id"), py::arg("filepath"), py::arg("type"), py::arg("read_only") = false)
        .def("eject_scsi_device", &S760DriveManager::eject_scsi_device, py::arg("scsi_id"))
        .def("flush_scsi_device", &S760DriveManager::flush_scsi_device, py::arg("scsi_id"))
        .def("flush_all", &S760DriveManager::flush_all)
        .def("get_scsi_status", &S760DriveManager::get_scsi_status, py::arg("scsi_id"))
        .def_static("scan_image_folder", &S760DriveManager::scan_image_folder, py::arg("directory_path"));

    // -------------------------------------------------------------------------
    // Libretro Host Bridge
    // -------------------------------------------------------------------------
    py::class_<AudioBufferStats>(m, "AudioBufferStats")
        .def_readwrite("available_frames", &AudioBufferStats::available_frames)
        .def_readwrite("capacity_frames", &AudioBufferStats::capacity_frames)
        .def_readwrite("sample_rate", &AudioBufferStats::sample_rate);

    py::class_<VideoFrame>(m, "VideoFrame")
        .def_readwrite("width", &VideoFrame::width)
        .def_readwrite("height", &VideoFrame::height)
        .def_readwrite("rgba_pixels", &VideoFrame::rgba_pixels);

    py::class_<S760LibretroHost>(m, "S760LibretroHost")
        .def(py::init<>())
        .def("load_core", &S760LibretroHost::load_core, py::arg("core_path"))
        .def("unload_core", &S760LibretroHost::unload_core)
        .def("is_core_loaded", &S760LibretroHost::is_core_loaded)
        .def("load_system", &S760LibretroHost::load_system,
             py::arg("system_name") = "s760",
             py::arg("system_dir") = "roms/s760",
             py::arg("save_dir") = "saves")
        .def("unload_system", &S760LibretroHost::unload_system)
        .def("is_system_running", &S760LibretroHost::is_system_running)
        .def("run_frame", &S760LibretroHost::run_frame)
        .def("reset", &S760LibretroHost::reset)
        .def("get_audio_stats", &S760LibretroHost::get_audio_stats)
        .def("get_latest_video_frame", &S760LibretroHost::get_latest_video_frame)
        .def("send_midi_byte", &S760LibretroHost::send_midi_byte, py::arg("byte"))
        .def("send_midi_message", [](S760LibretroHost& host, py::bytes msg) {
            std::string s = msg;
            host.send_midi_message(reinterpret_cast<const uint8_t*>(s.data()), s.size());
        }, py::arg("msg"))
        .def("get_drive_manager", py::overload_cast<>(&S760LibretroHost::get_drive_manager), py::return_value_policy::reference)
        .def("get_state_size", &S760LibretroHost::get_state_size)
        .def("save_state", [](S760LibretroHost& host) {
            auto state = host.save_state();
            return py::bytes(reinterpret_cast<const char*>(state.data()), state.size());
        })
        .def("load_state", [](S760LibretroHost& host, py::bytes state_bytes) {
            std::string s = state_bytes;
            std::vector<uint8_t> vec(s.begin(), s.end());
            return host.load_state(vec);
        }, py::arg("state_bytes"));
}
