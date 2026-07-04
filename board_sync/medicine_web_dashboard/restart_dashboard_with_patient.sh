#!/bin/bash
# Standalone dashboard restart with patient_port enabled (replaces the launch child).
# This kills only the dashboard child (PID 9036), launch (PID 8991) keeps other nodes alive.

set -e

# Kill any existing dashboard node so we don't double-bind the ports.
pkill -INT -f 'medicine_web_dashboard/lib/medicine_web_dashboard/web_dashboard_node' || true
sleep 1.0
pkill -KILL -f 'medicine_web_dashboard/lib/medicine_web_dashboard/web_dashboard_node' || true
sleep 0.5

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

patient_secret_args=()
if [ -n "${MEDICINE_PATIENT_ACCESS_SECRET:-}" ]; then
  patient_secret_args=(-p patient_access_secret:="${MEDICINE_PATIENT_ACCESS_SECRET}")
fi

cd /tmp
nohup setsid ros2 run medicine_web_dashboard web_dashboard_node \
  --ros-args \
  -r __node:=medicine_web_dashboard \
  -p host:=0.0.0.0 \
  -p port:=8085 \
  -p patient_port:=8081 \
  -p patient_web_dist_dir:=/mnt/sdcard/medicine_robot_data/patient_web/dist \
  "${patient_secret_args[@]}" \
  > /tmp/patient_dashboard.log 2>&1 < /dev/null &

disown
echo "dashboard restart launched, log /tmp/patient_dashboard.log"
