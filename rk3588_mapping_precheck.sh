#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/rk3588_carto_mapping.log
HZ_LOG=/tmp/rk3588_mapping_scan_hz.log
TF_LOG=/tmp/rk3588_mapping_tf_base_to_laser.log
LIDAR_LASER_YAW="${LIDAR_LASER_YAW:-0.0}"
MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}"
STATIC_DRIFT_DURATION="${STATIC_DRIFT_DURATION:-90}"

publisher_count() {
  ros2 topic info "$1" 2>/dev/null | awk -F: '/Publisher count/ {gsub(/ /, "", $2); print $2; exit}'
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

stop_optional_processes() {
  local pattern
  for pattern in \
    "teleop_twist_keyboard" \
    "kbd_drive" \
    "rk3588_start_mapping_keyboard_drive.sh"; do
    local pids
    pids="$(pgrep -f "$pattern" || true)"
    if [[ -n "$pids" ]]; then
      echo "[mapping-precheck] stopping optional drive process: $pattern"
      while read -r pid; do
        [[ -z "$pid" || "$pid" = "$$" || "$pid" = "$PPID" ]] && continue
        kill "$pid" 2>/dev/null || true
      done <<< "$pids"
    fi
  done
}

echo "[mapping-precheck] checking brake state"
if ! /mnt/sdcard/rk3588_check_brake_status.sh; then
  echo "[mapping-precheck] brake was not safe; applying safe stop"
  /mnt/sdcard/rk3588_safe_stop.sh
  /mnt/sdcard/rk3588_check_brake_status.sh
fi
stop_optional_processes

echo "[mapping-precheck] starting fresh mapping graph for precheck"
echo "[mapping-precheck] map resolution: ${MAP_RESOLUTION} m/cell"
RESTART_LIDAR_FOR_MAPPING=1 LIDAR_LASER_YAW="$LIDAR_LASER_YAW" MAP_RESOLUTION="$MAP_RESOLUTION" \
  nohup /mnt/sdcard/rk3588_start_carto_mapping.sh > "$LOG" 2>&1 &
echo "[mapping-precheck] mapping launch pid: $!"
echo "[mapping-precheck] log: $LOG"

wait_for_node /cartographer_node 45 || {
  echo "[mapping-precheck] ERROR: /cartographer_node did not start"
  tail -120 "$LOG" 2>/dev/null || true
  exit 1
}

wait_for_topic_once /scan 45 || {
  echo "[mapping-precheck] ERROR: no /scan message"
  tail -120 "$LOG" 2>/dev/null || true
  exit 1
}

SCAN_PUBS="$(publisher_count /scan)"
TF_STATIC_PUBS="$(publisher_count /tf_static)"
SCAN_FRAME="$(timeout 12 ros2 topic echo /scan --once 2>/dev/null | awk '/frame_id:/ {print $2; exit}')"
SCAN_FRAME="${SCAN_FRAME//\'/}"
SCAN_FRAME="${SCAN_FRAME//\"/}"
SCAN_FRAME="${SCAN_FRAME// /}"
SCAN_FRAME="${SCAN_FRAME//$'\r'/}"

echo "[mapping-precheck] /scan publishers: ${SCAN_PUBS:-unknown}"
echo "[mapping-precheck] /tf_static publishers: ${TF_STATIC_PUBS:-unknown}"
echo "[mapping-precheck] /scan frame: ${SCAN_FRAME:-unknown}"

if [[ "$SCAN_PUBS" != "1" || "$TF_STATIC_PUBS" != "1" ]]; then
  echo "[mapping-precheck] refreshing ROS daemon once before final publisher count check"
  ros2 daemon stop >/dev/null 2>&1 || true
  sleep 2
  ros2 daemon start >/dev/null 2>&1 || true
  sleep 2
  SCAN_PUBS="$(publisher_count /scan)"
  TF_STATIC_PUBS="$(publisher_count /tf_static)"
  echo "[mapping-precheck] /scan publishers after refresh: ${SCAN_PUBS:-unknown}"
  echo "[mapping-precheck] /tf_static publishers after refresh: ${TF_STATIC_PUBS:-unknown}"
fi

if [[ "$SCAN_PUBS" != "1" ]]; then
  echo "[mapping-precheck] ERROR: expected exactly one /scan publisher"
  ros2 topic info /scan || true
  exit 1
fi

if [[ "$TF_STATIC_PUBS" != "1" ]]; then
  echo "[mapping-precheck] ERROR: expected exactly one /tf_static publisher"
  ros2 topic info /tf_static || true
  exit 1
fi

if [[ "$SCAN_FRAME" != "laser" ]]; then
  echo "[mapping-precheck] ERROR: expected /scan frame_id laser"
  exit 1
fi

timeout 7 ros2 topic hz /scan > "$HZ_LOG" 2>&1 || true
echo "[mapping-precheck] /scan hz sample:"
cat "$HZ_LOG" || true

timeout 5 ros2 run tf2_ros tf2_echo base_link laser > "$TF_LOG" 2>&1 || true
echo "[mapping-precheck] base_link -> laser:"
head -40 "$TF_LOG" || true

wait_for_topic_once /submap_list 30 || {
  echo "[mapping-precheck] ERROR: no /submap_list message"
  tail -120 "$LOG" 2>/dev/null || true
  exit 1
}

wait_for_topic_once /map 30 || {
  echo "[mapping-precheck] ERROR: no /map message"
  tail -120 "$LOG" 2>/dev/null || true
  exit 1
}

echo "[mapping-precheck] checking static Cartographer drift for ${STATIC_DRIFT_DURATION} seconds"
if ! python3 /mnt/sdcard/medicine_robot_data/scripts/carto_static_drift_check.py \
  --duration "$STATIC_DRIFT_DURATION" \
  --max-xy-drift 0.03 \
  --max-yaw-drift-deg 1.0; then
  echo "[mapping-precheck] ERROR: map is drifting while the robot is stationary"
  echo "[mapping-precheck] Do not start full mapping until this passes."
  exit 1
fi

echo "[mapping-precheck] RESULT OK: mapping topics and TF are healthy"
echo "[mapping-precheck] VISUAL CHECK: in RViz, /scan should quickly overlay the newly generated /map."
echo "[mapping-precheck] If the scan is globally reversed, run /mnt/sdcard/rk3588_set_lidar_yaw.sh reverse, then rerun this precheck."
