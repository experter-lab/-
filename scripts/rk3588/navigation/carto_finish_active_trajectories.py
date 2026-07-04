#!/usr/bin/env python3
"""Finish every active Cartographer trajectory before writing a map."""

import time

import rclpy
from cartographer_ros_msgs.srv import FinishTrajectory, GetTrajectoryStates
from rclpy.node import Node


ACTIVE = 0


class FinishActiveTrajectories(Node):
    def __init__(self):
        super().__init__("carto_finish_active_trajectories")
        self.states = self.create_client(GetTrajectoryStates, "/get_trajectory_states")
        self.finish = self.create_client(FinishTrajectory, "/finish_trajectory")

    def wait_for_services(self):
        for name, client in (
            ("/get_trajectory_states", self.states),
            ("/finish_trajectory", self.finish),
        ):
            if not client.wait_for_service(timeout_sec=20.0):
                raise RuntimeError(f"service not available: {name}")

    def call(self, client, request, timeout_sec=30.0):
        future = client.call_async(request)
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if future.done():
                return future.result()
        raise TimeoutError("service call timed out")

    def finish_active(self):
        self.wait_for_services()
        result = self.call(self.states, GetTrajectoryStates.Request())
        active_ids = [
            trajectory_id
            for trajectory_id, state in zip(
                result.trajectory_states.trajectory_id,
                result.trajectory_states.trajectory_state,
            )
            if state == ACTIVE
        ]
        if not active_ids:
            print("[save] no active Cartographer trajectories")
            return
        for trajectory_id in active_ids:
            req = FinishTrajectory.Request()
            req.trajectory_id = int(trajectory_id)
            response = self.call(self.finish, req)
            print(f"[save] finish_trajectory {trajectory_id}: {response.status.message}")


def main():
    rclpy.init()
    node = FinishActiveTrajectories()
    try:
        node.finish_active()
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
