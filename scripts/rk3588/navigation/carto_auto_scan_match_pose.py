#!/usr/bin/env python3
"""Estimate and optionally apply Cartographer initial pose by scan-to-map matching."""

import argparse
import hashlib
import json
import math
import os
import time

import cv2
import numpy as np
import rclpy
import yaml
from cartographer_ros_msgs.srv import FinishTrajectory, GetTrajectoryStates, StartTrajectory
from geometry_msgs.msg import Pose
from rclpy.node import Node
from sensor_msgs.msg import LaserScan


ACTIVE = 0
FROZEN = 2
CONFIG_DIR = "/mnt/sdcard/medicine_robot_ws/install/medicine_robot_bringup/share/medicine_robot_bringup/config"
CONFIG_BASENAME = "rk3588_carto_localization.lua"


def yaw_to_quat(yaw):
    return 0.0, 0.0, math.sin(yaw * 0.5), math.cos(yaw * 0.5)


def yaw_from_quat(qx, qy, qz, qw):
    siny_cosp = 2.0 * (qw * qz + qx * qy)
    cosy_cosp = 1.0 - 2.0 * (qy * qy + qz * qz)
    return math.atan2(siny_cosp, cosy_cosp)


def yaw_diff(a, b):
    return math.atan2(math.sin(a - b), math.cos(a - b))


