#!/usr/bin/env python3
"""Nav2 + scan 对齐诊断 - 一次性运行。
- 订阅 /map (Nav2/carto 用的那张 OccupancyGrid)
- 订阅 /scan
- tf lookup map -> laser
- 把每个 scan 点投影到 map 坐标
- 查每个点在 occupancy grid 上的值
- 输出统计 + 保存 PNG (绿=free, 黑=occupied, 灰=unknown, 红点=scan 投影位置)
"""
import math
import sys
import time

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener


OUTPUT_PNG = "/tmp/nav2_scan_diag.png"
OUTPUT_TXT = "/tmp/nav2_scan_diag.txt"


class Diag(Node):
    def __init__(self):
        super().__init__("nav2_scan_diag")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.map = None
        self.scan = None

        # /map 是 transient_local 的,需要匹配 QoS
        map_qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(OccupancyGrid, "/map", self.on_map, map_qos)
        self.create_subscription(LaserScan, "/scan", self.on_scan, 10)

    def on_map(self, msg):
        self.map = msg

    def on_scan(self, msg):
        self.scan = msg


def quat_to_yaw(q):
    siny = 2.0 * (q.w * q.z + q.x * q.y)
    cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny, cosy)


def main():
    rclpy.init()
    n = Diag()

    # 等数据
    t0 = time.time()
    while time.time() - t0 < 5.0 and (n.map is None or n.scan is None):
        rclpy.spin_once(n, timeout_sec=0.2)

    if n.map is None:
        print("ERROR: 5s 内没收到 /map")
        sys.exit(1)
    if n.scan is None:
        print("ERROR: 5s 内没收到 /scan")
        sys.exit(1)

    # 等 TF
    t0 = time.time()
    tf = None
    while time.time() - t0 < 5.0:
        try:
            tf = n.tf_buffer.lookup_transform(
                n.map.header.frame_id, n.scan.header.frame_id, rclpy.time.Time())
            break
        except Exception as e:
            rclpy.spin_once(n, timeout_sec=0.2)
    if tf is None:
        print(f"ERROR: 拿不到 TF {n.map.header.frame_id} -> {n.scan.header.frame_id}")
        sys.exit(1)

    # 地图参数
    mw = n.map.info.width
    mh = n.map.info.height
    res = n.map.info.resolution
    ox = n.map.info.origin.position.x
    oy = n.map.info.origin.position.y
    grid = np.array(n.map.data, dtype=np.int8).reshape(mh, mw)

    # 雷达在 map 坐标系下的位姿
    lx = tf.transform.translation.x
    ly = tf.transform.translation.y
    lyaw = quat_to_yaw(tf.transform.rotation)

    # 投影 scan
    s = n.scan
    angles = np.arange(len(s.ranges)) * s.angle_increment + s.angle_min
    ranges = np.array(s.ranges, dtype=np.float32)
    valid = (ranges >= s.range_min) & (ranges <= s.range_max) & np.isfinite(ranges)
    a = angles[valid]
    r = ranges[valid]

    # 在 laser frame: (r*cos(a), r*sin(a))
    # 在 map frame: 旋转 lyaw 再平移 (lx, ly)
    cos_y, sin_y = math.cos(lyaw), math.sin(lyaw)
    px = lx + r * np.cos(a + lyaw)
    py = ly + r * np.sin(a + lyaw)

    # 投影到栅格索引
    ix = ((px - ox) / res).astype(np.int32)
    iy = ((py - oy) / res).astype(np.int32)
    in_map = (ix >= 0) & (ix < mw) & (iy >= 0) & (iy < mh)

    # 统计 occupancy
    vals = np.full(len(ix), -2, dtype=np.int8)  # -2 = 地图外
    vals[in_map] = grid[iy[in_map], ix[in_map]]

    n_total = len(vals)
    n_hit = int(np.sum(vals >= 50))           # 命中障碍
    n_free = int(np.sum((vals >= 0) & (vals < 50)))  # 落在 free space (说明 scan 看到了地图认为空的地方)
    n_unknown = int(np.sum(vals == -1))       # 地图未知区域
    n_out = int(np.sum(vals == -2))           # 地图外

    # 计算 scan 点到最近障碍的距离(只对 in_map 部分)
    # 简化: 用障碍点 vs scan 点的二维距离统计
    obs_mask = grid >= 50
    obs_iy, obs_ix = np.where(obs_mask)
    nearest_dist = []
    if len(obs_ix) > 0 and np.any(in_map):
        # 随机取 200 个 scan 点算最近距离(全算太慢)
        idx = np.where(in_map)[0]
        if len(idx) > 200:
            idx = np.random.choice(idx, 200, replace=False)
        for i in idx:
            d = np.min(np.sqrt((obs_ix - ix[i])**2 + (obs_iy - iy[i])**2)) * res
            nearest_dist.append(d)
    nearest_dist = np.array(nearest_dist) if nearest_dist else np.array([0.0])

    # 文本输出
    lines = []
    lines.append("=" * 60)
    lines.append("Nav2 + scan 对齐诊断")
    lines.append("=" * 60)
    lines.append(f"map: {mw}x{mh} cells, res={res:.3f}m/cell")
    lines.append(f"  origin: ({ox:.2f}, {oy:.2f}) frame={n.map.header.frame_id}")
    lines.append(f"  覆盖范围 x:[{ox:.2f}, {ox+mw*res:.2f}] y:[{oy:.2f}, {oy+mh*res:.2f}]")
    lines.append(f"  free cells: {int(np.sum((grid >= 0) & (grid < 50)))}")
    lines.append(f"  occupied cells: {int(np.sum(grid >= 50))}")
    lines.append(f"  unknown cells: {int(np.sum(grid == -1))}")
    lines.append("")
    lines.append(f"scan: {len(s.ranges)} 束, frame={n.scan.header.frame_id}")
    lines.append(f"  range: [{s.range_min:.2f}, {s.range_max:.2f}]")
    lines.append(f"  angle: [{math.degrees(s.angle_min):.1f}°, {math.degrees(s.angle_max):.1f}°]")
    lines.append(f"  valid 点数: {int(np.sum(valid))} / {len(s.ranges)}")
    lines.append("")
    lines.append(f"laser 在 map 中的位姿: ({lx:.3f}, {ly:.3f}, yaw={math.degrees(lyaw):.1f}°)")
    lines.append("")
    lines.append("scan 点投影到 map 的分布:")
    lines.append(f"  命中障碍 (occupancy>=50): {n_hit:4d} ({100*n_hit/n_total:.1f}%)  ← 越多越对齐")
    lines.append(f"  落在 free space:        {n_free:4d} ({100*n_free/n_total:.1f}%)  ← 太多 = 错位 / 偏角")
    lines.append(f"  落在 unknown:           {n_unknown:4d} ({100*n_unknown/n_total:.1f}%)  ← 地图没建过的区域")
    lines.append(f"  地图外:                 {n_out:4d} ({100*n_out/n_total:.1f}%)  ← 地图边界外")
    lines.append("")
    lines.append("scan 点到最近障碍 cell 的距离 (单位 m, 仅 in_map 子集):")
    lines.append(f"  中位数: {np.median(nearest_dist):.3f}  ← 健康定位 <0.10")
    lines.append(f"  P90:    {np.percentile(nearest_dist, 90):.3f}")
    lines.append(f"  最大:   {np.max(nearest_dist):.3f}")
    lines.append("")

    # 诊断结论
    align_pct = 100 * n_hit / n_total
    median_d = float(np.median(nearest_dist))
    if align_pct > 60 and median_d < 0.15:
        verdict = "✓ 对齐良好"
    elif align_pct > 30 and median_d < 0.30:
        verdict = "△ 对齐一般 - 可优化"
    else:
        verdict = "✗ 对齐差 - 需要重定位或修 TF"
    lines.append(f"结论: {verdict}")
    lines.append("=" * 60)

    text = "\n".join(lines)
    print(text)
    with open(OUTPUT_TXT, "w") as f:
        f.write(text)

    # 保存 PNG
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap

        # occupancy grid: -1=unknown 灰, 0=free 白, 100=occupied 黑
        img = np.full_like(grid, 128, dtype=np.uint8)
        img[grid == 0] = 255
        img[grid > 50] = 0
        # 翻转 y 让 origin 在左下
        img = np.flipud(img)

        fig, ax = plt.subplots(figsize=(10, 10))
        ax.imshow(img, cmap="gray", extent=[ox, ox + mw * res, oy, oy + mh * res], origin="lower")

        # scan 点(只画 in_map 部分)
        ax.scatter(px[in_map], py[in_map], c="red", s=2, alpha=0.6, label="scan 点")
        # 雷达位置
        ax.scatter([lx], [ly], c="lime", s=80, marker="*", edgecolor="black", label="laser", zorder=5)
        # 雷达朝向
        ax.arrow(lx, ly, 0.3 * math.cos(lyaw), 0.3 * math.sin(lyaw),
                 head_width=0.08, fc="lime", ec="black", zorder=5)

        ax.set_title(f"对齐质量: {verdict}  |  命中障碍 {align_pct:.0f}%  |  中位偏差 {median_d:.2f}m")
        ax.legend()
        ax.set_xlabel("map x (m)")
        ax.set_ylabel("map y (m)")
        ax.set_aspect("equal")
        plt.tight_layout()
        plt.savefig(OUTPUT_PNG, dpi=110)
        print(f"\nPNG: {OUTPUT_PNG}")
    except ImportError:
        print("(matplotlib 未装,跳过 PNG)")
    except Exception as e:
        print(f"(PNG 保存失败: {e})")

    n.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
