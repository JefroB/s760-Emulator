cmake_minimum_required(VERSION 3.15)
project(s760_core VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# Static Core Library
add_library(s760_core STATIC
    src/s760_disk.cpp
    src/s760_dsp.cpp
    src/akai_disk.cpp
    src/s760_drive_manager.cpp
    src/s760_libretro_host.cpp
    src/s760_clap_plugin.cpp
    src/s760_vst_plugin.cpp
    src/s760_vst3_plugin.cpp
)

target_include_directories(s760_core PUBLIC
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:include>
)

# VST3 Plugin Shared Library (.vst3)
add_library(s760_vst3 MODULE
    src/s760_vst3_plugin.cpp
)
target_link_libraries(s760_vst3 PRIVATE s760_core)
set_target_properties(s760_vst3 PROPERTIES
    OUTPUT_NAME "Roland_S760"
    SUFFIX ".vst3"
)

# VST2 Plugin Shared Library (.dll)
add_library(s760_vst MODULE
    src/s760_vst_plugin.cpp
)
target_link_libraries(s760_vst PRIVATE s760_core)
set_target_properties(s760_vst PROPERTIES
    OUTPUT_NAME "Roland_S760"
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
