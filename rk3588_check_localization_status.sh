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

check_any_node() {
  local label="$1"
  shift
  local node
  local nodes
  nodes="$(ros2 node list 2>/dev/null || true)"
  for node in "$@"; do
    if echo "$nodes" | grep -Fxq "$node"; then
      echo "OK node $label as $node"
      return 0
    fi
  done
  echo "FAIL node $label missing; expected one of: $*"
  FAIL=1
}

warn_any_node_count_exact() {
  local label="$1"
  local expected="$2"
  shift 2
  local node count total=0
  local nodes
  nodes="$(ros2 node list 2>/dev/null || true)"
  for node in "$@"; do
    count="$(echo "$nodes" | awk -v node="$node" '$0 == node {count++} END {print count + 0}')"
    total=$((total + count))
  done
  if [[ "$total" = "$expected" ]]; then
    echo "OK node-count $label count=$total"
  else
    echo "WARN node-count $label count=$total expected=$expected; relying on single /odom publisher and TF checks"
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

check_topic_publishers_exact() {
  local topic="$1"
  local expected="$2"
  local info count
  info="$(ros2 topic info "$topic" 2>/dev/null || true)"
  count="$(echo "$info" | awk '/Publisher count:/ {print $3; found=1} END {if (!found) print 0}')"
  if [[ "$count" = "$expected" ]]; then
    echo "OK topic-publishers $topic count=$count"
    echo "$info" | sed 's/^/  /'
  else
    echo "FAIL topic-publishers $topic count=$count expected=$expected"
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

check_process_absent() {
  local pattern="$1"
  if pgrep -f "$pattern" >/dev/null 2>&1; then
    echo "FAIL obsolete process still running: $pattern"
    pgrep -fa "$pattern" | sed 's/^/  /'
    FAIL=1
  else
    echo "OK obsolete process absent: $pattern"
  fi
}

echo "=== RK3588 Cartographer localization status ==="
date
hostname
uptime

echo "--- device ---"
ls -l /dev/rplidar /dev/ttyUSB* /dev/ttyACM* 2>/dev/null || true

echo "--- disk ---"
df -h / /mnt/sdcard 2>/dev/null || df -h /

echo "--- ros nodes ---"
ros2 node list || true

check_lifecycle_active /static_map_server
check_any_node RF2O /CLaserOdometry2DNode /rf2o_laser_odometry
warn_any_node_count_exact RF2O 1 /CLaserOdometry2DNode /rf2o_laser_odometry
check_node /rk3588_guarded_odom
check_node /ekf_filter_node

check_topic_publishers_exact /scan 1
check_topic_publishers_exact /imu 1
check_topic_publishers_exact /rf2o/odom_raw 1
check_topic_publishers_exact /odom_rf2o_guarded 1
check_topic_publishers_exact /odom 1
check_topic_publishers /map
check_topic_publishers /map_static
check_topic_publishers /tf
check_topic_publishers /tf_static

check_msg_once /scan 8
check_msg_once /map_static 8

check_tf map odom
check_tf odom base_link
check_tf base_link laser
check_process_absent "rk3588_tf_odom_publisher.py"

if [ "$FAIL" -eq 0 ]; then
  echo "RESULT OK localization stack is healthy"
else
  echo "RESULT FAIL localization stack has errors"
fi

exit "$FAIL"
