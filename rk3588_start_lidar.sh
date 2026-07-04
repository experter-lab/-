#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LIDAR_MOUNT_ENV="${LIDAR_MOUNT_ENV:-/mnt/sdcard/medicine_robot_data/config/lidar_mount.env}"
if [[ -f "$LIDAR_MOUNT_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$LIDAR_MOUNT_ENV"
fi

ros2 launch medicine_robot_bringup rk3588_lidar_bringup.launch.py \
  serial_port:=/dev/rplidar \
  serial_baudrate:=256000 \
  frame_id:=laser \
  enable_static_tf:=true \
  base_frame_id:=base_link \
  laser_x:=0.15 \
  laser_y:=0.00 \
  laser_z:=0.12 \
  laser_yaw:="${LIDAR_LASER_YAW:-0.0}" \
  range_min_filter:=0.55
