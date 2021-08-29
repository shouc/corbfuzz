cmake_minimum_required(VERSION 3.8)
project(hsfuzz)
set(CMAKE_CXX_STANDARD 11)

add_compile_definitions(HAVE_SKELETON)

set(SOURCE_FILES php_hsfuzz hsfuzz.cc)

execute_process (
        COMMAND php-config --include-dir
        OUTPUT_VARIABLE PHP_SOURCE
)
string(REGEX REPLACE "\n$" "" PHP_SOURCE "${PHP_SOURCE}")

message("Using source directory: ${PHP_SOURCE}")

include_directories(${PHP_SOURCE})
include_directories(${PHP_SOURCE}/main)
include_directories(${PHP_SOURCE}/Zend)
include_directories(${PHP_SOURCE}/TSRM)
include_directories(..)
add_custom_target(configure
        COMMAND phpize && configure
        DEPENDS ${SOURCE_FILES}
        WORKING_DIRECTORY ..)

add_library(___ SHARED ${SOURCE_FILES})
