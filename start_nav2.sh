#!/usr/bin/env bash
# 启动 Nav2 导航栈 (配合 Cartographer localization)
# carto 已在后台提供 map->odom->base_link TF + /map topic
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PARAMS=/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml
LOG=/tmp/rk3588_nav2_navigation.log

echo "==> params: $PARAMS"
echo "==> checking prerequisites:"
echo -n "  /map topic: "
timeout 2 ros2 topic info /map 2>&1 | grep -q "Publisher count: 1" && echo "OK" || echo "MISSING"
echo -n "  cartographer_node: "
ros2 node list 2>/dev/null | grep -q cartographer_node && echo "OK" || echo "MISSING"
echo -n "  chassis_bridge: "
ros2 node list 2>/dev/null | grep -q chassis_bridge && echo "OK" || echo "MISSING"

echo
echo "==> stopping any existing Nav2"
pkill -f "nav2_" || true
pkill -f "bt_navigator" || true
pkill -f "planner_server" || true
pkill -f "controller_server" || true
sleep 2

echo "==> launching Nav2 bringup"
nohup ros2 launch nav2_bringup navigation_launch.py \
  params_file:="$PARAMS" \
  use_sim_time:=false \
  autostart:=true \
 \
  > "$LOG" 2>&1 &
echo "PID=$!"
sleep 8

echo
echo "==> checking Nav2 actions (30s timeout)"
for i in $(seq 1 30); do
  if ros2 action list 2>/dev/null | grep -q navigate_to_pose; then
    echo "✓ /navigate_to_pose available"
    break
  fi
  sleep 1
  echo -n "."
done

ros2 action list 2>/dev/null

echo
echo "==> log tail:"
tail -40 "$LOG" | grep -iE "error|warn|info.*config|lifecycle|activate" | tail -20
