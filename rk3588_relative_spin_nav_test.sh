#!/usr/bin/env bash
set -euo pipefail

SPIN_RAD="${1:-0.35}"
TIMEOUT_SEC="${2:-90}"

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

python3 - "$SPIN_RAD" "$TIMEOUT_SEC" <<'PY'
import math
import sys
import time

import rclpy
from nav2_msgs.action import Spin
from rclpy.action import ActionClient
import tf2_ros

spin_rad = float(sys.argv[1])
timeout_sec = float(sys.argv[2])


def yaw_from_quat(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


rclpy.init()
node = rclpy.create_node("rk3588_relative_spin_nav_test")
tf_buffer = tf2_ros.Buffer()
tf_listener = tf2_ros.TransformListener(tf_buffer, node)
spin_client = ActionClient(node, Spin, "/spin")

try:
    current = None
    deadline = time.monotonic() + 8.0
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            current = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
            break
        except Exception:
            pass
    if current is None:
        raise RuntimeError("current tf unavailable")

    q = current.transform.rotation
    yaw0 = yaw_from_quat(q)
    start_x = current.transform.translation.x
    start_y = current.transform.translation.y
    target_yaw = spin_rad

    print(
        f"START_TF x={start_x:.3f} y={start_y:.3f} "
        f"yaw_deg={math.degrees(yaw0):.2f}"
    )
    print(f"SPIN_TARGET yaw_rad={target_yaw:.3f} yaw_deg={math.degrees(target_yaw):.2f}")

    if not spin_client.wait_for_server(timeout_sec=5.0):
        raise RuntimeError("/spin unavailable")

    goal = Spin.Goal()
    goal.target_yaw = target_yaw
    goal.time_allowance.sec = int(timeout_sec)
    goal.time_allowance.nanosec = 0

    send_future = spin_client.send_goal_async(goal)
    rclpy.spin_until_future_complete(node, send_future, timeout_sec=5.0)
    handle = send_future.result()
    if handle is None:
        raise RuntimeError("spin send failed")
    if not handle.accepted:
        raise RuntimeError("spin goal rejected")

    result_future = handle.get_result_async()
    last_print = 0.0
    deadline = time.monotonic() + timeout_sec
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        if result_future.done():
            break
        now = time.monotonic()
        if now - last_print > 1.0:
            last_print = now
            try:
                pose = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
                pyaw = yaw_from_quat(pose.transform.rotation)
                print(
                    f"POSE x={pose.transform.translation.x:.3f} "
                    f"y={pose.transform.translation.y:.3f} "
                    f"yaw_deg={math.degrees(pyaw):.2f}"
                )
            except Exception:
                pass

    if not result_future.done():
        print("TIMEOUT cancelling goal")
        handle.cancel_goal_async()
        raise RuntimeError("spin timeout")

    result = result_future.result()
    end = None
    for _ in range(30):
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            end = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
            break
        except Exception:
            pass
    if end is None:
        end = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())

    yaw1 = yaw_from_quat(end.transform.rotation)
    end_x = end.transform.translation.x
    end_y = end.transform.translation.y
    dyaw = yaw1 - yaw0
    while dyaw > math.pi:
        dyaw -= 2.0 * math.pi
    while dyaw < -math.pi:
        dyaw += 2.0 * math.pi

    print(
        f"END_TF x={end_x:.3f} y={end_y:.3f} "
        f"yaw_deg={math.degrees(yaw1):.2f}"
    )
    print(
        "TF_DELTA "
        f"distance={math.hypot(end_x - start_x, end_y - start_y):.3f} "
        f"dx={end_x - start_x:.3f} "
        f"dy={end_y - start_y:.3f} "
        f"dyaw_deg={math.degrees(dyaw):.2f}"
    )
    print(f"RESULT status={result.status}")
finally:
    node.destroy_node()
    rclpy.shutdown()
PY
