#!/usr/bin/env bash
# 唤醒底盘控制链路 - 4 步标准顺序
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

call() {
    local svc=$1; local data=$2; local label=$3
    echo "==> $label"
    ros2 service call "$svc" std_srvs/srv/SetBool "{data: $data}" 2>&1 | tail -3
    sleep 1
}

echo "=== Step 1/4: clear software estop ==="
call /chassis_bridge/set_emergency_stop false "set_emergency_stop=false"

echo
echo "=== Step 2/4: authorize control (L3 解锁) ==="
call /chassis_bridge/authorize_control true "authorize_control=true (30 min)"

echo
echo "=== Step 3/4: switch to MANUAL ==="
call /chassis_bridge/set_mode true "set_mode=true (MANUAL)"

echo
echo "=== Step 4/4: ARM ==="
call /chassis_bridge/arm true "arm=true"

echo
echo "=== verifying status ==="
sleep 1
bash /tmp/probe_chassis_status.sh
