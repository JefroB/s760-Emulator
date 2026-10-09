#pragma once

// =============================================================================
//  s760_backend_selector.hpp
//
//  Backend selection factory (spec `mame-live-backend`, task 9.1).
//
//  The S760Bridge is driven by exactly ONE IS760Host backend for its whole
//  lifetime (Requirement 7.1). Two backends exist behind the one contract:
//
//    * Core_Backend : s760::S760LibretroHost  (always linkable in this build)
//    * MAME_Backend : s760::S760MameHost       (available iff s760224.img loads)
//
//  This module is the documented selection seam (Requirement 7.3). It:
//
//    * determines the REQUESTED backend from (a) a compile-time default
//      (`S760_BACKEND_DEFAULT`, compile-defined from the CMake cache option
//      `S760_BACKEND=core|mame`) and/or (b) an optional runtime config value
//      (an enum, or a string "core"/"mame"/"" where "" means "use the build
//      default");
//    * defaults to Core when no selection is supplied (Requirement 7.3);
//    * when MAME is requested but UNAVAILABLE, FALLS BACK to Core and records
//      the fallback (Requirement 7.4);
//    * when BOTH backends are unavailable, sets `bothUnavailable`, leaves `host`
//      null, populates an observable `error` message, and returns WITHOUT
//      crashing so the caller can surface the error and terminate backend
//      startup (Requirement 7.5).
//
//  The caller HOLDS the returned `host` for the Bridge's lifetime, keeping the
//  selection fixed (Requirement 7.1).
//
//  TESTABILITY (task 9.2)
//  ----------------------
//  "Availability" of a backend means its init() succeeded (image/artifacts
//  present). To make 7.4/7.5 deterministically unit-testable WITHOUT the real
//  s760224.img, the core factory takes two injectable factory callbacks
//  (`make_core`, `make_mame`), each returning a constructed+init()'d
//  std::unique_ptr<IS760Host> or nullptr to represent "unavailable". The
//  production overload wires those callbacks to the real backends.
//
//  Note on Core availability: S760LibretroHost::init() returns is_system_running(),
//  which is false unless a core+system are loaded, so init() alone cannot be the
//  production Core-availability signal. At the library level the Core backend is
//  ALWAYS present (it is always linkable), so the production make_core treats
//  "constructed successfully" as "available" — it returns the host regardless of
//  whether a game is loaded. Tests use their own make_core/make_mame callbacks to
//  simulate each availability combination directly.
// =============================================================================

// Pull in IS760Host via s760_libretro_host.hpp so the mutual VideoFrame /
// IS760Host include ordering stays well-formed (that header defines VideoFrame
// before including the interface, matching how s760_mame_host.hpp does it).
#include "s760/s760_libretro_host.hpp"

#include <functional>
#include <memory>
#include <string>

namespace s760 {

// Which backend. Mirrors the design "Backend selection model".
enum class BackendKind { Core, Mame };

// Result of a selection attempt. Holds the constructed, init()'d backend the
// caller keeps for the Bridge lifetime, plus observable status fields.
struct BackendSelectionResult {
    BackendKind requested = BackendKind::Core; // what was asked for (R7.3)
    BackendKind active    = BackendKind::Core; // the backend actually selected
    bool fellBackToCore   = false;             // MAME requested but unavailable (R7.4)
    bool bothUnavailable  = false;             // neither backend available (R7.5)
    std::string error;                         // observable error message (R7.5)
    std::unique_ptr<IS760Host> host;           // the live backend (null iff bothUnavailable)
};

// A backend factory callback: construct + init() a backend and return it, or
// return nullptr to signal the backend is UNAVAILABLE. Represents the
// availability of exactly one backend. The production factory wires these to
// the real S760LibretroHost / S760MameHost; tests inject their own to simulate
// availability without real artifacts.
using HostFactory = std::function<std::unique_ptr<IS760Host>()>;

// The compile-time build default, driven by the CMake cache option
// `S760_BACKEND`. core/CMakeLists.txt compile-defines S760_BACKEND_DEFAULT to
// the token `core` or `mame`; this header maps that token to a BackendKind.
// When the macro is unset (unexpected), default to Core (Requirement 7.3).
#ifndef S760_BACKEND_DEFAULT
#define S760_BACKEND_DEFAULT core
#endif

namespace detail {
// Stringize the S760_BACKEND_DEFAULT token so it can be compared as text.
#define S760_BACKEND_STRINGIZE_IMPL(x) #x
#define S760_BACKEND_STRINGIZE(x) S760_BACKEND_STRINGIZE_IMPL(x)
inline constexpr const char* kBuildDefaultToken = S760_BACKEND_STRINGIZE(S760_BACKEND_DEFAULT);
#undef S760_BACKEND_STRINGIZE
#undef S760_BACKEND_STRINGIZE_IMPL
} // namespace detail

// The backend chosen at build time by the CMake `S760_BACKEND` option
// (default Core when the token is unrecognized / unset). Requirement 7.3.
BackendKind build_default_backend();

// Parse a runtime selection string into a requested BackendKind, using
// `build_default` when the string is empty (""), null-equivalent, or
// unrecognized. Case-insensitive; "core" -> Core, "mame" -> Mame. This is the
// documented runtime-config entry point (Requirement 7.3).
BackendKind parse_requested_backend(const std::string& value,
                                    BackendKind build_default);

// -----------------------------------------------------------------------------
//  Core (testable) factory
//
//  Selects a backend using the two injectable availability callbacks:
//
//    * requested == Core : try make_core(); if it returns a host -> active Core.
//                          if make_core() returns null -> bothUnavailable (there
//                          is nothing to fall back to), error populated, host null.
//    * requested == Mame : try make_mame(); if it returns a host -> active Mame.
//                          if make_mame() returns null -> FALL BACK: try
//                          make_core(); if that returns a host -> active Core,
//                          fellBackToCore=true (R7.4). If make_core() ALSO
//                          returns null -> bothUnavailable, error populated,
//                          host null (R7.5).
//
//  Never crashes/throws for an unavailable backend. The returned host (when
//  non-null) is already init()'d by its factory and is held by the caller for
//  the Bridge lifetime (R7.1).
// -----------------------------------------------------------------------------
BackendSelectionResult select_backend(BackendKind requested,
                                      const HostFactory& make_core,
                                      const HostFactory& make_mame);

// -----------------------------------------------------------------------------
//  Production factory (wires the real backends)
//
//  make_core  : constructs an S760LibretroHost (always available at the library
//               level) and returns it (does NOT require a loaded game).
//  make_mame  : constructs an S760MameHost, resolving s760224.img from
//               `roms_dir` (empty => the host resolves via S760_ROMS_DIR / its
//               relative defaults); returns the host iff init() succeeds (image
//               present + readable), otherwise nullptr (unavailable).
//
//  `requested` chooses the backend; the three selection overloads below cover
//  the common entry points:
//    (a) explicit BackendKind,
//    (b) runtime string + build default (empty string => build default),
//    (c) no argument => build default (Requirement 7.3 "default when unset").
// -----------------------------------------------------------------------------
BackendSelectionResult select_backend(BackendKind requested,
                                      const std::string& roms_dir = std::string());

BackendSelectionResult select_backend(const std::string& runtime_value,
                                      const std::string& roms_dir = std::string());

BackendSelectionResult select_backend();

} // namespace s760
