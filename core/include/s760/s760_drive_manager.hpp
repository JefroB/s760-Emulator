#pragma once

#include <cstdint>
#include <string>
#include <vector>
#include <memory>
#include <fstream>
#include <mutex>

namespace s760 {

enum class DeviceType {
    None,
    Floppy_35_HD,    // 1.44MB Floppy (512-byte sectors, 2880 sectors)
    HardDisk_SCSI,   // SCSI Hard Disk (512-byte sectors)
    CDROM_SCSI,      // SCSI CD-ROM / ISO (2048-byte blocks)
    MODrive_SCSI     // Magneto-Optical Drive (512-byte sectors)
};

struct DriveStatus {
    DeviceType type = DeviceType::None;
    bool is_mounted = false;
    bool is_write_protected = false;
    bool is_dirty = false;
    std::string file_path;
    std::string image_name;
    size_t total_bytes = 0;
    size_t sector_size = 512;
    size_t total_sectors = 0;
};

class VirtualBlockDevice {
public:
    virtual ~VirtualBlockDevice() = default;

    virtual bool mount_file(const std::string& path, bool read_only = false) = 0;
    virtual bool unmount(bool flush = true) = 0;
    virtual bool flush_to_disk() = 0;

    virtual bool read_sector(uint64_t lba, uint8_t* out_buffer) = 0;
    virtual bool write_sector(uint64_t lba, const uint8_t* in_buffer) = 0;

    virtual DriveStatus get_status() const = 0;
    virtual const uint8_t* get_raw_memory() const = 0;
    virtual size_t get_size_bytes() const = 0;
};

class FileBackedBlockDevice : public VirtualBlockDevice {
public:
    FileBackedBlockDevice(DeviceType type, size_t sector_size);
    ~FileBackedBlockDevice() override;

    bool mount_file(const std::string& path, bool read_only = false) override;
    bool unmount(bool flush = true) override;
    bool flush_to_disk() override;

    bool read_sector(uint64_t lba, uint8_t* out_buffer) override;
    bool write_sector(uint64_t lba, const uint8_t* in_buffer) override;

    DriveStatus get_status() const override;
    const uint8_t* get_raw_memory() const override { return m_buffer.data(); }
    size_t get_size_bytes() const override { return m_buffer.size(); }

private:
    bool unmount_locked(bool flush);
    bool flush_to_disk_locked();

    DeviceType m_type;
    size_t m_sector_size;
    std::string m_file_path;
    bool m_is_mounted = false;
    bool m_read_only = false;
    bool m_dirty = false;
    std::vector<uint8_t> m_buffer;
    mutable std::mutex m_mutex;
};

class S760DriveManager {
public:
    S760DriveManager();
    ~S760DriveManager();

    // Floppy Drive (FDD 0)
    bool mount_floppy(const std::string& filepath, bool read_only = false);
    bool eject_floppy();
    bool flush_floppy();
    DriveStatus get_floppy_status() const;
    std::shared_ptr<VirtualBlockDevice> get_floppy_device() const;

    // SCSI Bus (IDs 0..6)
    bool mount_scsi_device(uint8_t scsi_id, const std::string& filepath, DeviceType type, bool read_only = false);
    bool eject_scsi_device(uint8_t scsi_id);
    bool flush_scsi_device(uint8_t scsi_id);
    void flush_all();
    DriveStatus get_scsi_status(uint8_t scsi_id) const;
    std::shared_ptr<VirtualBlockDevice> get_scsi_device(uint8_t scsi_id) const;

    // Scan a folder for compatible disk images (.img, .hda, .iso, .dsk)
    static std::vector<std::string> scan_image_folder(const std::string& directory_path);

private:
    mutable std::mutex m_manager_mutex;
    std::shared_ptr<FileBackedBlockDevice> m_floppy;
    std::shared_ptr<FileBackedBlockDevice> m_scsi_devices[7];
};

} // namespace s760
