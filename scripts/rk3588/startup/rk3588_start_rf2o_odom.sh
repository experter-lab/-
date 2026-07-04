#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG="${RF2O_LOG:-/tmp/rk3588_rf2o_odom.log}"
SCAN_TOPIC="${RF2O_SCAN_TOPIC:-/scan}"
ODOM_TOPIC="${RF2O_ODOM_TOPIC:-/rf2o/odom_raw}"
RF2O_FREQ="${RF2O_FREQ:-10.0}"
RF2O_NODE_NAME="${RF2O_NODE_NAME:-/CLaserOdometry2DNode}"
RF2O_PUBLISH_TF="${RF2O_PUBLISH_TF:-false}"
if [[ "$RF2O_PUBLISH_TF" = "true" ]]; then
  BASE_FRAME="${RF2O_BASE_FRAME:-base_link}"
  ODOM_FRAME="${RF2O_ODOM_FRAME:-odom}"
else
  # RF2O still needs a real base frame that can transform to the laser frame.
  # Any stray TF is isolated below by remapping /tf away from the official tree.
  BASE_FRAME="${RF2O_BASE_FRAME:-base_link}"
  ODOM_FRAME="${RF2O_ODOM_FRAME:-rf2o_odom_raw}"
fi
RF2O_STATIC_DRIFT_SECONDS="${RF2O_STATIC_DRIFT_SECONDS:-0}"
RF2O_STATIC_DRIFT_MAX_XY="${RF2O_STATIC_DRIFT_MAX_XY:-0.05}"
RF2O_STATIC_DRIFT_MAX_YAW_DEG="${RF2O_STATIC_DRIFT_MAX_YAW_DEG:-2.0}"

node_count() {
  ros2 node list 2>/dev/null | grep -Fx "$1" | wc -l | tr -d ' '
}

topic_pub_count() {
  ros2 topic info "$1" 2>/dev/null | awk '/Publisher count:/ {print $3; found=1} END {if (!found) print 0}'
}

