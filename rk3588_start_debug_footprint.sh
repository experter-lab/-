#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

pkill -f "robot_debug_footprint_pub.py" || true
nohup python3 /mnt/sdcard/medicine_robot_data/scripts/robot_debug_footprint_pub.py \
  > /tmp/rk3588_robot_debug_footprint.log 2>&1 &
echo "[footprint] pid: $!"
sleep 2
ros2 topic info /robot_debug_footprint || true
