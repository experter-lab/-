#!/usr/bin/env bash
# 修复 carto lua: 去掉 provide_odom_frame,让 carto 直接发 map->base_link
# 这台车没有任何 odom 来源,中间这层 odom_frame 反而触发 carto 不发 TF
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LUA=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config/rk3588_carto_mapping.lua
BAK="$LUA.bak.$(date +%s)"
cp "$LUA" "$BAK"
echo "==> backup: $BAK"

# 把 provide_odom_frame = true 改成 false
sed -i 's/provide_odom_frame = true/provide_odom_frame = false/' "$LUA"

echo "==> changes:"
grep -E 'provide_odom_frame|published_frame|odom_frame|tracking_frame' "$LUA"

echo
echo "==> restart cartographer"
pkill -f cartographer_node
sleep 2
CONF=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config
LOG=/tmp/cartographer_fix.log
nohup ros2 run cartographer_ros cartographer_node \
  -configuration_directory "$CONF" \
  -configuration_basename rk3588_carto_mapping.lua \
  --ros-args -r scan:=/scan \
  > "$LOG" 2>&1 &
echo "PID=$!"

sleep 8
echo
echo "==> /tf rate 5s"
timeout 5 ros2 topic hz /tf 2>&1 | tail -3
echo
echo "==> submap_list"
timeout 2 ros2 topic echo /submap_list --once 2>&1 | head -8
echo
echo "==> map -> base_link"
timeout 3 ros2 run tf2_ros tf2_echo map base_link --once 2>&1 | head -8
