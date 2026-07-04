#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PBSTREAM="${1:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream}"
MAP_STEM="${2:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static}"
MAP_YAML="${MAP_STEM}.yaml"
CONFIG_DIR="/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config"
INITIAL_POSE_FILE="${INITIAL_POSE_FILE:-/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json}"
LIDAR_MOUNT_ENV="${LIDAR_MOUNT_ENV:-/mnt/sdcard/medicine_robot_data/config/lidar_mount.env}"
if [[ -f "$LIDAR_MOUNT_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$LIDAR_MOUNT_ENV"
fi
LIDAR_LOG=/tmp/rk3588_lidar_clean.log
RF2O_LOG=/tmp/rk3588_rf2o_odom.log
GUARD_LOG=/tmp/rk3588_guarded_odom.log
EKF_LOG=/tmp/rk3588_ekf_odom.log
ODOM_FUSION_LOG=/tmp/rk3588_odom_fusion.log
CARTO_LOG=/tmp/rk3588_carto_localization.log
MAP_LOG=/tmp/rk3588_static_map_server.log
RVIZ_LOG=/tmp/rk3588_rviz_localization.log
FOOTPRINT_LOG=/tmp/rk3588_robot_debug_footprint.log
AUTO_POSE_LOG=/tmp/rk3588_carto_apply_saved_pose.log
AUTO_SCAN_MATCH_LOG=/tmp/rk3588_carto_auto_scan_match_pose.log
LOCAL_REFINE_INITIAL_POSE="${LOCAL_REFINE_INITIAL_POSE:-1}"
AUTO_GLOBAL_INITIAL_POSE="${AUTO_GLOBAL_INITIAL_POSE:-1}"
ALLOW_GLOBAL_SCAN_MATCH="${ALLOW_GLOBAL_SCAN_MATCH:-$AUTO_GLOBAL_INITIAL_POSE}"
LOCAL_SCAN_MATCH_XY_WINDOW="${LOCAL_SCAN_MATCH_XY_WINDOW:-0.5}"
LOCAL_SCAN_MATCH_YAW_WINDOW_DEG="${LOCAL_SCAN_MATCH_YAW_WINDOW_DEG:-20}"
GLOBAL_SCAN_MATCH_MAX_SCORE="${GLOBAL_SCAN_MATCH_MAX_SCORE:-0.18}"
GLOBAL_SCAN_MATCH_MIN_SCORE_GAP="${GLOBAL_SCAN_MATCH_MIN_SCORE_GAP:-0.05}"
GLOBAL_SCAN_MATCH_MIN_SCORE_RATIO="${GLOBAL_SCAN_MATCH_MIN_SCORE_RATIO:-1.25}"
START_INITIALPOSE_LISTENER="${START_INITIALPOSE_LISTENER:-0}"
LIDAR_LASER_YAW="${LIDAR_LASER_YAW:-0.0}"
MAP_RESOLUTION="${MAP_RESOLUTION:-0.03}"

laser_yaw_deg() {
  python3 - <<'PY'
import math
import os

print(math.degrees(float(os.environ.get("LIDAR_LASER_YAW", "0.0"))))
PY
}

node_exists() {
  ros2 node list 2>/dev/null | grep -Fxq "$1"
}

topic_has_pub() {
  ros2 topic info "$1" 2>/dev/null | grep -Eq "Publisher count: [1-9]"
}

wait_for_node() {
  local node_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    node_exists "$node_name" && return 0
    sleep 1
  done
  return 1
}

wait_for_topic_pub() {
  local topic_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    topic_has_pub "$topic_name" && return 0
    sleep 1
  done
  return 1
}

wait_for_scan_message() {
  local seconds="$1"
  for _ in $(seq 1 "$seconds"); do
    if timeout 2 ros2 topic echo /scan --once >/tmp/rk3588_last_scan_check.log 2>&1; then
      return 0
    fi
    sleep 1
  done
  return 1
}

ensure_brake_safe() {
  local log=/tmp/rk3588_loc_only_brake_check.log
  echo "[safety] checking brake state before localization"
  if /mnt/sdcard/rk3588_check_brake_status.sh > "$log" 2>&1; then
    cat "$log"
    return 0
  fi
  echo "[safety] brake state was not safe; applying safe stop"
  cat "$log" 2>/dev/null || true
  /mnt/sdcard/rk3588_safe_stop.sh
  /mnt/sdcard/rk3588_check_brake_status.sh
}

hash_file() {
  local path="$1"
  if [[ -f "$path" ]]; then
    sha256sum "$path" | awk '{print $1}'
  else
    echo "missing"
  fi
}

pose_file_valid() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  python3 - "$path" <<'PY'
import json
import math
import sys

path = sys.argv[1]
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)
for key in ("x", "y", "qz", "qw"):
    value = float(data[key])
    if not math.isfinite(value):
        raise ValueError(key)
print("OK")
PY
}

