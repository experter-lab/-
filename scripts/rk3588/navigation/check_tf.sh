#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "=== /tf_static dump ==="
timeout 2 ros2 topic echo /tf_static --once 2>&1 | head -40

echo
echo "=== 全 tf frames (5s yaml) ==="
timeout 5 ros2 run tf2_tools view_frames 2>&1 | tail -10 || true

echo
echo "=== base_link -> laser ==="
timeout 3 ros2 run tf2_ros tf2_echo base_link laser 2>&1 | head -10

echo
echo "=== /scan frame_id (1帧) ==="
timeout 2 ros2 topic echo /scan --once --field header 2>&1 | head -10

echo
echo "=== carto log tail ==="
tail -30 /tmp/rk3588_carto_mapping.log
