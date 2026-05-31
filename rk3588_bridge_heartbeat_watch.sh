#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

pkill -f '[c]hassis_bridge_node' || true

nohup ros2 run medicine_chassis_bridge chassis_bridge_node --ros-args \
  --params-file /mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml \
  -p ardupilot_port:=/dev/ttyS9 \
  -p ardupilot_baudrate:=115200 \
  >/tmp/chassis_bridge_ttys9.log 2>&1 &
BRIDGE_PID=$!
sleep 2

echo "BRIDGE_PID=${BRIDGE_PID}"
echo "--- bridge log ---"
tail -n 20 /tmp/chassis_bridge_ttys9.log || true

echo "--- heartbeat watch: keep serial assistant sending HEX periodically now ---"
python3 - <<'PY'
import json
import time

import rclpy
from std_msgs.msg import String

latest = None

def cb(msg):
    global latest
    try:
        latest = json.loads(msg.data)
    except Exception:
        latest = {"raw": msg.data}

rclpy.init()
node = rclpy.create_node("ardupilot_heartbeat_watch")
node.create_subscription(String, "/medicine/chassis_status", cb, 10)
start = time.time()
while time.time() - start < 30.0:
    rclpy.spin_once(node, timeout_sec=0.2)
    ap = (latest or {}).get("ardupilot", {})
    print(
        "t=%.1f heartbeat_ok=%s count=%s age=%s port=%s error=%s"
        % (
            time.time() - start,
            ap.get("heartbeat_ok"),
            ap.get("heartbeat_count"),
            ap.get("heartbeat_age_sec"),
            ap.get("port"),
            ap.get("error"),
        ),
        flush=True,
    )
    if ap.get("heartbeat_count", 0) and ap.get("heartbeat_ok"):
        print(json.dumps(latest, ensure_ascii=False), flush=True)
        break
    time.sleep(0.8)
node.destroy_node()
rclpy.shutdown()
PY
