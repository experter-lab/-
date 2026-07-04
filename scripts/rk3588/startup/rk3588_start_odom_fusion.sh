#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

RF2O_LOG="${RF2O_LOG:-/tmp/rk3588_rf2o_odom_raw.log}"
GUARD_LOG="${GUARD_LOG:-/tmp/rk3588_guarded_odom.log}"
EKF_LOG="${EKF_LOG:-/tmp/rk3588_ekf_odom.log}"
EKF_CONFIG="${EKF_CONFIG:-/mnt/sdcard/medicine_robot_data/config/rk3588_ekf_odom.yaml}"
GUARD_SCRIPT="${GUARD_SCRIPT:-/mnt/sdcard/medicine_robot_data/scripts/rk3588_guarded_odom.py}"
GUARD_RAW_X_SIGN="${GUARD_RAW_X_SIGN:--1.0}"
GUARD_RAW_Y_SIGN="${GUARD_RAW_Y_SIGN:--1.0}"

topic_pub_count() {
  ros2 topic info "$1" 2>/dev/null | awk '/Publisher count:/ {print $3; found=1} END {if (!found) print 0}'
}

node_exists() {
  ros2 node list 2>/dev/null | grep -Fxq "$1"
}

wait_for_topic_pub_count() {
  local topic="$1"
  local expected="$2"
  local seconds="$3"
  for _ in $(seq 1 "$seconds"); do
    if [[ "$(topic_pub_count "$topic")" = "$expected" ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
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

wait_for_tf() {
  local parent="$1"
  local child="$2"
  local seconds="$3"
  for _ in $(seq 1 "$seconds"); do
    timeout 3 ros2 run tf2_ros tf2_echo "$parent" "$child" >/tmp/rk3588_odom_fusion_tf_check.log 2>&1 || true
    if grep -q "Translation:" /tmp/rk3588_odom_fusion_tf_check.log; then
      return 0
    fi
    sleep 1
  done
  return 1
}

kill_pattern() {
  local pattern="$1"
  if pgrep -f "$pattern" >/dev/null 2>&1; then
    echo "[odom-fusion] stopping stale process: $pattern"
    pkill -f "$pattern" || true
  fi
}

if ! ros2 pkg prefix robot_localization >/dev/null 2>&1; then
  echo "[odom-fusion] ERROR: robot_localization is not installed"
  echo "[odom-fusion] install package: sudo apt install ros-humble-robot-localization"
  exit 1
fi

if [[ ! -f "$EKF_CONFIG" ]]; then
  echo "[odom-fusion] ERROR: missing EKF config: $EKF_CONFIG"
  exit 1
fi

if [[ ! -f "$GUARD_SCRIPT" ]]; then
  echo "[odom-fusion] ERROR: missing guarded odom script: $GUARD_SCRIPT"
  exit 1
fi

echo "[odom-fusion] resetting odom chain"
kill_pattern "rk3588_tf_odom_publisher.py"
kill_pattern "rk3588_guarded_odom.py"
kill_pattern "robot_localization.*ekf_node"
kill_pattern "ekf_node"
kill_pattern "rf2o_laser_odometry_node"
sleep 2

if [[ "$(topic_pub_count /scan)" != "1" ]]; then
  echo "[odom-fusion] ERROR: /scan publisher count must be 1"
  ros2 topic info /scan 2>/dev/null || true
  exit 1
fi

if [[ "$(topic_pub_count /imu)" != "1" ]]; then
  echo "[odom-fusion] ERROR: /imu publisher count must be 1"
  ros2 topic info /imu 2>/dev/null || true
  exit 1
fi

echo "[odom-fusion] starting RF2O raw odometry"
RF2O_LOG="$RF2O_LOG" \
RF2O_ODOM_TOPIC="/rf2o/odom_raw" \
RF2O_PUBLISH_TF="false" \
RF2O_STATIC_DRIFT_SECONDS="0" \
  /mnt/sdcard/rk3588_start_rf2o_odom.sh

wait_for_topic_pub_count /rf2o/odom_raw 1 60 || {
  echo "[odom-fusion] ERROR: /rf2o/odom_raw publisher count is not 1"
  ros2 topic info /rf2o/odom_raw 2>/dev/null || true
  tail -120 "$RF2O_LOG" 2>/dev/null || true
  exit 1
}

echo "[odom-fusion] starting guarded odom"
: > "$GUARD_LOG"
nohup python3 "$GUARD_SCRIPT" --ros-args \
  -p raw_x_sign:="$GUARD_RAW_X_SIGN" \
  -p raw_y_sign:="$GUARD_RAW_Y_SIGN" \
  > "$GUARD_LOG" 2>&1 &
echo "[odom-fusion] guarded odom pid: $!"

wait_for_node /rk3588_guarded_odom 20 || {
  echo "[odom-fusion] ERROR: guarded odom node is not visible"
  tail -120 "$GUARD_LOG" 2>/dev/null || true
  exit 1
}

wait_for_topic_pub_count /odom_rf2o_guarded 1 30 || {
  echo "[odom-fusion] ERROR: /odom_rf2o_guarded publisher count is not 1"
  ros2 topic info /odom_rf2o_guarded 2>/dev/null || true
  tail -120 "$GUARD_LOG" 2>/dev/null || true
  exit 1
}

echo "[odom-fusion] starting EKF official odom"
: > "$EKF_LOG"
nohup ros2 run robot_localization ekf_node --ros-args \
  -r __node:=ekf_filter_node \
  -r odometry/filtered:=/odom \
  --params-file "$EKF_CONFIG" \
  > "$EKF_LOG" 2>&1 &
echo "[odom-fusion] ekf pid: $!"

wait_for_node /ekf_filter_node 30 || {
  echo "[odom-fusion] ERROR: /ekf_filter_node is not visible"
  tail -160 "$EKF_LOG" 2>/dev/null || true
  exit 1
}

wait_for_topic_pub_count /odom 1 40 || {
  echo "[odom-fusion] ERROR: /odom publisher count is not 1"
  ros2 topic info /odom 2>/dev/null || true
  tail -160 "$EKF_LOG" 2>/dev/null || true
  exit 1
}

wait_for_tf odom base_link 30 || {
  echo "[odom-fusion] ERROR: missing TF odom -> base_link from EKF"
  cat /tmp/rk3588_odom_fusion_tf_check.log 2>/dev/null || true
  tail -160 "$EKF_LOG" 2>/dev/null || true
  exit 1
}

echo "[odom-fusion] ready: /rf2o/odom_raw + /odom_rf2o_guarded + /odom; EKF owns odom->base_link"
