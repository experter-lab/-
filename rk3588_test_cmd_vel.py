import time

import rclpy
from geometry_msgs.msg import Twist


def main():
    rclpy.init()
    node = rclpy.create_node("cmd_vel_test_publisher")
    pub = node.create_publisher(Twist, "/cmd_vel", 10)
    time.sleep(0.5)
    msg = Twist()
    msg.linear.x = 0.12
    msg.angular.z = 0.20
    end = time.time() + 2.0
    while time.time() < end:
        pub.publish(msg)
        rclpy.spin_once(node, timeout_sec=0.01)
        time.sleep(0.1)
    stop = Twist()
    for _ in range(5):
        pub.publish(stop)
        rclpy.spin_once(node, timeout_sec=0.01)
        time.sleep(0.05)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
