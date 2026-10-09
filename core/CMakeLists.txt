cmake_minimum_required(VERSION 3.15)
project(s760_core VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# Backend selection build option (spec `mame-live-backend`, task 9.1 /
# Requirement 7.3). Chooses the backend the selector defaults to when no runtime
# config value is supplied. Allowed values: core | mame (default core). The
# chosen token is compile-defined as S760_BACKEND_DEFAULT on s760_core so the
# selector's build-option path (build_default_backend()) resolves it.
set(S760_BACKEND "core" CACHE STRING "Default backend: core|mame")
set_property(CACHE S760_BACKEND PROPERTY STRINGS core mame)
if (NOT S760_BACKEND STREQUAL "core" AND NOT S760_BACKEND STREQUAL "mame")
    message(WARNING "S760_BACKEND='${S760_BACKEND}' is not core|mame; defaulting to core")
    set(S760_BACKEND "core" CACHE STRING "Default backend: core|mame" FORCE)
endif()

# Static Core Library
add_library(s760_core STATIC
    src/s760_disk.cpp
    src/s760_dsp.cpp
    src/akai_disk.cpp
    src/s760_drive_manager.cpp
    src/s760_recorder.cpp
    src/s760_crt_gate.cpp
    src/s760_libretro_host.cpp
    src/s760_crt_normalize.cpp
    src/s760_lcd_raster.cpp
    src/s760_mame_host.cpp
    src/s760_backend_selector.cpp
    src/s760_bridge.cpp
    src/s760_webview_host.cpp
    src/s760_clap_plugin.cpp
    src/s760_vst_plugin.cpp
    src/s760_vst3_plugin.cpp
)

# Compile-define the chosen backend token so the selector's build-option path
# (S760_BACKEND_DEFAULT) resolves at compile time (Requirement 7.3).
target_compile_definitions(s760_core PUBLIC S760_BACKEND_DEFAULT=${S760_BACKEND})

target_include_directories(s760_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# Platform networking + threading for the in-process bridge's optional loopback
# WebSocket server (minimal self-contained RFC6455; no third-party dependency).
find_package(Threads REQUIRED)
target_link_libraries(s760_core PUBLIC Threads::Threads)
if (WIN32)
    target_link_libraries(s760_core PUBLIC ws2_32)
endif()

# VST3 Plugin Shared Library (.vst3)
add_library(s760_vst3 MODULE
    src/s760_vst3_plugin.cpp
)
target_link_libraries(s760_vst3 PRIVATE s760_core)
set_target_properties(s760_vst3 PROPERTIES
    OUTPUT_NAME "Roland_S760"
    SUFFIX ".vst3"
)

# VST2 Instrument Shared Library (.dll)
add_library(s760_vst MODULE
    src/s760_vst_main.cpp
)
target_link_libraries(s760_vst PRIVATE s760_core)
set_target_properties(s760_vst PROPERTIES
    OUTPUT_NAME "Roland_S760"
    SUFFIX ".dll"
)

# VST2 Audio Effect / Live Sampler Shared Library (.dll)
add_library(s760_vst_fx MODULE
    src/s760_vst_fx_main.cpp
)
target_link_libraries(s760_vst_fx PRIVATE s760_core)
set_target_properties(s760_vst_fx PROPERTIES
    OUTPUT_NAME "Roland_S760_FX"
    SUFFIX ".dll"
)

# CLAP Plugin Shared Library (.clap)
add_library(s760_clap MODULE
    src/s760_clap_plugin.cpp
)
target_link_libraries(s760_clap PRIVATE s760_core)
set_target_properties(s760_clap PROPERTIES
    OUTPUT_NAME "Roland_S760"
    SUFFIX ".clap"
)

# Mock Libretro Core (Shared Library for testing)
add_library(mock_core SHARED
    tests/mock_core.cpp
)
target_include_directories(mock_core PRIVATE include)

# Core Test Runner Executable
add_executable(s760_core_tests
    tests/test_core.cpp
)
target_link_libraries(s760_core_tests PRIVATE s760_core)
add_dependencies(s760_core_tests mock_core)

# Plugin Host Test Executable (VST3 + VST2 + CLAP)
add_executable(s760_plugin_tests
    tests/test_plugin_host.cpp
)
target_link_libraries(s760_plugin_tests PRIVATE s760_core)
add_dependencies(s760_plugin_tests mock_core)

# Bridge Loopback / Integration Test Executable (S760Bridge in-process API)
add_executable(s760_bridge_tests
    tests/test_bridge.cpp
)
target_link_libraries(s760_bridge_tests PRIVATE s760_core)

# Plugin WebView Editor Test Executable (VST3 IPlugView / VST2 effEditOpen /
# CLAP clap.gui, wired to the in-process S760Bridge — task 3.6)
add_executable(s760_plugin_editor_tests
    tests/test_plugin_editor.cpp
)
target_link_libraries(s760_plugin_editor_tests PRIVATE s760_core)

# Host Seam Compile/Link + Smoke Test Executable (IS760Host contract: proves
# both S760LibretroHost and a stub IS760Host build against the S760Bridge, and
# that PROTOCOL_VERSION == 1 with the protocol header unchanged —
# mame-live-backend task 1.4)
add_executable(s760_host_seam_tests
    tests/test_host_seam.cpp
)
target_link_libraries(s760_host_seam_tests PRIVATE s760_core)

# Backend Selector Unit Test Executable (mame-live-backend task 9.2;
# Requirements 7.1, 7.3, 7.4, 7.5). Drives the injectable
# select_backend(requested, make_core, make_mame) overload with stub
# HostFactory lambdas to deterministically exercise default-Core, explicit
# selection, MAME-unavailable fallback (R7.4), and both-unavailable error
# (R7.5) WITHOUT real s760224.img / MAME artifacts. Also checks
# parse_requested_backend token mapping and build_default_backend() == Core for
# this build. Runs with no MAME binary present (Requirement 8.5).
add_executable(s760_backend_selector_tests
    tests/test_backend_selector.cpp
)
target_link_libraries(s760_backend_selector_tests PRIVATE s760_core)

# CRT Gate Property Test Executable (mame-live-backend Property 3: CRT
# rasterization + VDP VRAM-activity inference gate — task 3.5)
add_executable(s760_prop_crt_gate_tests
    tests/test_prop_crt_gate.cpp
)
target_link_libraries(s760_prop_crt_gate_tests PRIVATE s760_core)

# Failed-Frame Property Test Executable (mame-live-backend task 6.3, Property 1:
# "Failed frame advance preserves surfaces"; Requirement 1.5). Drives
# S760MameHost::run_frame() on an uninitialized host (the failed-advance seam)
# and asserts the CRT/LCD surfaces exposed by get_latest_video_frame() /
# get_lcd_surface() stay byte-for-byte identical across >=100 failing advances.
# Runs with no MAME binary present (Requirement 8.5).
add_executable(s760_prop_failed_frame_tests
    tests/test_prop_failed_frame.cpp
)
target_link_libraries(s760_prop_failed_frame_tests PRIVATE s760_core)

# LCD Raster Property Test Executable (mame-live-backend task 3.7, Property 2:
# the LCD surface is a pure function of SED1335 VRAM with exact MONO1 160x64
# payload size — exercises the pure lcd_rasterize() transform with no MAME
# binary present)
add_executable(s760_prop_lcd_raster_tests
    tests/test_prop_lcd_raster.cpp
)
target_link_libraries(s760_prop_lcd_raster_tests PRIVATE s760_core)

# CRT Geometry Normalization Property Test Executable (design Property 4:
# "CRT geometry normalization fabricates no pixels"; Requirement 4.4 —
# mame-live-backend task 3.3). Exercises the pure s760::crt_line_double
# transform with no MAME binary present.
add_executable(s760_prop_crt_normalize_tests
    tests/test_prop_crt_normalize.cpp
)
target_link_libraries(s760_prop_crt_normalize_tests PRIVATE s760_core)

# Surface Suppression Property Test Executable (mame-live-backend task 4.3,
# Property 8: "Malformed-length surfaces are suppressed"; Requirement 5.6).
# Oracle-equivalence test of the documented emit_surface() suppression predicate
# (emit iff payload_len == bridge::payload_size(format,w,h)); runs with no MAME
# binary present (Requirement 8.5).
add_executable(s760_prop_surface_suppression_tests
    tests/test_prop_surface_suppression.cpp
)
target_link_libraries(s760_prop_surface_suppression_tests PRIVATE s760_core)

# Frame Round-Trip Property Test Executable (mame-live-backend task 4.2,
# Property 5: "Frame framing round-trip and payload-length rule"; Requirements
# 5.1, 5.5). Exercises the static S760Bridge::build_frame framing + the
# protocol payload-length rule with no MAME binary present.
add_executable(s760_prop_frame_roundtrip_tests
    tests/test_prop_frame_roundtrip.cpp
)
target_link_libraries(s760_prop_frame_roundtrip_tests PRIVATE s760_core)

# Backend-Identity Property Test Executable (mame-live-backend task 9.4,
# Property 6: "Framing and telemetry bytes are backend-independent";
# Requirements 5.2, 7.2). Drives two IS760Host stubs (a CoreLike + a MameLike
# stub) made to present IDENTICAL surface content + telemetry sources through
# two S760Bridge instances and asserts the emitted binary frames + telemetry are
# byte-for-byte identical regardless of which backend is active; also checks the
# static build_frame / encode_telemetry encoders are deterministic (they take no
# backend input). Runs with no MAME binary present (Requirement 8.5).
add_executable(s760_prop_backend_identity_tests
    tests/test_prop_backend_identity.cpp
)
target_link_libraries(s760_prop_backend_identity_tests PRIVATE s760_core)

# Telemetry Property Test Executable (mame-live-backend task 4.5, Property 7:
# "Telemetry carries fixed geometry and bounded fps"; Requirement 5.3).
# Exercises the static S760Bridge::encode_telemetry encoder: fixed geometry
# (crt 640x480, lcd 160x64, gotek 128x32) and fps bounded to [0,240]. Runs with
# no MAME binary present (Requirement 8.5).
add_executable(s760_prop_telemetry_tests
    tests/test_prop_telemetry.cpp
)
target_link_libraries(s760_prop_telemetry_tests PRIVATE s760_core)

# Dial-Delta Property Test Executable (mame-live-backend task 7.4, Property 10:
# "Dial delta is applied as a signed detent count"; Requirement 6.2). Exercises
# S760MameHost::apply_dial_delta (id-less + id-aware) and encoder_detents()
# across >= 100 seeded signed deltas; models the per-frame boundary by starting
# from a fresh/zero host. Runs with no MAME binary present (Requirement 8.5).
add_executable(s760_prop_dial_delta_tests
    tests/test_prop_dial_delta.cpp
)
target_link_libraries(s760_prop_dial_delta_tests PRIVATE s760_core)

# Button Matrix Property Test Executable (mame-live-backend task 7.2, Property 9:
# "Button press/release toggles exactly its matrix bit"; Requirement 6.1).
# Exercises S760MameHost::apply_button / key_matrix with a dual-port expected
# model so "exactly that bit; all other bits unchanged" is verified; runs with
# no MAME binary present (Requirement 8.5).
add_executable(s760_prop_button_matrix_tests
    tests/test_prop_button_matrix.cpp
)
target_link_libraries(s760_prop_button_matrix_tests PRIVATE s760_core)

# currentMode Telemetry Unit Test Executable (mame-live-backend task 4.6,
# Requirement 5.4): the Bridge reports currentMode as the EMPTY string when it
# is not derivable (never an invented default), and reports a derived mode
# verbatim at the telemetry-encoding boundary. Unit test (not a property test);
# runs with no MAME binary present (Requirement 8.5).
add_executable(s760_currentmode_tests
    tests/test_currentmode.cpp
)
target_link_libraries(s760_currentmode_tests PRIVATE s760_core)

# OLED Sizing Unit Test Executable (mame-live-backend task 6.5, Requirement
# 4.7): the OLED_Surface (SurfaceId::OLED, Gotek drive-bay readout) is
# React-owned and emitted by the Bridge as an authentic-blank 128x32 MONO1
# surface whose payload length equals payload_size(MONO1, 128, 32) == 512.
# Unit test (not a property test); runs with no MAME binary present.
add_executable(s760_oled_sizing_tests
    tests/test_oled_sizing.cpp
)
target_link_libraries(s760_oled_sizing_tests PRIVATE s760_core)

# Pointer Scaling Property Test Executable (mame-live-backend task 7.6,
# Property 11: "Pointer coordinates scale deterministically into the VDP mouse
# registers"; Requirement 6.3). Exercises S760MameHost::apply_pointer absolute
# normalized->pixel scaling (std::lround into regs 0x20/0x21/0x22/0x24) and
# reconstruction via pointer_x_pixels()/pointer_y_pixels(); runs with no MAME
# binary present (Requirement 8.5).
add_executable(s760_prop_pointer_scaling_tests
    tests/test_prop_pointer_scaling.cpp
)
target_link_libraries(s760_prop_pointer_scaling_tests PRIVATE s760_core)

# Invalid-Input Ignore Property Test Executable (mame-live-backend task 7.8,
# Property 12: "Invalid input is ignored without state change"; Requirement
# 6.4). Exercises S760MameHost::apply_pointer (out-of-range / NaN / inf),
# apply_button (unknown id), and apply_dial_delta(id,delta) (unknown encoder id)
# and asserts the full input snapshot (both key-matrix bytes, encoder_detents(),
# and the 256-byte VDP register file) stays byte-for-byte unchanged; runs with
# no MAME binary present (Requirement 8.5).
add_executable(s760_prop_invalid_input_tests
    tests/test_prop_invalid_input.cpp
)
target_link_libraries(s760_prop_invalid_input_tests PRIVATE s760_core)

# MIDI Routing + Mount Unit Test Executable (mame-live-backend task 7.10,
# Requirements 6.6, 6.7, 6.8): S760MameHost MIDI NOTE_ON/NOTE_OFF delivery via
# send_midi_message()/midi_in_bytes(), successful mount_disk() of a valid image,
# and bad-path handling that keeps the current image and never crashes/throws.
# Unit test (not a property test); runs with no MAME binary present.
add_executable(s760_midi_mount_tests
    tests/test_midi_mount.cpp
)
target_link_libraries(s760_midi_mount_tests PRIVATE s760_core)

# Build/Smoke Test Executable (mame-live-backend task 10.5; Requirements 1.1,
# 1.6, 6.5, 8.1, 8.2, 8.5). Mixes in-process behavioral smoke with static
# source checks: (1) process model — no child process spawned; (2) Python-free
# runtime TUs; (3) pointer path uses absolute normalized->pixel scaling (no
# wrapped 8-bit deltas); (4) host-only framing/decode/sizing with no MAME binary
# present. The static scans open the runtime .cpp/.hpp deterministically via the
# S760_CORE_SRC_DIR compile definition below. R8.1 (build) is validated by this
# target compiling + linking + running with zero exit status.
add_executable(s760_smoke_build_tests
    tests/test_smoke_build.cpp
)
target_link_libraries(s760_smoke_build_tests PRIVATE s760_core)
target_compile_definitions(s760_smoke_build_tests
    PRIVATE S760_CORE_SRC_DIR="${CMAKE_CURRENT_SOURCE_DIR}")

# Python Bindings Module
find_package(Python 3.13 COMPONENTS Interpreter Development REQUIRED)
if (Python_FOUND)
    execute_process(
        COMMAND "${Python_EXECUTABLE}" -m pybind11 --cmakedir
        OUTPUT_VARIABLE pybind11_DIR
        OUTPUT_STRIP_TRAILING_WHITESPACE
        RESULT_VARIABLE pybind11_RESULT
    )
    message(STATUS "pybind11_DIR: ${pybind11_DIR}")
    find_package(pybind11 CONFIG REQUIRED)
    pybind11_add_module(s760_cpp src/bindings.cpp)
    target_link_libraries(s760_cpp PRIVATE s760_core)
    set_target_properties(s760_cpp PROPERTIES
        OUTPUT_NAME "s760_cpp"
        LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../tests"
        RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/../tests"
    )
endif()
