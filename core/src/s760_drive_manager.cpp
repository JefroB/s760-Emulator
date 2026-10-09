#include "s760/s760_drive_manager.hpp"
#include <filesystem>
#include <iostream>
#include <cstring>

namespace s760 {

namespace fs = std::filesystem;

constexpr size_t MAX_IMAGE_SIZE = 2ULL * 1024 * 1024 * 1024; // 2GB policy limit

FileBackedBlockDevice::FileBackedBlockDevice(DeviceType type, size_t sector_size)
    : m_type(type), m_sector_size(sector_size) {}

FileBackedBlockDevice::~FileBackedBlockDevice() {
    unmount(true);
}

bool FileBackedBlockDevice::mount_file(const std::string& path, bool read_only) {
    std::lock_guard<std::mutex> lock(m_mutex);

    // If already mounted, unmount first without dropping lock or self-deadlocking
    if (m_is_mounted) {
        if (!unmount_locked(true)) {
            // Flush of dirty prior image failed: preserve dirty data, do not overwrite mount
            return false;
        }
    }

    std::ifstream file(path, std::ios::binary | std::ios::ate);
    if (!file.is_open()) {
        return false;
    }

    std::streamsize size = file.tellg();
    if (size <= 0 || m_sector_size == 0) {
        return false;
    }

    if (size < static_cast<std::streamsize>(m_sector_size) ||
        size > static_cast<std::streamsize>(MAX_IMAGE_SIZE)) {
        return false;
    }

    file.seekg(0, std::ios::beg);
    std::vector<uint8_t> temp_buf(static_cast<size_t>(size));
    if (!file.read(reinterpret_cast<char*>(temp_buf.data()), size)) {
        return false;
    }

    m_buffer = std::move(temp_buf);
    m_file_path = path;
    m_read_only = read_only;
    m_dirty = false;
    m_is_mounted = true;
    return true;
}

bool FileBackedBlockDevice::unmount(bool flush) {
    std::lock_guard<std::mutex> lock(m_mutex);
    return unmount_locked(flush);
}

bool FileBackedBlockDevice::unmount_locked(bool flush) {
    if (!m_is_mounted) return true;

    if (flush && m_dirty && !m_read_only) {
        if (!flush_to_disk_locked()) {
            // Flush failed: preserve buffer, path, and dirty state to prevent data loss
            return false;
        }
    }

    m_buffer.clear();
    m_file_path.clear();
    m_is_mounted = false;
    m_dirty = false;
    return true;
}

bool FileBackedBlockDevice::flush_to_disk() {
    std::lock_guard<std::mutex> lock(m_mutex);
    return flush_to_disk_locked();
}

bool FileBackedBlockDevice::flush_to_disk_locked() {
    if (!m_is_mounted || !m_dirty || m_read_only || m_file_path.empty()) {
        return true;
    }

    std::ofstream out(m_file_path, std::ios::binary | std::ios::trunc);
    if (!out.is_open()) {
        return false;
    }

    out.write(reinterpret_cast<const char*>(m_buffer.data()), m_buffer.size());
    if (!out.good()) {
        return false;
    }

    m_dirty = false;
    return true;
}

bool FileBackedBlockDevice::read_sector(uint64_t lba, uint8_t* out_buffer) {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (!m_is_mounted || !out_buffer || m_sector_size == 0 || m_buffer.size() < m_sector_size) {
        return false;
    }

    uint64_t max_lba = (m_buffer.size() - m_sector_size) / m_sector_size;
    if (lba > max_lba) {
        return false;
    }

    size_t byte_offset = static_cast<size_t>(lba) * m_sector_size;
    std::memcpy(out_buffer, m_buffer.data() + byte_offset, m_sector_size);
    return true;
}

bool FileBackedBlockDevice::write_sector(uint64_t lba, const uint8_t* in_buffer) {
    std::lock_guard<std::mutex> lock(m_mutex);
    if (!m_is_mounted || !in_buffer || m_read_only || m_sector_size == 0 || m_buffer.size() < m_sector_size) {
        return false;
    }

    uint64_t max_lba = (m_buffer.size() - m_sector_size) / m_sector_size;
    if (lba > max_lba) {
        return false;
    }

    size_t byte_offset = static_cast<size_t>(lba) * m_sector_size;
    std::memcpy(m_buffer.data() + byte_offset, in_buffer, m_sector_size);
    m_dirty = true;
    return true;
}

DriveStatus FileBackedBlockDevice::get_status() const {
    std::lock_guard<std::mutex> lock(m_mutex);
    DriveStatus s;
    s.type = m_type;
    s.is_mounted = m_is_mounted;
    s.is_write_protected = m_read_only;
    s.is_dirty = m_dirty;
    s.file_path = m_file_path;
    if (m_is_mounted && !m_file_path.empty()) {
        s.image_name = fs::path(m_file_path).filename().string();
    }
    s.total_bytes = m_buffer.size();
    s.sector_size = m_sector_size;
    s.total_sectors = (m_sector_size > 0) ? (m_buffer.size() / m_sector_size) : 0;
    return s;
}

// -----------------------------------------------------------------------------
// S760DriveManager
// -----------------------------------------------------------------------------

S760DriveManager::S760DriveManager() {
    m_floppy = std::make_shared<FileBackedBlockDevice>(DeviceType::Floppy_35_HD, 512);
    for (int i = 0; i < 7; ++i) {
        m_scsi_devices[i] = std::make_shared<FileBackedBlockDevice>(DeviceType::HardDisk_SCSI, 512);
    }
}

S760DriveManager::~S760DriveManager() {
    flush_all();
}

bool S760DriveManager::mount_floppy(const std::string& filepath, bool read_only) {
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    return m_floppy ? m_floppy->mount_file(filepath, read_only) : false;
}

bool S760DriveManager::eject_floppy() {
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    return m_floppy ? m_floppy->unmount(true) : false;
}

bool S760DriveManager::flush_floppy() {
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    return m_floppy ? m_floppy->flush_to_disk() : false;
}

DriveStatus S760DriveManager::get_floppy_status() const {
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    return m_floppy ? m_floppy->get_status() : DriveStatus{};
}

std::shared_ptr<VirtualBlockDevice> S760DriveManager::get_floppy_device() const {
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    return m_floppy;
}

bool S760DriveManager::mount_scsi_device(uint8_t scsi_id, const std::string& filepath, DeviceType type, bool read_only) {
    if (scsi_id >= 7) return false;
    size_t sector_size = (type == DeviceType::CDROM_SCSI) ? 2048 : 512;
    auto dev = std::make_shared<FileBackedBlockDevice>(type, sector_size);
    if (!dev->mount_file(filepath, read_only)) {
        return false;
    }
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    m_scsi_devices[scsi_id] = dev;
    return true;
}

bool S760DriveManager::eject_scsi_device(uint8_t scsi_id) {
    if (scsi_id >= 7) return false;
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    if (!m_scsi_devices[scsi_id]) return false;
    return m_scsi_devices[scsi_id]->unmount(true);
}

bool S760DriveManager::flush_scsi_device(uint8_t scsi_id) {
    if (scsi_id >= 7) return false;
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    if (!m_scsi_devices[scsi_id]) return false;
    return m_scsi_devices[scsi_id]->flush_to_disk();
}

void S760DriveManager::flush_all() {
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    if (m_floppy) m_floppy->flush_to_disk();
    for (int i = 0; i < 7; ++i) {
        if (m_scsi_devices[i]) {
            m_scsi_devices[i]->flush_to_disk();
        }
    }
}

DriveStatus S760DriveManager::get_scsi_status(uint8_t scsi_id) const {
    if (scsi_id >= 7) return DriveStatus{};
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    if (!m_scsi_devices[scsi_id]) return DriveStatus{};
    return m_scsi_devices[scsi_id]->get_status();
}

std::shared_ptr<VirtualBlockDevice> S760DriveManager::get_scsi_device(uint8_t scsi_id) const {
    if (scsi_id >= 7) return nullptr;
    std::lock_guard<std::mutex> lock(m_manager_mutex);
    return m_scsi_devices[scsi_id];
}

std::vector<std::string> S760DriveManager::scan_image_folder(const std::string& directory_path) {
    std::vector<std::string> results;
    if (!fs::exists(directory_path) || !fs::is_directory(directory_path)) {
        return results;
    }

    for (const auto& entry : fs::directory_iterator(directory_path)) {
        if (entry.is_regular_file()) {
            std::string ext = entry.path().extension().string();
            for (char& c : ext) c = static_cast<char>(tolower(c));
            if (ext == ".img" || ext == ".hda" || ext == ".iso" || ext == ".dsk" || ext == ".out") {
                results.push_back(entry.path().string());
            }
        }
    }
    std::sort(results.begin(), results.end());
    return results;
}

} // namespace s760
