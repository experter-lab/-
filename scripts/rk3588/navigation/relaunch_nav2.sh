#!/usr/bin/env bash
# 启 Nav2 (后台,新 yaml)
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
PARAMS=/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml
LOG=/tmp/rk3588_nav2_relaunch.log

echo "==> launching nav2_bringup"
nohup ros2 launch nav2_bringup navigation_launch.py \
  params_file:="$PARAMS" use_sim_time:=false autostart:=true \
  > "$LOG" 2>&1 &
echo "PID=$!"
sleep 25
echo
echo "==> lifecycle states"
for n in controller_server planner_server bt_navigator behavior_server smoother_server waypoint_follower velocity_smoother; do
  s=$(timeout 2 ros2 service call /$n/get_state lifecycle_msgs/srv/GetState 2>/dev/null | grep -E 'label' | head -1)
  echo "  $n: $s"
done
echo
echo "==> nav2 nodes alive:"
ros2 node list 2>/dev/null | grep -E '^/(controller_server|planner_server|bt_navigator|behavior_server|smoother_server|waypoint_follower|velocity_smoother|lifecycle_manager_navigation|local_costmap|global_costmap)' | sort
echo
echo "==> log tail (errors only)"
grep -iE 'error|fatal|exception' "$LOG" | tail -10
