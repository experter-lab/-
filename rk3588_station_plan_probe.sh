#!/usr/bin/env bash
set -euo pipefail

set +u
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash 2>/dev/null || true
set -u

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

STATIONS_FILE="${1:-/mnt/sdcard/medicine_robot_ws/install/medicine_task_manager/share/medicine_task_manager/config/stations.yaml}"
shift || true

python3 - "$STATIONS_FILE" "$@" <<'PY'
import math
import sys
import time

import rclpy
from geometry_msgs.msg import PoseStamped
from nav2_msgs.action import ComputePathToPose
from rclpy.action import ActionClient
import tf2_ros
import yaml


def quat_from_yaw(yaw):
    return 0.0, 0.0, math.sin(yaw / 2.0), math.cos(yaw / 2.0)


def yaw_from_quat(q):
    return math.atan2(
        2.0 * (q.w * q.z + q.x * q.y),
        1.0 - 2.0 * (q.y * q.y + q.z * q.z),
    )


def path_length(path):
    total = 0.0
    for a, b in zip(path.poses, path.poses[1:]):
        total += math.hypot(
            b.pose.position.x - a.pose.position.x,
            b.pose.position.y - a.pose.position.y,
        )
    return total


stations_file = sys.argv[1]
requested = sys.argv[2:]
with open(stations_file, "r", encoding="utf-8") as file:
    stations = (yaml.safe_load(file) or {}).get("stations", {})

if not stations:
    raise SystemExit(f"no stations found in {stations_file}")

station_ids = requested or sorted(stations.keys())

rclpy.init()
node = rclpy.create_node("rk3588_station_plan_probe")
tf_buffer = tf2_ros.Buffer()
tf_listener = tf2_ros.TransformListener(tf_buffer, node)
client = ActionClient(node, ComputePathToPose, "/compute_path_to_pose")

try:
    current = None
    deadline = time.monotonic() + 5.0
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        try:
            current = tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
            break
        except Exception:
            pass
    if current is not None:
        yaw = yaw_from_quat(current.transform.rotation)
        print(
            "current "
            f"x={current.transform.translation.x:.3f} "
            f"y={current.transform.translation.y:.3f} "
            f"yaw_deg={math.degrees(yaw):.2f}"
        )
    else:
        print("current tf unavailable")

    if not client.wait_for_server(timeout_sec=5.0):
        raise SystemExit("/compute_path_to_pose unavailable")

    for station_id in station_ids:
        station = stations.get(station_id)
        if station is None:
            print(f"{station_id}: missing")
            continue
        pose = PoseStamped()
        pose.header.frame_id = "map"
        pose.header.stamp = node.get_clock().now().to_msg()
        pose.pose.position.x = float(station.get("x", 0.0))
        pose.pose.position.y = float(station.get("y", 0.0))
        qx, qy, qz, qw = quat_from_yaw(float(station.get("yaw", 0.0)))
        pose.pose.orientation.x = qx
        pose.pose.orientation.y = qy
        pose.pose.orientation.z = qz
        pose.pose.orientation.w = qw

        goal = ComputePathToPose.Goal()
        goal.goal = pose
        goal.planner_id = "GridBased"
        goal.use_start = False

        send_future = client.send_goal_async(goal)
        rclpy.spin_until_future_complete(node, send_future, timeout_sec=5.0)
        handle = send_future.result()
        if handle is None:
            print(f"{station_id}: send_failed")
            continue
        if not handle.accepted:
            print(f"{station_id}: rejected")
            continue

        result_future = handle.get_result_async()
        rclpy.spin_until_future_complete(node, result_future, timeout_sec=8.0)
        result = result_future.result()
        if result is None:
            print(f"{station_id}: timeout")
            continue
        path = result.result.path
        print(
            f"{station_id}: status={result.status} "
            f"poses={len(path.poses)} "
            f"length={path_length(path):.3f} "
            f"target=({pose.pose.position.x:.3f},{pose.pose.position.y:.3f})"
        )
finally:
    node.destroy_node()
    rclpy.shutdown()
PY
