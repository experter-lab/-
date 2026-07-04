#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

call_bool_once() {
  local service="$1"
  local value="$2"
  local label="$3"
  local timeout_sec="${4:-5}"
  timeout "$timeout_sec" ros2 service call "$service" std_srvs/srv/SetBool "{data: $value}" >/tmp/rk3588_safe_stop_last_call.log 2>&1 || return 1
}

for _ in 1 2 3 4 5; do
  ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{}" >>/tmp/rk3588_safe_stop_zero_cmd.log 2>&1 || true
  sleep 0.05
done

call_bool_once /chassis_bridge/set_mode false "set_mode=HOLD" 5 || true
call_bool_once /chassis_bridge/arm false "arm=DISARM" 5 || true
call_bool_once /chassis_bridge/set_emergency_stop true "emergency_stop=true" 5 || true
call_bool_once /chassis_bridge/authorize_control false "authorize_control=false" 5 || true

echo "[safe-stop] zero cmd burst, HOLD, DISARM, emergency_stop=true, authorization=false"
