#!/usr/bin/env bash
set -e
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash || true
python3 - <<'PY'
import rclpy, time
from rclpy.node import Node
from std_msgs.msg import String
rclpy.init()
node=Node('kb_manual_test_pub')
pub=node.create_publisher(String, '/medicine/ai_chat_text', 10)
time.sleep(0.5)
msg=String(); msg.data='\u8001\u4eba\u6f0f\u670d\u964d\u7cd6\u836f\u600e\u4e48\u529e\uff1f'
pub.publish(msg)
time.sleep(0.8)
node.destroy_node(); rclpy.shutdown()
PY
sleep 10
tail -80 /tmp/medicine_ai_voice_chat_bridge.log
