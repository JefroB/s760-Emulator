#include "s760/s760_mame_host.hpp"
#include "s760/s760_drive_manager.hpp"

#include <iostream>
#include <vector>
#include <string>
#include <cassert>
#include <cstdint>
#include <cstddef>
#include <fstream>
#include <filesystem>

// =============================================================================
//  test_midi_mount.cpp — S760MameHost MIDI routing + disk mount unit tests.
//
//  Spec: .kiro/specs/mame-live-backend/ (task 7.10, Requirements 6.6, 6.7, 6.8).
//
//  Exercises the adapter-level seams implemented in task 7.9 on the real
//  S760MameHost (no MAME binary required — the host owns a MIDI-in buffer and a
//  S760DriveManager directly):
//
//    * send_midi_message() / midi_in_bytes() — NOTE_ON / NOTE_OFF delivery is
//      recorded in order; null / zero-len is a no-op (Requirement 6.8).
//    * mount_disk() — delegates to get_drive_manager().mount_floppy(); true on a
//      mountable image, false on a bad path (Requirement 6.6, 6.7). A failed
//      mount keeps the currently mounted image and never crashes/throws, and is
//      surfaced via last_mount_ok() / last_mount_error().
//
//  Dependency-free, self-contained, assert-style executable in the style of
//  test_bridge.cpp. Any temporary image file created for the success case is
//  cleaned up before the process exits.
// =============================================================================

