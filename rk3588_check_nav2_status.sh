#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

FAIL=0

has_line() {
  local expected="$1"
  while IFS= read -r item; do
    if [ "$item" = "$expected" ]; then
      return 0
    fi
  done
  return 1
}

check_node() {
  local node_name="$1"
  if ros2 node list 2>/dev/null | has_line "$node_name"; then
    echo "OK node $node_name"
  else
    echo "FAIL node $node_name"
    FAIL=1
  fi
}

check_action() {
  local action_name="$1"
  if ros2 action list 2>/dev/null | has_line "$action_name"; then
    echo "OK action $action_name"
    timeout 6s ros2 action info "$action_name" || true
  else
    echo "FAIL action $action_name"
    FAIL=1
  fi
}

check_lifecycle_active() {
  local node_name="$1"
  local state
  state="$(ros2 lifecycle get "$node_name" 2>/dev/null || true)"
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

echo "=== RK3588 Nav2 status ==="
date
hostname
uptime

echo "--- actions ---"
ros2 action list || true

echo "--- nodes ---"
ros2 node list || true

check_node /controller_server
check_node /planner_server
check_node /bt_navigator
check_node /behavior_server
check_node /waypoint_follower
check_node /velocity_smoother

check_lifecycle_active /controller_server
check_lifecycle_active /planner_server
check_lifecycle_active /bt_navigator
check_lifecycle_active /behavior_server
check_lifecycle_active /waypoint_follower
check_lifecycle_active /velocity_smoother

check_action /navigate_to_pose
check_topic_publishers /cmd_vel
check_topic_publishers /local_costmap/costmap
check_topic_publishers /global_costmap/costmap

if [ "$FAIL" -eq 0 ]; then
  echo "RESULT OK Nav2 navigation action server is healthy"
else
  echo "RESULT FAIL Nav2 navigation action server has errors"
fi

exit "$FAIL"
