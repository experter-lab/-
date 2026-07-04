#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PARAM_FILE="${1:-/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_params.yaml}"
PBSTREAM="${2:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream}"
MAP_YAML="${3:-/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static.yaml}"
INITIAL_POSE_FILE="${INITIAL_POSE_FILE:-/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json}"
LIDAR_MOUNT_ENV="${LIDAR_MOUNT_ENV:-/mnt/sdcard/medicine_robot_data/config/lidar_mount.env}"
if [[ -f "$LIDAR_MOUNT_ENV" ]]; then
  # shellcheck disable=SC1090
  source "$LIDAR_MOUNT_ENV"
fi
NAV2_LOG=/tmp/rk3588_nav2_carto_navigation.log
RF2O_LOG=/tmp/rk3588_rf2o_odom.log
GUARD_LOG=/tmp/rk3588_guarded_odom.log
EKF_LOG=/tmp/rk3588_ekf_odom.log
ODOM_FUSION_LOG=/tmp/rk3588_odom_fusion.log
CARTO_LOG=/tmp/rk3588_carto_localization.log
MAP_LOG=/tmp/rk3588_static_map_server.log
RELOC_LOG=/tmp/carto_reloc.log
AUTO_POSE_LOG=/tmp/rk3588_carto_apply_saved_pose.log
AUTO_SCAN_MATCH_LOG=/tmp/rk3588_carto_auto_scan_match_pose.log
ENABLE_DRIVE="${NAV2_ENABLE_DRIVE:-0}"
CARTO_STARTED=0
LOCAL_REFINE_INITIAL_POSE="${LOCAL_REFINE_INITIAL_POSE:-1}"
AUTO_GLOBAL_INITIAL_POSE="${AUTO_GLOBAL_INITIAL_POSE:-1}"
ALLOW_GLOBAL_SCAN_MATCH="${ALLOW_GLOBAL_SCAN_MATCH:-$AUTO_GLOBAL_INITIAL_POSE}"
LOCAL_SCAN_MATCH_XY_WINDOW="${LOCAL_SCAN_MATCH_XY_WINDOW:-0.5}"
LOCAL_SCAN_MATCH_YAW_WINDOW_DEG="${LOCAL_SCAN_MATCH_YAW_WINDOW_DEG:-20}"
GLOBAL_SCAN_MATCH_MAX_SCORE="${GLOBAL_SCAN_MATCH_MAX_SCORE:-0.18}"
GLOBAL_SCAN_MATCH_MIN_SCORE_GAP="${GLOBAL_SCAN_MATCH_MIN_SCORE_GAP:-0.05}"
GLOBAL_SCAN_MATCH_MIN_SCORE_RATIO="${GLOBAL_SCAN_MATCH_MIN_SCORE_RATIO:-1.25}"

laser_yaw_deg() {
  python3 - <<'PY'
import math
import os

print(math.degrees(float(os.environ.get("LIDAR_LASER_YAW", "0.0"))))
PY
}

node_exists() {
  local node_name="$1"
  local nodes
  nodes="$(ros2 node list 2>/dev/null || true)"
  grep -Fxq "$node_name" <<< "$nodes"
}

topic_has_pub() {
  local topic_name="$1"
  local info
  info="$(ros2 topic info "$topic_name" 2>/dev/null || true)"
  grep -Eq "Publisher count: [1-9]" <<< "$info"
}

action_exists() {
  local action_name="$1"
  local actions
  actions="$(ros2 action list 2>/dev/null || true)"
  grep -Fxq "$action_name" <<< "$actions"
}

action_server_exists() {
  local action_name="$1"
  local info
  info="$(timeout 6s ros2 action info "$action_name" 2>/dev/null || true)"
  grep -Eq "Action servers: [1-9]" <<< "$info"
}

process_exists() {
  local pattern="$1"
  pgrep -f "$pattern" >/dev/null 2>&1
}

carto_running() {
  process_exists "cartographer_node.*rk3588_carto_localization.lua" &&
    process_exists "cartographer_occupancy_grid_node"
}

carto_matches_pbstream() {
  pgrep -fa "cartographer_node.*rk3588_carto_localization.lua" |
    grep -F -- "$PBSTREAM" >/dev/null 2>&1
}

