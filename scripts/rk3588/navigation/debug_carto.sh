#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/cartographer_debug.log

echo "==> kill cartographer_node"
pkill -f cartographer_node
sleep 2

CONF=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config

# 用 ros2 run + 调高 verbosity
nohup ros2 run cartographer_ros cartographer_node \
  -configuration_directory "$CONF" \
  -configuration_basename rk3588_carto_mapping.lua \
  --ros-args -r scan:=/scan --log-level debug \
  > "$LOG" 2>&1 &
echo "PID=$!"

sleep 6
echo
echo "==> log tail (error/warn 过滤):"
grep -E 'WARN|ERROR|reject|skip|dropping|fail|cannot|invalid|timeout' "$LOG" | head -30 || echo "(no warns)"
echo
echo "==> log tail all 30:"
tail -30 "$LOG"
echo
echo "==> rosgraph node info cartographer_node:"
ros2 node info /cartographer_node 2>&1 | head -40