print_map_hashes() {
  echo "[loc-only] pbstream sha256: $(hash_file "$PBSTREAM")"
  echo "[loc-only] static map sha256: $(hash_file "$MAP_YAML")"
}

pose_file_matches_current_map() {
  local path="$1"
  [[ -f "$path" ]] || return 1
  python3 - "$path" "$PBSTREAM" "$MAP_YAML" <<'PY'
import hashlib
import json
import sys

pose_path, pbstream_path, map_yaml_path = sys.argv[1:4]

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

with open(pose_path, "r", encoding="utf-8") as f:
    pose = json.load(f)

expected_pbstream = pose.get("pbstream_sha256")
expected_map = pose.get("map_yaml_sha256")
actual_pbstream = sha256_file(pbstream_path)
actual_map = sha256_file(map_yaml_path) if map_yaml_path else None

if expected_pbstream != actual_pbstream:
    print(
        "POSE_MAP_MISMATCH pbstream "
        f"pose={expected_pbstream} current={actual_pbstream}"
    )
    raise SystemExit(1)

if expected_map and actual_map and expected_map != actual_map:
    print(
        "POSE_MAP_MISMATCH map_yaml "
        f"pose={expected_map} current={actual_map}"
    )
    raise SystemExit(1)

print("POSE_MAP_MATCH")
PY
}

if [[ ! -f "$PBSTREAM" ]]; then
  echo "[loc-only] ERROR: missing pbstream: $PBSTREAM"
  exit 1
fi

echo "[loc-only] canonical pbstream: $PBSTREAM"
echo "[loc-only] canonical static map: $MAP_YAML"
print_map_hashes

ensure_brake_safe

/mnt/sdcard/rk3588_clean_nav_runtime.sh

if node_exists /sllidar_node && node_exists /base_to_laser_tf && wait_for_scan_message 3; then
  echo "[loc-only] lidar already running"
else
  echo "[loc-only] starting lidar + base_link->laser TF"
  pkill -f "rk3588_lidar_bringup.launch.py" || true
  pkill -f "sllidar_node" || true
  pkill -f "static_transform_publisher.*base_to_laser_tf" || true
  nohup ros2 launch medicine_robot_bringup rk3588_lidar_bringup.launch.py \
    serial_port:=/dev/rplidar \
    serial_baudrate:=256000 \
    frame_id:=laser \
    enable_static_tf:=true \
    base_frame_id:=base_link \
    laser_x:=0.15 \
    laser_y:=0.00 \
    laser_z:=0.12 \
    laser_yaw:="$LIDAR_LASER_YAW" \
    range_min_filter:=0.55 \
    > "$LIDAR_LOG" 2>&1 &
fi

wait_for_scan_message 90 || {
  echo "[loc-only] ERROR: no /scan message arrived"
  cat /tmp/rk3588_last_scan_check.log 2>/dev/null || true
  tail -80 "$LIDAR_LOG" 2>/dev/null || true
  exit 1
}
wait_for_node /base_to_laser_tf 20 || {
  echo "[loc-only] ERROR: /base_to_laser_tf not ready"
  tail -80 "$LIDAR_LOG" 2>/dev/null || true
  exit 1
}

echo "[loc-only] starting guarded RF2O + IMU + EKF odom fusion"
RF2O_LOG="$RF2O_LOG" GUARD_LOG="$GUARD_LOG" EKF_LOG="$EKF_LOG" \
  /mnt/sdcard/rk3588_start_odom_fusion.sh > "$ODOM_FUSION_LOG" 2>&1 || {
  echo "[loc-only] ERROR: odom fusion failed"
  tail -160 "$ODOM_FUSION_LOG" 2>/dev/null || true
  tail -120 "$RF2O_LOG" 2>/dev/null || true
  tail -120 "$GUARD_LOG" 2>/dev/null || true
  tail -120 "$EKF_LOG" 2>/dev/null || true
  exit 1
}
cat "$ODOM_FUSION_LOG"

