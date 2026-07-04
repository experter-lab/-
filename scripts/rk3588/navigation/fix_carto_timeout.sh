#!/usr/bin/env bash
# 把 lookup_transform_timeout_sec 拉大,解决 carto 静默丢 scan 问题
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LUA=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config/rk3588_carto_mapping.lua

# 把 0.2 改成 1.0
sed -i 's/lookup_transform_timeout_sec = 0.2/lookup_transform_timeout_sec = 1.0/' "$LUA"

echo "==> changes:"
grep -E 'lookup_transform_timeout_sec|provide_odom_frame|published_frame|tracking_frame' "$LUA"

echo
echo "==> restart cartographer"
pkill -f cartographer_node
sleep 2
CONF=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config
LOG=/tmp/cartographer_t2.log
nohup ros2 run cartographer_ros cartographer_node \
  -configuration_directory "$CONF" \
  -configuration_basename rk3588_carto_mapping.lua \
  --ros-args -r scan:=/scan \
  > "$LOG" 2>&1 &
echo "PID=$!"

sleep 8
echo
echo "==> /tf rate"
timeout 5 ros2 topic hz /tf 2>&1 | tail -3
echo
echo "==> submap_list"
timeout 2 ros2 topic echo /submap_list --once 2>&1 | head -10
echo
echo "==> map -> base_link"
timeout 3 ros2 run tf2_ros tf2_echo map base_link --once 2>&1 | head -10
