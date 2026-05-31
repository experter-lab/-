#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
mkdir -p /mnt/sdcard/medicine_robot_data/maps
stamp="$(date +%Y%m%d_%H%M%S)"
ros2 run nav2_map_server map_saver_cli -f "/mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_${stamp}"
cp "/mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_${stamp}.yaml" /mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_latest.yaml
cp "/mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_${stamp}.pgm" /mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_latest.pgm
ls -lh /mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_${stamp}.* /mnt/sdcard/medicine_robot_data/maps/a1_handheld_map_latest.*