if [[ ! -f "$MAP_YAML" || "$PBSTREAM" -nt "$MAP_YAML" ]]; then
  echo "[loc-only] exporting static map from canonical pbstream"
  rm -f "${MAP_STEM}.yaml" "${MAP_STEM}.pgm"
  /opt/ros/humble/lib/cartographer_ros/cartographer_pbstream_to_ros_map \
    -pbstream_filename="$PBSTREAM" \
    -map_filestem="$MAP_STEM" \
    -resolution="$MAP_RESOLUTION"
fi

echo "[loc-only] starting Cartographer localization"
nohup ros2 launch medicine_robot_bringup rk3588_carto_localization.launch.py \
  pbstream:="$PBSTREAM" \
  start_lidar:=false \
  > "$CARTO_LOG" 2>&1 &
echo "[loc-only] cartographer launch pid: $!"

wait_for_node /cartographer_node 30 || {
  echo "[loc-only] ERROR: /cartographer_node not ready"
  tail -100 "$CARTO_LOG" 2>/dev/null || true
  exit 1
}

if [[ "${AUTO_INITIAL_POSE:-1}" = "1" ]] &&
  pose_file_valid "$INITIAL_POSE_FILE" >/tmp/rk3588_initial_pose_validate.log 2>&1 &&
  pose_file_matches_current_map "$INITIAL_POSE_FILE" >/tmp/rk3588_initial_pose_map_match.log 2>&1; then
  echo "[loc-only] initial pose source: saved_pose"
  echo "[loc-only] applying saved Cartographer initial pose: $INITIAL_POSE_FILE"
  if python3 /mnt/sdcard/medicine_robot_data/scripts/carto_apply_saved_pose.py \
    --pose-file "$INITIAL_POSE_FILE" \
    --relative-to-trajectory-id latest > "$AUTO_POSE_LOG" 2>&1; then
    tail -30 "$AUTO_POSE_LOG"
  else
    echo "[loc-only] WARN: failed to apply saved initial pose"
    cat "$AUTO_POSE_LOG" 2>/dev/null || true
  fi
  if [[ "$LOCAL_REFINE_INITIAL_POSE" = "1" &&
    "${AUTO_SCAN_MATCH_POSE:-1}" = "1" &&
    -f /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py ]]; then
    echo "[loc-only] initial pose source: local_refine"
    if python3 /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py \
      --map "$MAP_YAML" \
      --anchor-pose-file "$INITIAL_POSE_FILE" \
      --laser-yaw-deg "$(laser_yaw_deg)" \
      --scan-timeout 12 \
      --local-xy-window "$LOCAL_SCAN_MATCH_XY_WINDOW" \
      --local-yaw-window-deg "$LOCAL_SCAN_MATCH_YAW_WINDOW_DEG" \
      --max-score "${AUTO_SCAN_MATCH_MAX_SCORE:-0.22}" \
      --relative-to-trajectory-id latest \
      --apply > "$AUTO_SCAN_MATCH_LOG" 2>&1; then
      tail -50 "$AUTO_SCAN_MATCH_LOG"
    else
      echo "[loc-only] WARN: local scan-match refine failed; keeping saved pose result"
      cat "$AUTO_SCAN_MATCH_LOG" 2>/dev/null || true
    fi
  fi
elif [[ "${AUTO_SCAN_MATCH_POSE:-1}" = "1" &&
  "$ALLOW_GLOBAL_SCAN_MATCH" = "1" &&
  -f /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py ]]; then
  echo "[loc-only] initial pose source: global_auto_bootstrap"
  echo "[loc-only] no saved pose; running guarded whole-map scan-match"
  if python3 /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py \
    --map "$MAP_YAML" \
    --pbstream "$PBSTREAM" \
    --allow-global-search \
    --allow-global-apply \
    --laser-yaw-deg "$(laser_yaw_deg)" \
    --scan-timeout 12 \
    --coarse-stride-px 4 \
    --coarse-yaw-step-deg 10 \
    --refine-xy-window 0.3 \
    --refine-xy-step 0.05 \
    --refine-yaw-window-deg 12 \
    --refine-yaw-step-deg 1 \
    --max-score "$GLOBAL_SCAN_MATCH_MAX_SCORE" \
    --min-score-gap "$GLOBAL_SCAN_MATCH_MIN_SCORE_GAP" \
    --min-score-ratio "$GLOBAL_SCAN_MATCH_MIN_SCORE_RATIO" \
    --relative-to-trajectory-id latest \
    --save-result-pose-file "$INITIAL_POSE_FILE" \
    --apply > "$AUTO_SCAN_MATCH_LOG" 2>&1; then
    tail -60 "$AUTO_SCAN_MATCH_LOG"
    echo "[loc-only] accepted automatic initial pose and saved it to $INITIAL_POSE_FILE"
  else
    echo "[loc-only] WARN: guarded whole-map scan-match failed or was ambiguous; no pose was applied"
    cat "$AUTO_SCAN_MATCH_LOG" 2>/dev/null || true
  fi
