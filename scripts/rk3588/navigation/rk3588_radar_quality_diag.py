#!/usr/bin/env python3
"""One-shot radar/navigation quality diagnostics for the RK3588 robot.

This intentionally reads live ROS topics only. It does not publish motion
commands or change parameters.
"""

from __future__ import annotations

import math
import statistics
import time

import rclpy
from nav_msgs.msg import OccupancyGrid, Odometry
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener


def stamp_seconds(msg) -> float:
    stamp = getattr(getattr(msg, "header", None), "stamp", None)
    if stamp is None:
        return time.time()
    value = float(stamp.sec) + float(stamp.nanosec) * 1e-9
    return value if value > 0 else time.time()


class RadarQualityDiag(Node):
    def __init__(self) -> None:
        super().__init__("radar_quality_diag_once")
        self.scans: list[tuple[float, int, int, int, int, int, float | None, float | None, float | None, int | None, int | None]] = []
        self.odom: list[tuple[float, float, float, float]] = []
        self.costmaps: list[tuple[float, int, int, float, int, int, int]] = []
        self.create_subscription(LaserScan, "/scan", self.on_scan, 10)
        self.create_subscription(Odometry, "/odom", self.on_odom, 10)
        self.create_subscription(OccupancyGrid, "/local_costmap/costmap", self.on_costmap, 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

    def on_scan(self, msg: LaserScan) -> None:
        ranges = list(msg.ranges)
        finite = [v for v in ranges if math.isfinite(v)]
        valid_indices = [
            i for i, v in enumerate(ranges)
            if math.isfinite(v) and msg.range_min <= v <= msg.range_max
        ]
        valid = [ranges[i] for i in valid_indices]
        inf_count = sum(1 for v in ranges if math.isinf(v))
        nan_count = sum(1 for v in ranges if math.isnan(v))
        self.scans.append((
            stamp_seconds(msg),
            len(ranges),
            len(finite),
            len(valid),
            inf_count,
            nan_count,
            min(valid) if valid else None,
            max(valid) if valid else None,
            statistics.mean(valid) if valid else None,
            valid_indices[0] if valid_indices else None,
            valid_indices[-1] if valid_indices else None,
        ))
        self.scans = self.scans[-120:]

    def on_odom(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.odom.append((stamp_seconds(msg), p.x, p.y, yaw))
        self.odom = self.odom[-120:]

    def on_costmap(self, msg: OccupancyGrid) -> None:
        total = len(msg.data)
        occupied = sum(1 for value in msg.data if value > 50)
        unknown = sum(1 for value in msg.data if value < 0)
        self.costmaps.append((stamp_seconds(msg), msg.info.width, msg.info.height, msg.info.resolution, occupied, unknown, total))
        self.costmaps = self.costmaps[-20:]


def value_range(rows: list[tuple], index: int) -> float:
    values = [row[index] for row in rows]
    return max(values) - min(values) if values else 0.0


def print_tf(node: RadarQualityDiag, parent: str, child: str) -> None:
    try:
        tr = node.tf_buffer.lookup_transform(parent, child, rclpy.time.Time())
    except Exception as exc:  # noqa: BLE001 - diagnostic output should include the raw failure.
        print(f"TF {parent}->{child}: FAIL {exc}")
        return
    t = tr.transform.translation
    q = tr.transform.rotation
    yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
    print(f"TF {parent}->{child}: x={t.x:.3f} y={t.y:.3f} z={t.z:.3f} yaw={math.degrees(yaw):.2f}deg")


def main() -> None:
    rclpy.init()
    node = RadarQualityDiag()
    deadline = time.time() + 8.0
    while time.time() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)

    print("=== RK3588 Radar Quality Diagnostic ===")
    print(f"scan_samples={len(node.scans)}")
    if node.scans:
        rates = []
        for prev, cur in zip(node.scans, node.scans[1:]):
            dt = cur[0] - prev[0]
            if dt > 0:
                rates.append(1.0 / dt)
        latest = node.scans[-1]
        valid_ratios = [row[3] / row[1] for row in node.scans if row[1]]
        first_indices = [row[9] for row in node.scans if row[9] is not None]
        last_indices = [row[10] for row in node.scans if row[10] is not None]
        print(f"scan_hz_avg={statistics.mean(rates):.2f}" if rates else "scan_hz_avg=-")
        print(
            "scan_points="
            f"{latest[1]} finite_latest={latest[2]} valid_latest={latest[3]} "
            f"valid_ratio_avg={statistics.mean(valid_ratios):.3f}"
        )
        print(f"invalid_latest: inf={latest[4]} nan={latest[5]}")
        if latest[6] is not None:
            print(f"range_valid_latest: min={latest[6]:.3f} max={latest[7]:.3f} mean={latest[8]:.3f}")
        if first_indices and last_indices:
            print(f"valid_index_span: first~{round(statistics.mean(first_indices))} last~{round(statistics.mean(last_indices))}")

    print(f"odom_samples={len(node.odom)}")
    if node.odom:
        xy_range = max(value_range(node.odom, 1), value_range(node.odom, 2))
        yaw_range = math.degrees(value_range(node.odom, 3))
        latest = node.odom[-1]
        print(f"odom_stationary_range: xy={xy_range:.4f}m yaw={yaw_range:.3f}deg")
        print(f"odom_latest: x={latest[1]:.3f} y={latest[2]:.3f} yaw={math.degrees(latest[3]):.2f}deg")

    if node.costmaps:
        latest = node.costmaps[-1]
        total = latest[6] or 1
        print(
            "local_costmap: "
            f"{latest[1]}x{latest[2]} res={latest[3]:.3f} "
            f"occupied_ratio={latest[4] / total:.4f} unknown_ratio={latest[5] / total:.4f}"
        )

    for parent, child in (("map", "odom"), ("odom", "base_link"), ("base_link", "laser")):
        print_tf(node, parent, child)

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()

