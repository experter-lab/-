#!/usr/bin/env bash
set -e
. /opt/ros/humble/setup.bash
. /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo '=== create task ==='
ros2 service call /medicine/create_delivery_task medicine_interfaces/srv/CreateDeliveryTask "{medicine_name: '摄像头联调药品', source_station: 'pharmacy', target_station: 'ward_a', patient_id: 'patient_cam', patient_name: '摄像头测试', ward_id: 'ward_a', bed_no: 'A-09', product_code: '', product_model: 'camera-demo', quantity: '1', trace_id: '', order_no: 'CAMERA-E2E-001', medications_json: '[]'}"
sleep 1

echo '=== load confirm ==='
ros2 service call /medicine/verify_delivery_task medicine_interfaces/srv/VerifyDeliveryTask "{task_id: '', product_code: '', trace_id: '', stage: 'load'}"
sleep 5

echo '=== state after navigation ==='
timeout 5s ros2 topic echo /medicine/delivery_state --once

echo '=== dispense confirm ==='
ros2 service call /medicine/verify_delivery_task medicine_interfaces/srv/VerifyDeliveryTask "{task_id: '', product_code: '', trace_id: '', stage: 'dispense'}"
sleep 1

echo '=== final state ==='
timeout 5s ros2 topic echo /medicine/delivery_state --once
