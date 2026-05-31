#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
PARAM_FILE="${1:-/mnt/sdcard/medicine_robot_data/config/rk3588_amcl_localization.yaml}"
ros2 run nav2_amcl amcl --ros-args --params-file "${PARAM_FILE}" &
AMCL_PID=$!
sleep 2
ros2 lifecycle set /amcl configure
sleep 1
ros2 lifecycle set /amcl activate
wait "${AMCL_PID}"