def sha256_file(path):
    if not path or not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_anchor_pose(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    x = float(data["x"])
    y = float(data["y"])
    if "yaw_deg" in data:
        yaw = math.radians(float(data["yaw_deg"]))
    else:
        yaw = yaw_from_quat(
            float(data.get("qx", 0.0)),
            float(data.get("qy", 0.0)),
            float(data["qz"]),
            float(data["qw"]),
        )
    return x, y, yaw


class ScanGrabber(Node):
    def __init__(self):
        super().__init__(f"carto_auto_scan_match_pose_{os.getpid()}")
        self.scan = None
        self.create_subscription(LaserScan, "/scan", self._on_scan, 10)

    def _on_scan(self, msg):
        if self.scan is None:
            self.scan = msg

    def wait_scan(self, timeout_sec):
        deadline = time.monotonic() + timeout_sec
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.scan is not None:
                return self.scan
        raise RuntimeError("timeout waiting for /scan")


class CartoApplier(Node):
    def __init__(self):
        super().__init__(f"carto_auto_scan_match_apply_{os.getpid()}")
        self.cli_states = self.create_client(GetTrajectoryStates, "/get_trajectory_states")
        self.cli_finish = self.create_client(FinishTrajectory, "/finish_trajectory")
        self.cli_start = self.create_client(StartTrajectory, "/start_trajectory")

    def wait_for_services(self):
        for name, client in (
            ("/get_trajectory_states", self.cli_states),
            ("/finish_trajectory", self.cli_finish),
            ("/start_trajectory", self.cli_start),
        ):
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

    def get_ids(self):
        result = self.call(self.cli_states, GetTrajectoryStates.Request(), 20.0)
        active = []
        frozen = []
        for trajectory_id, state in zip(
            result.trajectory_states.trajectory_id,
            result.trajectory_states.trajectory_state,
        ):
            if state == ACTIVE:
                active.append(trajectory_id)
            elif state == FROZEN:
                frozen.append(trajectory_id)
        return active, frozen

    def resolve_relative_id(self, frozen, selector):
        if selector == "latest":
            return max(frozen)
        if selector == "oldest":
            return min(frozen)
        relative_id = int(selector)
        if relative_id not in frozen:
            raise RuntimeError(
                f"relative trajectory {relative_id} is not frozen; frozen trajectories: {frozen}"
            )
        return relative_id

    def apply_pose(self, pose, relative_to_trajectory_id):
        self.wait_for_services()
        active, frozen = self.get_ids()
        if not frozen:
            raise RuntimeError("no frozen trajectory found")
        relative_id = self.resolve_relative_id(frozen, relative_to_trajectory_id)
        self.get_logger().info(f"active trajectories before apply: {active}")
        self.get_logger().info(f"frozen trajectories before apply: {frozen}")
        self.get_logger().info(
            f"selected frozen trajectory {relative_id} using selector '{relative_to_trajectory_id}'"
        )
        for trajectory_id in active:
            req = FinishTrajectory.Request()
            req.trajectory_id = int(trajectory_id)
            result = self.call(self.cli_finish, req, 30.0)
            self.get_logger().info(
                f"finish trajectory {trajectory_id}: {result.status.message}"
            )
        time.sleep(1.0)
        req = StartTrajectory.Request()
        req.configuration_directory = CONFIG_DIR
        req.configuration_basename = CONFIG_BASENAME
        req.use_initial_pose = True
        req.initial_pose = pose
        req.relative_to_trajectory_id = int(relative_id)
        result = self.call(self.cli_start, req, 45.0)
        self.get_logger().info(
            f"start trajectory {result.trajectory_id} relative_to={relative_id}: {result.status.message}"
        )
        if result.status.code != 0:
            raise RuntimeError(result.status.message)


def load_map(map_yaml):
    with open(map_yaml, "r", encoding="utf-8") as f:
        meta = yaml.safe_load(f)
    img = cv2.imread(meta["image"], cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise RuntimeError(f"failed to load map image: {meta['image']}")
    res = float(meta["resolution"])
    origin = meta["origin"]
    return img, res, float(origin[0]), float(origin[1])


def scan_points(scan, max_range, max_points, laser_x, laser_y, laser_yaw):
    ranges = np.asarray(scan.ranges, dtype=np.float32)
    angles = scan.angle_min + np.arange(ranges.size, dtype=np.float32) * scan.angle_increment
    valid = np.isfinite(ranges)
    valid &= ranges >= max(float(scan.range_min), 0.05)
    valid &= ranges <= min(float(scan.range_max), max_range)
    ranges = ranges[valid]
    angles = angles[valid]
    if ranges.size == 0:
        raise RuntimeError("no valid scan points")
    if ranges.size > max_points:
        idx = np.linspace(0, ranges.size - 1, max_points).astype(np.int32)
        ranges = ranges[idx]
        angles = angles[idx]
    laser_xs = ranges * np.cos(angles)
    laser_ys = ranges * np.sin(angles)
    c = math.cos(laser_yaw)
    s = math.sin(laser_yaw)
    xs = c * laser_xs - s * laser_ys + laser_x
    ys = s * laser_xs + c * laser_ys + laser_y
    return xs.astype(np.float32), ys.astype(np.float32)


def make_candidates(img, res, origin_x, origin_y, stride_px):
    free = img > 245
    ys, xs = np.nonzero(free[::stride_px, ::stride_px])
    px = xs * stride_px
    py = ys * stride_px
    wx = origin_x + px.astype(np.float32) * res
    wy = origin_y + (img.shape[0] - 1 - py.astype(np.float32)) * res
    return wx, wy


def score_pose(dist_m, img_shape, res, origin_x, origin_y, scan_x, scan_y, x, y, yaw):
    c = math.cos(yaw)
    s = math.sin(yaw)
    wx = x + c * scan_x - s * scan_y
    wy = y + s * scan_x + c * scan_y
    cols = np.rint((wx - origin_x) / res).astype(np.int32)
    rows = np.rint((img_shape[0] - 1) - (wy - origin_y) / res).astype(np.int32)
    valid = (rows >= 0) & (rows < img_shape[0]) & (cols >= 0) & (cols < img_shape[1])
    if np.count_nonzero(valid) < max(30, int(0.25 * scan_x.size)):
        return 9.0
    d = np.full(scan_x.size, 1.0, dtype=np.float32)
    d[valid] = np.minimum(dist_m[rows[valid], cols[valid]], 1.0)
    return float(np.mean(d))


def search(dist_m, img, res, origin_x, origin_y, scan_x, scan_y, args):
    cand_x, cand_y = make_candidates(img, res, origin_x, origin_y, args.coarse_stride_px)
    yaws = np.deg2rad(np.arange(-180, 180, args.coarse_yaw_step_deg, dtype=np.float32))
    best = []
    for yaw in yaws:
        c = np.cos(yaw)
        s = np.sin(yaw)
        dx = c * scan_x - s * scan_y
        dy = s * scan_x + c * scan_y
        for start in range(0, cand_x.size, args.chunk_size):
            xs = cand_x[start : start + args.chunk_size]
            ys = cand_y[start : start + args.chunk_size]
            score = np.zeros(xs.size, dtype=np.float32)
            valid_count = np.zeros(xs.size, dtype=np.int32)
            for i in range(scan_x.size):
                cols = np.rint((xs + dx[i] - origin_x) / res).astype(np.int32)
                rows = np.rint((img.shape[0] - 1) - (ys + dy[i] - origin_y) / res).astype(np.int32)
                valid = (rows >= 0) & (rows < img.shape[0]) & (cols >= 0) & (cols < img.shape[1])
                score += np.where(valid, np.minimum(dist_m[np.clip(rows, 0, img.shape[0] - 1), np.clip(cols, 0, img.shape[1] - 1)], 1.0), 1.0)
                valid_count += valid.astype(np.int32)
            score /= scan_x.size
            score = np.where(valid_count >= max(30, int(0.25 * scan_x.size)), score, 9.0)
            if score.size:
                ids = np.argpartition(score, min(args.keep_best, score.size - 1))[: args.keep_best]
                for idx in ids:
                    best.append((float(score[idx]), float(xs[idx]), float(ys[idx]), float(yaw)))
        best = sorted(best, key=lambda item: item[0])[: args.keep_best]

    refined = []
    for _, bx, by, byaw in best[: args.refine_seed_count]:
        xs = np.arange(bx - args.refine_xy_window, bx + args.refine_xy_window + 1e-6, args.refine_xy_step)
        ys = np.arange(by - args.refine_xy_window, by + args.refine_xy_window + 1e-6, args.refine_xy_step)
        yaws = np.deg2rad(
            np.arange(
                math.degrees(byaw) - args.refine_yaw_window_deg,
                math.degrees(byaw) + args.refine_yaw_window_deg + 1e-6,
                args.refine_yaw_step_deg,
            )
        )
        for x in xs:
            for y in ys:
                for yaw in yaws:
                    refined.append(
                        (score_pose(dist_m, img.shape, res, origin_x, origin_y, scan_x, scan_y, x, y, yaw), x, y, yaw)
                    )
    return sorted(refined, key=lambda item: item[0])[: args.keep_best]


def search_local(dist_m, img, res, origin_x, origin_y, scan_x, scan_y, anchor, args):
    ax, ay, ayaw = anchor
    xs = np.arange(
        ax - args.local_xy_window,
        ax + args.local_xy_window + 1e-6,
        args.local_xy_step,
    )
    ys = np.arange(
        ay - args.local_xy_window,
        ay + args.local_xy_window + 1e-6,
        args.local_xy_step,
    )
    yaws = np.deg2rad(
        np.arange(
            math.degrees(ayaw) - args.local_yaw_window_deg,
            math.degrees(ayaw) + args.local_yaw_window_deg + 1e-6,
            args.local_yaw_step_deg,
        )
    )
    scored = []
    for x in xs:
        for y in ys:
            for yaw in yaws:
                score = score_pose(
                    dist_m,
                    img.shape,
                    res,
                    origin_x,
                    origin_y,
                    scan_x,
                    scan_y,
                    float(x),
                    float(y),
                    float(yaw),
                )
                scored.append((score, float(x), float(y), float(yaw)))
    return sorted(scored, key=lambda item: item[0])[: args.keep_best]


def independent_candidates(matches, xy_distance, yaw_distance_deg):
    independent = []
    yaw_distance = math.radians(yaw_distance_deg)
    for candidate in matches:
        _, x, y, yaw = candidate
        if all(
            math.hypot(x - ox, y - oy) >= xy_distance
            or abs(yaw_diff(yaw, oyaw)) >= yaw_distance
            for _, ox, oy, oyaw in independent
        ):
            independent.append(candidate)
    return independent


def write_result_pose(path, pose, yaw, args, score, source):
    data = {
        "frame_id": "map",
        "child_frame_id": "base_link",
        "x": pose.position.x,
        "y": pose.position.y,
        "z": pose.position.z,
        "qx": pose.orientation.x,
        "qy": pose.orientation.y,
        "qz": pose.orientation.z,
        "qw": pose.orientation.w,
        "yaw_deg": math.degrees(yaw),
        "pbstream": args.pbstream,
        "pbstream_sha256": sha256_file(args.pbstream),
        "map_yaml": args.map,
        "map_yaml_sha256": sha256_file(args.map),
        "scan_match_score": score,
        "initial_pose_source": source,
        "saved_unix_time": time.time(),
    }
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", default="/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static.yaml")
    parser.add_argument("--pbstream", default="/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--anchor-pose-file",
        default="/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json",
        help="Saved fixed-start map pose used to limit automatic scan matching.",
    )
    parser.add_argument(
        "--allow-global-search",
        action="store_true",
        help="Diagnostic escape hatch: permit whole-map search when no anchor is available.",
    )
    parser.add_argument(
        "--allow-global-apply",
        action="store_true",
        help="Permit applying a whole-map match when confidence and uniqueness checks pass.",
    )
    parser.add_argument(
        "--save-result-pose-file",
        help="Write the accepted match as a reusable fixed-start pose after successful checks.",
    )
    parser.add_argument("--scan-timeout", type=float, default=10.0)
    parser.add_argument("--laser-x", type=float, default=0.15)
    parser.add_argument("--laser-y", type=float, default=0.0)
    parser.add_argument("--laser-yaw-deg", type=float, default=0.0)
    parser.add_argument("--max-range", type=float, default=8.0)
    parser.add_argument("--max-points", type=int, default=260)
    parser.add_argument("--coarse-stride-px", type=int, default=4)
    parser.add_argument("--coarse-yaw-step-deg", type=float, default=10.0)
    parser.add_argument("--chunk-size", type=int, default=256)
    parser.add_argument("--keep-best", type=int, default=12)
    parser.add_argument("--refine-seed-count", type=int, default=6)
    parser.add_argument("--refine-xy-window", type=float, default=0.25)
    parser.add_argument("--refine-xy-step", type=float, default=0.05)
    parser.add_argument("--refine-yaw-window-deg", type=float, default=10.0)
    parser.add_argument("--refine-yaw-step-deg", type=float, default=1.0)
    parser.add_argument("--local-xy-window", type=float, default=0.5)
    parser.add_argument("--local-xy-step", type=float, default=0.05)
    parser.add_argument("--local-yaw-window-deg", type=float, default=20.0)
    parser.add_argument("--local-yaw-step-deg", type=float, default=1.0)
    parser.add_argument("--max-anchor-offset", type=float, default=0.6)
    parser.add_argument(
        "--relative-to-trajectory-id",
        default="latest",
        help="Frozen trajectory used for Cartographer StartTrajectory initial_pose; use latest, oldest, or an integer id.",
    )
    parser.add_argument(
        "--max-score",
        type=float,
        default=0.22,
        help="Refuse --apply when the best average scan-to-obstacle distance is larger than this many meters.",
    )
    parser.add_argument("--ambiguity-xy-distance", type=float, default=1.0)
    parser.add_argument("--ambiguity-yaw-distance-deg", type=float, default=35.0)
    parser.add_argument(
        "--min-score-gap",
        type=float,
        default=0.035,
        help="For whole-map apply, second independent candidate must be this much worse.",
    )
    parser.add_argument(
        "--min-score-ratio",
        type=float,
        default=1.18,
        help="For whole-map apply, second independent candidate must be this ratio worse.",
    )
    args = parser.parse_args()

    rclpy.init()
    grabber = ScanGrabber()
    try:
        scan = grabber.wait_scan(args.scan_timeout)
    finally:
        grabber.destroy_node()

    img, res, origin_x, origin_y = load_map(args.map)
    obstacle = img < 80
    free_for_dt = np.where(obstacle, 0, 255).astype(np.uint8)
    dist_m = cv2.distanceTransform(free_for_dt, cv2.DIST_L2, 5).astype(np.float32) * res
    sx, sy = scan_points(
        scan,
        args.max_range,
        args.max_points,
        args.laser_x,
        args.laser_y,
        math.radians(args.laser_yaw_deg),
    )

    anchor = None
    source = "global"
    if args.anchor_pose_file and os.path.isfile(args.anchor_pose_file):
        anchor = load_anchor_pose(args.anchor_pose_file)
        source = "local_refine"
    elif not args.allow_global_search:
        raise RuntimeError(
            "no saved anchor pose found; refusing whole-map scan matching. "
            "Calibrate once with RViz 2D Pose Estimate and carto_save_current_pose.py, "
            "or pass --allow-global-search for diagnostics only."
        )

    t0 = time.monotonic()
    if anchor is None:
        matches = search(dist_m, img, res, origin_x, origin_y, sx, sy, args)
    else:
        matches = search_local(dist_m, img, res, origin_x, origin_y, sx, sy, anchor, args)
    elapsed = time.monotonic() - t0
    if not matches:
        raise RuntimeError("no scan-map match found")

    print(f"scan points: {sx.size}")
    print(f"initial pose source: {source}")
    if anchor is not None:
        print(
            "anchor: x={:.3f} y={:.3f} yaw={:.1f} local_window=+/-{:.2f}m +/-{:.1f}deg".format(
                anchor[0],
                anchor[1],
                math.degrees(anchor[2]),
                args.local_xy_window,
                args.local_yaw_window_deg,
            )
        )
    print(f"search time: {elapsed:.2f}s")
    for i, (score, x, y, yaw) in enumerate(matches[:5], start=1):
        if anchor is None:
            suffix = ""
        else:
            suffix = " offset={:.3f}m".format(math.hypot(x - anchor[0], y - anchor[1]))
        print(
            f"candidate {i}: score={score:.4f} x={x:.3f} y={y:.3f} "
            f"yaw={math.degrees(yaw):.1f}{suffix}"
        )

    best_score, best_x, best_y, best_yaw = matches[0]
    independent = independent_candidates(
        matches,
        args.ambiguity_xy_distance,
        args.ambiguity_yaw_distance_deg,
    )
    if len(independent) > 1:
        second_score = independent[1][0]
        print(
            "second independent candidate: score={:.4f} x={:.3f} y={:.3f} yaw={:.1f}".format(
                independent[1][0],
                independent[1][1],
                independent[1][2],
                math.degrees(independent[1][3]),
            )
        )
    else:
        second_score = None
        print("second independent candidate: none")

    if args.apply and anchor is None and not args.allow_global_apply:
        raise RuntimeError(
            "whole-map scan match found a candidate, but --allow-global-apply was not set; refusing to apply"
        )
    if anchor is not None:
        best_offset = math.hypot(best_x - anchor[0], best_y - anchor[1])
        if args.apply and best_offset > args.max_anchor_offset:
            raise RuntimeError(
                f"best scan-map offset {best_offset:.3f}m is above max-anchor-offset "
                f"{args.max_anchor_offset:.3f}m; refusing to apply"
            )
    if args.apply and best_score > args.max_score:
        raise RuntimeError(
            f"best scan-map score {best_score:.4f} is above max-score {args.max_score:.4f}; refusing to apply"
        )
    if args.apply and anchor is None and second_score is not None:
        if second_score < best_score + args.min_score_gap:
            raise RuntimeError(
                "whole-map scan match is ambiguous: second score "
                f"{second_score:.4f} is not at least {args.min_score_gap:.4f} worse than best {best_score:.4f}"
            )
        ratio_target = best_score * args.min_score_ratio
        if second_score < ratio_target:
            raise RuntimeError(
                "whole-map scan match is ambiguous: second score "
                f"{second_score:.4f} is below ratio target {ratio_target:.4f}"
            )

    pose = Pose()
    pose.position.x = float(best_x)
    pose.position.y = float(best_y)
    pose.position.z = 0.0
    qx, qy, qz, qw = yaw_to_quat(float(best_yaw))
    pose.orientation.x = qx
    pose.orientation.y = qy
    pose.orientation.z = qz
    pose.orientation.w = qw

    if args.apply:
        applier = CartoApplier()
        try:
            applier.apply_pose(pose, args.relative_to_trajectory_id)
        finally:
            applier.destroy_node()
        if args.save_result_pose_file:
            write_result_pose(args.save_result_pose_file, pose, best_yaw, args, best_score, source)
            print(f"saved accepted pose: {args.save_result_pose_file}")
    rclpy.shutdown()


if __name__ == "__main__":
    main()
