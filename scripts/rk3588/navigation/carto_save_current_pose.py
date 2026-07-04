#!/usr/bin/env python3
"""Save current map->base_link pose as the next Cartographer startup pose."""

import argparse
import hashlib
import json
import math
import os
import time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def sha256_file(path):
    if not path or not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PoseSaver(Node):
    def __init__(self):
        super().__init__("carto_save_current_pose")
        self.buffer = Buffer()
        self.listener = TransformListener(self.buffer, self)

    def lookup(self, timeout_sec):
        deadline = time.monotonic() + timeout_sec
        last_error = None
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            try:
                return self.buffer.lookup_transform(
                    "map",
                    "base_link",
                    rclpy.time.Time(),
                    timeout=Duration(seconds=0.5),
                )
            except TransformException as exc:
                last_error = exc
        raise RuntimeError(f"failed to read map->base_link TF: {last_error}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json",
    )
    parser.add_argument(
        "--pbstream",
        default="/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream",
    )
    parser.add_argument(
        "--map-yaml",
        default="/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static.yaml",
    )
    parser.add_argument("--timeout", type=float, default=10.0)
    args = parser.parse_args()

    rclpy.init()
    node = PoseSaver()
    try:
        tf = node.lookup(args.timeout)
        t = tf.transform.translation
        q = tf.transform.rotation
        data = {
            "frame_id": "map",
            "child_frame_id": "base_link",
            "x": t.x,
            "y": t.y,
            "z": t.z,
            "qx": q.x,
            "qy": q.y,
            "qz": q.z,
            "qw": q.w,
            "yaw_deg": math.degrees(yaw_from_quat(q)),
            "pbstream": args.pbstream,
            "pbstream_sha256": sha256_file(args.pbstream),
            "map_yaml": args.map_yaml,
            "map_yaml_sha256": sha256_file(args.map_yaml),
            "saved_unix_time": time.time(),
        }
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, sort_keys=True)
            f.write("\n")
        node.get_logger().info(
            f"saved pose to {args.output}: "
            f"x={data['x']:.3f} y={data['y']:.3f} yaw={data['yaw_deg']:.1f} deg"
        )
        node.get_logger().info(
            f"pose map hash: pbstream={data['pbstream_sha256']} map_yaml={data['map_yaml_sha256']}"
        )
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
