#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

node_exists() {
  ros2 node list 2>/dev/null | grep -qx "$1"
}

lifecycle_active() {
  ros2 lifecycle get "$1" 2>/dev/null | grep -q "active"
}

if node_exists /sllidar_node; then
  echo "sllidar_node already running"
else
  nohup ros2 launch medicine_robot_bringup rk3588_lidar_bringup.launch.py > /tmp/rk3588_lidar_bringup.log 2>&1 &
  echo "started sllidar bringup pid=$!"
fi

sleep 5

echo "starting guarded RF2O + IMU + EKF odom fusion"
/mnt/sdcard/rk3588_start_odom_fusion.sh

sleep 5

if lifecycle_active /map_server; then
  echo "map_server already active"
else
  nohup /mnt/sdcard/rk3588_start_map_server.sh > /tmp/rk3588_map_server.log 2>&1 &
  echo "started map_server pid=$!"
fi

sleep 6

if lifecycle_active /amcl; then
  echo "amcl already active"
else
  nohup /mnt/sdcard/rk3588_start_amcl.sh > /tmp/rk3588_amcl.log 2>&1 &
  echo "started amcl pid=$!"
fi

sleep 5
ros2 node list
