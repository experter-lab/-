#!/usr/bin/env bash
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PARAM_FILE="${1:-/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml}"

node_exists() {
  local node_name="$1"
  while IFS= read -r item; do
    if [ "$item" = "$node_name" ]; then
      return 0
    fi
  done < <(ros2 node list 2>/dev/null || true)
  return 1
}

action_exists() {
  local action_name="$1"
  while IFS= read -r item; do
    if [ "$item" = "$action_name" ]; then
      return 0
    fi
  done < <(ros2 action list 2>/dev/null || true)
  return 1
}

if [ ! -f "$PARAM_FILE" ]; then
  echo "missing params file: $PARAM_FILE"
  exit 1
fi

if node_exists /map_server && node_exists /amcl; then
  echo "localization nodes already running"
else
  nohup /mnt/sdcard/rk3588_start_localization_stack.sh > /tmp/rk3588_localization_stack.log 2>&1 &
  echo "started localization stack pid=$!"
fi

for _ in $(seq 1 30); do
  if node_exists /map_server && node_exists /amcl; then
    break
  fi
  sleep 1
done

if action_exists /navigate_to_pose; then
  echo "navigate_to_pose action already available"
else
  nohup ros2 launch nav2_bringup navigation_launch.py params_file:="$PARAM_FILE" use_sim_time:=false autostart:=true > /tmp/rk3588_nav2_navigation.log 2>&1 &
  echo "started nav2 navigation stack pid=$!"
fi

for _ in $(seq 1 30); do
  if action_exists /navigate_to_pose; then
    echo "navigate_to_pose action available"
    ros2 action list
    exit 0
  fi
  sleep 1
done

echo "navigate_to_pose action not available after timeout"
echo "--- nav2 log tail ---"
tail -80 /tmp/rk3588_nav2_navigation.log 2>/dev/null || true
exit 1
