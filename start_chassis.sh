#!/usr/bin/env bash
# 启动 chassis_bridge_node（后台）
# 不用 set -u（ROS setup.bash 会引用未绑定变量）
set -eo pipefail

LOG=/tmp/chassis_bridge.log
YAML=/mnt/sdcard/medicine_robot_ws/install/medicine_chassis_bridge/share/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml

echo "==> kill any existing chassis_bridge_node"
pkill -f chassis_bridge_node || true
sleep 1

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "==> ttyS9 status:"
ls -l /dev/ttyS9

echo "==> launching node, log: $LOG"
nohup ros2 run medicine_chassis_bridge chassis_bridge_node \
  --ros-args --params-file "$YAML" \
  > "$LOG" 2>&1 &

NEWPID=$!
echo "PID=$NEWPID"
sleep 4

echo "==> running processes:"
ps -ef | grep chassis_bridge_node | grep -v grep || echo "(none)"

echo "==> last log lines:"
tail -30 "$LOG" || true
