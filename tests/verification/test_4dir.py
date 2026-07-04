#!/usr/bin/env python3
"""4 方向各发 2s cmd_vel + 在中间采样状态。"""
import time, json, subprocess, os, threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import Twist

LIN = 0.10
ANG = 0.30
DUR = 2.0
GAP = 1.5

rclpy.init()
latest = {}
class N(Node):
    def __init__(self):
        super().__init__("t_4dir")
        self.create_subscription(String, "/medicine/chassis_status", lambda m: latest.update(json.loads(m.data)), 10)
        self.cmd = self.create_publisher(Twist, "/cmd_vel", 10)

n = N()
stop = False
def spin_bg():
    while not stop:
        rclpy.spin_once(n, timeout_sec=0.05)
th = threading.Thread(target=spin_bg, daemon=True); th.start()

def snap(label):
    time.sleep(0.6)  # 等 status 更新
    a = latest.get("ardupilot", {})
    rc = a.get("rc_override", {})
    print(f"  [{label}] mode={a.get('custom_mode')} status={a.get('system_status')}")
    print(f"    PWM thr={rc.get('last_throttle_pwm')} st={rc.get('last_steering_pwm')}")
    print(f"    target_lin={latest.get('target_linear',0):.4f} current_lin={latest.get('current_linear',0):.4f}")

def drive(lx, az, label, dur=DUR):
    print(f"\n>>> {label}: lin={lx:+.2f} ang={az:+.2f} for {dur}s")
    t0 = time.time()
    rate = 0.1  # 10 Hz
    snapped = False
    while time.time() - t0 < dur:
        msg = Twist()
        msg.linear.x = lx
        msg.angular.z = az
        n.cmd.publish(msg)
        if not snapped and time.time() - t0 > 1.0:
            snap(label)
            snapped = True
        time.sleep(rate)
    # 停
    for _ in range(5):
        n.cmd.publish(Twist())
        time.sleep(0.05)

try:
    drive(LIN, 0.0, "W 前进")
    time.sleep(GAP)
    drive(-LIN, 0.0, "S 后退")
    time.sleep(GAP)
    drive(0.0, ANG, "A 左转 (ang=+0.3)")
    time.sleep(GAP)
    drive(0.0, -ANG, "D 右转 (ang=-0.3)")
finally:
    # 收尾
    for _ in range(10):
        n.cmd.publish(Twist())
        time.sleep(0.05)
    stop = True; th.join(timeout=1)
    n.destroy_node(); rclpy.shutdown()
    print("\nDONE")