stop_cartographer_localization() {
  pkill -f "cartographer_node.*rk3588_carto_localization.lua" || true
  pkill -f "cartographer_occupancy_grid_node" || true
  pkill -f "rk3588_start_carto_localization.sh" || true
  sleep 2
}

odom_fusion_running() {
  process_exists "rf2o_laser_odometry_node" &&
    process_exists "rk3588_guarded_odom.py" &&
    node_exists /ekf_filter_node &&
    topic_has_pub /rf2o/odom_raw &&
    topic_has_pub /odom_rf2o_guarded &&
    topic_has_pub /odom
}

reloc_bridge_running() {
  process_exists "carto_relocalize_bridge.py" && node_exists /carto_reloc_bridge
}

static_map_running() {
  node_exists /static_map_server && topic_has_pub /map_static
}

nav2_launch_count() {
  pgrep -fc "nav2_bringup navigation_launch.py" || true
}

nav2_uses_static_map() {
  local topic
  topic="$(ros2 param get /global_costmap/global_costmap static_layer.map_topic 2>/dev/null || true)"
  grep -Fq "/map_static" <<< "$topic"
}

nav2_running() {
  [[ "$(nav2_launch_count)" = "1" ]] &&
    node_exists /controller_server &&
    node_exists /planner_server &&
    node_exists /bt_navigator &&
    node_exists /velocity_smoother &&
    nav2_uses_static_map
}

stop_nav2() {
  pkill -f "nav2_bringup navigation_launch.py" || true
  pkill -f "nav2_controller/controller_server" || true
  pkill -f "nav2_planner/planner_server" || true
  pkill -f "nav2_bt_navigator/bt_navigator" || true
  pkill -f "nav2_behaviors/behavior_server" || true
  pkill -f "nav2_velocity_smoother/velocity_smoother" || true
  pkill -f "nav2_waypoint_follower/waypoint_follower" || true
  pkill -f "nav2_lifecycle_manager/lifecycle_manager" || true
  sleep 3
}

wait_for_node() {
  local node_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    if node_exists "$node_name"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_topic_pub() {
  local topic_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    if topic_has_pub "$topic_name"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_action() {
  local action_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    if action_exists "$action_name" && action_server_exists "$action_name"; then
      return 0
    fi
    sleep 1
  done
  return 1
}

lifecycle_state() {
  local node_name="$1"
  local state
  state="$(timeout 5s ros2 lifecycle get "/$node_name" 2>/dev/null || true)"
  state="${state%% *}"
  echo "$state"
}

ensure_lifecycle_active() {
  local node_name="$1"
  local state
  local log="/tmp/rk3588_nav2_lifecycle_${node_name}.log"

  for _ in $(seq 1 6); do
    state="$(lifecycle_state "$node_name")"
    echo "[nav2-carto] lifecycle $node_name state=${state:-unknown}"
    case "$state" in
      active)
        return 0
        ;;
      unconfigured)
        timeout 20s ros2 lifecycle set "/$node_name" configure >"$log" 2>&1 || true
        ;;
      inactive)
        timeout 20s ros2 lifecycle set "/$node_name" activate >"$log" 2>&1 || true
        ;;
      *)
        sleep 2
        ;;
    esac
  done

  echo "[nav2-carto] ERROR: lifecycle $node_name did not become active"
  cat "$log" 2>/dev/null || true
  return 1
}

recover_nav2_lifecycles() {
  local node_name
  for node_name in \
    controller_server \
    smoother_server \
    planner_server \
    behavior_server \
    bt_navigator \
    waypoint_follower \
    velocity_smoother; do
    ensure_lifecycle_active "$node_name" || return 1
  done
}

ensure_brake_safe() {
  local log=/tmp/rk3588_nav2_brake_check.log
  echo "[safety] checking brake state"
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
  echo "[nav2-carto] pbstream sha256: $(hash_file "$PBSTREAM")"
  echo "[nav2-carto] static map sha256: $(hash_file "$MAP_YAML")"
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
actual_map = sha256_file(map_yaml_path)

if expected_pbstream != actual_pbstream:
    print(
        "POSE_MAP_MISMATCH pbstream "
        f"pose={expected_pbstream} current={actual_pbstream}"
    )
    raise SystemExit(1)

if expected_map and expected_map != actual_map:
    print(
        "POSE_MAP_MISMATCH map_yaml "
        f"pose={expected_map} current={actual_map}"
    )
    raise SystemExit(1)

print("POSE_MAP_MATCH")
PY
}

