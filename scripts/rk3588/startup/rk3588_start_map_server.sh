#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
MAP_FILE="${1:-/mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_latest.yaml}"
ros2 run nav2_map_server map_server --ros-args -p yaml_filename:="${MAP_FILE}" &
MAP_PID=$!
sleep 2
ros2 lifecycle set /map_server configure
sleep 1
ros2 lifecycle set /map_server activate
wait "${MAP_PID}"
