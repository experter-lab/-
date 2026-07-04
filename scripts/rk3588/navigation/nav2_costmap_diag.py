#!/usr/bin/env python3
"""拉 Nav2 的 local 和 global costmap, 输出统计 + 保存 PNG 看 inflation 分布."""
import math
import time

import numpy as np
import rclpy
from nav_msgs.msg import OccupancyGrid
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy, QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import LaserScan
from tf2_ros import Buffer, TransformListener


class Diag(Node):
    def __init__(self):
        super().__init__("nav2_costmap_diag")
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.gmap = None
        self.lmap = None
        self.scan = None
        qos = QoSProfile(
            history=QoSHistoryPolicy.KEEP_LAST, depth=1,
            reliability=QoSReliabilityPolicy.RELIABLE,
            durability=QoSDurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(OccupancyGrid, "/global_costmap/costmap", self.on_g, qos)
        self.create_subscription(OccupancyGrid, "/local_costmap/costmap", self.on_l, qos)
        self.create_subscription(LaserScan, "/scan", self.on_scan, 10)

    def on_g(self, m): self.gmap = m
    def on_l(self, m): self.lmap = m
    def on_scan(self, m): self.scan = m


def quat_to_yaw(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def stat_costmap(name, m):
    g = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
    n = g.size
    free = int(np.sum(g == 0))
    inflated = int(np.sum((g > 0) & (g < 99)))  # inflation 区域
    lethal = int(np.sum(g >= 99))
    unknown = int(np.sum(g < 0))
    print(f"\n=== {name} ===")
    print(f"  尺寸: {m.info.width}x{m.info.height} = {n} cells, res={m.info.resolution:.3f}")
    print(f"  origin: ({m.info.origin.position.x:.2f}, {m.info.origin.position.y:.2f}) frame={m.header.frame_id}")
    print(f"  free (0):           {free:6d} ({100*free/n:.1f}%)")
    print(f"  inflated (1-98):    {inflated:6d} ({100*inflated/n:.1f}%)  ← 可通过但有代价")
    print(f"  lethal (99-100):    {lethal:6d} ({100*lethal/n:.1f}%)  ← 障碍物本身")
    print(f"  unknown (-1):       {unknown:6d} ({100*unknown/n:.1f}%)")
    return g


def main():
    rclpy.init()
    n = Diag()
    t0 = time.time()
    while time.time() - t0 < 8.0 and (n.gmap is None or n.lmap is None):
        rclpy.spin_once(n, timeout_sec=0.3)
    if n.gmap is None:
        print("ERROR: 没收到 /global_costmap/costmap")
        return
    if n.lmap is None:
        print("ERROR: 没收到 /local_costmap/costmap")
        return

    gg = stat_costmap("Global Costmap", n.gmap)
    lg = stat_costmap("Local Costmap", n.lmap)

    # 找 base_link 在 map 中的位姿
    try:
        tf = n.tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
        bx = tf.transform.translation.x
        by = tf.transform.translation.y
        byaw = quat_to_yaw(tf.transform.rotation)
        print(f"\n=== robot 在 map ===")
        print(f"  pos: ({bx:.3f}, {by:.3f})  yaw: {math.degrees(byaw):.1f}°")

        # 看机器人脚下 global costmap 值是什么 (能反映是不是站在 inflation 上)
        gi = int((bx - n.gmap.info.origin.position.x) / n.gmap.info.resolution)
        gj = int((by - n.gmap.info.origin.position.y) / n.gmap.info.resolution)
        if 0 <= gi < n.gmap.info.width and 0 <= gj < n.gmap.info.height:
            print(f"  脚下 global cost: {gg[gj, gi]}  (0=安全, 99-100=致命)")

        # 检查机器人周围 0.3m 范围内的 cost 分布
        r = 0.3
        rad = int(r / n.gmap.info.resolution)
        i0, j0 = max(0, gi - rad), max(0, gj - rad)
        i1 = min(n.gmap.info.width, gi + rad + 1)
        j1 = min(n.gmap.info.height, gj + rad + 1)
        nearby = gg[j0:j1, i0:i1]
        nb_lethal = int(np.sum(nearby >= 99))
        nb_inflated = int(np.sum((nearby > 0) & (nearby < 99)))
        nb_total = nearby.size
        print(f"  机器人周围 {r}m 内 global cost:")
        print(f"    lethal: {nb_lethal}/{nb_total} ({100*nb_lethal/nb_total:.0f}%)")
        print(f"    inflated: {nb_inflated}/{nb_total} ({100*nb_inflated/nb_total:.0f}%)")
        if nb_lethal > 0:
            print(f"    ⚠ 机器人周围有 lethal cell - Nav2 不会让车启动")
    except Exception as e:
        print(f"TF 失败: {e}")

    # 画 global costmap (重点显示 inflation 分布)
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        info = n.gmap.info
        ox, oy = info.origin.position.x, info.origin.position.y
        ext = [ox, ox + info.width * info.resolution, oy, oy + info.height * info.resolution]
        img = np.flipud(gg.astype(np.float32))
        img[img < 0] = 50  # unknown 显示为中灰

        fig, ax = plt.subplots(figsize=(10, 10))
        im = ax.imshow(img, cmap="hot_r", extent=ext, origin="lower", vmin=0, vmax=100)
        plt.colorbar(im, ax=ax, label="cost (0=free, 100=lethal)")

        if 'bx' in dir():
            ax.scatter([bx], [by], c="cyan", s=200, marker="*", edgecolor="black", zorder=5)
            ax.arrow(bx, by, 0.4 * math.cos(byaw), 0.4 * math.sin(byaw),
                     head_width=0.12, fc="cyan", ec="black", zorder=5)

        ax.set_title(f"Global Costmap  inflation_radius=0.40 cost_scale=5.0")
        ax.set_xlabel("map x (m)")
        ax.set_ylabel("map y (m)")
        ax.set_aspect("equal")
        plt.tight_layout()
        out = "/tmp/nav2_costmap_global.png"
        plt.savefig(out, dpi=110)
        print(f"\nGlobal PNG: {out}")
        plt.close()

        # local costmap (滚动窗口,看机器人周围细节)
        info = n.lmap.info
        ox, oy = info.origin.position.x, info.origin.position.y
        ext = [ox, ox + info.width * info.resolution, oy, oy + info.height * info.resolution]
        img = np.flipud(lg.astype(np.float32))
        img[img < 0] = 50

        fig, ax = plt.subplots(figsize=(10, 10))
        im = ax.imshow(img, cmap="hot_r", extent=ext, origin="lower", vmin=0, vmax=100)
        plt.colorbar(im, ax=ax, label="cost")
        if 'bx' in dir() and ox <= bx <= ext[1] and oy <= by <= ext[3]:
            ax.scatter([bx], [by], c="cyan", s=200, marker="*", edgecolor="black", zorder=5)
            ax.arrow(bx, by, 0.3 * math.cos(byaw), 0.3 * math.sin(byaw),
                     head_width=0.08, fc="cyan", ec="black", zorder=5)
        ax.set_title(f"Local Costmap (3x3m rolling)  inflation_radius=0.25")
        ax.set_aspect("equal")
        plt.tight_layout()
        out = "/tmp/nav2_costmap_local.png"
        plt.savefig(out, dpi=110)
        print(f"Local PNG: {out}")
    except Exception as e:
        print(f"PNG fail: {e}")

    n.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
