#!/usr/bin/env bash
set -euo pipefail

TARGET_STATION="${1:-test_forward_20}"
TIMEOUT_SEC="${2:-35}"

set +u
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash 2>/dev/null || true
set -u

export ROS_DOMAIN_ID="${ROS_DOMAIN_ID:-0}"
export RMW_IMPLEMENTATION="${RMW_IMPLEMENTATION:-rmw_fastrtps_cpp}"

robust_stop() {
  echo "=== robust stop ==="
  timeout 2 ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}" >/dev/null 2>&1 || true
  timeout 2 ros2 topic pub --once /cmd_vel_nav geometry_msgs/msg/Twist "{linear: {x: 0.0}, angular: {z: 0.0}}" >/dev/null 2>&1 || true
  timeout 4 ros2 service call /chassis_bridge/set_emergency_stop std_srvs/srv/SetBool "{data: true}" || true
  timeout 4 ros2 service call /chassis_bridge/authorize_control std_srvs/srv/SetBool "{data: false}" || true
  timeout 4 ros2 service call /chassis_bridge/set_mode std_srvs/srv/SetBool "{data: false}" || true
  /mnt/sdcard/rk3588_check_brake_status.sh || true
}

trap robust_stop EXIT INT TERM

robust_stop
/mnt/sdcard/rk3588_enable_nav2_drive.sh --confirm

python3 - "$TARGET_STATION" "$TIMEOUT_SEC" <<'PY'
import json
import math
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from medicine_interfaces.msg import DeliveryState
from medicine_interfaces.srv import CancelDeliveryTask, CreateDeliveryTask
from rclpy.node import Node
from std_msgs.msg import String
import tf2_ros


target_station = sys.argv[1]
timeout_sec = float(sys.argv[2])


class FixedPointNavTaskTest(Node):
    def __init__(self):
        super().__init__("rk3588_fixed_point_nav_task_test")
        self.chassis = None
        self.state = None
        self.cmd_vel = None
        self.cmd_vel_nav = None
        self.create_client_ = self.create_client(
            CreateDeliveryTask, "/medicine/create_delivery_task"
        )
        self.cancel_client = self.create_client(
            CancelDeliveryTask, "/medicine/cancel_delivery_task"
        )
        self.create_subscription(String, "/medicine/chassis_status", self.on_chassis, 10)
        self.create_subscription(DeliveryState, "/medicine/delivery_state", self.on_state, 10)
        self.create_subscription(Twist, "/cmd_vel", self.on_cmd_vel, 10)
        self.create_subscription(Twist, "/cmd_vel_nav", self.on_cmd_vel_nav, 10)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

    def on_chassis(self, msg):
        try:
            self.chassis = json.loads(msg.data)
        except Exception:
            self.chassis = {"raw": msg.data}

    def on_state(self, msg):
        self.state = msg

    def on_cmd_vel(self, msg):
        self.cmd_vel = msg

    def on_cmd_vel_nav(self, msg):
        self.cmd_vel_nav = msg

    def current_tf(self):
        try:
            tf = self.tf_buffer.lookup_transform("map", "base_link", rclpy.time.Time())
        except Exception:
            return None
        q = tf.transform.rotation
        yaw = math.atan2(
            2.0 * (q.w * q.z + q.x * q.y),
            1.0 - 2.0 * (q.y * q.y + q.z * q.z),
        )
        return tf.transform.translation.x, tf.transform.translation.y, yaw

    def wait_for_chassis_ready(self, timeout=10.0):
        deadline = time.monotonic() + timeout
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            data = self.chassis or {}
            ardupilot = data.get("ardupilot") or {}
            if (
                ardupilot.get("custom_mode_name") == "MANUAL"
                and int(ardupilot.get("base_mode") or 0) == 193
                and data.get("emergency_stop") is False
                and data.get("control_authorized") is True
            ):
                return True
        return False

    def wait_for_idle(self, timeout=5.0):
        deadline = time.monotonic() + timeout
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.state is None or self.state.state == "IDLE":
                return True
        return False

    def wait_for_tf(self, timeout=6.0):
        deadline = time.monotonic() + timeout
        while rclpy.ok() and time.monotonic() < deadline:
            rclpy.spin_once(self, timeout_sec=0.1)
            pose = self.current_tf()
            if pose is not None:
                return pose
        return None

    def create_task(self):
        if not self.create_client_.wait_for_service(timeout_sec=5.0):
            raise RuntimeError("/medicine/create_delivery_task unavailable")
        request = CreateDeliveryTask.Request()
        request.medicine_name = "定点导航测试"
        request.source_station = "pharmacy"
        request.target_station = target_station
        request.patient_id = "nav_probe"
        request.patient_name = "NavProbe"
        request.ward_id = target_station
        request.quantity = "1"
        request.order_no = f"nav_probe_{target_station}"
        request.medications_json = json.dumps(
            [{"id": "nav_test", "medicine_name": "定点导航测试", "load_confirmed": True}],
            ensure_ascii=False,
        )
        future = self.create_client_.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=6.0)
        if not future.done():
            raise RuntimeError("create task timeout")
        return future.result()

    def cancel_task(self, task_id):
        if not task_id or not self.cancel_client.wait_for_service(timeout_sec=3.0):
            return None
        request = CancelDeliveryTask.Request()
        request.task_id = task_id
        future = self.cancel_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        return future.result() if future.done() else None


