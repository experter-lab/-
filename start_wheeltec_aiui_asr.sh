#!/usr/bin/env bash
set -eo pipefail

pkill -f "ros2 run wheeltec_mic_aiui wheeltec_mic_aiui" 2>/dev/null || true

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

export LD_LIBRARY_PATH="/mnt/sdcard/medicine_robot_ws/src/wheeltec_mic_aiui/libs/arm64:${LD_LIBRARY_PATH:-}"

nohup ros2 run wheeltec_mic_aiui wheeltec_mic_aiui \
  >/tmp/wheeltec_mic_aiui_asr.log 2>&1 &

echo "$!"
