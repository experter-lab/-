#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOG=/tmp/carto_initialpose_once.log
SCRIPT=/mnt/sdcard/medicine_robot_data/scripts/carto_initialpose_once.py
YAW_OFFSET="${1:-${INITIALPOSE_YAW_OFFSET_DEG:-0}}"
KEEP_ALIVE="${2:-${INITIALPOSE_KEEP_ALIVE:-0}}"

pkill -f "carto_initialpose_once.py" || true
rm -f "$LOG"
INITIALPOSE_YAW_OFFSET_DEG="$YAW_OFFSET" \
INITIALPOSE_KEEP_ALIVE="$KEEP_ALIVE" \
nohup python3 "$SCRIPT" > "$LOG" 2>&1 &
echo "[initialpose-once] pid: $!"
echo "[initialpose-once] yaw offset deg: $YAW_OFFSET"
echo "[initialpose-once] keep alive: $KEEP_ALIVE"
sleep 2
cat "$LOG" 2>/dev/null || true
if [[ "$KEEP_ALIVE" = "1" ]]; then
  echo "[initialpose-once] waiting for repeated RViz 2D Pose Estimate clicks"
else
  echo "[initialpose-once] waiting for one RViz 2D Pose Estimate click"
fi