rclpy.init()
node = FixedPointNavTaskTest()
task_id = ""
try:
    if not node.wait_for_idle():
        raise RuntimeError("task manager is not IDLE")
    if not node.wait_for_chassis_ready():
        raise RuntimeError("chassis not ready for Nav2 drive")

    start = node.wait_for_tf()
    if start is not None:
        print(f"START_TF x={start[0]:.3f} y={start[1]:.3f} yaw_deg={math.degrees(start[2]):.2f}")

    response = node.create_task()
    print(f"CREATE accepted={response.accepted} task_id={response.task_id} message={response.message}")
    if not response.accepted:
        raise RuntimeError("task rejected")
    task_id = response.task_id

    terminal_state = None
    deadline = time.monotonic() + timeout_sec
    last_print = 0.0
    while rclpy.ok() and time.monotonic() < deadline:
        rclpy.spin_once(node, timeout_sec=0.1)
        now = time.monotonic()
        if node.state and now - last_print > 1.0:
            last_print = now
            pose = node.current_tf()
            pose_text = "tf=none" if pose is None else f"tf=({pose[0]:.3f},{pose[1]:.3f},{math.degrees(pose[2]):.1f}deg)"
            cmd = node.cmd_vel
            cmd_nav = node.cmd_vel_nav
            cmd_text = "cmd=none" if cmd is None else f"cmd=({cmd.linear.x:.3f},{cmd.angular.z:.3f})"
            cmd_nav_text = "cmd_nav=none" if cmd_nav is None else f"cmd_nav=({cmd_nav.linear.x:.3f},{cmd_nav.angular.z:.3f})"
            print(f"STATE {node.state.state} progress={node.state.progress:.2f} msg={node.state.message} {pose_text} {cmd_nav_text} {cmd_text}")
        if node.state and node.state.state in {
            "WAITING_DISPENSE_CONFIRMATION",
            "NAVIGATION_FAILED",
            "COMPLETED",
            "CANCELED",
        }:
            terminal_state = node.state.state
            break

    end = node.wait_for_tf(timeout=1.0) or node.current_tf()
    if end is not None:
        print(f"END_TF x={end[0]:.3f} y={end[1]:.3f} yaw_deg={math.degrees(end[2]):.2f}")
    if start is not None and end is not None:
        print(
            f"TF_DELTA distance={math.hypot(end[0] - start[0], end[1] - start[1]):.3f} "
            f"dx={end[0] - start[0]:.3f} dy={end[1] - start[1]:.3f} "
            f"dyaw_deg={math.degrees(end[2] - start[2]):.2f}"
        )
    print(f"TERMINAL_STATE {terminal_state or 'timeout'}")

    cancel_response = node.cancel_task(task_id)
    if cancel_response is not None:
        print(f"CANCEL success={cancel_response.success} message={cancel_response.message}")
    if terminal_state not in {"WAITING_DISPENSE_CONFIRMATION", "COMPLETED"}:
        raise RuntimeError(f"navigation did not succeed: {terminal_state or 'timeout'}")
finally:
    if task_id:
        try:
            node.cancel_task(task_id)
        except Exception:
            pass
    node.destroy_node()
    rclpy.shutdown()
PY
