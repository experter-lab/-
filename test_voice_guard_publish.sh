#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash || true
python3 - <<'PY'
import rclpy, time
from rclpy.node import Node
from std_msgs.msg import String
rclpy.init()
node = Node('test_voice_capability_guard_pub')
pub = node.create_publisher(String, '/medicine/ai_chat_text', 10)
time.sleep(0.5)
msg = String()
msg.data = '\u5e2e\u6211\u628a\u836f\u6446\u597d\uff0c\u518d\u5012\u4e00\u676f\u6e29\u6c34\u3002'
pub.publish(msg)
time.sleep(0.8)
node.destroy_node()
rclpy.shutdown()
PY
sleep 8
tail -80 /tmp/medicine_ai_voice_chat.log 2>/dev/null || tail -80 /tmp/medicine_ai_chat.log 2>/dev/null || true
