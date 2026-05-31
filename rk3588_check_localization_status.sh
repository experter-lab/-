#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

FAIL=0

check_node() {
  local node="$1"
  if ros2 node list 2>/dev/null | grep -qx "$node"; then
    echo "OK node $node"
  else
    echo "FAIL node $node"
    FAIL=1
  fi
}

check_lifecycle_active() {
  local node="$1"
  local state
  state="$(ros2 lifecycle get "$node" 2>/dev/null || true)"
  if echo "$state" | grep -q "active"; then
    echo "OK lifecycle $node $state"
  else
    echo "FAIL lifecycle $node ${state:-not_available}"
    FAIL=1
  fi
}

check_topic_publishers() {
  local topic="$1"
  local info
  info="$(ros2 topic info "$topic" 2>/dev/null || true)"
  if echo "$info" | grep -q "Publisher count: [1-9]"; then
    echo "OK topic $topic"
    echo "$info" | sed 's/^/  /'
  else
    echo "FAIL topic $topic"
    echo "$info" | sed 's/^/  /'
    FAIL=1
  fi
}

check_msg_once() {
  local topic="$1"
  local timeout_sec="$2"
  if timeout "${timeout_sec}s" ros2 topic echo "$topic" --once >/tmp/rk3588_status_msg.txt 2>/tmp/rk3588_status_msg.err; then
    echo "OK message $topic"
    head -20 /tmp/rk3588_status_msg.txt | sed 's/^/  /'
  else
    echo "FAIL message $topic"
    cat /tmp/rk3588_status_msg.err | sed 's/^/  /'
    FAIL=1
  fi
}

check_tf() {
  local parent="$1"
  local child="$2"
  timeout 5s ros2 run tf2_ros tf2_echo "$parent" "$child" >/tmp/rk3588_status_tf.txt 2>/tmp/rk3588_status_tf.err || true
  if grep -q "Translation:" /tmp/rk3588_status_tf.txt; then
    echo "OK tf $parent -> $child"
    head -18 /tmp/rk3588_status_tf.txt | sed 's/^/  /'
  else
    echo "FAIL tf $parent -> $child"
    cat /tmp/rk3588_status_tf.err | sed 's/^/  /'
    FAIL=1
  fi
}

echo "=== RK3588 localization status ==="
date
hostname
uptime

echo "--- device ---"
ls -l /dev/rplidar /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true

echo "--- disk ---"
df -h / /mnt/sdcard 2>/dev/null || df -h /

echo "--- ros nodes ---"
ros2 node list || true

check_node /sllidar_node
check_node /base_to_laser_tf
check_node /CLaserOdometry2DNode
check_node /map_server
check_node /amcl

check_lifecycle_active /map_server
check_lifecycle_active /amcl

check_topic_publishers /scan
check_topic_publishers /odom
check_topic_publishers /map
check_topic_publishers /amcl_pose
check_topic_publishers /particle_cloud

check_msg_once /scan 8
check_msg_once /odom 8
check_msg_once /amcl_pose 8

check_tf map odom
check_tf odom base_link
check_tf base_link laser

if [ "$FAIL" -eq 0 ]; then
  echo "RESULT OK localization stack is healthy"
else
  echo "RESULT FAIL localization stack has errors"
fi

exit "$FAIL"