call_bool() {
  local service="$1"
  local value="$2"
  local label="$3"
  local services
  services="$(ros2 service list 2>/dev/null || true)"
  if grep -Fxq "$service" <<< "$services"; then
    echo "[chassis] $label"
    timeout 8 ros2 service call "$service" std_srvs/srv/SetBool "{data: $value}" >/tmp/rk3588_nav2_last_service_call.log 2>&1 || {
      echo "[chassis] WARN: service call failed: $service"
      cat /tmp/rk3588_nav2_last_service_call.log
      return 1
    }
  else
    echo "[chassis] WARN: missing service: $service"
    return 1
  fi
}

if [[ ! -f "$PARAM_FILE" ]]; then
  echo "[nav2-carto] ERROR: missing params file: $PARAM_FILE"
  exit 1
fi

if [[ ! -f "$PBSTREAM" ]]; then
  echo "[nav2-carto] ERROR: missing pbstream: $PBSTREAM"
  exit 1
fi

if [[ ! -f "$MAP_YAML" ]]; then
  echo "[nav2-carto] ERROR: missing map yaml: $MAP_YAML"
  exit 1
fi

echo "[nav2-carto] pbstream: $PBSTREAM"
echo "[nav2-carto] static map: $MAP_YAML"
print_map_hashes

ensure_brake_safe

if pgrep -f "rk3588_keyboard_drive.py" >/dev/null 2>&1; then
  echo "[nav2-carto] stopping keyboard drive to release /cmd_vel"
  pkill -INT -f "rk3588_keyboard_drive.py" || true
  sleep 2
fi

if pgrep -f "rk3588_tf_odom_publisher.py" >/dev/null 2>&1; then
  echo "[nav2-carto] stopping obsolete TF-to-/odom publisher"
  pkill -f "rk3588_tf_odom_publisher.py" || true
  sleep 1
fi

echo "[nav2-carto] starting guarded RF2O + IMU + EKF odom fusion"
RF2O_LOG="$RF2O_LOG" GUARD_LOG="$GUARD_LOG" EKF_LOG="$EKF_LOG" \
  /mnt/sdcard/rk3588_start_odom_fusion.sh > "$ODOM_FUSION_LOG" 2>&1 || {
  echo "[nav2-carto] ERROR: odom fusion failed"
  tail -160 "$ODOM_FUSION_LOG" 2>/dev/null || true
  tail -120 "$RF2O_LOG" 2>/dev/null || true
  tail -120 "$GUARD_LOG" 2>/dev/null || true
  tail -120 "$EKF_LOG" 2>/dev/null || true
  exit 1
}
cat "$ODOM_FUSION_LOG"

if carto_running || (node_exists /cartographer_node && node_exists /cartographer_occupancy_grid_node); then
  if carto_matches_pbstream; then
    echo "[nav2-carto] Cartographer localization already running with matching pbstream"
  else
    echo "[nav2-carto] restarting Cartographer localization: running pbstream does not match $PBSTREAM"
    stop_cartographer_localization
    echo "[nav2-carto] starting Cartographer localization"
    START_ODOM_FUSION=0 nohup /mnt/sdcard/rk3588_start_carto_localization.sh "$PBSTREAM" > "$CARTO_LOG" 2>&1 &
    echo "[nav2-carto] cartographer launch pid: $!"
    CARTO_STARTED=1
  fi
else
  echo "[nav2-carto] starting Cartographer localization"
  START_ODOM_FUSION=0 nohup /mnt/sdcard/rk3588_start_carto_localization.sh "$PBSTREAM" > "$CARTO_LOG" 2>&1 &
  echo "[nav2-carto] cartographer launch pid: $!"
  CARTO_STARTED=1
fi

wait_for_node /cartographer_node 30 || {
  echo "[nav2-carto] ERROR: cartographer_node not ready"
  tail -80 "$CARTO_LOG" 2>/dev/null || true
  exit 1
}

