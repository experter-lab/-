#!/usr/bin/env bash
# 后台启 vision, 完全脱离 SSH
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
pkill -f drug_info_detector_node 2>/dev/null
sleep 1
PARAMS=/mnt/sdcard/medicine_robot_data/config/current_vision_config.yaml
setsid bash -c "ros2 run medicine_vision_detector drug_info_detector_node --ros-args --params-file $PARAMS > /tmp/vision.log 2>&1" </dev/null >/dev/null 2>&1 &
disown
echo "scheduled, sleeping 2s"
sleep 2
pgrep -af drug_info_detector | grep -v "$$" | head -1
echo "log tail:"
sleep 2
tail -3 /tmp/vision.log 2>/dev/null
