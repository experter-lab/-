#!/usr/bin/env bash
set -e
. /opt/ros/humble/setup.bash
. /mnt/sdcard/medicine_robot_ws/install/setup.bash
ros2 service call /medicine/cancel_delivery_task medicine_interfaces/srv/CancelDeliveryTask "{task_id: '9e06efaf'}"