if [[ "${AUTO_INITIAL_POSE:-1}" = "1" ]] &&
  pose_file_valid "$INITIAL_POSE_FILE" >/tmp/rk3588_initial_pose_validate.log 2>&1 &&
  pose_file_matches_current_map "$INITIAL_POSE_FILE" >/tmp/rk3588_initial_pose_map_match.log 2>&1; then
  echo "[nav2-carto] initial pose source: saved_pose"
  echo "[nav2-carto] applying saved Cartographer initial pose: $INITIAL_POSE_FILE"
  if python3 /mnt/sdcard/medicine_robot_data/scripts/carto_apply_saved_pose.py \
    --pose-file "$INITIAL_POSE_FILE" \
    --relative-to-trajectory-id latest > "$AUTO_POSE_LOG" 2>&1; then
    tail -30 "$AUTO_POSE_LOG"
  else
    echo "[nav2-carto] WARN: failed to apply saved initial pose"
    cat "$AUTO_POSE_LOG" 2>/dev/null || true
  fi
  if [[ "$LOCAL_REFINE_INITIAL_POSE" = "1" &&
    "${AUTO_SCAN_MATCH_POSE:-1}" = "1" &&
    -f /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py ]]; then
    echo "[nav2-carto] initial pose source: local_refine"
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
      echo "[nav2-carto] WARN: local scan-match refine failed; keeping saved pose result"
      cat "$AUTO_SCAN_MATCH_LOG" 2>/dev/null || true
    fi
  fi
elif [[ "${AUTO_SCAN_MATCH_POSE:-1}" = "1" &&
  -f /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py &&
  "$ALLOW_GLOBAL_SCAN_MATCH" = "1" &&
  ( "$CARTO_STARTED" = "1" || "${APPLY_INITIAL_POSE_ALWAYS:-0}" = "1" ) ]]; then
  echo "[nav2-carto] initial pose source: global_auto_bootstrap"
  echo "[nav2-carto] no saved pose; running guarded whole-map scan-match"
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
    echo "[nav2-carto] accepted automatic initial pose and saved it to $INITIAL_POSE_FILE"
  else
    echo "[nav2-carto] WARN: guarded whole-map scan-match failed or was ambiguous; no pose was applied"
    cat "$AUTO_SCAN_MATCH_LOG" 2>/dev/null || true
    if [[ "${REQUIRE_INITIAL_POSE_FOR_NAV2:-1}" = "1" ]]; then
      ensure_brake_safe
      exit 2
    fi
  fi
else
  echo "[nav2-carto] initial pose source: manual_required"
  echo "[nav2-carto] no valid saved pose and automatic bootstrap is disabled or unavailable"
  if [[ -f /tmp/rk3588_initial_pose_map_match.log ]]; then
    cat /tmp/rk3588_initial_pose_map_match.log 2>/dev/null || true
  fi
  if [[ "${REQUIRE_INITIAL_POSE_FOR_NAV2:-1}" = "1" ]]; then
    echo "[nav2-carto] ERROR: guarded automatic startup did not produce a trusted initial pose"
    echo "[nav2-carto] keep Nav2 drive disabled; do not authorize motion until localization is visually verified"
    cat /tmp/rk3588_initial_pose_validate.log 2>/dev/null || true
    ensure_brake_safe
    exit 2
  fi
fi

wait_for_topic_pub /map 90 || {
  echo "[nav2-carto] ERROR: /map has no publisher"
  ros2 node list
  ros2 topic info /map 2>/dev/null || true
  exit 1
}

if [[ "${ENABLE_RELOC_BRIDGE:-0}" = "1" && -f /mnt/sdcard/medicine_robot_data/scripts/carto_relocalize_bridge.py ]]; then
  if reloc_bridge_running; then
    echo "[nav2-carto] Cartographer relocalize bridge already running"
  else
    echo "[nav2-carto] starting Cartographer relocalize bridge for RViz 2D Pose Estimate"
    pkill -f "carto_relocalize_bridge.py" || true
    nohup python3 /mnt/sdcard/medicine_robot_data/scripts/carto_relocalize_bridge.py > "$RELOC_LOG" 2>&1 &
    echo "[nav2-carto] relocalize bridge pid: $!"
  fi
