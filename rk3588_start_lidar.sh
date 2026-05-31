#!/usr/bin/env bash
set -euo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
ros2 launch medicine_robot_bringup rk3588_lidar_bringup.launch.py \
  serial_port:=/dev/rplidar \
  serial_baudrate:=115200 \
  frame_id:=laser \
  enable_static_tf:=true \
  base_frame_id:=base_link \
  laser_x:=0.10 \
  laser_y:=0.00 \
  laser_z:=0.12
