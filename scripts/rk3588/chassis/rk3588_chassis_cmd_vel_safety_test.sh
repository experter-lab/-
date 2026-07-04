#!/usr/bin/env bash
set -eo pipefail

PORT="${1:-/dev/ttyS9}"
BAUD="${2:-115200}"
LOG_FILE="/tmp/chassis_bridge_cmd_vel_safety.log"

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

pkill -f '[c]hassis_bridge_node' || true

ros2 run medicine_chassis_bridge chassis_bridge_node --ros-args \
  --params-file /mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml \
  -p ardupilot_port:="${PORT}" \
  -p ardupilot_baudrate:="${BAUD}" \
  -p ardupilot_readonly:=true \
  -p ardupilot_control_enabled:=false \
  -p emergency_stop:=true \
  >"${LOG_FILE}" 2>&1 &
BRIDGE_PID=$!

cleanup() {
  kill "${BRIDGE_PID}" 2>/dev/null || true
  pkill -f '[c]hassis_bridge_node' || true
}
trap cleanup EXIT

sleep 2

echo "=== RK3588 chassis /cmd_vel safety test ==="
echo "PORT=${PORT}"
echo "BAUD=${BAUD}"
echo "BRIDGE_PID=${BRIDGE_PID}"
echo "LOG_FILE=${LOG_FILE}"
echo "--- bridge log ---"
tail -n 20 "${LOG_FILE}" || true

python3 - <<'PY'
import json
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from std_msgs.msg import String
from std_srvs.srv import SetBool

latest = None
failures = []


def record_failure(message):
    failures.append(message)
    print(f"FAIL {message}", flush=True)


def check(condition, message):
    if condition:
        print(f"OK {message}", flush=True)
    else:
        record_failure(message)


def status_cb(msg):
    global latest
    try:
        latest = json.loads(msg.data)
    except Exception as exc:
        latest = {"parse_error": str(exc), "raw": msg.data}


def spin_until(node, predicate, timeout_sec, label):
    start = time.time()
    while time.time() - start < timeout_sec:
        rclpy.spin_once(node, timeout_sec=0.1)
        if latest is not None and predicate(latest):
            return latest
    record_failure(f"timeout waiting for {label}")
    return latest


def publish_cmd(node, pub, linear, angular, duration_sec):
    msg = Twist()
    msg.linear.x = linear
    msg.angular.z = angular
    end = time.time() + duration_sec
    while time.time() < end:
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.02)
        time.sleep(0.08)


def call_estop(node, client, enabled):
    if not client.wait_for_service(timeout_sec=3.0):
        record_failure("set_emergency_stop service unavailable")
        return False
    req = SetBool.Request()
    req.data = enabled
    future = client.call_async(req)
    deadline = time.time() + 3.0
    while time.time() < deadline and not future.done():
        rclpy.spin_once(node, timeout_sec=0.1)
    if not future.done():
        record_failure(f"set_emergency_stop({enabled}) timeout")
        return False
    response = future.result()
    check(response.success, f"set_emergency_stop({enabled}) service success")
    return bool(response.success)


rclpy.init()
node = rclpy.create_node("chassis_cmd_vel_safety_tester")
status_sub = node.create_subscription(String, "/medicine/chassis_status", status_cb, 10)
cmd_pub = node.create_publisher(Twist, "/cmd_vel", 10)
estop_client = node.create_client(SetBool, "/chassis_bridge/set_emergency_stop")

first = spin_until(node, lambda s: s.get("mode") == "ardupilot", 5.0, "initial chassis status") or {}
print("INITIAL_STATUS", json.dumps(first, ensure_ascii=False), flush=True)
ap = first.get("ardupilot", {})
check(first.get("mode") == "ardupilot", "bridge mode is ardupilot")
check(first.get("publish_odom") is False, "publish_odom is disabled")
check(first.get("emergency_stop") is True, "emergency_stop starts enabled")
check(ap.get("readonly") is True, "ardupilot_readonly is true")
check(ap.get("control_enabled") is False, "ardupilot_control_enabled is false")
check(ap.get("error") is None, "ardupilot serial open has no error")

