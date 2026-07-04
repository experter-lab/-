#!/usr/bin/env python3
"""RK3588 键盘遥控 chassis bridge。

用法（先在另一个终端启动 chassis_bridge_node）：
  python3 rk3588_keyboard_drive.py

控制：
  W / S    前进 / 后退
  A / D    左转 / 右转
  Z / C    原地左转 / 原地右转
  空格     立即停止
  +  /  -  增 / 减速度档位
  Q        退出（切 HOLD + 加锁 + 急停）

按住一个键，速度上升；松开（停止按键），节点的 cmd_timeout_sec 会让车自动归零。
"""
import sys, os, time, json, termios, tty, select, threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist


SPEED_STEPS = [0.04, 0.07, 0.10, 0.13, 0.16]   # 线性档位 m/s（建图慢速档）
REVERSE_STEPS = [0.05, 0.09, 0.13, 0.16, 0.18] # 后退档位，略高于前进以补偿底盘死区
TURN_STEPS  = [0.18, 0.28, 0.38, 0.46, 0.50]   # A/D 左右转档位，更接近原地转力度
SPIN_STEPS  = [0.18, 0.28, 0.38, 0.46, 0.50]   # Z/C 原地转向档位

KEY_HELP = """
  ┌─────────────────────────────┐
  │  W 前  S 后  A 左  D 右     │
  │  Z 原地左转    C 原地右转    │
  │  空格 停   +/- 档位   Q 退出 │
  └─────────────────────────────┘
"""


def getch_nb():
    """非阻塞读一个键。无则返回 None。"""
    fd = sys.stdin.fileno()
    r, _, _ = select.select([fd], [], [], 0.02)
    if r:
        return sys.stdin.read(1)
    return None


class Driver(Node):
    def __init__(self):
        super().__init__("kbd_drive")
        self.create_subscription(String, "/medicine/chassis_status",
                                 self.on_status, 10)
        self.cmd = self.create_publisher(Twist, "/cmd_vel", 10)
        self.latest = {}
        # service clients (异步)
        self.cli_set_mode = self.create_client(SetBool, "/chassis_bridge/set_mode")
        self.cli_arm = self.create_client(SetBool, "/chassis_bridge/arm")
        self.cli_auth = self.create_client(SetBool, "/chassis_bridge/authorize_control")
        self.cli_estop = self.create_client(SetBool, "/chassis_bridge/set_emergency_stop")

    def on_status(self, msg):
        try:
            self.latest = json.loads(msg.data)
        except Exception:
            pass

    def call(self, client, data, name):
        if not client.wait_for_service(3.0):
            print(f"  ⚠️  {name}: 服务不可用")
            return False
        req = SetBool.Request(); req.data = data
        f = client.call_async(req)
        start = time.time()
        while time.time() - start < 3.0:
            rclpy.spin_once(self, timeout_sec=0.1)
            if f.done():
                r = f.result()
                print(f"  {name}: success={r.success} {r.message}")
                return r.success
        print(f"  ⚠️  {name}: 超时")
        return False


def main():
    rclpy.init()
    drv = Driver()

    # 后台 spin
    stop_spin = threading.Event()
    def spin():
        while not stop_spin.is_set() and rclpy.ok():
            rclpy.spin_once(drv, timeout_sec=0.05)
    t = threading.Thread(target=spin, daemon=True); t.start()

    # 等心跳
    print("等待 chassis bridge 心跳...")
    for _ in range(40):
        a = drv.latest.get("ardupilot", {})
        if a.get("heartbeat_ok"):
            print(f"✓ HB OK  mode={a.get('custom_mode')}  base={a.get('base_mode')}")
            break
        time.sleep(0.3)
    else:
        print("✗ 没收到 chassis bridge 心跳，先启动 chassis_bridge_node")
        rclpy.shutdown(); return

    # 初始化：先授权并解除软件急停，再切 MANUAL 和 arm。
    print("\n准备开控：")
    ok = True
    ok = drv.call(drv.cli_auth, True, "authorize_control") and ok
    ok = drv.call(drv.cli_estop, False, "set_emergency_stop → False") and ok
    time.sleep(0.5)
    ok = drv.call(drv.cli_set_mode, True, "set_mode → MANUAL") and ok
    time.sleep(1)
    ok = drv.call(drv.cli_arm, True, "arm") and ok
    if not ok:
        print("✗ 开控失败，保持安全状态并退出")
        drv.cmd.publish(Twist())
        drv.call(drv.cli_set_mode, False, "set_mode → HOLD")
        drv.call(drv.cli_arm, False, "disarm")
        drv.call(drv.cli_estop, True, "set_emergency_stop → True")
        stop_spin.set(); t.join(timeout=1)
        drv.destroy_node(); rclpy.shutdown()
        return

    print(KEY_HELP)

    # raw 模式
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    tty.setraw(fd)

    step_idx = 3  # 默认 4 档，仍低于底盘桥安全限速
    lin = 0.0
    ang = 0.0
    last_key_time = 0.0
    try:
        while True:
            k = getch_nb()
            now = time.time()
            if k:
                k = k.lower()
                if k == 'q':
                    break
                elif k == 'w':
                    lin = SPEED_STEPS[step_idx]; last_key_time = now
                elif k == 's':
                    lin = -REVERSE_STEPS[step_idx]; last_key_time = now
                elif k == 'a':
                    ang = TURN_STEPS[step_idx]; last_key_time = now
                elif k == 'd':
                    ang = -TURN_STEPS[step_idx]; last_key_time = now
                elif k == 'z':
                    lin = 0.0; ang = SPIN_STEPS[step_idx]; last_key_time = now
                elif k == 'c':
                    lin = 0.0; ang = -SPIN_STEPS[step_idx]; last_key_time = now
                elif k == ' ':
                    lin = 0.0; ang = 0.0; last_key_time = now
                elif k == '+' or k == '=':
                    step_idx = min(step_idx + 1, len(SPEED_STEPS) - 1)
                elif k == '-' or k == '_':
                    step_idx = max(step_idx - 1, 0)

            # 0.35 秒无按键就归零（手放开了）
            if now - last_key_time > 0.35:
                lin = 0.0; ang = 0.0

            # 持续 pub cmd_vel
            t_msg = Twist(); t_msg.linear.x = lin; t_msg.angular.z = ang
            drv.cmd.publish(t_msg)

            # 状态行（终端覆盖式）
            a = drv.latest.get("ardupilot", {})
            rc = a.get("rc_override", {})
            thr_pwm = rc.get("last_throttle_pwm")
            st_pwm = rc.get("last_steering_pwm")
            sys.stdout.write(
                f"\r档{step_idx+1}/{len(SPEED_STEPS)}  "
                f"cmd_vel(lin={lin:+.4f}, ang={ang:+.4f})  "
                f"PWM(thr={thr_pwm} st={st_pwm})  "
                f"mode={a.get('custom_mode')} batt={a.get('battery',{}).get('voltage_v')}V    "
            )
            sys.stdout.flush()
            time.sleep(0.03)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        print("\n\n退出，恢复安全状态...")
        drv.cmd.publish(Twist())
        time.sleep(0.3)
        drv.call(drv.cli_set_mode, False, "set_mode → HOLD")
        drv.call(drv.cli_arm, False, "disarm")
        drv.call(drv.cli_estop, True, "set_emergency_stop → True")
        drv.call(drv.cli_auth, False, "authorize_control → False")
        stop_spin.set(); t.join(timeout=1)
        drv.destroy_node(); rclpy.shutdown()
        print("done")


if __name__ == "__main__":
    main()
