#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PBSTREAM=/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream
MAP_YAML=/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static.yaml
POSE_FILE=/mnt/sdcard/medicine_robot_data/config/carto_initial_pose.json
BACKUP_DIR=/mnt/sdcard/medicine_robot_data/backups/fixed_start_pose_$(date +%Y%m%d_%H%M%S)

echo "[fixed-pose-save] checking brake state"
/mnt/sdcard/rk3588_check_brake_status.sh

if [[ -f "$POSE_FILE" ]]; then
  mkdir -p "$BACKUP_DIR"
  cp -a "$POSE_FILE" "$BACKUP_DIR/"
  echo "[fixed-pose-save] previous pose backed up to $BACKUP_DIR"
fi

python3 /mnt/sdcard/medicine_robot_data/scripts/carto_save_current_pose.py \
  --output "$POSE_FILE" \
  --pbstream "$PBSTREAM" \
  --map-yaml "$MAP_YAML" \
  --timeout 10

echo "[fixed-pose-save] saved pose:"
cat "$POSE_FILE"

echo "[fixed-pose-save] local scan-match dry run around saved fixed pose"
python3 /mnt/sdcard/medicine_robot_data/scripts/carto_auto_scan_match_pose.py \
  --map "$MAP_YAML" \
  --anchor-pose-file "$POSE_FILE" \
  --scan-timeout 12 \
  --local-xy-window "${LOCAL_SCAN_MATCH_XY_WINDOW:-0.5}" \
  --local-yaw-window-deg "${LOCAL_SCAN_MATCH_YAW_WINDOW_DEG:-20}" \
  --max-score "${AUTO_SCAN_MATCH_MAX_SCORE:-0.22}"

echo "[fixed-pose-save] fixed start pose is ready for future automatic startup"
