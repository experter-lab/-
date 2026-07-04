#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

kill_pattern() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -n "$pids" ]]; then
    echo "[clean] stopping: $pattern"
    while read -r pid; do
      [[ -z "$pid" || "$pid" = "$$" ]] && continue
      kill "$pid" 2>/dev/null || true
    done <<< "$pids"
  fi
}

echo "[clean] preserving web/task services; stopping localization/navigation processes"
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
kill_pattern "cartographer_node.*rk3588_carto_localization.lua"
kill_pattern "cartographer_node.*rk3588_carto_mapping.lua"
kill_pattern "cartographer_occupancy_grid_node"
kill_pattern "rk3588_start_carto_localization.sh"
kill_pattern "rk3588_start_carto_mapping.sh"
kill_pattern "rk3588_carto_mapping.launch.py"
kill_pattern "rk3588_tf_odom_publisher.py"
kill_pattern "rk3588_guarded_odom.py"
kill_pattern "rk3588_start_odom_fusion.sh"
kill_pattern "robot_localization.*ekf_node"
kill_pattern "ekf_node"
kill_pattern "rf2o_laser_odometry_node"
kill_pattern "rviz2 -d /mnt/sdcard/medicine_robot_data/config/rk3588_nav2_view.rviz"
kill_pattern "rviz2_carto_view"
kill_pattern "rk3588_carto_view.launch.py"
kill_pattern "amcl"
kill_pattern "slam_toolbox"

sleep 3

echo "[clean] remaining key ROS nodes:"
ros2 node list 2>/dev/null | sort | grep -E "cartographer|rf2o|guarded|ekf|nav2|map_server|rviz|chassis|sllidar|base_to_laser|web|task|voice" || true
echo "[clean] done"
