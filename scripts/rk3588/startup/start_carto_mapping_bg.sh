#!/usr/bin/env bash
# 后台启动 carto mapping(雷达 + carto + occupancy_grid)
# 用法: bash start_carto_mapping_bg.sh
# 不用 set -u: ROS setup.bash 引用未绑定变量

LOG=/tmp/rk3588_carto_mapping.log

echo "==> kill any leftover carto / sllidar processes"
pkill -f cartographer_node 2>/dev/null
pkill -f cartographer_occupancy_grid 2>/dev/null
pkill -f sllidar_node 2>/dev/null
pkill -f rk3588_carto_mapping 2>/dev/null
sleep 2

echo "==> /dev/rplidar:"
ls -l /dev/rplidar

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "==> launching carto mapping, log: $LOG"
nohup ros2 launch medicine_robot_bringup rk3588_carto_mapping.launch.py > "$LOG" 2>&1 &
echo "PID=$!"
sleep 8

echo "==> processes:"
ps -ef | grep -E 'cartographer|sllidar|occupancy_grid' | grep -v grep || echo "(none)"

echo
echo "==> /scan rate (3s window):"
timeout 3 ros2 topic hz /scan 2>&1 | tail -3 || true

echo
echo "==> last 20 log lines:"
tail -20 "$LOG"
