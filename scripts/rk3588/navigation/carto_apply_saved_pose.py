#!/usr/bin/env python3
"""Start a Cartographer trajectory from a saved map-frame pose."""

import argparse
import json
import math
import time

import rclpy
from cartographer_ros_msgs.srv import FinishTrajectory, GetTrajectoryStates, StartTrajectory
from geometry_msgs.msg import Pose
from rclpy.node import Node


ACTIVE = 0
FROZEN = 2
CONFIG_DIR = "/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config"
CONFIG_BASENAME = "rk3588_carto_localization.lua"


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class SavedPoseApplier(Node):
    def __init__(self):
        super().__init__("carto_apply_saved_pose")
        self.cli_states = self.create_client(GetTrajectoryStates, "/get_trajectory_states")
        self.cli_finish = self.create_client(FinishTrajectory, "/finish_trajectory")
        self.cli_start = self.create_client(StartTrajectory, "/start_trajectory")

    def wait_for_services(self):
        for name, client in (
            ("/get_trajectory_states", self.cli_states),
            ("/finish_trajectory", self.cli_finish),
            ("/start_trajectory", self.cli_start),
        ):
            self.get_logger().info(f"waiting for {name}")
            if not client.wait_for_service(timeout_sec=20.0):
                raise RuntimeError(f"service not available: {name}")

    def call(self, client, request, timeout_sec):
        future = client.call_async(request)
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if future.done():
                return future.result()
        raise TimeoutError(f"service call timed out after {timeout_sec:.0f}s")

    def get_trajectory_ids(self):
        result = self.call(self.cli_states, GetTrajectoryStates.Request(), 20.0)
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

    def resolve_relative_id(self, frozen_ids, selector):
        if selector == "latest":
            return max(frozen_ids)
        if selector == "oldest":
            return min(frozen_ids)
        relative_id = int(selector)
        if relative_id not in frozen_ids:
            raise RuntimeError(
                f"relative trajectory {relative_id} is not frozen; frozen trajectories: {frozen_ids}"
            )
        return relative_id

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


def pose_from_file(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    pose = Pose()
    pose.position.x = float(data["x"])
    pose.position.y = float(data["y"])
    pose.position.z = float(data.get("z", 0.0))
    pose.orientation.x = float(data.get("qx", 0.0))
    pose.orientation.y = float(data.get("qy", 0.0))
    pose.orientation.z = float(data["qz"])
    pose.orientation.w = float(data["qw"])
    return pose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--pose-file",
        default="/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json",
    )
    parser.add_argument(
        "--relative-to-trajectory-id",
        default="latest",
        help="Frozen trajectory used for StartTrajectory; use latest, oldest, or an integer id.",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    pose = pose_from_file(args.pose_file)
    yaw_deg = math.degrees(yaw_from_quat(pose.orientation))

    rclpy.init()
    node = SavedPoseApplier()
    try:
        node.get_logger().info(
            f"loaded saved pose: x={pose.position.x:.3f} "
            f"y={pose.position.y:.3f} yaw={yaw_deg:.1f} deg"
        )
        node.wait_for_services()
        active_ids, frozen_ids = node.get_trajectory_ids()
        if not frozen_ids:
            raise RuntimeError("no frozen trajectory found; pbstream is not loaded as frozen state")
        relative_id = node.resolve_relative_id(frozen_ids, args.relative_to_trajectory_id)
        node.get_logger().info(
            f"selected frozen trajectory {relative_id} using selector '{args.relative_to_trajectory_id}'"
        )
        if args.dry_run:
            node.get_logger().info("dry run complete; not changing Cartographer trajectory")
            return 0
        node.finish_active(active_ids)
        time.sleep(1.0)
        new_id = node.start_with_pose(pose, relative_id)
        node.get_logger().info(f"done; new active trajectory is {new_id}")
    finally:
        node.destroy_node()
        rclpy.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
