#!/usr/bin/env python3
"""Full control test: start node → switch MANUAL → arm → pub cmd_vel → check PWM."""
import subprocess, time, json, rclpy, os, sys
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import SetBool
from geometry_msgs.msg import Twist

params_file = ("/mnt/sdcard/medicine_robot_ws/install/medicine_chassis_bridge/"
               "share/medicine_chassis_bridge/config/"
               "chassis_bridge_ardupilot_serial_readonly.yaml")

# Start chassis bridge
proc = subprocess.Popen(
    ["ros2", "run", "medicine_chassis_bridge", "chassis_bridge_node",
     "--ros-args", "--params-file", params_file],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    env={**os.environ, "RCUTILS_COLORIZED_OUTPUT": "0"}, text=True
)

rclpy.init()
latest = {}

class Node_(Node):
    def __init__(self):
        super().__init__("test_ctrl")
        self.create_subscription(String, "/medicine/chassis_status", self.cb, 10)
        self.cmd_pub = self.create_publisher(Twist, "/cmd_vel", 10)

    def cb(self, msg):
        global latest
        latest = json.loads(msg.data)

    def call_srv(self, name, data_bool, timeout=8.0):
        client = self.create_client(SetBool, f"/chassis_bridge/{name}")
        if not client.wait_for_service(timeout):
            return None, f"service {name} timeout"
        req = SetBool.Request()
        req.data = data_bool
        future = client.call_async(req)
        start = time.time()
        while time.time() - start < timeout:
            rclpy.spin_once(self, timeout_sec=0.1)
            if future.done():
                r = future.result()
                return r.success, r.message
        return None, "no response"

node = Node_()

# Wait for heartbeat
print("waiting for heartbeat...")
for _ in range(60):
    rclpy.spin_once(node, timeout_sec=0.3)
    a = latest.get("ardupilot", {})
    if a.get("heartbeat_ok"):
        print(f"  HEARTBEAT OK  count={a['heartbeat_count']}  mode={a['custom_mode_name']}({a['custom_mode']})  "
              f"readonly={a['readonly']}  control={a['control_enabled']}")
        break

# Step 1: Switch to MANUAL
print("\n>>> set_mode → MANUAL")
ok, msg = node.call_srv("set_mode", True)
print(f"  success={ok}  msg={msg}")

# Step 2: Arm
print("\n>>> arm → True")
ok, msg = node.call_srv("arm", True)
print(f"  success={ok}  msg={msg}")

# Wait for mode change
time.sleep(3)
for _ in range(10):
    rclpy.spin_once(node, timeout_sec=0.3)
a = latest.get("ardupilot", {})
print(f"  mode after: {a.get('custom_mode_name')}({a.get('custom_mode')})  base_mode={a.get('base_mode')}")

# Step 3: Authorize control
print("\n>>> authorize_control")
ok, msg = node.call_srv("authorize_control", True)
print(f"  success={ok}  msg={msg}")

# Step 4: Disable emergency stop
print("\n>>> set_emergency_stop → False")
ok, msg = node.call_srv("set_emergency_stop", False)
print(f"  success={ok}  msg={msg}")

# Step 5: Send cmd_vel (slow forward + slight turn)
print("\n>>> pub cmd_vel: linear=0.10, angular=0.10")
twist = Twist()
twist.linear.x = 0.10  # slow forward
twist.angular.z = 0.10  # slight turn
for _ in range(10):
    node.cmd_pub.publish(twist)
    rclpy.spin_once(node, timeout_sec=0.15)
    time.sleep(0.15)

# Check RC PWM
time.sleep(1)
for _ in range(10):
    rclpy.spin_once(node, timeout_sec=0.2)
rc = latest.get("ardupilot", {}).get("rc_override", {})
print(f"  RC throttle(PWM): ch{rc['throttle_channel']}={rc['last_throttle_pwm']}")
print(f"  RC steering(PWM): ch{rc['steering_channel']}={rc['last_steering_pwm']}")

# Step 6: Zero cmd_vel
print("\n>>> pub cmd_vel: STOP (0,0)")
twist.linear.x = 0.0
twist.angular.z = 0.0
for _ in range(8):
    node.cmd_pub.publish(twist)
    rclpy.spin_once(node, timeout_sec=0.15)
    time.sleep(0.15)

time.sleep(1)
for _ in range(10):
    rclpy.spin_once(node, timeout_sec=0.2)
rc = latest.get("ardupilot", {}).get("rc_override", {})
print(f"  RC throttle: ch{rc['throttle_channel']}={rc['last_throttle_pwm']}")
print(f"  RC steering: ch{rc['steering_channel']}={rc['last_steering_pwm']}")

# Cleanup: back to HOLD + disarm + estop
print("\n>>> cleanup: HOLD + disarm + estop")
node.call_srv("set_mode", False)
node.call_srv("arm", False)
node.call_srv("set_emergency_stop", True)

proc.terminate(); proc.wait(timeout=3)
node.destroy_node(); rclpy.shutdown()
print("\nDONE")
