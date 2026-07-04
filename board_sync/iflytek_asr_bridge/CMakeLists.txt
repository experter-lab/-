cmake_minimum_required(VERSION 3.8)
project(iflytek_asr_bridge)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(std_msgs REQUIRED)

set(IFLYTEK_SDK_DIR "/mnt/sdcard/iflytek_tts_df41b4a2" CACHE PATH "iFlytek SDK directory")
set(IFLYTEK_MSC_LIB_DIR "${IFLYTEK_SDK_DIR}/libs/arm64" CACHE PATH "iFlytek ARM64 library directory")

include_directories(
  ${CMAKE_CURRENT_SOURCE_DIR}
  ${IFLYTEK_SDK_DIR}/include
)

add_executable(iflytek_asr_bridge
  iflytek_asr_bridge.cpp
  linuxrec.c
  speech_recognizer.c
)

ament_target_dependencies(iflytek_asr_bridge rclcpp std_msgs)
target_link_directories(iflytek_asr_bridge PRIVATE ${IFLYTEK_MSC_LIB_DIR})
target_link_libraries(iflytek_asr_bridge msc asound rt dl pthread)

install(TARGETS iflytek_asr_bridge
  RUNTIME DESTINATION lib/${PROJECT_NAME}
)

ament_package()
