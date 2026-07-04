#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/rk3588_carto_mapping.log
START_LIDAR=false
LIDAR_MOUNT_ENV="${LIDAR_MOUNT_ENV:-/mnt/sdcard/medicine_robot_data/config/lidar_mount.env}"
if [[ -f "$LIDAR_MOUNT_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$LIDAR_MOUNT_ENV"
fi
LIDAR_LASER_YAW="${LIDAR_LASER_YAW:-0.0}"
MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}"
RESTART_LIDAR_FOR_MAPPING="${RESTART_LIDAR_FOR_MAPPING:-0}"

topic_has_once() {
  timeout 3 ros2 topic echo "$1" --once >/dev/null 2>&1
}

wait_for_lidar() {
  local seconds="$1"
  for _ in $(seq 1 "$seconds"); do
    if ros2 node list 2>/dev/null | grep -Fxq /sllidar_node; then
      if topic_has_once /scan; then
        return 0
      fi
    fi
    sleep 1
  done
  return 1
}

kill_pattern() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -n "$pids" ]]; then
    echo "[mapping] stopping: $pattern"
    while read -r pid; do
      [[ -z "$pid" || "$pid" = "$$" || "$pid" = "$PPID" ]] && continue
      kill "$pid" 2>/dev/null || true
    done <<< "$pids"
  fi
}

echo "[mapping] log file: $LOG"
echo "[mapping] checking brake state before mapping"
if ! /mnt/sdcard/rk3588_check_brake_status.sh; then
  echo "[mapping] brake was not safe; applying safe stop"
  /mnt/sdcard/rk3588_safe_stop.sh
  /mnt/sdcard/rk3588_check_brake_status.sh
fi

echo "[mapping] cleaning old localization/navigation/cartographer processes"
kill_pattern "carto_relocalize_bridge.py"
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
kill_pattern "cartographer_node.*rk3588_carto_mapping.lua"
kill_pattern "cartographer_node.*rk3588_carto_localization.lua"
kill_pattern "rk3588_carto_mapping.launch.py"
kill_pattern "cartographer_occupancy_grid_node"
kill_pattern "rk3588_tf_odom_publisher.py"
kill_pattern "rviz2 -d /mnt/sdcard/medicine_robot_data/config/rk3588_nav2_view.rviz"
kill_pattern "rviz2_carto_view"
kill_pattern "rk3588_carto_view.launch.py"
kill_pattern "amcl"
kill_pattern "slam_toolbox"
sleep 2

if [[ "$RESTART_LIDAR_FOR_MAPPING" = "1" ]]; then
  echo "[mapping] requesting lidar restart before mapping"
  pkill -f "rk3588_lidar_bringup.launch.py" || true
  pkill -f "sllidar_node" || true
  pkill -f "static_transform_publisher.*base_to_laser_tf" || true
  sleep 3
  if wait_for_lidar 25; then
    echo "[mapping] using restarted persistent /scan publisher"
    START_LIDAR=false
  else
    echo "[mapping] ERROR: persistent lidar did not recover; refusing to start a duplicate mapping lidar"
    exit 1
  fi
elif wait_for_lidar 3; then
  echo "[mapping] reusing existing /scan publisher"
  START_LIDAR=false
else
  echo "[mapping] requesting persistent lidar recovery"
  pkill -f "rk3588_lidar_bringup.launch.py" || true
  pkill -f "sllidar_node" || true
  pkill -f "static_transform_publisher.*base_to_laser_tf" || true
  sleep 3
  wait_for_lidar 25 || {
    echo "[mapping] ERROR: no persistent /scan publisher; refusing to start a duplicate mapping lidar"
    exit 1
  }
  START_LIDAR=false
fi

echo "[mapping] starting Cartographer mapping, start_lidar=$START_LIDAR"
echo "[mapping] lidar yaw: $LIDAR_LASER_YAW"
echo "[mapping] map resolution: $MAP_RESOLUTION m/cell"
exec ros2 launch medicine_robot_bringup rk3588_carto_mapping.launch.py \
  start_lidar:="$START_LIDAR" \
  laser_yaw:="$LIDAR_LASER_YAW" \
  resolution:="$MAP_RESOLUTION" 2>&1 | tee "$LOG"
