#!/usr/bin/env bash
# 切到 Cartographer 纯定位模式
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LUA=/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config/rk3588_carto_localization.lua
PBSTREAM=/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream

echo "==> pbstream: $(du -h $PBSTREAM | cut -f1)"

# 修 localization lua 的 timeout (和 mapping 一样的问题)
if grep -q 'lookup_transform_timeout_sec = 0.2' "$LUA"; then
    sed -i 's/lookup_transform_timeout_sec = 0.2/lookup_transform_timeout_sec = 1.0/' "$LUA"
    echo "==> patched lookup_transform_timeout_sec to 1.0"
fi

# kill mapping 节点,保留雷达
echo "==> stopping mapping mode"
pkill -f cartographer_node || true
pkill -f cartographer_occupancy_grid || true
sleep 2

LOG=/tmp/cartographer_loc.log
echo "==> starting localization with $PBSTREAM"

nohup ros2 run cartographer_ros cartographer_node \
  -configuration_directory "$(dirname "$LUA")" \
  -configuration_basename rk3588_carto_localization.lua \
  -load_state_filename "$PBSTREAM" \
  -load_frozen_state true \
  --ros-args -r scan:=/scan \
  > "$LOG" 2>&1 &
echo "cartographer_node PID=$!"

sleep 8

echo "==> log tail:"
tail -10 "$LOG"

echo
echo "==> occupancy grid (重新起一个)"
pkill -f cartographer_occupancy_grid_node || true
sleep 1
nohup ros2 run cartographer_ros cartographer_occupancy_grid_node \
  -resolution 0.05 -publish_period_sec 1.0 \
  > /tmp/occ_grid.log 2>&1 &
echo "occ_grid PID=$!"

sleep 5

echo
echo "==> submap_list (应该看到加载的 submaps)"
timeout 2 ros2 topic echo /submap_list --once 2>&1 | head -15

echo
echo "==> /tf rate:"
timeout 3 ros2 topic hz /tf 2>&1 | tail -3

echo
echo "==> map -> base_link"
timeout 3 ros2 run tf2_ros tf2_echo map base_link -r 1 2>&1 | head -15

echo
echo "==> DONE - localization active"
