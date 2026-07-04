#!/usr/bin/env python3
"""Test: start chassis bridge, switch mode MANUAL/HOLD, verify."""
import subprocess, time, json, rclpy, os
from rclpy.node import Node
from std_msgs.msg import String
from std_srvs.srv import SetBool

params_file = ("/mnt/sdcard/medicine_robot_ws/install/medicine_chassis_bridge/"
               "share/medicine_chassis_bridge/config/"
               "chassis_bridge_ardupilot_serial_readonly.yaml")

# Start chassis bridge in background
proc = subprocess.Popen(
    ["ros2", "run", "medicine_chassis_bridge", "chassis_bridge_node",
     "--ros-args", "--params-file", params_file],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    env={**os.environ, "RCUTILS_COLORIZED_OUTPUT": "0"}, text=True
)

rclpy.init()
last_mode = None

class ChkNode(Node):
    def __init__(self):
        super().__init__("chk")
        self.create_subscription(String, "/medicine/chassis_status", self.cb, 10)

    def cb(self, msg):
        global last_mode
        j = json.loads(msg.data)
        a = j["ardupilot"]
        last_mode = (a.get("custom_mode"), a.get("custom_mode_name"))

node = ChkNode()
client = node.create_client(SetBool, "/chassis_bridge/set_mode")

print("waiting for HB...")
# Spin until we get heartbeat
for _ in range(60):
    rclpy.spin_once(node, timeout_sec=0.3)
    if last_mode is not None:
        break

print(f"initial mode: {last_mode}")

# Wait for set_mode service
if not client.wait_for_service(5.0):
    print("set_mode service not available")
    proc.terminate(); proc.wait()
    rclpy.shutdown()
    exit(1)

# Test: HOLD→MANUAL
print("\n>>> ros2 service call /chassis_bridge/set_mode {data: true}")
req = SetBool.Request()
req.data = True
future = client.call_async(req)
for _ in range(30):
    rclpy.spin_once(node, timeout_sec=0.2)
    if future.done():
        break
resp = future.result()
print(f"response: success={resp.success} message={resp.message}")

# Wait 2 seconds for mode to update
time.sleep(2)
for _ in range(10):
    rclpy.spin_once(node, timeout_sec=0.3)
print(f"after set_mode(True):  mode={last_mode}")

# Test: MANUAL→HOLD
print("\n>>> ros2 service call /chassis_bridge/set_mode {data: false}")
req.data = False
future = client.call_async(req)
for _ in range(30):
    rclpy.spin_once(node, timeout_sec=0.2)
    if future.done():
        break
resp = future.result()
print(f"response: success={resp.success} message={resp.message}")

time.sleep(2)
for _ in range(10):
    rclpy.spin_once(node, timeout_sec=0.3)
print(f"after set_mode(False): mode={last_mode}")

# Cleanup
proc.terminate(); proc.wait(timeout=3)
node.destroy_node()
rclpy.shutdown()
print("\nDONE")
