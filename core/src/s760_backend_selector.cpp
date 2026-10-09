// =============================================================================
//  s760_backend_selector.cpp
//
//  Backend selection factory implementation (spec `mame-live-backend`, task 9.1).
//  See s760_backend_selector.hpp for the full contract and the mapping of each
//  Requirement (7.1, 7.3, 7.4, 7.5) onto the behavior here.
// =============================================================================

#include "s760/s760_backend_selector.hpp"

#include "s760/s760_libretro_host.hpp"
#include "s760/s760_mame_host.hpp"

#include <cctype>
#include <memory>
#include <string>

namespace s760 {

namespace {

// Lower-case a copy of `s` for case-insensitive token comparison.
std::string to_lower(const std::string& s) {
    std::string out;
    out.reserve(s.size());
    for (char c : s) {
        out.push_back(static_cast<char>(
            std::tolower(static_cast<unsigned char>(c))));
    }
    return out;
}

} // namespace

BackendKind build_default_backend() {
    // detail::kBuildDefaultToken is the stringized S760_BACKEND_DEFAULT macro,
    // compile-defined from the CMake `S760_BACKEND` option. Only an exact
    // (case-insensitive) "mame" selects the MAME default; anything else
    // (including "core" and any unrecognized/unset token) defaults to Core
    // (Requirement 7.3).
    if (to_lower(detail::kBuildDefaultToken) == "mame") {
        return BackendKind::Mame;
    }
    return BackendKind::Core;
}

BackendKind parse_requested_backend(const std::string& value,
                                    BackendKind build_default) {
    const std::string v = to_lower(value);
    if (v == "core") return BackendKind::Core;
    if (v == "mame") return BackendKind::Mame;
    // Empty or unrecognized -> use the build default (Requirement 7.3: "when no
    // selection input is supplied, default to the Core_Backend" — the build
    // default is Core unless the build option overrode it).
    return build_default;
}

BackendSelectionResult select_backend(BackendKind requested,
                                      const HostFactory& make_core,
                                      const HostFactory& make_mame) {
    BackendSelectionResult result;
    result.requested = requested;

    if (requested == BackendKind::Mame) {
        // Try MAME first.
        std::unique_ptr<IS760Host> mame = make_mame ? make_mame() : nullptr;
        if (mame) {
            result.active = BackendKind::Mame;
            result.host = std::move(mame);
            return result;
        }

        // MAME unavailable -> FALL BACK to Core (Requirement 7.4).
        std::unique_ptr<IS760Host> core = make_core ? make_core() : nullptr;
        if (core) {
            result.active = BackendKind::Core;
            result.fellBackToCore = true;
            result.host = std::move(core);
            return result;
        }

        // Both unavailable (Requirement 7.5).
        result.active = BackendKind::Core;
        result.fellBackToCore = true;   // the fallback to Core was attempted
        result.bothUnavailable = true;
        result.host = nullptr;
        result.error =
            "Backend startup failed: MAME backend unavailable (s760224.img "
            "missing or unreadable) and the Core backend is also unavailable. "
            "No backend could be initialized.";
        return result;
    }

    // requested == Core: construct Core directly; there is nothing to fall back
    // to, so a null Core is the both-unavailable case (Requirement 7.5).
    std::unique_ptr<IS760Host> core = make_core ? make_core() : nullptr;
    if (core) {
        result.active = BackendKind::Core;
        result.host = std::move(core);
        return result;
    }

    result.active = BackendKind::Core;
    result.bothUnavailable = true;
    result.host = nullptr;
    result.error =
        "Backend startup failed: the Core backend is unavailable and no backend "
        "could be initialized.";
    return result;
}

namespace {

// Production make_core: the Core backend is ALWAYS available at the library
// level (always linkable). We construct an S760LibretroHost and return it
// regardless of whether a game/system is loaded; the selector treats a
// successful construction as "available". See the header's "Note on Core
// availability".
HostFactory production_make_core() {
    return []() -> std::unique_ptr<IS760Host> {
        return std::make_unique<S760LibretroHost>();
    };
}

// Production make_mame: construct the MAME adapter and return it ONLY when its
// init() succeeds (s760224.img present + readable). On any failure init()
// returns false WITHOUT spawning a process or terminating the host; we then
// return nullptr to signal "unavailable" so the selector falls back to Core
// (Requirement 7.4) or reports both-unavailable (Requirement 7.5).
HostFactory production_make_mame(const std::string& roms_dir) {
    return [roms_dir]() -> std::unique_ptr<IS760Host> {
        auto mame = std::make_unique<S760MameHost>(roms_dir);
        if (!mame->init()) {
            return nullptr; // unavailable: artifacts missing/unreadable
        }
        return mame;
    };
}

} // namespace

BackendSelectionResult select_backend(BackendKind requested,
                                      const std::string& roms_dir) {
    return select_backend(requested,
                          production_make_core(),
                          production_make_mame(roms_dir));
}

BackendSelectionResult select_backend(const std::string& runtime_value,
                                      const std::string& roms_dir) {
    const BackendKind requested =
        parse_requested_backend(runtime_value, build_default_backend());
    return select_backend(requested, roms_dir);
}

BackendSelectionResult select_backend() {
    // No selection supplied -> the build default (Core unless the CMake option
    // set mame). Requirement 7.3.
    return select_backend(build_default_backend(), std::string());
}

} // namespace s760
