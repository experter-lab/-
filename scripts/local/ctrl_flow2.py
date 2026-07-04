#!/usr/bin/env python3
"""Simple control flow: start node, switch MANUAL, arm, pub cmd_vel, check PWM."""
import subprocess, os, time, json, rclpy
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist

PARAMS = "/mnt/sdcard/medicine_robot_ws/install/medicine_chassis_bridge/share/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml"

p = subprocess.Popen(["ros2","run","medicine_chassis_bridge","chassis_bridge_node",
    "--ros-args","--params-file",PARAMS],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    env={**os.environ}, text=True)

rclpy.init()
latest = {}

class N(Node):
    def __init__(self):
        super().__init__("t")
        self.create_subscription(String, "/medicine/chassis_status", lambda m: latest.update(json.loads(m.data)), 10)
        self.cmd = self.create_publisher(Twist, "/cmd_vel", 10)

n = N()

def svc(name, val):
    c = n.create_client(SetBool, f"/chassis_bridge/{name}")
    if not c.wait_for_service(8.0):
        return f"{name}: SERVICE TIMEOUT"
    req = SetBool.Request(); req.data = val
    f = c.call_async(req)
    for _ in range(40):
        rclpy.spin_once(n, timeout_sec=0.15)
        if f.done(): return str(f.result().message)
    return f"{name}: NO RESPONSE"

# Wait for HB
for _ in range(80):
    rclpy.spin_once(n, timeout_sec=0.3)
    a = latest.get("ardupilot", {})
    if a.get("heartbeat_ok"):
        print(f"HB OK  rc_on={a['control_enabled']}  estop={latest.get('emergency_stop')}")
        break

# Flow
print("set_mode MANUAL:", svc("set_mode", True))
time.sleep(2)
print("arm:", svc("arm", True))
time.sleep(2)
print("authorize:", svc("authorize_control", True))
time.sleep(1)

# Check mode
for _ in range(20): rclpy.spin_once(n, timeout_sec=0.15)
a = latest.get("ardupilot", {})
print(f"mode={a.get('custom_mode')}({a.get('custom_mode_name')}) base={a.get('base_mode')}")

# pub cmd_vel
t = Twist(); t.linear.x = 0.10; t.angular.z = 0.10
for _ in range(10):
    n.cmd.publish(t)
    rclpy.spin_once(n, timeout_sec=0.12); time.sleep(0.12)
time.sleep(2)

# Check PWM
for _ in range(20): rclpy.spin_once(n, timeout_sec=0.15)
rc = latest.get("ardupilot", {}).get("rc_override", {})
print(f"PWM: throttle={rc.get('last_throttle_pwm')} steering={rc.get('last_steering_pwm')}")

# Stop
t.linear.x = 0.0; t.angular.z = 0.0
for _ in range(8): n.cmd.publish(t); rclpy.spin_once(n, timeout_sec=0.12); time.sleep(0.12)
time.sleep(1)

# Cleanup
print("cleanup:", svc("set_mode", False), svc("arm", False), svc("set_emergency_stop", True))
p.terminate(); p.wait(5)
n.destroy_node(); rclpy.shutdown()
print("DONE")
