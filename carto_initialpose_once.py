#!/usr/bin/env python3
"""Apply one RViz /initialpose message to Cartographer as a new trajectory."""

import math
import os
import sys
import time

import rclpy
from cartographer_ros_msgs.srv import FinishTrajectory, GetTrajectoryStates, StartTrajectory
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node


ACTIVE = 0
FROZEN = 2
CONFIG_DIR = "/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config"
CONFIG_BASENAME = "rk3588_carto_localization.lua"
YAW_OFFSET_DEG = float(os.environ.get("INITIALPOSE_YAW_OFFSET_DEG", "0"))
KEEP_ALIVE = os.environ.get("INITIALPOSE_KEEP_ALIVE", "0") == "1"


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def quat_from_yaw(yaw):
    q = type("QuaternionLike", (), {})()
    q.x = 0.0
    q.y = 0.0
    q.z = math.sin(yaw * 0.5)
    q.w = math.cos(yaw * 0.5)
    return q


def apply_yaw_offset(pose):
    if abs(YAW_OFFSET_DEG) < 1e-9:
        return pose
    yaw = yaw_from_quat(pose.orientation)
    yaw += math.radians(YAW_OFFSET_DEG)
    q = quat_from_yaw(yaw)
    pose.orientation.x = q.x
    pose.orientation.y = q.y
    pose.orientation.z = q.z
    pose.orientation.w = q.w
    return pose


class InitialPoseOnce(Node):
    def __init__(self):
        super().__init__("carto_initialpose_once")
        self.pose_msg = None
        self.create_subscription(PoseWithCovarianceStamped, "/initialpose", self._on_pose, 10)
        self.cli_states = self.create_client(GetTrajectoryStates, "/get_trajectory_states")
        self.cli_finish = self.create_client(FinishTrajectory, "/finish_trajectory")
        self.cli_start = self.create_client(StartTrajectory, "/start_trajectory")

    def _on_pose(self, msg):
        if self.pose_msg is None:
            self.pose_msg = msg
            p = msg.pose.pose.position
            q = msg.pose.pose.orientation
            self.get_logger().info(
                "received /initialpose: "
                f"x={p.x:.3f} y={p.y:.3f} yaw={math.degrees(yaw_from_quat(q)):.1f} deg"
            )
            if abs(YAW_OFFSET_DEG) > 1e-9:
                self.get_logger().info(f"will apply yaw offset: {YAW_OFFSET_DEG:.1f} deg")

    def wait_for_services(self):
        for name, client in (
            ("/get_trajectory_states", self.cli_states),
            ("/finish_trajectory", self.cli_finish),
            ("/start_trajectory", self.cli_start),
        ):
            self.get_logger().info(f"waiting for {name}")
            if not client.wait_for_service(timeout_sec=15.0):
                raise RuntimeError(f"service not available: {name}")

    def call(self, client, request, timeout_sec):
        future = client.call_async(request)
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if future.done():
                return future.result()
        raise TimeoutError(f"service call timed out after {timeout_sec:.0f}s")

    def wait_for_initial_pose(self, timeout_sec):
        self.get_logger().info("click '2D Pose Estimate' in RViz")
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.pose_msg is not None:
                return self.pose_msg.pose.pose
        raise TimeoutError("no /initialpose received")

    def get_trajectory_ids(self):
        result = self.call(self.cli_states, GetTrajectoryStates.Request(), 15.0)
        if result.status.code != 0:
            raise RuntimeError(f"get_trajectory_states failed: {result.status.message}")

        active_ids = []
        frozen_ids = []
        for trajectory_id, state in zip(
            result.trajectory_states.trajectory_id,
            result.trajectory_states.trajectory_state,
        ):
            if state == ACTIVE:
                active_ids.append(trajectory_id)
            elif state == FROZEN:
                frozen_ids.append(trajectory_id)
        self.get_logger().info(f"active trajectories: {active_ids}")
        self.get_logger().info(f"frozen trajectories: {frozen_ids}")
        return active_ids, frozen_ids

    def finish_active(self, active_ids):
        for trajectory_id in active_ids:
            req = FinishTrajectory.Request()
            req.trajectory_id = int(trajectory_id)
            result = self.call(self.cli_finish, req, 30.0)
            self.get_logger().info(
                f"finish trajectory {trajectory_id}: "
                f"code={result.status.code} message='{result.status.message}'"
            )

    def start_with_pose(self, pose, relative_to_trajectory_id):
        req = StartTrajectory.Request()
        req.configuration_directory = CONFIG_DIR
        req.configuration_basename = CONFIG_BASENAME
        req.use_initial_pose = True
        req.initial_pose = pose
        req.relative_to_trajectory_id = int(relative_to_trajectory_id)
        result = self.call(self.cli_start, req, 45.0)
        self.get_logger().info(
            f"start trajectory: id={result.trajectory_id} "
            f"code={result.status.code} message='{result.status.message}'"
        )
        if result.status.code != 0:
            raise RuntimeError(f"start_trajectory failed: {result.status.message}")
        return result.trajectory_id


def main():
    rclpy.init()
    node = InitialPoseOnce()
    try:
        node.wait_for_services()
        while rclpy.ok():
            pose = node.wait_for_initial_pose(timeout_sec=900.0)
            pose = apply_yaw_offset(pose)
            if abs(YAW_OFFSET_DEG) > 1e-9:
                node.get_logger().info(
                    f"applied pose yaw={math.degrees(yaw_from_quat(pose.orientation)):.1f} deg"
                )
            active_ids, frozen_ids = node.get_trajectory_ids()
            if not frozen_ids:
                raise RuntimeError("no frozen trajectory found; pbstream is not loaded as frozen state")
            relative_id = max(frozen_ids)
            node.get_logger().info(f"selected frozen trajectory: {relative_id}")
            node.finish_active(active_ids)
            time.sleep(1.0)
            new_id = node.start_with_pose(pose, relative_id)
            node.get_logger().info(f"done; new active trajectory is {new_id}")
            if not KEEP_ALIVE:
                break
            node.pose_msg = None
            node.get_logger().info("keep-alive enabled; waiting for another RViz 2D Pose Estimate")
    except Exception as exc:
        node.get_logger().error(str(exc))
        node.destroy_node()
        rclpy.shutdown()
        return 1
    node.destroy_node()
    rclpy.shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
