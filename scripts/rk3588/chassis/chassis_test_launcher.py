#!/usr/bin/env python3
"""Launch chassis bridge for 10s, subscribe to status, dump ardupilot section."""
import subprocess, threading, time, json, rclpy, sys, os
from rclpy.node import Node
from std_msgs.msg import String

params_file = sys.argv[1] if len(sys.argv) > 1 else (
    "/mnt/sdcard/medicine_robot_ws/install/medicine_chassis_bridge/share/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml"
)

# Start chassis bridge
proc = subprocess.Popen(
    ["ros2", "run", "medicine_chassis_bridge", "chassis_bridge_node",
     "--ros-args", "--params-file", params_file],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    env={**os.environ, "RCUTILS_COLORIZED_OUTPUT": "0"},
    text=True
)

rclpy.init()
result = {"received": False, "data": None}

class ChkNode(Node):
    def __init__(self):
        super().__init__("status_check")
        self.create_subscription(String, "/medicine/chassis_status", self.cb, 10)

    def cb(self, msg):
        if not result["received"]:
            result["data"] = json.loads(msg.data)
            result["received"] = True

node = ChkNode()

def spin_until():
    end = time.time() + 10
    while time.time() < end and rclpy.ok() and not result["received"]:
        rclpy.spin_once(node, timeout_sec=0.2)

try:
    spin_until()
finally:
    node.destroy_node()
    rclpy.shutdown()
    proc.terminate()
    proc.wait(timeout=5)

if result["received"]:
    a = result["data"]["ardupilot"]
    print(json.dumps(a, ensure_ascii=False, indent=2))
else:
    print("NO_STATUS_RECEIVED")
    # Print any bridge output
    out, _ = proc.communicate(timeout=2)
    if out:
        print("bridge stdout:")
        for line in out.strip().split("\n")[-6:]:
            print("  " + line)
