#!/bin/bash
exec </dev/null
exec >/tmp/vision.log 2>&1
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash
exec ros2 run medicine_vision_detector drug_info_detector_node --ros-args --params-file /mnt/sdcard/medicine_robot_data/config/current_vision_config.yaml
