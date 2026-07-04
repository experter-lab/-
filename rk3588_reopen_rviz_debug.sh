#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

pkill -f "robot_debug_footprint_pub.py" || true
nohup python3 /mnt/sdcard/medicine_robot_data/scripts/robot_debug_footprint_pub.py \
  > /tmp/rk3588_robot_debug_footprint.log 2>&1 &
echo "[rviz-debug] footprint pid: $!"

pkill -f "rviz2" || true
sleep 2

XAUTHORITY_FILE="$(ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -n 1)"
DISPLAY=:0 \
XDG_RUNTIME_DIR=/run/user/1000 \
XAUTHORITY="$XAUTHORITY_FILE" \
LIBGL_ALWAYS_SOFTWARE=1 \
QT_OPENGL=software \
MESA_LOADER_DRIVER_OVERRIDE=llvmpipe \
nohup rviz2 -d /mnt/sdcard/medicine_robot_data/config/rk3588_nav2_view.rviz \
  > /tmp/rk3588_rviz_localization.log 2>&1 &
echo "[rviz-debug] rviz pid: $!"

sleep 3
echo "[rviz-debug] visible debug topics:"
ros2 topic info /robot_debug_footprint || true
echo "[rviz-debug] key nodes:"
ros2 node list | sort | grep -E "cartographer|static_map|rviz|sllidar|base_to_laser|robot_debug|chassis" || true
