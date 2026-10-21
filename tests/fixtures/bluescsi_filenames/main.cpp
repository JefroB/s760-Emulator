// Project-owned regression driver for pinned upstream GPL source loaded by pytest.
#include "env.hpp"
#include "upstream_functions.inc"
#include "BlueSCSI_Toolbox.cpp"

int checks = 0;
void check(bool ok, const char *message) {
    ++checks;
    if (!ok) throw std::runtime_error(message);
}
void command(int id, int opcode, int index = 0) {
    std::memset(scsiDev.cdb, 0, sizeof(scsiDev.cdb));
    scsiDev.cdb[0] = uint8_t(opcode); scsiDev.cdb[1] = uint8_t(index);
    scsiDev.target = &scsiDev.targets[id]; scsiDev.status = 0;
    scsiDev.phase = STATUS; scsiDev.dataLen = 0; scsiDev.target->sense = {};
    check(scsiToolboxCommand(), "command dispatched");
}
void create(const std::string &path, int value) {
    fs::create_directories((sdroot / path).parent_path());
    std::ofstream f(sdroot / path, std::ios::binary);
    f << std::string(4096, char(value));
}
int first_byte(int id) {
    uint8_t b = 0; images[id].file.seekSet(0);
    check(images[id].file.read(&b, 1) == 1, "selected image readable");
    return b;
}
void expect_catalog(int id, const std::vector<std::string> &names) {
    command(id, 0xda);
    check(scsiDev.status == 0 && scsiDev.data[0] == names.size(), "count uses complete filename filter");
    command(id, 0xd7);
    check(scsiDev.status == 0 && scsiDev.dataLen == names.size() * 40, "list agrees with count");
    for (size_t i = 0; i < names.size(); ++i) {
        auto row = scsiDev.data + i * 40;
        check(row[0] == i, "wire index retained");
        check(std::string((char *)row + 2) == names[i].substr(0, 32), "32-byte wire label retained");
    }
    for (size_t i = 0; i < names.size(); ++i) {
        command(id, 0xd8, int(i));
        check(scsiDev.status == 0, "valid switch succeeds");
        check(images[id].opened == "CD" + std::to_string(id) + "/" + names[i], "index opens displayed image");
        check(first_byte(id) == int(i + 1), "selected image contents match index");
    }
}
void filters() {
    for (int id : {1, 2, 3, 6}) {
        std::string dir = "CD" + std::to_string(id);
        fs::create_directories(sdroot / dir);
        std::string ignored = std::string(29, 'A') + ".txt";
        create(dir + "/" + ignored, 99); create(dir + "/Z.iso", 1);
        expect_catalog(id, {"Z.iso"});
        fs::remove(sdroot / dir / "Z.iso");
        std::string image = std::string(28, 'B') + ".txt.iso";
        create(dir + "/" + image, 1);
        expect_catalog(id, {image});
        create(dir + "/Z.iso", 2);
        // Both original enumerators now have count2, yet index0 differs.
        expect_catalog(id, {image, "Z.iso"});
        create(dir + "/.hidden.iso", 99); create(dir + "/_skip.iso", 99);
        create(dir + "/notes.TXT", 99); fs::create_directories(sdroot / dir / "Subfolder");
        expect_catalog(id, {image, "Z.iso"});
    }
}
void boundaries() {
    for (int id : {1, 2, 3, 6}) {
        std::string dir = "CD" + std::to_string(id);
        for (int length : {31, 32, 33, 59}) {
            std::string name = std::string(length - 4, 'A') + ".iso";
            create(dir + "/" + name, 1); expect_catalog(id, {name});
            fs::remove(sdroot / dir / name);
        }
    }
}
void capacity() {
    for (int id : {1, 2, 3, 6}) {
        std::string dir = "CD" + std::to_string(id);
        std::vector<std::string> names;
        for (int i = 0; i < 100; ++i) {
            char name[20]; std::snprintf(name, sizeof(name), "%03d.iso", i);
            names.emplace_back(name); create(dir + "/" + name, i + 1);
        }
        expect_catalog(id, names);
        create(dir + "/101.iso", 101); command(id, 0xda);
        check(scsiDev.status == CHECK_CONDITION && scsiDev.phase == STATUS,
              "101 images still report explicit overflow");
    }
}
void seed_old(int id) {
    create("old.iso", 77); check(images[id].file.open("old.iso"), "old image open");
    images[id].opened = "old.iso"; images[id].ejected = false;
    images[id].reinsert_after_eject = false; images[id].cdrom_events = 0;
}
void old_preserved(int id, int opens, int audio) {
    check(switch_calls == opens && audio_calls == audio, "reject before switch/audio side effects");
    check(images[id].opened == "old.iso" && images[id].file.isOpen(), "old image retained");
    check(!images[id].ejected && !images[id].reinsert_after_eject && !images[id].cdrom_events,
          "rejected request retains media flags");
    check(first_byte(id) == 77, "old contents still readable");
}
void paths() {
    // Exact63-byte input fits;64 bytes has no terminator inside the old array.
    std::string fit = "CD1/" + std::string(55, 'A') + ".iso";
    check(fit.size() == 63, "boundary fixture length");
    create(fit, 1); check(switchNextImage(images[1], fit.c_str()), "63-byte path accepted");
    for (int length : {64, 65, 127, 128, 255}) {
        seed_old(1); int opens = switch_calls, audio = audio_calls;
        std::string path = fit + std::string(length - 63, 'B');
        check(!switchNextImage(images[1], path.c_str()), "overlong direct path rejected");
        old_preserved(1, opens, audio);
    }
    // The automatic cycle path must retain its established behavior.
    images[1].cycle = {fit};
    check(switchNextImage(images[1], nullptr), "automatic image cycling retained");
}
void command_errors() {
    for (int length : {60, 61, 63, 64, 100, 127}) {
        fs::remove_all(sdroot / "CD1");
        std::string name = std::string(length - 4, 'A') + ".iso";
        create("CD1/" + name, 1); seed_old(1);
        int opens = switch_calls, audio = audio_calls;
        command(1, 0xd8);
        check(scsiDev.status == CHECK_CONDITION && scsiDev.phase == STATUS && scsiDev.dataLen == 0,
              "D8 overlong path reports CHECK CONDITION");
        check(scsiDev.target->sense.code == ILLEGAL_REQUEST && scsiDev.target->sense.asc == INVALID_FIELD_IN_CDB,
              "D8 error supplies sense");
        old_preserved(1, opens, audio);
    }
    fs::remove_all(sdroot / "CD1"); create("CD1/valid.iso", 1); seed_old(1);
    int opens = switch_calls, audio = audio_calls;
    command(1, 0xd8, 99);
    check(scsiDev.status == CHECK_CONDITION, "invalid index reports error");
    old_preserved(1, opens, audio);
    force_open_fail = true; command(1, 0xd8, 0);
    check(scsiDev.status == CHECK_CONDITION && scsiDev.phase == STATUS, "failed open result propagated");
    // The original switcher closes before a real I/O failure; no rollback claim.
}
void expect_switch_error(int id, int index, const char *kind) {
    command(id, 0xd8, index);
    std::cout << "SWITCH_ERROR id=" << id << " kind=" << kind
              << " status=" << scsiDev.status << " phase=" << scsiDev.phase
              << " data=" << scsiDev.dataLen << " sense=" << scsiDev.target->sense.code
              << " asc=" << scsiDev.target->sense.asc
              << " backing_open=" << images[id].file.isOpen() << "\n";
    check(scsiDev.status == CHECK_CONDITION, "BUG137 failed D8 must report CHECK CONDITION");
    check(scsiDev.phase == STATUS && scsiDev.dataLen == 0, "failed D8 has no DATA IN phase");
    check(scsiDev.target->sense.code == ILLEGAL_REQUEST && scsiDev.target->sense.asc == INVALID_FIELD_IN_CDB,
          "failed D8 supplies error sense");
}
void switch_failures(const std::string &kind) {
    for (int id : {1, 2, 3, 6}) {
        std::string dir = "CD" + std::to_string(id);
        create(dir + "/A.iso", 1); create(dir + "/B.iso", 2); seed_old(id);
        int opens = switch_calls, audio = audio_calls;
        if (kind == "index") {
            expect_switch_error(id, 255, "invalid-index");
            old_preserved(id, opens, audio);
        } else if (kind == "missing") {
            fs::remove_all(sdroot / dir);
            expect_switch_error(id, 0, "missing-directory");
            old_preserved(id, opens, audio);
            create(dir + "/A.iso", 1); create(dir + "/B.iso", 2);
        } else if (kind == "open") {
            force_open_fail = true;
            expect_switch_error(id, 1, "backing-open-failed");
            check(switch_calls == opens + 1, "valid index reached the real switch function");
            check(!images[id].file.isOpen(), "upstream closes old backing before an actual open failure");
            check(!images[id].ejected && !images[id].reinsert_after_eject && !images[id].cdrom_events,
                  "failed open does not publish successful-media flags");
            force_open_fail = false;
        } else throw std::runtime_error("unknown switch-failure kind");
        // An explicit command after failure must mount the requested image,
        // clear the command error and retain normal native eject/attention flow.
        command(id, 0xd8, 1);
        check(scsiDev.status == 0 && scsiDev.phase == STATUS && scsiDev.dataLen == 0,
              "explicit retry succeeds without a data transfer");
        check(images[id].opened == dir + "/B.iso" && first_byte(id) == 2,
              "retry mounts exact requested backing image");
        check(images[id].ejected && images[id].reinsert_after_eject && images[id].cdrom_events == 2,
              "successful retry publishes media-change flags");
        cdromCloseTray(images[id]);
        check(!images[id].ejected && scsiDev.targets[id].unitAttention == NOT_READY_TO_READY_TRANSITION_MEDIUM_MAY_HAVE_CHANGED,
              "normal tray close posts unit attention after retry");
    }
}
int main(int argc, char **argv) {
    try {
        if (argc != 4) throw std::runtime_error("root scenario getName-mode required");
        sdroot = fs::absolute(argv[1]); fs::create_directories(sdroot);
        get_name_mode = std::atoi(argv[3]);
        for (int i = 0; i < 8; ++i) {
            images[i].scsiId = i; scsiDev.targets[i].cfg = &images[i];
            settings[i].blockSize = 2048; images[i].deviceType = 2;
        }
        std::string scenario(argv[2]);
        if (scenario == "filters") filters();
        else if (scenario == "boundaries") boundaries();
        else if (scenario == "capacity") capacity();
        else if (scenario == "paths") paths();
        else if (scenario == "errors") command_errors();
        else if (scenario == "switch-index") switch_failures("index");
        else if (scenario == "switch-open") switch_failures("open");
        else if (scenario == "switch-missing") switch_failures("missing");
        else throw std::runtime_error("unknown scenario");
        std::cout << "PASS checks=" << checks << " scenario=" << scenario << "\n";
        return 0;
    } catch (const std::exception &e) {
        std::cerr << "FAIL checks=" << checks << " " << e.what() << "\n"; return 1;
    }
}
