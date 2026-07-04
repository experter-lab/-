#!/usr/bin/env bash
set -e

PORT=8085

if ss -ltn | grep -q ":${PORT} "; then
  echo "Web dashboard already running on port ${PORT}."
  ss -ltnp | grep ":${PORT}" || true
  exit 0
fi

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

if [ -x /mnt/sdcard/rk3588_start_m2_voice.sh ]; then
      ENABLE_M2_BRIDGE=false \
      TTS_BACKEND="${TTS_BACKEND:-iflytek_msc}" \
      APLAY_DEVICE="${APLAY_DEVICE:-plughw:CARD=Device,DEV=0}" \
      PULSE_SINK="${PULSE_SINK:-}" \
      CI1302_OPEN_DELAY_SEC="${CI1302_OPEN_DELAY_SEC:-3.0}" \
    /mnt/sdcard/rk3588_start_m2_voice.sh || true
fi

exec ros2 launch medicine_robot_bringup pc_delivery_demo.launch.py \
  web_port:=8085 \
  enable_vision_detector:=false \
  enable_voice_console:=false \
  enable_tts:=false \
  enable_aikit_esr:=false \
  enable_m2_voice_bridge:=false \
  navigation_backend:=nav2
