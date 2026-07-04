#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

pkill -f '[c]hassis_bridge_node' || true
pkill -f '[a]rdupilot_pty_feeder.py' || true

cat >/tmp/ardupilot_pty_feeder.py <<'PY'
import os
import pty
import time

heartbeat = bytes.fromhex("FE 09 00 01 01 00 00 00 00 00 0A 03 00 03 03 00 00")
link_path = "/tmp/ardupilot_mavlink_pty"
master_fd, slave_fd = pty.openpty()
slave_name = os.ttyname(slave_fd)
try:
    os.unlink(link_path)
except FileNotFoundError:
    pass
os.symlink(slave_name, link_path)
print(f"PTY_READY {link_path} -> {slave_name}", flush=True)
while True:
    os.write(master_fd, heartbeat)
    time.sleep(0.5)
PY

nohup python3 /tmp/ardupilot_pty_feeder.py >/tmp/ardupilot_pty_feeder.log 2>&1 &
FEEDER_PID=$!
sleep 1
cat /tmp/ardupilot_pty_feeder.log
ls -l /tmp/ardupilot_mavlink_pty

nohup ros2 run medicine_chassis_bridge chassis_bridge_node --ros-args \
  --params-file /mnt/sdcard/medicine_robot_ws/src/medicine_chassis_bridge/config/chassis_bridge_ardupilot_serial_readonly.yaml \
  -p ardupilot_port:=/tmp/ardupilot_mavlink_pty \
  -p ardupilot_baudrate:=115200 \
  >/tmp/chassis_bridge_pty.log 2>&1 &
BRIDGE_PID=$!
sleep 3

echo "--- bridge log ---"
tail -n 40 /tmp/chassis_bridge_pty.log

echo "--- chassis status ---"
timeout 8s ros2 topic echo /medicine/chassis_status --once --field data || true

echo "--- pids ---"
echo "FEEDER_PID=${FEEDER_PID}"
echo "BRIDGE_PID=${BRIDGE_PID}"
pgrep -af 'ardupilot_pty_feeder|chassis_bridge_node' || true
