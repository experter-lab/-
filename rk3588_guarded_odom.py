#!/usr/bin/env python3
import json
import math
import time
from dataclasses import dataclass
from typing import Optional

import rclpy
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Imu
from std_msgs.msg import String


def yaw_from_quat(z: float, w: float) -> float:
    return math.atan2(2.0 * w * z, 1.0 - 2.0 * z * z)


def quat_from_yaw(yaw: float) -> tuple[float, float]:
    return math.sin(yaw * 0.5), math.cos(yaw * 0.5)


def norm_angle(angle: float) -> float:
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


@dataclass
class RawPose:
    x: float
    y: float
    yaw: float
    stamp: float


class GuardedOdom(Node):
    def __init__(self) -> None:
        super().__init__("rk3588_guarded_odom")

        self.declare_parameter("raw_odom_topic", "/rf2o/odom_raw")
        self.declare_parameter("output_odom_topic", "/odom_rf2o_guarded")
        self.declare_parameter("imu_topic", "/imu")
        self.declare_parameter("cmd_vel_topic", "/cmd_vel")
        self.declare_parameter("chassis_status_topic", "/medicine/chassis_status")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_rate_hz", 30.0)
        self.declare_parameter("cmd_timeout_sec", 0.6)
        self.declare_parameter("status_timeout_sec", 1.0)
        self.declare_parameter("linear_cmd_threshold", 0.015)
        self.declare_parameter("angular_cmd_threshold", 0.03)
        self.declare_parameter("imu_timeout_sec", 0.5)
        self.declare_parameter("use_imu_yaw_rate", True)
        self.declare_parameter("invert_imu_yaw_rate", False)
        self.declare_parameter("raw_x_sign", 1.0)
        self.declare_parameter("raw_y_sign", 1.0)
        self.declare_parameter("force_linear_direction_from_cmd", True)

        self.raw_topic = self.get_parameter("raw_odom_topic").value
        self.out_topic = self.get_parameter("output_odom_topic").value
        self.imu_topic = self.get_parameter("imu_topic").value
        self.cmd_topic = self.get_parameter("cmd_vel_topic").value
        self.status_topic = self.get_parameter("chassis_status_topic").value
        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        self.cmd_timeout = float(self.get_parameter("cmd_timeout_sec").value)
        self.status_timeout = float(self.get_parameter("status_timeout_sec").value)
        self.linear_cmd_threshold = float(self.get_parameter("linear_cmd_threshold").value)
        self.angular_cmd_threshold = float(self.get_parameter("angular_cmd_threshold").value)
        self.imu_timeout = float(self.get_parameter("imu_timeout_sec").value)
        self.use_imu_yaw_rate = bool(self.get_parameter("use_imu_yaw_rate").value)
        self.imu_sign = -1.0 if bool(self.get_parameter("invert_imu_yaw_rate").value) else 1.0
        self.raw_x_sign = float(self.get_parameter("raw_x_sign").value)
        self.raw_y_sign = float(self.get_parameter("raw_y_sign").value)
        self.force_linear_direction_from_cmd = bool(
            self.get_parameter("force_linear_direction_from_cmd").value
        )

        self.raw_prev: Optional[RawPose] = None
        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vyaw = 0.0

        self.last_cmd: Optional[Twist] = None
        self.last_cmd_time = 0.0
        self.last_status = {}
        self.last_status_time = 0.0
        self.last_imu_time = 0.0
        self.last_imu_integrate_time: Optional[float] = None
        self.last_imu_z = 0.0
        self.freeze_reason = "no_raw_odom"
        self.initialized = False

        self.pub = self.create_publisher(Odometry, self.out_topic, 20)
        self.create_subscription(Odometry, self.raw_topic, self.on_raw_odom, 50)
        self.create_subscription(Imu, self.imu_topic, self.on_imu, 100)
        self.create_subscription(Twist, self.cmd_topic, self.on_cmd, 20)
        self.create_subscription(String, self.status_topic, self.on_status, 20)
        period = 1.0 / max(float(self.get_parameter("publish_rate_hz").value), 1.0)
        self.create_timer(period, self.publish_guarded_odom)

        self.get_logger().info(
            f"guarding {self.raw_topic} -> {self.out_topic}; "
            f"frames {self.odom_frame}->{self.base_frame}; "
            f"raw_signs x={self.raw_x_sign:+.1f} y={self.raw_y_sign:+.1f}; "
            f"force_linear_direction_from_cmd={self.force_linear_direction_from_cmd}"
        )

    def now_sec(self) -> float:
        return self.get_clock().now().nanoseconds / 1e9

    def on_cmd(self, msg: Twist) -> None:
        self.last_cmd = msg
        self.last_cmd_time = self.now_sec()

    def on_status(self, msg: String) -> None:
        try:
            self.last_status = json.loads(msg.data)
            self.last_status_time = self.now_sec()
        except Exception as exc:
            self.get_logger().warn(f"cannot parse chassis status JSON: {exc}", throttle_duration_sec=5.0)

    def is_motion_allowed(self) -> tuple[bool, str]:
        now = self.now_sec()
        if self.last_cmd is None or now - self.last_cmd_time > self.cmd_timeout:
            return False, "cmd_vel_stale_or_missing"
        if now - self.last_status_time > self.status_timeout:
            return False, "chassis_status_stale"

        if self.last_status.get("emergency_stop") is True:
            return False, "emergency_stop"
        if self.last_status.get("control_authorized") is not True:
            return False, "not_authorized"

        ardupilot = self.last_status.get("ardupilot") or {}
        mode = ardupilot.get("custom_mode_name")
        if mode and mode.upper() == "HOLD":
            return False, "hold_mode"

        lin = abs(float(self.last_cmd.linear.x))
        ang = abs(float(self.last_cmd.angular.z))
        if lin < self.linear_cmd_threshold and ang < self.angular_cmd_threshold:
            return False, "zero_cmd"

        return True, "moving"

    def on_imu(self, msg: Imu) -> None:
        now = self.now_sec()
        self.last_imu_time = now
        z_rate = self.imu_sign * float(msg.angular_velocity.z)
        allowed, _ = self.is_motion_allowed()

        if (
            self.use_imu_yaw_rate
            and allowed
            and self.last_imu_integrate_time is not None
            and now - self.last_imu_integrate_time < self.imu_timeout
        ):
            self.yaw = norm_angle(self.yaw + z_rate * (now - self.last_imu_integrate_time))

        self.last_imu_integrate_time = now
        self.last_imu_z = z_rate

    def on_raw_odom(self, msg: Odometry) -> None:
        now = self.now_sec()
        raw = RawPose(
            x=float(msg.pose.pose.position.x),
            y=float(msg.pose.pose.position.y),
            yaw=yaw_from_quat(float(msg.pose.pose.orientation.z), float(msg.pose.pose.orientation.w)),
            stamp=now,
        )

        if self.raw_prev is None:
            self.raw_prev = raw
            self.x = 0.0
            self.y = 0.0
            self.yaw = 0.0
            self.initialized = True
            return

        allowed, reason = self.is_motion_allowed()
        self.freeze_reason = reason
        dt = max(now - self.raw_prev.stamp, 1e-3)
        dx = self.raw_x_sign * (raw.x - self.raw_prev.x)
        dy = self.raw_y_sign * (raw.y - self.raw_prev.y)
        dyaw_raw = norm_angle(raw.yaw - self.raw_prev.yaw)

        if allowed:
            if (
                self.force_linear_direction_from_cmd
                and self.last_cmd is not None
                and abs(float(self.last_cmd.linear.x)) >= self.linear_cmd_threshold
            ):
                distance = math.hypot(dx, dy)
                direction = 1.0 if float(self.last_cmd.linear.x) > 0.0 else -1.0
                heading = self.yaw
                dx = direction * distance * math.cos(heading)
                dy = direction * distance * math.sin(heading)
            self.x += dx
            self.y += dy
            if not (self.use_imu_yaw_rate and now - self.last_imu_time < self.imu_timeout):
                self.yaw = norm_angle(self.yaw + dyaw_raw)
            self.vx = dx / dt
            self.vy = dy / dt
            self.vyaw = self.last_imu_z if now - self.last_imu_time < self.imu_timeout else dyaw_raw / dt
        else:
            self.vx = 0.0
            self.vy = 0.0
            self.vyaw = 0.0

        # Always advance the raw anchor. This discards RF2O drift accumulated while frozen.
        self.raw_prev = raw

    def publish_guarded_odom(self) -> None:
        if not self.initialized:
            return

        msg = Odometry()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame
        msg.pose.pose.position.x = self.x
        msg.pose.pose.position.y = self.y
        msg.pose.pose.position.z = 0.0
        qz, qw = quat_from_yaw(self.yaw)
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw
        msg.twist.twist.linear.x = self.vx
        msg.twist.twist.linear.y = self.vy
        msg.twist.twist.angular.z = self.vyaw

        msg.pose.covariance[0] = 0.04
        msg.pose.covariance[7] = 0.04
        msg.pose.covariance[14] = 1e6
        msg.pose.covariance[21] = 1e6
        msg.pose.covariance[28] = 1e6
        msg.pose.covariance[35] = 0.03
        msg.twist.covariance[0] = 0.08
        msg.twist.covariance[7] = 0.08
        msg.twist.covariance[14] = 1e6
        msg.twist.covariance[21] = 1e6
        msg.twist.covariance[28] = 1e6
        msg.twist.covariance[35] = 0.03
        self.pub.publish(msg)


def main() -> None:
    rclpy.init()
    node = GuardedOdom()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
