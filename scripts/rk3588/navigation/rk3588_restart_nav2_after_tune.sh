#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "[restart-nav2-tune] safe stop first"
/mnt/sdcard/rk3588_safe_stop.sh || true

kill_pattern() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -n "$pids" ]]; then
    echo "[restart-nav2-tune] stopping: $pattern"
    while read -r pid; do
      [[ -z "$pid" || "$pid" = "$$" ]] && continue
      kill "$pid" 2>/dev/null || true
    done <<< "$pids"
  fi
}

kill_pattern "nav2_bringup navigation_launch.py"
kill_pattern "nav2_controller/controller_server"
kill_pattern "nav2_planner/planner_server"
kill_pattern "nav2_bt_navigator/bt_navigator"
kill_pattern "nav2_behaviors/behavior_server"
kill_pattern "nav2_smoother/smoother_server"
kill_pattern "nav2_velocity_smoother/velocity_smoother"
kill_pattern "nav2_waypoint_follower/waypoint_follower"
kill_pattern "nav2_lifecycle_manager/lifecycle_manager"
kill_pattern "nav2_map_server.*static_map_server"
kill_pattern "map_server.*static_map_server"
kill_pattern "rk3588_tf_odom_publisher.py"

sleep 4

echo "[restart-nav2-tune] starting Nav2 with drive disabled"
NAV2_ENABLE_DRIVE=0 /mnt/sdcard/rk3588_start_nav2_carto.sh

echo "[restart-nav2-tune] checking Nav2"
/mnt/sdcard/rk3588_check_nav2_status.sh
