#!/usr/bin/env python3
import rclpy
from std_msgs.msg import String


def main():
    rclpy.init()
    node = rclpy.create_node("publish_ai_chat_test")
    pub = node.create_publisher(String, "/medicine/ai_chat_text", 10)
    msg = String()
    msg.data = "你好，请用一句话回答你是谁。"
    for _ in range(5):
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.2)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
