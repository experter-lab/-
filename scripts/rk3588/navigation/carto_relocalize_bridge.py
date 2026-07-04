#!/usr/bin/env python3
"""Bridge RViz /initialpose into Cartographer trajectory relocalization."""

import copy
import threading
import time

import rclpy
from cartographer_ros_msgs.srv import FinishTrajectory, GetTrajectoryStates, StartTrajectory
from geometry_msgs.msg import PoseWithCovarianceStamped
from rclpy.node import Node

CARTO_CONFIG_DIR = "/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config"
CARTO_CONFIG_BASENAME = "rk3588_carto_localization.lua"
FROZEN_TRAJECTORY_ID = 0


class RelocBridge(Node):
    def __init__(self):
        super().__init__("carto_reloc_bridge")
        self.cli_finish = self.create_client(FinishTrajectory, "/finish_trajectory")
        self.cli_start = self.create_client(StartTrajectory, "/start_trajectory")
        self.cli_states = self.create_client(GetTrajectoryStates, "/get_trajectory_states")
        for client in (self.cli_finish, self.cli_start, self.cli_states):
            client.wait_for_service(timeout_sec=5.0)

        # With one frozen pbstream trajectory, the active localization trajectory
        # created at startup is normally 1. Track later IDs from StartTrajectory.
        self.active_trajectory_id = 1
        self._busy = False
        self.create_subscription(PoseWithCovarianceStamped, "/initialpose", self.on_pose, 10)
        self.get_logger().info("ready - send 2D Pose Estimate in RViz")

    def wait_future(self, future, timeout_sec):
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            if future.done():
                return future.result()
            time.sleep(0.05)
        return None

    def get_active_trajectory_ids(self):
        fallback = [self.active_trajectory_id]
        future = self.cli_states.call_async(GetTrajectoryStates.Request())
        result = self.wait_future(future, 2.0)
        if result is None:
            self.get_logger().warn(
                f"get_trajectory_states timeout; fallback active trajectory {self.active_trajectory_id}"
            )
            return fallback

        states = result.trajectory_states
        active_ids = [
            trajectory_id
            for trajectory_id, state in zip(states.trajectory_id, states.trajectory_state)
            if state == 0
        ]
        if not active_ids:
            self.get_logger().warn(
                f"no active trajectory reported; fallback active trajectory {self.active_trajectory_id}"
            )
            return fallback
        self.active_trajectory_id = active_ids[-1]
        return active_ids

    def finish_trajectories(self, trajectory_ids):
        for trajectory_id in trajectory_ids:
            req = FinishTrajectory.Request()
            req.trajectory_id = trajectory_id
            future = self.cli_finish.call_async(req)
            result = self.wait_future(future, 10.0)
            if result is None:
                self.get_logger().warn(f"finish trajectory {trajectory_id}: TIMEOUT")
            else:
                self.get_logger().info(
                    f"finish trajectory {trajectory_id}: {result.status.message}"
                )

    def start_trajectory(self, pose):
        req = StartTrajectory.Request()
        req.configuration_directory = CARTO_CONFIG_DIR
        req.configuration_basename = CARTO_CONFIG_BASENAME
        req.use_initial_pose = True
        req.initial_pose = pose
        req.relative_to_trajectory_id = FROZEN_TRAJECTORY_ID

        future = self.cli_start.call_async(req)
        result = self.wait_future(future, 10.0)
        if result is None:
            self.get_logger().error("start_trajectory TIMEOUT")
            return

        self.active_trajectory_id = result.trajectory_id
        self.get_logger().info(
            f"started trajectory {result.trajectory_id}: {result.status.message}"
        )

    def relocalize(self, pose):
        try:
            active_ids = self.get_active_trajectory_ids()
            self.get_logger().info(f"active trajectories: {active_ids}")
            self.finish_trajectories(active_ids)
            self.start_trajectory(pose)
        finally:
            self._busy = False

    def on_pose(self, msg: PoseWithCovarianceStamped):
        if self._busy:
            self.get_logger().warn("relocalization already running; ignored initialpose")
            return
        self._busy = True
        pose = msg.pose.pose
        self.get_logger().info(
            "got initialpose: "
            f"xy=({pose.position.x:.2f}, {pose.position.y:.2f}) "
            "q=("
            f"{pose.orientation.x:.3f},"
            f"{pose.orientation.y:.3f},"
            f"{pose.orientation.z:.3f},"
            f"{pose.orientation.w:.3f})"
        )
        threading.Thread(target=self.relocalize, args=(copy.deepcopy(pose),), daemon=True).start()


def main():
    rclpy.init()
    node = RelocBridge()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
