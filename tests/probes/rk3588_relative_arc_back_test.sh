#!/usr/bin/env bash
set -euo pipefail

LINEAR_X="${1:--0.08}"
ANGULAR_Z="${2:-0.10}"
DURATION_SEC="${3:-2.5}"
TIMEOUT_SEC="${4:-90}"

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

python3 - "$LINEAR_X" "$ANGULAR_Z" "$DURATION_SEC" "$TIMEOUT_SEC" <<'PY'
import json
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
import tf2_ros

linear_x = float(sys.argv[1])
angular_z = float(sys.argv[2])
duration_sec = float(sys.argv[3])
timeout_sec = float(sys.argv[4])

if abs(linear_x) > 0.12:
    raise SystemExit(f"refusing oversized linear_x={linear_x}")
if abs(angular_z) > 0.15:
    raise SystemExit(f"refusing oversized angular_z={angular_z}")
if duration_sec > 5.0:
    raise SystemExit(f"refusing oversized duration_sec={duration_sec}")


def yaw_from_quat(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


latest_status = {}


def on_status(msg):
    try:
        latest_status.clear()
        latest_status.update(json.loads(msg.data))
    except Exception:
        pass


def get_rc(status):
    ardupilot = status.get("ardupilot", {}) or {}
    return (ardupilot.get("rc_override", {}) or {})


rclpy.init()
node = rclpy.create_node("rk3588_relative_arc_back_test")
status_sub = node.create_subscription(String, "/medicine/chassis_status", on_status, 10)
cmd_pub = node.create_publisher(Twist, "/cmd_vel", 10)
tf_buffer = tf2_ros.Buffer()
tf_listener = tf2_ros.TransformListener(tf_buffer, node)

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
    print(
        f"START_TF x={start_x:.3f} y={start_y:.3f} "
        f"yaw_deg={math.degrees(yaw0):.2f}"
    )

    if latest_status:
        rc = get_rc(latest_status)
        print(
            "START_STATUS "
            f"mode={latest_status.get('mode')} "
            f"estop={latest_status.get('emergency_stop')} "
            f"auth={latest_status.get('control_authorized')} "
            f"ardupilot_mode={(latest_status.get('ardupilot', {}) or {}).get('custom_mode_name')} "
            f"base_mode={(latest_status.get('ardupilot', {}) or {}).get('base_mode')} "
            f"thr={rc.get('last_throttle_pwm')} "
            f"st={rc.get('last_steering_pwm')}"
        )

    twist = Twist()
    twist.linear.x = linear_x
    twist.angular.z = angular_z
    print(
        f"CMD linear_x={linear_x:.3f} angular_z={angular_z:.3f} "
        f"duration_sec={duration_sec:.2f}"
    )

    end_drive = time.monotonic() + duration_sec
    last_print = 0.0
    while rclpy.ok() and time.monotonic() < end_drive:
        cmd_pub.publish(twist)
        rclpy.spin_once(node, timeout_sec=0.05)
        now = time.monotonic()
        if now - last_print >= 0.5:
            last_print = now
            try:
                pose = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
                pyaw = yaw_from_quat(pose.transform.rotation)
                rc = get_rc(latest_status)
                print(
                    f"POSE x={pose.transform.translation.x:.3f} "
                    f"y={pose.transform.translation.y:.3f} "
                    f"yaw_deg={math.degrees(pyaw):.2f} "
                    f"thr={rc.get('last_throttle_pwm')} st={rc.get('last_steering_pwm')}"
                )
            except Exception:
                pass
        time.sleep(0.08)

    stop = Twist()
    for _ in range(8):
        cmd_pub.publish(stop)
        rclpy.spin_once(node, timeout_sec=0.02)
        time.sleep(0.05)

    settle_deadline = time.monotonic() + 2.0
    end = None
    while rclpy.ok() and time.monotonic() < settle_deadline:
        rclpy.spin_once(node, timeout_sec=0.05)
        try:
            end = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
            break
        except Exception:
            pass
    if end is None:
        end = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())

    q1 = end.transform.rotation
    yaw1 = yaw_from_quat(q1)
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
finally:
    node.destroy_node()
    rclpy.shutdown()
PY
