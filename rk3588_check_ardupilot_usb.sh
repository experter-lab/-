#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "=== RK3588 ArduPilot USB check ==="
date
hostname
uptime

echo "--- usb devices ---"
lsusb || true

echo "--- tty devices ---"
ls -l /dev/ttyACM* /dev/ttyUSB* /dev/serial/by-id/* 2>/dev/null || true

echo "--- recent kernel messages ---"
dmesg | grep -Ei 'ttyACM|ttyUSB|Ardu|MAV|H743|STM|Cube|PX4|usb' | tail -n 80 || true

echo "--- chassis bridge readonly smoke test ---"
timeout 10s ros2 run medicine_chassis_bridge chassis_bridge_node --ros-args \
  --params-file /mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_readonly.yaml >/tmp/rk3588_ardupilot_readonly.log 2>&1 &
BRIDGE_PID=$!
sleep 3
if timeout 5s ros2 topic echo /medicine/chassis_status --once >/tmp/rk3588_ardupilot_status.json 2>/tmp/rk3588_ardupilot_status.err; then
  echo "OK status /medicine/chassis_status"
  cat /tmp/rk3588_ardupilot_status.json
else
  echo "FAIL status /medicine/chassis_status"
  cat /tmp/rk3588_ardupilot_status.err || true
fi
wait "$BRIDGE_PID" || true

echo "--- readonly bridge log ---"
cat /tmp/rk3588_ardupilot_readonly.log || true
