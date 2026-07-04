#!/usr/bin/env bash
set -euo pipefail

BACK_M="${1:-0.15}"
SPEED="${2:-0.05}"
TIME_ALLOW_SEC="${3:-8}"

unset AMENT_TRACE_SETUP_FILES
unset COLCON_TRACE_SETUP_FILES
set +u
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash 2>/dev/null || true
set -u

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"
export PYTHONUNBUFFERED=1

robust_stop() {
  /mnt/sdcard/rk3588_safe_stop.sh || true
}

trap robust_stop EXIT INT TERM

robust_stop
/mnt/sdcard/rk3588_enable_nav2_drive.sh --confirm

python3 - "$BACK_M" "$SPEED" "$TIME_ALLOW_SEC" <<'PY'
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Point
from nav2_msgs.action import BackUp
from rclpy.action import ActionClient
import tf2_ros

back_m = float(sys.argv[1])
speed = float(sys.argv[2])
time_allow_sec = int(sys.argv[3])


def yaw_from_quat(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


def wait_tf(buf, node, parent="map", child="base_link", timeout_sec=8.0):
    deadline = time.monotonic() + timeout_sec
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            return buf.lookup_transform(parent, child, rclpy.time.Time())
        except Exception:
            pass
    return None


rclpy.init()
node = rclpy.create_node("rk3588_backup_short_test")
tf_buffer = tf2_ros.Buffer()
tf_listener = tf2_ros.TransformListener(tf_buffer, node)
client = ActionClient(node, BackUp, "/backup")

try:
    start = wait_tf(tf_buffer, node)
    if start is None:
      raise RuntimeError("missing map->base_link")
    sy = yaw_from_quat(start.transform.rotation)
    sx = start.transform.translation.x
    syy = start.transform.translation.y
    print(f"START_TF x={sx:.3f} y={syy:.3f} yaw_deg={math.degrees(sy):.2f}")

    if not client.wait_for_server(timeout_sec=6.0):
        raise RuntimeError("/backup unavailable")

    goal = BackUp.Goal()
    goal.target = Point(x=back_m, y=0.0, z=0.0)
    goal.speed = speed
    goal.time_allowance.sec = time_allow_sec
    goal.time_allowance.nanosec = 0

    future = client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, future, timeout_sec=6.0)
    handle = future.result()
    if handle is None:
        raise RuntimeError("send goal failed")
    if not handle.accepted:
        raise RuntimeError("goal rejected")

    result_future = handle.get_result_async()
    last_print = 0.0
    deadline = time.monotonic() + max(time_allow_sec + 5, 15)
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if result_future.done():
            break
        now = time.monotonic()
        if now - last_print >= 1.0:
            last_print = now
            pose = wait_tf(tf_buffer, node, timeout_sec=0.1)
            if pose is not None:
                pyaw = yaw_from_quat(pose.transform.rotation)
                print(
                    f"POSE x={pose.transform.translation.x:.3f} "
                    f"y={pose.transform.translation.y:.3f} "
                    f"yaw_deg={math.degrees(pyaw):.2f}"
                )

    if not result_future.done():
        print("TIMEOUT cancelling goal")
        handle.cancel_goal_async()
        raise RuntimeError("backup timeout")

    result = result_future.result()
    end = wait_tf(tf_buffer, node, timeout_sec=2.0) or tf_buffer.lookup_transform(
        "map", "base_link", rclpy.time.Time()
    )
    ey = yaw_from_quat(end.transform.rotation)
    ex = end.transform.translation.x
    eyy = end.transform.translation.y
    print(f"END_TF x={ex:.3f} y={eyy:.3f} yaw_deg={math.degrees(ey):.2f}")
    print(
        "TF_DELTA "
        f"distance={math.hypot(ex - sx, eyy - syy):.3f} "
        f"dx={ex - sx:.3f} dy={eyy - syy:.3f} "
        f"dyaw_deg={math.degrees(ey - sy):.2f}"
    )
    print(f"RESULT status={result.status}")
finally:
    node.destroy_node()
    rclpy.shutdown()
PY
