#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

MODE="${1:-normal}"
CONFIG="/mnt/sdcard/medicine_robot_data/config/rk3588_raw_scan_view.rviz"
LOG="/tmp/rk3588_raw_scan_view.log"

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

kill_pattern() {
  local pattern="$1"
  local pids
  pids="$(pgrep -f "$pattern" || true)"
  if [[ -n "$pids" ]]; then
    echo "[raw-scan] stopping: $pattern"
    while read -r pid; do
      [[ -z "$pid" || "$pid" = "$$" || "$pid" = "$PPID" ]] && continue
      kill "$pid" 2>/dev/null || true
    done <<< "$pids"
  fi
}

echo "[raw-scan] applying safe stop"
/mnt/sdcard/rk3588_safe_stop.sh || true
if ! /mnt/sdcard/rk3588_check_brake_status.sh; then
  echo "[raw-scan] ERROR: brake status is not safe"
  exit 1
fi

echo "[raw-scan] stopping Cartographer and map RViz views"
kill_pattern "cartographer_node.*rk3588_carto_mapping.lua"
kill_pattern "cartographer_node.*rk3588_carto_localization.lua"
kill_pattern "cartographer_occupancy_grid_node"
kill_pattern "rk3588_start_carto_mapping.sh"
kill_pattern "rk3588_carto_mapping.launch.py"
kill_pattern "rviz2_carto_view"
kill_pattern "rk3588_carto_view.launch.py"
kill_pattern "rviz2 -d ${CONFIG}"
sleep 2

case "$MODE" in
  normal|0|0.0)
    echo "[raw-scan] selecting lidar yaw: normal / 0.0"
    /mnt/sdcard/rk3588_set_lidar_yaw.sh normal || \
      echo "[raw-scan] WARN: yaw helper returned non-zero; continuing to wait for /scan"
    ;;
  reverse|pi|3.14159|180)
    echo "[raw-scan] selecting lidar yaw: reverse / 3.14159"
    /mnt/sdcard/rk3588_set_lidar_yaw.sh reverse || \
      echo "[raw-scan] WARN: yaw helper returned non-zero; continuing to wait for /scan"
    ;;
  keep)
    echo "[raw-scan] keeping current lidar yaw"
    ;;
  *)
    echo "[raw-scan] ERROR: usage: /mnt/sdcard/rk3588_start_raw_scan_view.sh normal|reverse|keep"
    exit 2
    ;;
esac

wait_for_scan 45 || {
  echo "[raw-scan] ERROR: no /scan message"
  exit 1
}
echo "[raw-scan] /scan is alive"

SCAN_PUBS="$(publisher_count /scan)"
TF_STATIC_PUBS="$(publisher_count /tf_static)"
if [[ "$SCAN_PUBS" != "1" || "$TF_STATIC_PUBS" != "1" ]]; then
  echo "[raw-scan] refreshing ROS daemon before final publisher count check"
  ros2 daemon stop >/dev/null 2>&1 || true
  sleep 2
  ros2 daemon start >/dev/null 2>&1 || true
  sleep 2
  SCAN_PUBS="$(publisher_count /scan)"
  TF_STATIC_PUBS="$(publisher_count /tf_static)"
fi

SCAN_FRAME="$(timeout 8 ros2 topic echo /scan --once 2>/dev/null | awk '/frame_id:/ {print $2; exit}')"
echo "[raw-scan] /scan publishers: ${SCAN_PUBS:-unknown}"
echo "[raw-scan] /tf_static publishers: ${TF_STATIC_PUBS:-unknown}"
echo "[raw-scan] /scan frame: ${SCAN_FRAME:-unknown}"
cat /mnt/sdcard/medicine_robot_data/config/lidar_mount.env 2>/dev/null || true

if [[ "$SCAN_PUBS" != "1" || "$TF_STATIC_PUBS" != "1" || "$SCAN_FRAME" != "laser" ]]; then
  echo "[raw-scan] ERROR: raw scan graph is not clean"
  ros2 topic info /scan || true
  ros2 topic info /tf_static || true
  exit 1
fi

echo "[raw-scan] base_link -> laser:"
timeout 6 ros2 run tf2_ros tf2_echo base_link laser 2>&1 | sed -n '1,35p' || true

echo "[raw-scan] opening RViz raw scan view, fixed frame=base_link"
AUTH_FILE="$(ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -n 1)"
DISPLAY=:0 \
XDG_RUNTIME_DIR=/run/user/1000 \
XAUTHORITY="$AUTH_FILE" \
LIBGL_ALWAYS_SOFTWARE=1 \
QT_OPENGL=software \
MESA_LOADER_DRIVER_OVERRIDE=llvmpipe \
nohup rviz2 -d "$CONFIG" > "$LOG" 2>&1 &
echo "[raw-scan] rviz pid: $!"
sleep 3
tail -40 "$LOG" 2>/dev/null || true

echo "[raw-scan] VISUAL CHECK: front objects should appear in front of base_link, left on left, right on right."
echo "[raw-scan] To compare 180 deg yaw, run: /mnt/sdcard/rk3588_start_raw_scan_view.sh reverse"
