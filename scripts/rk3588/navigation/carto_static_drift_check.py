#!/usr/bin/env python3
"""Check Cartographer map->base_link drift while the robot is stationary."""

import argparse
import math
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def yaw_delta(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


class DriftChecker(Node):
    def __init__(self):
        super().__init__("carto_static_drift_check")
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)

    def lookup(self, timeout_sec=0.5):
        return self.buffer.lookup_transform(
            "map",
            "base_link",
            rclpy.time.Time(),
            timeout=Duration(seconds=timeout_sec),
        )

    def wait_tf(self, timeout_sec):
        deadline = time.monotonic() + timeout_sec
        last_error = None
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            try:
                return self.lookup()
            except TransformException as exc:
                last_error = exc
        raise RuntimeError(f"timeout waiting for map->base_link TF: {last_error}")


def pose_tuple(tf):
    t = tf.transform.translation
    q = tf.transform.rotation
    return t.x, t.y, yaw_from_quat(q)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--duration", type=float, default=30.0)
    parser.add_argument("--sample-period", type=float, default=1.0)
    parser.add_argument("--max-xy-drift", type=float, default=0.03)
    parser.add_argument("--max-yaw-drift-deg", type=float, default=1.0)
    args = parser.parse_args()

    rclpy.init()
    node = DriftChecker()
    try:
        first = pose_tuple(node.wait_tf(20.0))
        samples = [first]
        print(
            "start pose: x={:.3f} y={:.3f} yaw={:.2f}deg".format(
                first[0], first[1], math.degrees(first[2])
            )
        )
        deadline = time.monotonic() + args.duration
        while rclpy.ok() and time.monotonic() < deadline:
            time.sleep(args.sample_period)
            rclpy.spin_once(node, timeout_sec=0.1)
            samples.append(pose_tuple(node.lookup()))

        max_xy = 0.0
        max_yaw = 0.0
        last = samples[-1]
        for sample in samples:
            max_xy = max(max_xy, math.hypot(sample[0] - first[0], sample[1] - first[1]))
            max_yaw = max(max_yaw, abs(yaw_delta(sample[2], first[2])))
        print(
            "end pose:   x={:.3f} y={:.3f} yaw={:.2f}deg".format(
                last[0], last[1], math.degrees(last[2])
            )
        )
        print(f"max xy drift: {max_xy:.4f} m")
        print(f"max yaw drift: {math.degrees(max_yaw):.3f} deg")
        if max_xy > args.max_xy_drift or math.degrees(max_yaw) > args.max_yaw_drift_deg:
            print("RESULT FAIL: static Cartographer drift is too high")
            return 1
        print("RESULT OK: static Cartographer drift is within limits")
        return 0
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    raise SystemExit(main())
