#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

FAIL=0
NODE_LIST=""
ACTION_LIST=""

has_line_in() {
  local expected="$1"
  local haystack="$2"
  while IFS= read -r item; do
    if [ "$item" = "$expected" ]; then
      return 0
    fi
  done <<< "$haystack"
  return 1
}

check_node() {
  local node_name="$1"
  if has_line_in "$node_name" "$NODE_LIST"; then
    echo "OK node $node_name"
  else
    echo "FAIL node $node_name"
    FAIL=1
  fi
}

check_any_node() {
  local label="$1"
  shift
  local node_name
  for node_name in "$@"; do
    if has_line_in "$node_name" "$NODE_LIST"; then
      echo "OK node $label as $node_name"
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
  local node_name count total=0
  for node_name in "$@"; do
    count="$(printf '%s\n' "$NODE_LIST" | awk -v node="$node_name" '$0 == node {count++} END {print count + 0}')"
    total=$((total + count))
  done
  if [[ "$total" = "$expected" ]]; then
    echo "OK node-count $label count=$total"
  else
    echo "WARN node-count $label count=$total expected=$expected; relying on single /odom publisher and TF checks"
  fi
}

check_action() {
  local action_name="$1"
  if has_line_in "$action_name" "$ACTION_LIST"; then
    local info
    info="$(timeout 6s ros2 action info "$action_name" 2>&1 || true)"
    if echo "$info" | grep -Eq "Action servers: [1-9]"; then
      echo "OK action $action_name"
      echo "$info"
    else
      echo "FAIL action $action_name has no action server"
      echo "$info"
      FAIL=1
    fi
  else
    echo "FAIL action $action_name"
    FAIL=1
  fi
}

check_param_equals() {
  local node_name="$1"
  local param_name="$2"
  local expected="$3"
  local value
  value="$(timeout 6s ros2 param get "$node_name" "$param_name" 2>/dev/null || true)"
  if echo "$value" | grep -Fq "$expected"; then
    echo "OK param $node_name $param_name $value"
  else
    echo "FAIL param $node_name $param_name ${value:-not_available}"
    FAIL=1
  fi
}

check_brake_safe() {
  local info
  info="$(/mnt/sdcard/rk3588_check_brake_status.sh 2>&1 || true)"
  if echo "$info" | grep -Fq "BRAKE_STATUS_SAFE"; then
    echo "OK brake BRAKE_STATUS_SAFE"
    echo "$info" | sed 's/^/  /'
  else
    echo "FAIL brake not safe"
    echo "$info" | sed 's/^/  /'
    FAIL=1
  fi
}

check_lifecycle_active() {
  local node_name="$1"
  local state
  state="$(timeout 6s ros2 lifecycle get "$node_name" 2>/dev/null || true)"
  if [[ "$state" == active* ]]; then
    echo "OK lifecycle $node_name $state"
  else
    echo "FAIL lifecycle $node_name ${state:-not_available}"
    FAIL=1
  fi
}

check_topic_publishers() {
  local topic="$1"
  local info
  info="$(ros2 topic info "$topic" 2>/dev/null || true)"
  if [[ "$info" == *"Publisher count: 0"* ]] || [ -z "$info" ]; then
    echo "FAIL topic $topic"
    echo "$info" | sed 's/^/  /'
    FAIL=1
  else
    echo "OK topic $topic"
    echo "$info" | sed 's/^/  /'
  fi
}

check_topic_present() {
  local topic="$1"
  local info
  info="$(ros2 topic info "$topic" 2>/dev/null || true)"
  if [ -n "$info" ]; then
    echo "OK topic-present $topic"
    echo "$info" | sed 's/^/  /'
  else
    echo "FAIL topic-present $topic"
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

check_tf() {
  local parent="$1"
  local child="$2"
  timeout 5s ros2 run tf2_ros tf2_echo "$parent" "$child" >/tmp/rk3588_nav2_status_tf.txt 2>/tmp/rk3588_nav2_status_tf.err || true
  if grep -q "Translation:" /tmp/rk3588_nav2_status_tf.txt; then
    echo "OK tf $parent -> $child"
    head -18 /tmp/rk3588_nav2_status_tf.txt | sed 's/^/  /'
  else
    echo "FAIL tf $parent -> $child"
    cat /tmp/rk3588_nav2_status_tf.err | sed 's/^/  /'
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

echo "=== RK3588 Nav2 status ==="
date
hostname
uptime

echo "--- actions ---"
ACTION_LIST="$(ros2 action list 2>/dev/null || true)"
echo "$ACTION_LIST"

echo "--- nodes ---"
NODE_LIST="$(ros2 node list 2>/dev/null || true)"
echo "$NODE_LIST"

check_node /controller_server
check_node /planner_server
check_node /bt_navigator
check_node /behavior_server
check_node /waypoint_follower
check_node /velocity_smoother
check_node /static_map_server
check_any_node RF2O /CLaserOdometry2DNode /rf2o_laser_odometry
warn_any_node_count_exact RF2O 1 /CLaserOdometry2DNode /rf2o_laser_odometry
check_node /rk3588_guarded_odom
check_node /ekf_filter_node

check_lifecycle_active /controller_server
check_lifecycle_active /planner_server
check_lifecycle_active /bt_navigator
check_lifecycle_active /behavior_server
check_lifecycle_active /waypoint_follower
check_lifecycle_active /velocity_smoother
check_lifecycle_active /static_map_server

check_action /navigate_to_pose
check_topic_present /cmd_vel
check_topic_publishers_exact /imu 1
check_topic_publishers_exact /rf2o/odom_raw 1
check_topic_publishers_exact /odom_rf2o_guarded 1
check_topic_publishers_exact /odom 1
check_topic_publishers /map_static
check_topic_publishers /local_costmap/costmap
check_topic_publishers /global_costmap/costmap
check_param_equals /global_costmap/global_costmap static_layer.map_topic /map_static
check_tf map odom
check_tf odom base_link
check_tf base_link laser
check_process_absent "rk3588_tf_odom_publisher.py"
check_brake_safe

if [ "$FAIL" -eq 0 ]; then
  echo "RESULT OK Nav2 navigation action server is healthy"
else
  echo "RESULT FAIL Nav2 navigation action server has errors"
fi

exit "$FAIL"
