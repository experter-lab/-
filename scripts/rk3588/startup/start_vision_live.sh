#!/usr/bin/env bash
# 常驻启动 vision 节点 (MJPEG 预览端口 8090)
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
pkill -f drug_info_detector_node 2>/dev/null
sleep 1
PARAMS=/mnt/sdcard/medicine_robot_data/config/current_vision_config.yaml
LOG=/tmp/vision_live.log
setsid nohup ros2 run medicine_vision_detector drug_info_detector_node \
  --ros-args --params-file "$PARAMS" \
  </dev/null > "$LOG" 2>&1 &
disown
sleep 6
echo "=== proc ==="
pgrep -af drug_info_detector | grep -v grep
echo "=== port 8090 ==="
ss -tln 2>/dev/null | grep 8090
echo "=== log tail ==="
tail -10 "$LOG"
