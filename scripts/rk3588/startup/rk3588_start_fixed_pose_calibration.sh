#!/usr/bin/env bash
set -eo pipefail

echo "[fixed-pose-calibration] starting localization without saved/global initial pose"
echo "[fixed-pose-calibration] use RViz 2D Pose Estimate to set the real fixed start pose"
echo "[fixed-pose-calibration] after scan overlays the map, run:"
echo "[fixed-pose-calibration]   /mnt/sdcard/rk3588_save_fixed_start_pose.sh"

AUTO_INITIAL_POSE=0 \
AUTO_SCAN_MATCH_POSE=0 \
START_INITIALPOSE_LISTENER=1 \
/mnt/sdcard/rk3588_start_localization_only.sh \
  /mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream \
  /mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static
