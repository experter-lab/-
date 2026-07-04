#!/usr/bin/env python3
import math

import rclpy
from geometry_msgs.msg import TransformStamped
from nav_msgs.msg import Odometry
from rclpy.duration import Duration
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


def wrap_angle(angle):
    while angle > math.pi:
        angle -= 2.0 * math.pi
    while angle < -math.pi:
        angle += 2.0 * math.pi
    return angle


class TfOdomPublisher(Node):
    def __init__(self):
        super().__init__("tf_odom_publisher")
        self.declare_parameter("odom_frame", "odom")
        self.declare_parameter("base_frame", "base_link")
        self.declare_parameter("publish_hz", 20.0)
        self.odom_frame = self.get_parameter("odom_frame").value
        self.base_frame = self.get_parameter("base_frame").value
        publish_hz = float(self.get_parameter("publish_hz").value)

        self.tf_buffer = Buffer(cache_time=Duration(seconds=5.0))
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.pub = self.create_publisher(Odometry, "/odom", 20)
        self.last = None
        self.timer = self.create_timer(1.0 / publish_hz, self.on_timer)

    def on_timer(self):
        try:
            tf_msg = self.tf_buffer.lookup_transform(
                self.odom_frame, self.base_frame, rclpy.time.Time()
            )
        except TransformException as exc:
            self.get_logger().warn(f"waiting for TF {self.odom_frame}->{self.base_frame}: {exc}", throttle_duration_sec=2.0)
            return

        odom = self.to_odom(tf_msg)
        self.pub.publish(odom)

    def to_odom(self, tf_msg: TransformStamped):
        now = self.get_clock().now()
        t = tf_msg.transform.translation
        q = tf_msg.transform.rotation
        yaw = yaw_from_quat(q)

        msg = Odometry()
        msg.header.stamp = now.to_msg()
        msg.header.frame_id = self.odom_frame
        msg.child_frame_id = self.base_frame
        msg.pose.pose.position.x = t.x
        msg.pose.pose.position.y = t.y
        msg.pose.pose.position.z = t.z
        msg.pose.pose.orientation = q

        # Planar pose is trusted from Cartographer TF; twist is estimated for Nav2.
        msg.pose.covariance[0] = 0.02
        msg.pose.covariance[7] = 0.02
        msg.pose.covariance[35] = 0.05
        msg.twist.covariance[0] = 0.05
        msg.twist.covariance[7] = 0.05
        msg.twist.covariance[35] = 0.10

        current = (now.nanoseconds / 1e9, t.x, t.y, yaw)
        if self.last is not None:
            last_time, last_x, last_y, last_yaw = self.last
            dt = max(current[0] - last_time, 1e-3)
            vx_world = (t.x - last_x) / dt
            vy_world = (t.y - last_y) / dt
            msg.twist.twist.linear.x = math.cos(yaw) * vx_world + math.sin(yaw) * vy_world
            msg.twist.twist.linear.y = -math.sin(yaw) * vx_world + math.cos(yaw) * vy_world
            msg.twist.twist.angular.z = wrap_angle(yaw - last_yaw) / dt
        self.last = current
        return msg


def main():
    rclpy.init()
    node = TfOdomPublisher()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
