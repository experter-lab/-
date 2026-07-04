#!/usr/bin/env bash
# 重启 static_transform_publisher,让 base_link→laser 在 carto 起来之后再发一遍 (transient_local latched 消息)
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

pkill -f "static_transform_publisher.*base_link.*laser" 2>/dev/null
sleep 1

nohup ros2 run tf2_ros static_transform_publisher \
  --x 0.15 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link --child-frame-id laser \
  --ros-args -r __node:=base_to_laser_tf_v2 \
  > /tmp/static_tf_v2.log 2>&1 &
echo "PID=$!"
sleep 3

echo "==> /tf rate"
timeout 5 ros2 topic hz /tf 2>&1 | tail -3
echo "==> submap_list"
timeout 2 ros2 topic echo /submap_list --once 2>&1 | head -10
echo "==> map -> base_link"
timeout 3 ros2 run tf2_ros tf2_echo map base_link --once 2>&1 | head -10
