#!/usr/bin/env bash
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
pkill -f "static_transform_publisher.*base_link.*laser" 2>/dev/null
sleep 1
setsid nohup ros2 run tf2_ros static_transform_publisher \
  --x 0.15 --y 0.00 --z 0.12 \
  --roll 0.0 --pitch 0.0 --yaw 0.0 \
  --frame-id base_link --child-frame-id laser \
  --ros-args -r __node:=base_to_laser_tf \
  </dev/null > /tmp/static_tf_v3.log 2>&1 &
disown
echo "PID=$!"
sleep 3
echo
echo "=== verify ==="
ps -ef | grep static_transform | grep -v grep
echo
echo "=== TF ==="
timeout 3 ros2 run tf2_ros tf2_echo base_link laser -r 1 2>&1 | grep -A 1 'Translation' | head -3
