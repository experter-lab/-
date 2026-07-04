#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

DISTANCE="${1:-0.12}"
LATERAL="${2:-0.00}"
YAW_DELTA="${3:-0.00}"
DRY_RUN=0
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
  DISTANCE="${2:-0.12}"
  LATERAL="${3:-0.00}"
  YAW_DELTA="${4:-0.00}"
fi
RESULT_LOG=/tmp/rk3588_nav2_short_goal_result.log

safe_stop() {
  /mnt/sdcard/rk3588_safe_stop.sh >/tmp/rk3588_nav2_short_goal_safestop.log 2>&1 || true
}

trap safe_stop EXIT

echo "[short-goal] before brake"
/mnt/sdcard/rk3588_check_brake_status.sh || true

echo "[short-goal] before odom"
timeout 5 ros2 topic echo /odom --once --field pose.pose || true

echo "[short-goal] computing relative map goal distance=$DISTANCE lateral=$LATERAL yaw_delta=$YAW_DELTA"
GOAL_VALUES="$(python3 - "$DISTANCE" "$LATERAL" "$YAW_DELTA" <<'PY'
import math
import sys
import time

import rclpy
from rclpy.duration import Duration
from rclpy.time import Time
from tf2_ros import Buffer, TransformListener

distance = float(sys.argv[1])
lateral = float(sys.argv[2])
yaw_delta = float(sys.argv[3])

if abs(distance) > 0.20 or abs(lateral) > 0.10 or abs(yaw_delta) > 0.35:
    raise SystemExit(
        f"refusing oversized short goal: distance={distance} lateral={lateral} yaw_delta={yaw_delta}"
    )

rclpy.init()
node = rclpy.create_node("rk3588_short_goal_tf_lookup")
buffer = Buffer()
listener = TransformListener(buffer, node)
deadline = time.monotonic() + 5.0
transform = None
while time.monotonic() < deadline:
    rclpy.spin_once(node, timeout_sec=0.1)
    try:
        transform = buffer.lookup_transform("map", "base_link", Time(), timeout=Duration(seconds=0.2))
        break
    except Exception:
        pass
if transform is None:
    node.destroy_node()
    rclpy.shutdown()
    raise SystemExit("failed to lookup map -> base_link")

t = transform.transform.translation
q = transform.transform.rotation
siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
yaw = math.atan2(siny_cosp, cosy_cosp)
goal_x = t.x + distance * math.cos(yaw) - lateral * math.sin(yaw)
goal_y = t.y + distance * math.sin(yaw) + lateral * math.cos(yaw)
goal_yaw = yaw + yaw_delta
qz = math.sin(goal_yaw / 2.0)
qw = math.cos(goal_yaw / 2.0)
print(f"{t.x:.6f} {t.y:.6f} {yaw:.9f} {goal_x:.6f} {goal_y:.6f} {goal_yaw:.9f} {qz:.9f} {qw:.9f}")
node.destroy_node()
rclpy.shutdown()
PY
)"
read -r START_X START_Y START_YAW GOAL_X GOAL_Y GOAL_YAW QZ QW <<< "$GOAL_VALUES"
echo "[short-goal] current map pose x=$START_X y=$START_Y yaw=$START_YAW"
echo "[short-goal] target map pose x=$GOAL_X y=$GOAL_Y yaw=$GOAL_YAW"
printf '{pose: {header: {frame_id: map}, pose: {position: {x: %.6f, y: %.6f, z: 0.0}, orientation: {x: 0.0, y: 0.0, z: %.9f, w: %.9f}}}}\n' \
  "$GOAL_X" "$GOAL_Y" "$QZ" "$QW" > /tmp/rk3588_nav2_short_goal_msg.yaml
cat /tmp/rk3588_nav2_short_goal_msg.yaml

if [[ "$DRY_RUN" == "1" ]]; then
  echo "[short-goal] dry run only; drive not enabled and goal not sent"
  exit 0
fi

echo "[short-goal] enabling drive"
/mnt/sdcard/rk3588_enable_nav2_drive.sh --confirm

echo "[short-goal] sending navigate_to_pose relative goal distance=$DISTANCE lateral=$LATERAL yaw_delta=$YAW_DELTA"

timeout 45 ros2 action send_goal /navigate_to_pose nav2_msgs/action/NavigateToPose \
  "$(cat /tmp/rk3588_nav2_short_goal_msg.yaml)" --feedback > "$RESULT_LOG" 2>&1
GOAL_RC=$?
if grep -q 'Goal finished with status: SUCCEEDED' "$RESULT_LOG"; then
  GOAL_STATUS=SUCCEEDED
elif grep -q 'Goal finished with status:' "$RESULT_LOG"; then
  GOAL_STATUS="$(grep 'Goal finished with status:' "$RESULT_LOG" | tail -1 | sed 's/.*status: //')"
  GOAL_RC=1
else
  GOAL_STATUS=UNKNOWN
  GOAL_RC=1
fi

echo "[short-goal] action rc=$GOAL_RC status=$GOAL_STATUS"
tail -120 "$RESULT_LOG" || true

echo "[short-goal] explicit safe stop"
safe_stop

echo "[short-goal] after brake"
/mnt/sdcard/rk3588_check_brake_status.sh || true

echo "[short-goal] after odom"
timeout 5 ros2 topic echo /odom --once --field pose.pose || true

exit "$GOAL_RC"
