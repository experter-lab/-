#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/rk3588_carto_mapping.log

publisher_count() {
  ros2 topic info "$1" 2>/dev/null | awk -F: '/Publisher count/ {gsub(/ /, "", $2); print $2; exit}'
}

wait_for_scan() {
  local seconds="$1"
  for _ in $(seq 1 "$seconds"); do
    if timeout 3 ros2 topic echo /scan --once >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_topic_once() {
  local topic="$1"
  local timeout_sec="$2"
  timeout "$timeout_sec" ros2 topic echo "$topic" --once >/dev/null 2>&1
}

wait_for_node() {
  local node_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    if ros2 node list 2>/dev/null | grep -Fxq "$node_name"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

check_clean_lidar_graph() {
  wait_for_scan 20 || {
    echo "[mapping-shortcut] ERROR: no /scan message."
    return 1
  }

  local scan_pubs tf_static_pubs scan_frame
  scan_pubs="$(publisher_count /scan)"
  tf_static_pubs="$(publisher_count /tf_static)"
  scan_frame="$(timeout 8 ros2 topic echo /scan --once 2>/dev/null | awk '/frame_id:/ {print $2; exit}')"
  scan_frame="${scan_frame//\'/}"
  scan_frame="${scan_frame//\"/}"
  scan_frame="${scan_frame// /}"

  if [[ "$scan_pubs" != "1" || "$tf_static_pubs" != "1" ]]; then
    echo "[mapping-shortcut] refreshing ROS daemon before final lidar graph check"
    ros2 daemon stop >/dev/null 2>&1 || true
    sleep 2
    ros2 daemon start >/dev/null 2>&1 || true
    sleep 2
    scan_pubs="$(publisher_count /scan)"
    tf_static_pubs="$(publisher_count /tf_static)"
  fi

  echo "[mapping-shortcut] /scan publishers: ${scan_pubs:-unknown}"
  echo "[mapping-shortcut] /tf_static publishers: ${tf_static_pubs:-unknown}"
  echo "[mapping-shortcut] /scan frame: ${scan_frame:-unknown}"

  [[ "$scan_pubs" = "1" && "$tf_static_pubs" = "1" && "$scan_frame" = "laser" ]]
}

cleanup_after_failed_start() {
  echo "[mapping-shortcut] mapping startup failed; stopping Cartographer/RViz and returning to safe state"
  /mnt/sdcard/rk3588_safe_stop.sh || true
  pkill -TERM -f "cartographer_node" || true
  pkill -TERM -f "cartographer_occupancy_grid_node" || true
  pkill -TERM -f "rk3588_carto_mapping.launch.py" || true
  pkill -TERM -f "rk3588_start_carto_mapping.sh" || true
  pkill -TERM -f "rviz2_carto_view" || true
  sleep 2
  /mnt/sdcard/rk3588_check_brake_status.sh || true
}

clear
echo "RK3588 Cartographer mapping shortcut"
echo "Flow: safe-stop -> clean runtime -> lidar graph check -> start Cartographer -> RViz."
echo "This shortcut does not start keyboard drive and does not authorize chassis motion."
echo

/mnt/sdcard/rk3588_safe_stop.sh || true
/mnt/sdcard/rk3588_clean_nav_runtime.sh || true

echo
echo "[mapping-shortcut] checking lidar graph before Cartographer"
if ! check_clean_lidar_graph; then
  echo "[mapping-shortcut] lidar graph is not clean; trying one normal-yaw lidar recovery"
  /mnt/sdcard/rk3588_set_lidar_yaw.sh normal || true
  sleep 5
  if ! check_clean_lidar_graph; then
    echo "[mapping-shortcut] ERROR: /scan and /tf_static must each have exactly one publisher."
    echo "[mapping-shortcut] Refusing to start mapping."
    read -r -p "Press Enter to close." _
    exit 1
  fi
fi

echo
echo "[mapping-shortcut] starting Cartographer mapping without the static drift wait"
RESTART_LIDAR_FOR_MAPPING=0 MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}" \
  nohup /mnt/sdcard/rk3588_start_carto_mapping.sh > "$LOG" 2>&1 &
echo "[mapping-shortcut] mapping launch pid: $!"
echo "[mapping-shortcut] Cartographer log: $LOG"

if ! wait_for_node /cartographer_node 45; then
  cleanup_after_failed_start
  echo
  echo "[mapping-shortcut] RESULT FAIL: /cartographer_node did not start."
  echo "[mapping-shortcut] Cartographer log: $LOG"
  tail -120 "$LOG" 2>/dev/null || true
  read -r -p "Press Enter to close." _
  exit 1
fi

if ! wait_for_topic_once /submap_list 30 || ! wait_for_topic_once /map 30; then
  cleanup_after_failed_start
  echo
  echo "[mapping-shortcut] RESULT FAIL: /map or /submap_list did not appear."
  echo "[mapping-shortcut] Cartographer log: $LOG"
  tail -120 "$LOG" 2>/dev/null || true
  read -r -p "Press Enter to close." _
  exit 1
fi

echo
echo "[mapping-shortcut] RESULT OK: mapping graph is running. Opening Cartographer RViz."
echo "[mapping-shortcut] RViz displays the raw Cartographer /map directly."
echo "[mapping-shortcut] Keep the robot still briefly, then use keyboard control for slow mapping."
echo "[mapping-shortcut] Use the keyboard mapping shortcut only after visual confirmation."

export LIBGL_ALWAYS_SOFTWARE=1
export QT_OPENGL=software
export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe

exec ros2 launch medicine_robot_bringup rk3588_carto_view.launch.py
