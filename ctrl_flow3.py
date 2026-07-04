#!/usr/bin/env python3
"""Continuous cmd_vel + live PWM monitor."""
import subprocess, os, time, json, threading, rclpy
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
        return f"{name}: TIMEOUT"
    req = SetBool.Request(); req.data = val
    f = c.call_async(req)
    for _ in range(40):
        rclpy.spin_once(n, timeout_sec=0.15)
        if f.done(): return str(f.result().message)
    return f"{name}: NO_RESPONSE"

# Wait HB
for _ in range(80):
    rclpy.spin_once(n, timeout_sec=0.3)
    if latest.get("ardupilot", {}).get("heartbeat_ok"):
        print("HB OK")
        break

print(svc("set_mode", True)); time.sleep(2)
print(svc("arm", True)); time.sleep(2)
print(svc("authorize_control", True)); time.sleep(0.5)

for _ in range(10):
    rclpy.spin_once(n, timeout_sec=0.15)
a = latest.get("ardupilot", {})
print(f"MODE={a.get('custom_mode')} base={a.get('base_mode')} estop={latest.get('emergency_stop')} hw_estop={latest.get('hardware_estop_detected')} authorized={latest.get('control_authorized')}")

# Continuous cmd_vel in background
stop_flag = False
def pub_loop():
    t = Twist(); t.linear.x = 0.08; t.angular.z = 0.05
    while not stop_flag:
        n.cmd.publish(t)
        time.sleep(0.05)
th = threading.Thread(target=pub_loop, daemon=True)
th.start()
print("PUBLISHING cmd_vel (0.08, 0.05) ...")

# Monitor PWM for 5 seconds
for i in range(50):
    rclpy.spin_once(n, timeout_sec=0.1)
    rc = latest.get("ardupilot", {}).get("rc_override", {})
    if i % 10 == 0:
        print(f"  t={i*0.1:.1f}s  thr={rc.get('last_throttle_pwm')}  st={rc.get('last_steering_pwm')}")

stop_flag = True; th.join()
time.sleep(1)
for _ in range(15): rclpy.spin_once(n, timeout_sec=0.1)
rc = latest.get("ardupilot", {}).get("rc_override", {})
print(f"FINAL PWM: throttle={rc.get('last_throttle_pwm')} steering={rc.get('last_steering_pwm')}")

# Clear + cleanup
n.cmd.publish(Twist())
print(svc("set_mode", False), svc("arm", False), svc("set_emergency_stop", True))
p.terminate(); p.wait(5)
n.destroy_node(); rclpy.shutdown()
print("DONE")