wait_for_single_topic_pub() {
  local topic_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    if [[ "$(topic_pub_count "$topic_name")" = "1" ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_node_present() {
  local node_name="$1"
  local seconds="$2"
  for _ in $(seq 1 "$seconds"); do
    if [[ "$(node_count "$node_name")" -ge 1 ]]; then
      return 0
    fi
    sleep 1
  done
  return 1
}

wait_for_scan_message() {
  local seconds="$1"
  for _ in $(seq 1 "$seconds"); do
    if timeout 2 ros2 topic echo "$SCAN_TOPIC" --once >/tmp/rk3588_rf2o_scan_check.log 2>&1; then
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
    timeout 3 ros2 run tf2_ros tf2_echo "$parent" "$child" >/tmp/rk3588_rf2o_tf_check.log 2>&1 || true
    if grep -q "Translation:" /tmp/rk3588_rf2o_tf_check.log; then
      return 0
    fi
    sleep 1
  done
  return 1
}

sample_odom_pose() {
  local output="$1"
  timeout 5 ros2 topic echo "$ODOM_TOPIC" --once >/tmp/rk3588_rf2o_odom_sample.txt 2>/tmp/rk3588_rf2o_odom_sample.err || return 1
  awk -v output="$output" '
    /position:/ {in_pos=1; in_ori=0; next}
    /orientation:/ {in_ori=1; in_pos=0; next}
    in_pos && /^[[:space:]]*x:/ {x=$2}
    in_pos && /^[[:space:]]*y:/ {y=$2}
    in_ori && /^[[:space:]]*z:/ {z=$2}
    in_ori && /^[[:space:]]*w:/ {w=$2}
    END {
      if (x == "" || y == "" || z == "" || w == "") {
        exit 1
      }
      yaw = atan2(2.0 * w * z, 1.0 - 2.0 * z * z)
      printf "%s %.9f %.9f %.9f\n", output, x, y, yaw
    }
  ' /tmp/rk3588_rf2o_odom_sample.txt
}

check_static_drift() {
  local seconds="$1"
  local max_xy="$2"
  local max_yaw_deg="$3"
  local start_line end_line

  if [[ "$seconds" = "0" || "$seconds" = "0.0" ]]; then
    echo "[rf2o-odom] static drift check disabled"
    return 0
  fi

  start_line="$(sample_odom_pose start)" || {
    echo "[rf2o-odom] ERROR: cannot sample initial $ODOM_TOPIC pose"
    cat /tmp/rk3588_rf2o_odom_sample.err 2>/dev/null || true
    return 1
  }
  echo "[rf2o-odom] static drift check: holding $seconds seconds"
  sleep "$seconds"
  end_line="$(sample_odom_pose end)" || {
    echo "[rf2o-odom] ERROR: cannot sample final $ODOM_TOPIC pose"
    cat /tmp/rk3588_rf2o_odom_sample.err 2>/dev/null || true
    return 1
  }

  awk -v start_line="$start_line" -v end_line="$end_line" -v max_xy="$max_xy" -v max_yaw_deg="$max_yaw_deg" '
    function abs(v) { return v < 0 ? -v : v }
    function norm_angle(a) {
      while (a > 3.141592653589793) a -= 6.283185307179586
      while (a < -3.141592653589793) a += 6.283185307179586
      return a
    }
    BEGIN {
      split(start_line, s, " ")
      split(end_line, e, " ")
      dx = e[2] - s[2]
      dy = e[3] - s[3]
      dyaw = norm_angle(e[4] - s[4])
      xy = sqrt(dx * dx + dy * dy)
      yaw_deg = abs(dyaw) * 180.0 / 3.141592653589793
      printf "[rf2o-odom] static drift: xy=%.4fm yaw=%.3fdeg start=(%.3f,%.3f,%.2fdeg) end=(%.3f,%.3f,%.2fdeg)\n", xy, yaw_deg, s[2], s[3], s[4] * 180.0 / 3.141592653589793, e[2], e[3], e[4] * 180.0 / 3.141592653589793
      if (xy > max_xy || yaw_deg > max_yaw_deg) {
        printf "[rf2o-odom] ERROR: static drift exceeds limits xy<=%.4fm yaw<=%.3fdeg\n", max_xy, max_yaw_deg
        exit 1
      }
    }
  '
}

echo "[rf2o-odom] resetting RF2O odometry state"

if pgrep -f "rk3588_tf_odom_publisher.py" >/dev/null 2>&1; then
  echo "[rf2o-odom] stopping obsolete TF-to-/odom publisher"
  pkill -f "rk3588_tf_odom_publisher.py" || true
  sleep 1
fi

if pgrep -f "rf2o_laser_odometry_node" >/dev/null 2>&1; then
  echo "[rf2o-odom] stopping stale RF2O process"
  pkill -f "rf2o_laser_odometry_node" || true
  sleep 3
fi

wait_for_single_topic_pub "$SCAN_TOPIC" 20 || {
  echo "[rf2o-odom] ERROR: $SCAN_TOPIC publisher count is not exactly 1"
  ros2 topic info "$SCAN_TOPIC" 2>/dev/null || true
  exit 1
}

wait_for_scan_message 20 || {
  echo "[rf2o-odom] ERROR: no scan messages on $SCAN_TOPIC"
  cat /tmp/rk3588_rf2o_scan_check.log 2>/dev/null || true
  exit 1
}

echo "[rf2o-odom] starting RF2O raw: scan=$SCAN_TOPIC odom=$ODOM_TOPIC publish_tf=$RF2O_PUBLISH_TF frames=$ODOM_FRAME->$BASE_FRAME"
: > "$LOG"
nohup ros2 run rf2o_laser_odometry rf2o_laser_odometry_node --ros-args \
  -p laser_scan_topic:="$SCAN_TOPIC" \
  -p odom_topic:="$ODOM_TOPIC" \
  -p publish_tf:="$RF2O_PUBLISH_TF" \
  -p base_frame_id:="$BASE_FRAME" \
  -p odom_frame_id:="$ODOM_FRAME" \
  -p freq:="$RF2O_FREQ" \
  -r /tf:=/tf_rf2o_unused \
  > "$LOG" 2>&1 &
echo "[rf2o-odom] pid: $!"

wait_for_node_present "$RF2O_NODE_NAME" 30 || {
  echo "[rf2o-odom] ERROR: $RF2O_NODE_NAME node is not visible"
  ros2 node list 2>/dev/null | sort | grep -E "CLaser|rf2o|odom" || true
  tail -120 "$LOG" 2>/dev/null || true
  exit 1
}

if [[ "$(node_count "$RF2O_NODE_NAME")" != "1" ]]; then
  echo "[rf2o-odom] WARN: ros2 node list shows $(node_count "$RF2O_NODE_NAME") entries for $RF2O_NODE_NAME; continuing only because raw odom output is validated below"
fi

wait_for_single_topic_pub "$ODOM_TOPIC" 60 || {
  echo "[rf2o-odom] ERROR: $ODOM_TOPIC publisher count is not exactly 1"
  ros2 topic info "$ODOM_TOPIC" 2>/dev/null || true
  tail -120 "$LOG" 2>/dev/null || true
  exit 1
}

if [[ "$RF2O_PUBLISH_TF" = "true" ]]; then
  wait_for_tf "$ODOM_FRAME" "$BASE_FRAME" 20 || {
    echo "[rf2o-odom] ERROR: missing TF $ODOM_FRAME -> $BASE_FRAME"
    cat /tmp/rk3588_rf2o_tf_check.log 2>/dev/null || true
    tail -120 "$LOG" 2>/dev/null || true
    exit 1
  }
else
  echo "[rf2o-odom] RF2O TF disabled; EKF must own $ODOM_FRAME -> $BASE_FRAME"
fi

check_static_drift "$RF2O_STATIC_DRIFT_SECONDS" "$RF2O_STATIC_DRIFT_MAX_XY" "$RF2O_STATIC_DRIFT_MAX_YAW_DEG" || {
  tail -120 "$LOG" 2>/dev/null || true
  pkill -f "rf2o_laser_odometry_node" || true
  exit 1
}

echo "[rf2o-odom] ready: $(topic_pub_count "$ODOM_TOPIC") publisher on $ODOM_TOPIC, RF2O node=$RF2O_NODE_NAME count=$(node_count "$RF2O_NODE_NAME"), freq=$RF2O_FREQ publish_tf=$RF2O_PUBLISH_TF"
