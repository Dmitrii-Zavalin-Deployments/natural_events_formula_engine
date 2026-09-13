cmake_minimum_required(VERSION 3.15)
project({add here your project name, e.g., NumericalSolver} CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Options for coverage and sanitizers (General engineering plumbing)
option(ENABLE_COVERAGE "Enable gcov coverage flags" OFF)
option(ENABLE_ASAN "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)

if(ENABLE_COVERAGE)
    add_compile_options(--coverage -O0 -g)
    add_link_options(--coverage)
endif()

if(ENABLE_ASAN)
    message(STATUS "Building with AddressSanitizer and UndefinedBehaviorSanitizer")
    add_compile_options(-fsanitize=address,undefined -fno-omit-frame-pointer -g)
    add_link_options(-fsanitize=address,undefined)
endif()

# Find standard required packages (GTest, OpenMP, Python, pybind11)
find_package(GTest REQUIRED)
find_package(Threads REQUIRED)
find_package(nlohmann_json REQUIRED)
find_package(OpenMP REQUIRED)
find_package(Python3 COMPONENTS Interpreter Development REQUIRED)
find_package(pybind11 CONFIG REQUIRED)

enable_testing()

# Global include directory configuration
include_directories({add here your repository's global include path, e.g., ${CMAKE_CURRENT_SOURCE_DIR}/cpp/include})

# ---------------------------------------------------------------------------
# 1. Core C++ Library Target
# ---------------------------------------------------------------------------
# {add here your core source file collection, e.g., file(GLOB_RECURSE CORE_SOURCES "cpp/src/*.cpp")}
# Exclude language bindings or gateway files from the core static library
# {add here filter rules if needed, e.g., list(FILTER CORE_SOURCES EXCLUDE REGEX "python_gate\\.cpp$")}

add_library({add here your core static library target name, e.g., core_library} STATIC {add here core source variable})

# Ensure position-independent code for safe linkage into shared binding modules
set_target_properties({add here your core static library target name} PROPERTIES POSITION_INDEPENDENT_CODE ON)

target_link_libraries({add here your core static library target name}
    PUBLIC
        OpenMP::OpenMP_CXX
)

# ---------------------------------------------------------------------------
# 2. C++ Unit Tests Target
# ---------------------------------------------------------------------------
# {add here your unit test source file collection, e.g., file(GLOB UNIT_TEST_SOURCES "cpp/cpp_unit_tests/*.cpp")}
add_executable({add here unit test executable name, e.g., unit_tests} {add here unit test source variable})

target_link_libraries({add here unit test executable name}
    PRIVATE
        GTest::gtest_main
        {add here your core static library target name}
        nlohmann_json::nlohmann_json
        OpenMP::OpenMP_CXX
        Threads::Threads
)

add_test(NAME {add here CTest unit test identifier} COMMAND {add here unit test executable name})

# ---------------------------------------------------------------------------
# 3. C++ Integration Tests Targets
# ---------------------------------------------------------------------------
# Copy any required binary or text fixtures into the build tree
# {add here test fixture copy commands, e.g., file(COPY cpp/cpp_integration_tests/data DESTINATION ${CMAKE_CURRENT_BINARY_DIR})}

add_executable({add here integration test target name}
    {add here path to integration test source file}
)
target_link_libraries({add here integration test target name}
    PRIVATE
        GTest::gtest_main
        {add here your core static library target name}
        nlohmann_json::nlohmann_json
        OpenMP::OpenMP_CXX
        Threads::Threads
)
add_test(NAME {add here CTest integration test identifier} COMMAND {add here integration test target name})

# ---------------------------------------------------------------------------
# 4. Python Pybind11 Extension Module Target
# ---------------------------------------------------------------------------
# {add here collection of all sources including bindings, e.g., file(GLOB ALL_CPP_SOURCES "cpp/src/*.cpp")}

pybind11_add_module({add here python extension module name, e.g., solver_cpp} MODULE {add here all source variable})

# Force compiled module output directly into repository root for native Python import discovery
set_target_properties({add here python extension module name} PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_DEBUG "${CMAKE_CURRENT_SOURCE_DIR}"
    LIBRARY_OUTPUT_DIRECTORY_RELEASE "${CMAKE_CURRENT_SOURCE_DIR}"
)

target_link_libraries({add here python extension module name} 
    PRIVATE 
        {add here your core static library target name} 
        OpenMP::OpenMP_CXX
)