namespace {

using namespace s760;
namespace fs = std::filesystem;

// -----------------------------------------------------------------------------
//  Test 1 + 2 + 3: MIDI delivery (NOTE_ON / NOTE_OFF), accumulation, no-op guard.
// -----------------------------------------------------------------------------
void test_midi_delivery() {
    std::cout << "[TEST] S760MameHost MIDI NOTE_ON/NOTE_OFF delivery..." << std::endl;

    S760MameHost host;

    // Fresh host starts with an empty MIDI-in buffer.
    assert(host.midi_in_bytes().empty() && "MIDI-in buffer must start empty");

    // --- Test 1: NOTE_ON delivery (status 0x90, note 60, velocity 100) -------
    const uint8_t note_on[3] = {0x90, 60, 100};
    host.send_midi_message(note_on, 3);

    {
        const std::vector<uint8_t>& buf = host.midi_in_bytes();
        assert(buf.size() == 3 && "NOTE_ON must append exactly 3 bytes");
        assert(buf[0] == 0x90 && buf[1] == 60 && buf[2] == 100 &&
               "NOTE_ON bytes must be recorded in order");
    }

    // --- Test 2: NOTE_OFF delivery (status 0x80, note 60, velocity 0) --------
    const uint8_t note_off[3] = {0x80, 60, 0};
    host.send_midi_message(note_off, 3);

    {
        const std::vector<uint8_t>& buf = host.midi_in_bytes();
        // Buffer must now hold NOTE_ON then NOTE_OFF, 6 bytes total, in order.
        assert(buf.size() == 6 && "NOTE_ON + NOTE_OFF must total 6 bytes");
        assert(buf[0] == 0x90 && buf[1] == 60 && buf[2] == 100 && "NOTE_ON kept");
        assert(buf[3] == 0x80 && buf[4] == 60 && buf[5] == 0 && "NOTE_OFF appended");
    }

    // --- Test 3a: multiple messages accumulate in order ----------------------
    const uint8_t note_on2[3] = {0x90, 72, 64};
    host.send_midi_message(note_on2, 3);
    {
        const std::vector<uint8_t>& buf = host.midi_in_bytes();
        assert(buf.size() == 9 && "third message accumulates (9 bytes total)");
        assert(buf[6] == 0x90 && buf[7] == 72 && buf[8] == 64 &&
               "third message bytes recorded in order after the first two");
    }

    // --- Test 3b: null / zero-len is a no-op (buffer unchanged) --------------
    const std::size_t before = host.midi_in_bytes().size();
    host.send_midi_message(nullptr, 3);   // null msg -> no-op
    assert(host.midi_in_bytes().size() == before && "null msg must be a no-op");
    host.send_midi_message(note_on, 0);   // zero len -> no-op
    assert(host.midi_in_bytes().size() == before && "zero-len must be a no-op");
    // Confirm bytes are byte-for-byte unchanged after the no-op calls.
    {
        const std::vector<uint8_t>& buf = host.midi_in_bytes();
        assert(buf.size() == 9);
        assert(buf[0] == 0x90 && buf[1] == 60 && buf[2] == 100);
        assert(buf[3] == 0x80 && buf[4] == 60 && buf[5] == 0);
        assert(buf[6] == 0x90 && buf[7] == 72 && buf[8] == 64);
    }

    std::cout << "  -> MIDI delivery / accumulation / no-op guard PASSED!" << std::endl;
}

// Create a valid, mountable floppy image: a standard 1.44MB (1,474,560-byte)
// zero-filled file. mount_floppy() accepts any readable file whose size is at
// least one sector (512 bytes) and at most the 2GB policy cap, so a full-size
// floppy image is a correct, representative valid image for Floppy_35_HD.
// Returns true on success.
bool make_floppy_image(const fs::path& path) {
    constexpr std::size_t kFloppyBytes = 1474560; // 2880 * 512
    std::ofstream out(path, std::ios::binary | std::ios::trunc);
    if (!out.is_open()) return false;
    std::vector<char> zeros(kFloppyBytes, 0);
    out.write(zeros.data(), static_cast<std::streamsize>(zeros.size()));
    out.flush();
    return out.good();
}

// -----------------------------------------------------------------------------
//  Test 4 + 5: mount success, bad-path failure (keeps current image, no crash).
// -----------------------------------------------------------------------------
void test_mount_success_and_failure() {
    std::cout << "[TEST] S760MameHost mount_disk success + bad-path handling..." << std::endl;

    S760MameHost host;

    // Fresh host: no mount attempted yet.
    assert(host.last_mount_ok() == false && "last_mount_ok starts false");
    assert(host.last_mount_error().empty() && "last_mount_error starts empty");
    assert(host.get_drive_manager().get_floppy_status().is_mounted == false &&
           "nothing mounted on a fresh host");

    // --- Test 5a: bad path with NOTHING mounted leaves is_mounted false ------
    const std::string bad_path = "this/path/does/not/exist.img";
    bool bad_first = host.mount_disk(bad_path);               // must not throw/crash
    assert(bad_first == false && "mount of a non-existent path returns false");
    assert(host.last_mount_ok() == false && "last_mount_ok false after bad mount");
    assert(host.last_mount_error() == bad_path &&
           "last_mount_error records the offending path");
    assert(host.get_drive_manager().get_floppy_status().is_mounted == false &&
           "bad mount with nothing mounted leaves is_mounted false");

    // --- Test 4: successful mount of a valid image ---------------------------
    fs::path tmp = fs::temp_directory_path() /
                   "s760_test_floppy_7_10.img";
    // Make sure no stale file lingers from a prior run.
    std::error_code ec;
    fs::remove(tmp, ec);

    bool created = make_floppy_image(tmp);
    assert(created && "failed to create temporary floppy image for the success case");

    bool ok = host.mount_disk(tmp.string());
    assert(ok == true && "mount_disk of a valid image must return true");
    assert(host.last_mount_ok() == true && "last_mount_ok true after a successful mount");
    assert(host.last_mount_error().empty() &&
           "last_mount_error empty after a successful mount");

    DriveStatus st = host.get_drive_manager().get_floppy_status();
    assert(st.is_mounted == true && "floppy must report mounted after success");
    assert(st.total_bytes == 1474560 && "mounted image size matches the created file");

    // --- Test 5b: bad path AFTER a success keeps the current image -----------
    bool bad_after = host.mount_disk(bad_path);              // must not throw/crash
    assert(bad_after == false && "bad-path mount returns false");
    assert(host.last_mount_ok() == false && "last_mount_ok false after the bad mount");
    assert(host.last_mount_error() == bad_path &&
           "last_mount_error records the bad path again");
    // The previously-mounted image is KEPT (Requirement 6.7).
    DriveStatus st_after = host.get_drive_manager().get_floppy_status();
    assert(st_after.is_mounted == true &&
           "a failed mount must keep the currently mounted image");
    assert(st_after.total_bytes == 1474560 &&
           "the kept image is still the originally mounted one");

    // Clean up the temp file (release the mount first so the buffer is freed).
    host.get_drive_manager().eject_floppy();
    fs::remove(tmp, ec);
    assert(!fs::exists(tmp) && "temporary floppy image should be cleaned up");

    std::cout << "  -> mount success + bad-path (keep current image, no crash) PASSED!"
              << std::endl;
}

} // namespace

int main() {
    std::cout << "===============================================" << std::endl;
    std::cout << "  Roland S-760 MIDI Routing + Mount Test Suite " << std::endl;
    std::cout << "===============================================" << std::endl;

    try {
        test_midi_delivery();
        test_mount_success_and_failure();
    } catch (const std::exception& e) {
        std::cerr << "[FATAL TEST ERROR] " << e.what() << std::endl;
        return 1;
    }

    std::cout << "\n>>> ALL S760 MIDI/MOUNT TESTS PASSED SUCCESSFULLY! <<<" << std::endl;
    return 0;
}
