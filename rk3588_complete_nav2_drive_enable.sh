#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "[drive-enable-complete] refresh authorization"
timeout 12 ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool "{data: true}" || true
sleep 1

echo "[drive-enable-complete] clear emergency stop"
timeout 12 ros2 service call /chassis_bridge/set_emergency_stop std_srvs/srv/SetBool "{data: false}" || true
sleep 1

echo "[drive-enable-complete] set MANUAL"
timeout 12 ros2 service call /chassis_bridge/set_mode std_srvs/srv/SetBool "{data: true}" || true
sleep 1

echo "[drive-enable-complete] arm"
timeout 12 ros2 service call /chassis_bridge/arm std_srvs/srv/SetBool "{data: true}" || true
sleep 2

echo "[drive-enable-complete] status"
timeout 8 ros2 topic echo /medicine/chassis_status --once --field data
