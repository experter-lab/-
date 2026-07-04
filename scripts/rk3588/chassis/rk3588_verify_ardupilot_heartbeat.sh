#!/usr/bin/env bash
set -eo pipefail

PORT="${1:-/dev/ttyS9}"
BAUD="${2:-115200}"
WAIT_SEC="${3:-20}"
DOMAIN_ID="${4:-93}"
LOG_FILE="/tmp/rk3588_verify_ardupilot_heartbeat.log"
STATUS_FILE="/tmp/rk3588_verify_ardupilot_heartbeat_status.json"

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

export ROS_DOMAIN_ID="${DOMAIN_ID}"

echo "=== RK3588 real ArduPilot heartbeat readonly verification ==="
date
echo "PORT=${PORT}"
echo "BAUD=${BAUD}"
echo "WAIT_SEC=${WAIT_SEC}"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"

if [ ! -e "${PORT}" ]; then
  echo "RESULT FAIL missing serial port ${PORT}"
  exit 2
fi

rm -f "${LOG_FILE}" "${STATUS_FILE}"

ros2 run medicine_chassis_bridge chassis_bridge_node --ros-args \
  --params-file /mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml \
  -p ardupilot_port:="${PORT}" \
  -p ardupilot_baudrate:="${BAUD}" \
  -p ardupilot_readonly:=true \
  -p ardupilot_control_enabled:=false \
  -p emergency_stop:=true \
  -p serial_enabled:=false \
  -p publish_odom:=false \
  -p publish_tf:=false \
  >"${LOG_FILE}" 2>&1 &
BRIDGE_PID=$!

cleanup() {
  kill -INT "${BRIDGE_PID}" 2>/dev/null || true
  wait "${BRIDGE_PID}" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2

echo "--- bridge log tail ---"
tail -n 30 "${LOG_FILE}" || true

echo "--- waiting for heartbeat ---"
python3 - "${WAIT_SEC}" "${PORT}" "${BAUD}" "${STATUS_FILE}" <<'PY'
import json
import sys
import time

import rclpy
from std_msgs.msg import String

wait_sec = float(sys.argv[1])
expected_port = sys.argv[2]
expected_baud = int(sys.argv[3])
status_file = sys.argv[4]
latest = None


def cb(msg):
    global latest
    try:
        latest = json.loads(msg.data)
    except Exception:
        latest = {"raw": msg.data}


rclpy.init()
node = rclpy.create_node("verify_real_ardupilot_heartbeat")
node.create_subscription(String, "/medicine/chassis_status", cb, 10)
start = time.time()
passed = False
while time.time() - start < wait_sec:
    rclpy.spin_once(node, timeout_sec=0.2)
    status = latest or {}
    ap = status.get("ardupilot", {}) if isinstance(status.get("ardupilot"), dict) else {}
    print(
        "t=%.1f received=%s heartbeat_ok=%s count=%s age=%s port=%s baud=%s error=%s"
        % (
            time.time() - start,
            bool(latest),
            ap.get("heartbeat_ok"),
            ap.get("heartbeat_count"),
            ap.get("heartbeat_age_sec"),
            ap.get("port"),
            ap.get("baudrate"),
            ap.get("error"),
        ),
        flush=True,
    )
    if (
        status.get("mode") == "ardupilot"
        and status.get("emergency_stop") is True
        and status.get("publish_odom") is False
        and ap.get("readonly") is True
        and ap.get("control_enabled") is False
        and ap.get("error") is None
        and ap.get("port") == expected_port
        and int(ap.get("baudrate") or 0) == expected_baud
        and int(ap.get("heartbeat_count") or 0) > 0
        and ap.get("heartbeat_ok") is True
    ):
        passed = True
        break
    time.sleep(0.8)

if latest is not None:
    with open(status_file, "w", encoding="utf-8") as file:
        json.dump(latest, file, ensure_ascii=False, indent=2)

node.destroy_node()
rclpy.shutdown()

if not passed:
    print("RESULT FAIL real ArduPilot heartbeat not verified", flush=True)
    if latest is not None:
        print(json.dumps(latest, ensure_ascii=False), flush=True)
    sys.exit(2)

ap = latest.get("ardupilot", {})
print("RESULT PASS real ArduPilot heartbeat verified", flush=True)
print(
    "IDENTITY system_id=%s component_id=%s mavlink_version=%s type=%s autopilot=%s base_mode=%s custom_mode=%s system_status=%s"
    % (
        ap.get("system_id"),
        ap.get("component_id"),
        ap.get("mavlink_version"),
        ap.get("type"),
        ap.get("autopilot"),
        ap.get("base_mode"),
        ap.get("custom_mode"),
        ap.get("system_status"),
    ),
    flush=True,
)
print(json.dumps(latest, ensure_ascii=False), flush=True)
PY

echo "--- saved latest status ---"
cat "${STATUS_FILE}" 2>/dev/null || true
