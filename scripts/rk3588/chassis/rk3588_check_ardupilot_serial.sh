#!/usr/bin/env bash
set -eo pipefail

PORT="${1:-/dev/ttyUSB1}"
BAUD="${2:-115200}"

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

echo "=== RK3588 ArduPilot serial check ==="
date
hostname
uptime

echo "--- target serial ---"
echo "PORT=${PORT}"
echo "BAUD=${BAUD}"

echo "--- usb devices ---"
lsusb || true

echo "--- tty devices ---"
ls -l /dev/ttyACM* /dev/ttyUSB* /dev/ttyS* /dev/serial/by-id/* 2>/dev/null || true

echo "--- recent kernel messages ---"
dmesg | grep -Ei 'ttyACM|ttyUSB|ttyS|Ardu|MAV|H743|STM|CP210|CH34|FTDI|usb' | tail -n 100 || true

echo "--- port existence ---"
if [ -e "${PORT}" ]; then
  ls -l "${PORT}"
else
  echo "FAIL missing ${PORT}"
fi

echo "--- chassis bridge serial readonly smoke test ---"
timeout 12s ros2 run medicine_chassis_bridge chassis_bridge_node --ros-args \
  --params-file /mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml \
  -p ardupilot_port:="${PORT}" \
  -p ardupilot_baudrate:="${BAUD}" >/tmp/rk3588_ardupilot_serial_readonly.log 2>&1 &
BRIDGE_PID=$!
sleep 4
if timeout 6s ros2 topic echo /medicine/chassis_status --once >/tmp/rk3588_ardupilot_serial_status.json 2>/tmp/rk3588_ardupilot_serial_status.err; then
  echo "OK status /medicine/chassis_status"
  cat /tmp/rk3588_ardupilot_serial_status.json
else
  echo "FAIL status /medicine/chassis_status"
  cat /tmp/rk3588_ardupilot_serial_status.err || true
fi
wait "$BRIDGE_PID" || true

echo "--- readonly bridge log ---"
cat /tmp/rk3588_ardupilot_serial_readonly.log || true
