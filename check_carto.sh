#!/usr/bin/env bash
# 验证 carto 建图状态
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "=== TF map -> base_link ==="
timeout 3 ros2 run tf2_ros tf2_echo map base_link 2>&1 | head -20

echo
echo "=== /map rate 5s ==="
timeout 5 ros2 topic hz /map 2>&1 | tail -3

echo
echo "=== /submap_list ==="
timeout 3 ros2 topic echo /submap_list --once 2>&1 | head -8
