cmake_minimum_required(VERSION 2.8.12)
project(test_package)

set(CMAKE_VERBOSE_MAKEFILE TRUE)

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake")
    include(${CMAKE_BINARY_DIR}/../conanbuildinfo.cmake)
    conan_basic_setup()
endif()

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake_targets")
    include(${CMAKE_BINARY_DIR}/../conanbuildinfo.cmake)
    conan_basic_setup(TARGETS)
endif()

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake_find_package")
    find_package(sfml REQUIRED)
endif()

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake_find_package_multi")
    find_package(sfml REQUIRED CONFIG)
endif()

add_executable(${PROJECT_NAME} test_package.cpp)

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake")
    target_link_libraries(${PROJECT_NAME} ${CONAN_LIBS})
endif()

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake_targets")
    target_link_libraries(${PROJECT_NAME} CONAN_PKG::sfml)
endif()

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake_find_package")
    target_link_libraries(${PROJECT_NAME} sfml::sfml)
endif()

if(CONAN_CMAKE_GENERATOR STREQUAL "cmake_find_package_multi")
    target_link_libraries(${PROJECT_NAME} sfml::sfml)
endif()

function(add_option option)
    if(${option})
        target_compile_definitions(${CMAKE_PROJECT_NAME} PRIVATE "${option}")
    endif()
endfunction()

add_option(WITH_WINDOW)
add_option(WITH_GRAPHICS)
add_option(WITH_AUDIO)
add_option(WITH_NETWORK)