else
  echo "[nav2-carto] relocalize bridge disabled; /initialpose is not wired in this startup"
  pkill -f "carto_relocalize_bridge.py" || true
fi

if static_map_running || node_exists /static_map_server; then
  echo "[nav2-carto] restarting static map server"
  pkill -f "nav2_map_server.*static_map_server" || true
  pkill -f "map_server.*static_map_server" || true
  sleep 2
fi

echo "[nav2-carto] starting static map server"
nohup ros2 run nav2_map_server map_server --ros-args \
  -r __node:=static_map_server \
  -p yaml_filename:="$MAP_YAML" \
  -p topic_name:=/map_static \
  -p frame_id:=map \
  > "$MAP_LOG" 2>&1 &
echo "[nav2-carto] static map server pid: $!"
wait_for_node /static_map_server 15 || {
  echo "[nav2-carto] ERROR: static_map_server not ready"
  tail -80 "$MAP_LOG" 2>/dev/null || true
  exit 1
}
timeout 8 ros2 lifecycle set /static_map_server configure >/tmp/rk3588_static_map_lifecycle.log 2>&1 || true
timeout 8 ros2 lifecycle set /static_map_server activate >>/tmp/rk3588_static_map_lifecycle.log 2>&1 || true

wait_for_topic_pub /map_static 20 || {
  echo "[nav2-carto] ERROR: /map_static has no publisher"
  tail -80 "$MAP_LOG" 2>/dev/null || true
  cat /tmp/rk3588_static_map_lifecycle.log 2>/dev/null || true
  exit 1
}

if nav2_running; then
  echo "[nav2-carto] Nav2 already running"
else
  if process_exists "nav2_bringup navigation_launch.py" ||
    node_exists /controller_server ||
    node_exists /planner_server ||
    node_exists /bt_navigator ||
    node_exists /velocity_smoother; then
    echo "[nav2-carto] restarting Nav2 navigation stack: duplicate process or stale map_topic"
    stop_nav2
  fi
  echo "[nav2-carto] starting Nav2 navigation stack"
  nohup ros2 launch nav2_bringup navigation_launch.py \
    params_file:="$PARAM_FILE" use_sim_time:=false autostart:=true \
    > "$NAV2_LOG" 2>&1 &
  echo "[nav2-carto] nav2 launch pid: $!"
fi

if ! wait_for_action /navigate_to_pose 60; then
  echo "[nav2-carto] WARN: /navigate_to_pose action not ready; attempting Nav2 lifecycle recovery"
  recover_nav2_lifecycles || {
    echo "[nav2-carto] ERROR: Nav2 lifecycle recovery failed"
    tail -160 "$NAV2_LOG" 2>/dev/null || true
    exit 1
  }
  wait_for_action /navigate_to_pose 30 || {
    echo "[nav2-carto] ERROR: /navigate_to_pose action not available after lifecycle recovery"
    tail -160 "$NAV2_LOG" 2>/dev/null || true
    exit 1
  }
fi

if node_exists /chassis_bridge; then
  if [[ "$ENABLE_DRIVE" = "1" ]]; then
    if [[ "${CONFIRM_NAV2_DRIVE:-0}" != "1" ]]; then
      echo "[chassis] REFUSED: NAV2_ENABLE_DRIVE=1 also requires CONFIRM_NAV2_DRIVE=1"
      ensure_brake_safe
      exit 2
    fi
    call_bool /chassis_bridge/authorize_control true "authorize_control=true" || true
    call_bool /chassis_bridge/set_emergency_stop false "set_emergency_stop=false" || true
    sleep 0.5
    call_bool /chassis_bridge/set_mode true "set_mode=MANUAL" || true
    sleep 0.5
    call_bool /chassis_bridge/arm true "arm=true" || true
  else
    echo "[chassis] NAV2_ENABLE_DRIVE=0; enforcing BRAKE_STATUS_SAFE"
    ensure_brake_safe
  fi
else
  echo "[chassis] WARN: chassis_bridge not running; Nav2 can plan but cannot drive"
fi

echo "[nav2-carto] ready"
ros2 action list | grep -E "navigate|follow|spin|backup|wait" || true
