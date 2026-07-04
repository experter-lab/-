#!/usr/bin/env python3
"""Publish base_link footprint and map-frame pose text for RViz debugging."""

import math

import rclpy
from rclpy.duration import Duration
from geometry_msgs.msg import Point32, PolygonStamped
from rclpy.node import Node
from tf2_ros import Buffer, TransformException, TransformListener
from visualization_msgs.msg import Marker


def yaw_from_quat(q):
    siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
    cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
    return math.atan2(siny_cosp, cosy_cosp)


class RobotDebugFootprint(Node):
    def __init__(self):
        super().__init__("robot_debug_footprint_pub")
        self.pub = self.create_publisher(PolygonStamped, "/robot_debug_footprint", 10)
        self.pose_text_pub = self.create_publisher(Marker, "/robot_debug_pose_text", 10)
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.timer = self.create_timer(0.2, self.publish)

    def publish(self):
        now = self.get_clock().now().to_msg()
        msg = PolygonStamped()
        msg.header.stamp = now
        msg.header.frame_id = "base_link"
        # Real chassis footprint: 44 cm long x 36 cm wide, centered on base_link.
        half_width = 0.18
        rear = -0.22
        front = 0.22
        msg.polygon.points = [
            Point32(x=front, y=half_width, z=0.02),
            Point32(x=front, y=-half_width, z=0.02),
            Point32(x=rear, y=-half_width, z=0.02),
            Point32(x=rear, y=half_width, z=0.02),
            Point32(x=front, y=half_width, z=0.02),
        ]
        self.pub.publish(msg)

        try:
            tf = self.tf_buffer.lookup_transform(
                "map",
                "base_link",
                rclpy.time.Time(),
                timeout=Duration(seconds=0.02),
            )
        except TransformException:
            return

        t = tf.transform.translation
        q = tf.transform.rotation
        marker = Marker()
        marker.header.stamp = now
        marker.header.frame_id = "map"
        marker.ns = "robot_pose_text"
        marker.id = 1
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD
        marker.pose.position.x = t.x
        marker.pose.position.y = t.y
        marker.pose.position.z = 0.45
        marker.pose.orientation.w = 1.0
        marker.scale.z = 0.22
        marker.color.r = 1.0
        marker.color.g = 1.0
        marker.color.b = 0.2
        marker.color.a = 1.0
        marker.text = f"x={t.x:.2f}  y={t.y:.2f}  yaw={math.degrees(yaw_from_quat(q)):.1f} deg"
        self.pose_text_pub.publish(marker)


def main():
    rclpy.init()
    node = RobotDebugFootprint()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
