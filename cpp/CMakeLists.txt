cmake_minimum_required(VERSION 3.16)
project(SentinelStatArbRuntime LANGUAGES CXX)
find_package(Threads REQUIRED)

add_executable(sentinel_engine sentinel_engine.cpp)
target_compile_features(sentinel_engine PRIVATE cxx_std_17)
target_compile_options(sentinel_engine PRIVATE -Wall -Wextra -Wpedantic)
target_link_libraries(sentinel_engine PRIVATE Threads::Threads)

add_executable(sentinel_core_tests test_core.cpp)
target_compile_features(sentinel_core_tests PRIVATE cxx_std_17)
target_compile_options(sentinel_core_tests PRIVATE -Wall -Wextra -Wpedantic)
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  target_compile_options(sentinel_core_tests PRIVATE -UNDEBUG)
endif()
target_link_libraries(sentinel_core_tests PRIVATE Threads::Threads)

enable_testing()
add_test(NAME sentinel_core_tests COMMAND sentinel_core_tests)

# Native ZeroMQ benchmarks are optional on machines without libzmq development files.
find_package(PkgConfig QUIET)
if(PkgConfig_FOUND)
  pkg_check_modules(LIBZMQ QUIET IMPORTED_TARGET libzmq)
endif()

if(TARGET PkgConfig::LIBZMQ)
  add_executable(sentinel_zmq_ipc_benchmark zmq_ipc_benchmark.cpp)
  target_compile_features(sentinel_zmq_ipc_benchmark PRIVATE cxx_std_17)
  target_compile_options(sentinel_zmq_ipc_benchmark PRIVATE -Wall -Wextra -Wpedantic)
  target_link_libraries(sentinel_zmq_ipc_benchmark PRIVATE PkgConfig::LIBZMQ Threads::Threads)

  add_executable(sentinel_zmq_ipc_oneway_benchmark zmq_ipc_oneway_benchmark.cpp)
  target_compile_features(sentinel_zmq_ipc_oneway_benchmark PRIVATE cxx_std_17)
  target_compile_options(sentinel_zmq_ipc_oneway_benchmark PRIVATE -Wall -Wextra -Wpedantic)
  target_link_libraries(sentinel_zmq_ipc_oneway_benchmark PRIVATE PkgConfig::LIBZMQ Threads::Threads)

  add_test(NAME sentinel_zmq_ipc_oneway_smoke
    COMMAND sentinel_zmq_ipc_oneway_benchmark --messages 500 --warmup 100)
  add_test(NAME sentinel_zmq_ipc_roundtrip_smoke
    COMMAND sentinel_zmq_ipc_benchmark --messages 500 --warmup 100)
endif()
