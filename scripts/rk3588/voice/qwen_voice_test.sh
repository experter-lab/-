#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

rm -f /tmp/qwen_test_response.txt
timeout 45 ros2 topic echo /medicine/ai_chat_response --once > /tmp/qwen_test_response.txt 2>&1 &
echo_pid=$!

sleep 1
ros2 topic pub --once /medicine/ai_chat_text std_msgs/msg/String "{data: 你好，请用一句话介绍你自己}"
wait "${echo_pid}" || true

echo "[qwen-test] response:"
cat /tmp/qwen_test_response.txt || true

echo "[qwen-test] ai log:"
tail -60 /tmp/medicine_ai_voice_chat_bridge.log || true