cmd_before = int(first.get("cmd_count", 0))
publish_cmd(node, cmd_pub, 0.12, 0.20, 0.8)
estop_status = spin_until(node, lambda s: int(s.get("cmd_count", 0)) > cmd_before, 3.0, "cmd_count during estop") or {}
print("ESTOP_CMD_STATUS", json.dumps(estop_status, ensure_ascii=False), flush=True)
check(estop_status.get("emergency_stop") is True, "emergency_stop remains enabled while receiving /cmd_vel")
check(abs(float(estop_status.get("target_linear", 999.0))) < 0.001, "target_linear forced to zero by emergency_stop")
check(abs(float(estop_status.get("target_angular", 999.0))) < 0.001, "target_angular forced to zero by emergency_stop")
check(abs(float(estop_status.get("current_linear", 999.0))) < 0.001, "current_linear forced to zero by emergency_stop")
check(abs(float(estop_status.get("current_angular", 999.0))) < 0.001, "current_angular forced to zero by emergency_stop")

call_estop(node, estop_client, False)
spin_until(node, lambda s: s.get("emergency_stop") is False, 3.0, "emergency_stop disabled status")
cmd_before = int((latest or {}).get("cmd_count", 0))
publish_cmd(node, cmd_pub, 9.0, 9.0, 1.2)
limited_status = spin_until(node, lambda s: int(s.get("cmd_count", 0)) > cmd_before, 3.0, "limited cmd status") or {}
print("LIMITED_CMD_STATUS", json.dumps(limited_status, ensure_ascii=False), flush=True)
max_linear = float(limited_status.get("max_linear_speed", 0.2))
max_angular = float(limited_status.get("max_angular_speed", 0.5))
check(limited_status.get("emergency_stop") is False, "emergency_stop can be disabled for dry-run safety test")
check(abs(float(limited_status.get("target_linear", 999.0))) <= max_linear + 1e-6, "target_linear is clamped to max_linear_speed")
check(abs(float(limited_status.get("target_angular", 999.0))) <= max_angular + 1e-6, "target_angular is clamped to max_angular_speed")
check(abs(float(limited_status.get("current_linear", 999.0))) <= max_linear + 1e-6, "current_linear stays within max_linear_speed")
check(abs(float(limited_status.get("current_angular", 999.0))) <= max_angular + 1e-6, "current_angular stays within max_angular_speed")
check((limited_status.get("ardupilot", {}) or {}).get("readonly") is True, "readonly remains true after /cmd_vel")
check((limited_status.get("ardupilot", {}) or {}).get("control_enabled") is False, "control output remains disabled after /cmd_vel")

spin_until(node, lambda s: bool(s.get("cmd_timed_out")), 4.0, "cmd_vel timeout")
time.sleep(2.0)
timeout_status = spin_until(node, lambda s: bool(s.get("cmd_timed_out")), 2.0, "post-timeout status") or {}
print("TIMEOUT_STATUS", json.dumps(timeout_status, ensure_ascii=False), flush=True)
check(timeout_status.get("cmd_timed_out") is True, "cmd_vel watchdog timeout becomes true")
check(abs(float(timeout_status.get("target_linear", 999.0))) < 0.001, "target_linear returns to zero after timeout")
check(abs(float(timeout_status.get("target_angular", 999.0))) < 0.001, "target_angular returns to zero after timeout")
check(abs(float(timeout_status.get("current_linear", 999.0))) < 0.05, "current_linear decays near zero after timeout")
check(abs(float(timeout_status.get("current_angular", 999.0))) < 0.05, "current_angular decays near zero after timeout")

call_estop(node, estop_client, True)
final_status = spin_until(node, lambda s: s.get("emergency_stop") is True, 3.0, "final emergency_stop enabled status") or {}
print("FINAL_STATUS", json.dumps(final_status, ensure_ascii=False), flush=True)
check(final_status.get("emergency_stop") is True, "emergency_stop re-enabled at end")
check(abs(float(final_status.get("current_linear", 999.0))) < 0.001, "final current_linear is zero")
check(abs(float(final_status.get("current_angular", 999.0))) < 0.001, "final current_angular is zero")

node.destroy_node()
rclpy.shutdown()

if failures:
    print("RESULT FAIL", flush=True)
    for item in failures:
        print(f" - {item}", flush=True)
    sys.exit(1)

print("RESULT PASS", flush=True)
PY
