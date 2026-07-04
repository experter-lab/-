#!/usr/bin/env bash
set -euo pipefail

BACK_M="${1:-0.30}"
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

python3 - "$BACK_M" "$TIMEOUT_SEC" <<'PY'
import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose, NavigateToPose
from rclpy.action import ActionClient
import tf2_ros

back_m = float(sys.argv[1])
timeout_sec = float(sys.argv[2])


def yaw_from_quat(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


def quat_from_yaw(yaw):
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def path_length(path):
    total = 0.0
    for a, b in zip(path.poses, path.poses[1:]):
        total += math.hypot(
            b.pose.position.x - a.pose.position.x,
            b.pose.position.y - a.pose.position.y,
        )
    return total


rclpy.init()
node = rclpy.create_node("rk3588_relative_back_nav_test")
tf_buffer = tf2_ros.Buffer()
tf_listener = tf2_ros.TransformListener(tf_buffer, node)
plan_client = ActionClient(node, ComputePathToPose, "/compute_path_to_pose")
nav_client = ActionClient(node, NavigateToPose, "/navigate_to_pose")

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
    yaw = yaw_from_quat(q)
    start_x = current.transform.translation.x
    start_y = current.transform.translation.y
    goal_x = start_x - back_m * math.cos(yaw)
    goal_y = start_y - back_m * math.sin(yaw)

    goal = PoseStamped()
    goal.header.frame_id = "map"
    goal.header.stamp = node.get_clock().now().to_msg()
    goal.pose.position.x = goal_x
    goal.pose.position.y = goal_y
    goal.pose.position.z = 0.0
    qx, qy, qz, qw = quat_from_yaw(yaw)
    goal.pose.orientation.x = qx
    goal.pose.orientation.y = qy
    goal.pose.orientation.z = qz
    goal.pose.orientation.w = qw

    print(f"START_TF x={start_x:.3f} y={start_y:.3f} yaw_deg={math.degrees(yaw):.2f}")
    print(
        f"GOAL_TF x={goal_x:.3f} y={goal_y:.3f} "
        f"yaw_deg={math.degrees(yaw):.2f} back_m={back_m:.2f}"
    )

    if not plan_client.wait_for_server(timeout_sec=5.0):
        raise RuntimeError("/compute_path_to_pose unavailable")
    plan_goal = ComputePathToPose.Goal()
    plan_goal.goal = goal
    plan_goal.planner_id = "GridBased"
    plan_goal.use_start = False
    send_future = plan_client.send_goal_async(plan_goal)
    rclpy.spin_until_future_complete(node, send_future, timeout_sec=5.0)
    plan_handle = send_future.result()
    if plan_handle is None or not plan_handle.accepted:
        raise RuntimeError("plan goal rejected")
    plan_result_future = plan_handle.get_result_async()
    rclpy.spin_until_future_complete(node, plan_result_future, timeout_sec=10.0)
    plan_result = plan_result_future.result()
    if plan_result is None:
        raise RuntimeError("plan timeout")
    path = plan_result.result.path
    print(
        f"PLAN status={plan_result.status} poses={len(path.poses)} "
        f"length={path_length(path):.3f}"
    )
    if len(path.poses) == 0:
        raise RuntimeError("empty plan")

    if not nav_client.wait_for_server(timeout_sec=5.0):
        raise RuntimeError("/navigate_to_pose unavailable")

    nav_goal = NavigateToPose.Goal()
    nav_goal.pose = goal
    nav_goal.behavior_tree = ""
    nav_send_future = nav_client.send_goal_async(nav_goal)
    rclpy.spin_until_future_complete(node, nav_send_future, timeout_sec=5.0)
    nav_handle = nav_send_future.result()
    if nav_handle is None:
        raise RuntimeError("nav send failed")
    if not nav_handle.accepted:
        raise RuntimeError("nav goal rejected")

    result_future = nav_handle.get_result_async()
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
        nav_handle.cancel_goal_async()
        raise RuntimeError("navigation timeout")

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

    end_yaw = yaw_from_quat(end.transform.rotation)
    end_x = end.transform.translation.x
    end_y = end.transform.translation.y
    print(f"END_TF x={end_x:.3f} y={end_y:.3f} yaw_deg={math.degrees(end_yaw):.2f}")
    print(
        "TF_DELTA "
        f"distance={math.hypot(end_x - start_x, end_y - start_y):.3f} "
        f"dx={end_x - start_x:.3f} "
        f"dy={end_y - start_y:.3f} "
        f"dyaw_deg={math.degrees(end_yaw - yaw):.2f}"
    )
    print(f"RESULT status={result.status}")
finally:
    node.destroy_node()
    rclpy.shutdown()
PY
