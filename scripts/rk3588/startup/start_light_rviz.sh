#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

AUTH_FILE="$(ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -n 1 || true)"
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/1000
if [[ -n "$AUTH_FILE" ]]; then
  export XAUTHORITY="$AUTH_FILE"
fi
export LIBGL_ALWAYS_SOFTWARE=1
export QT_OPENGL=software

pkill -f "rviz2 -d /mnt/sdcard/medicine_robot_data/config/rk3588_map_scan_light.rviz" || true
nohup rviz2 -d /mnt/sdcard/medicine_robot_data/config/rk3588_map_scan_light.rviz \
  >/tmp/rk3588_map_scan_light_rviz.log 2>&1 &
echo "$!"