else
  echo "[loc-only] initial pose source: manual_required"
  echo "[loc-only] no valid saved pose and automatic bootstrap is disabled or unavailable"
  echo "[loc-only] enable AUTO_GLOBAL_INITIAL_POSE=1 for guarded automatic startup"
  if [[ -f /tmp/rk3588_initial_pose_validate.log ]]; then
    cat /tmp/rk3588_initial_pose_validate.log 2>/dev/null || true
  fi
  if [[ -f /tmp/rk3588_initial_pose_map_match.log ]]; then
    cat /tmp/rk3588_initial_pose_map_match.log 2>/dev/null || true
  fi
fi

wait_for_topic_pub /scan_matched_points2 45 || {
  echo "[loc-only] WARN: /scan_matched_points2 has no publisher yet"
}

echo "[loc-only] starting static map server"
nohup ros2 run nav2_map_server map_server --ros-args \
  -r __node:=static_map_server \
  -p yaml_filename:="$MAP_YAML" \
  -p topic_name:=/map_static \
  -p frame_id:=map \
  > "$MAP_LOG" 2>&1 &

wait_for_node /static_map_server 15 || {
  echo "[loc-only] ERROR: static_map_server not ready"
  tail -80 "$MAP_LOG" 2>/dev/null || true
  exit 1
}
timeout 8 ros2 lifecycle set /static_map_server configure >/tmp/rk3588_static_map_lifecycle.log 2>&1 || true
timeout 8 ros2 lifecycle set /static_map_server activate >>/tmp/rk3588_static_map_lifecycle.log 2>&1 || true
wait_for_topic_pub /map_static 20 || {
  echo "[loc-only] WARN: /map_static publisher not visible yet"
  tail -80 "$MAP_LOG" 2>/dev/null || true
  cat /tmp/rk3588_static_map_lifecycle.log 2>/dev/null || true
}

echo "[loc-only] starting debug robot footprint"
pkill -f "robot_debug_footprint_pub.py" || true
nohup python3 /mnt/sdcard/medicine_robot_data/scripts/robot_debug_footprint_pub.py \
  > "$FOOTPRINT_LOG" 2>&1 &

if [[ "$START_INITIALPOSE_LISTENER" = "1" ]]; then
  INITIALPOSE_YAW_OFFSET_DEG="${INITIALPOSE_YAW_OFFSET_DEG:-180}"
  INITIALPOSE_KEEP_ALIVE="${INITIALPOSE_KEEP_ALIVE:-1}"
  echo "[loc-only] starting 2D Pose Estimate listener with yaw offset ${INITIALPOSE_YAW_OFFSET_DEG} deg keep_alive=${INITIALPOSE_KEEP_ALIVE}"
  /mnt/sdcard/rk3588_start_initialpose_listener.sh "$INITIALPOSE_YAW_OFFSET_DEG" "$INITIALPOSE_KEEP_ALIVE" >/tmp/rk3588_initialpose_listener_start.log 2>&1 || {
    echo "[loc-only] WARN: failed to start initialpose listener"
    cat /tmp/rk3588_initialpose_listener_start.log 2>/dev/null || true
  }
else
  echo "[loc-only] 2D Pose Estimate listener disabled for no-manual startup"
  pkill -f "carto_initialpose_once.py" || true
fi

echo "[loc-only] opening RViz localization view"
DISPLAY=:0 \
XDG_RUNTIME_DIR=/run/user/1000 \
XAUTHORITY="$(ls /run/user/1000/.mutter-Xwaylandauth.* 2>/dev/null | head -n 1)" \
LIBGL_ALWAYS_SOFTWARE=1 \
QT_OPENGL=software \
MESA_LOADER_DRIVER_OVERRIDE=llvmpipe \
nohup rviz2 -d /mnt/sdcard/medicine_robot_data/config/rk3588_nav2_view.rviz \
  > "$RVIZ_LOG" 2>&1 &

echo "[loc-only] ready: localization-only graph"
ros2 node list | sort | grep -E "cartographer|static_map|rviz|sllidar|base_to_laser|chassis" || true
echo "[loc-only] Nav2 is intentionally not running in this stage"
