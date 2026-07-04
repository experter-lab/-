#!/usr/bin/env bash
# 只重启 cartographer_node 不动雷达,让它在 base_link->laser TF 已经稳定之后再起
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/cartographer_restart.log

echo "==> kill cartographer_node (保留 sllidar + static TF + occupancy)"
pkill -f cartographer_node
sleep 2

CONF=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config

nohup ros2 run cartographer_ros cartographer_node \
  -configuration_directory "$CONF" \
  -configuration_basename rk3588_carto_mapping.lua \
  --ros-args -r scan:=/scan \
  > "$LOG" 2>&1 &
echo "PID=$!"

sleep 6
echo
echo "==> log tail:"
tail -20 "$LOG"
echo
echo "==> submap_list:"
timeout 2 ros2 topic echo /submap_list --once 2>&1 | head -8
echo
echo "==> /tf has dynamic frames?"
timeout 3 ros2 topic echo /tf --once 2>&1 | head -20
