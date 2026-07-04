#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PBSTREAM=/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest.pbstream
MAP_STEM=/mnt/sdcard/medicine_robot_data/maps/rk3588_carto_latest_static
MAP_YAML="${MAP_STEM}.yaml"

clear
echo "RK3588 Cartographer localization RViz"
echo "Using canonical latest map:"
echo "  pbstream: $PBSTREAM"
echo "  static:   $MAP_YAML"
echo "Global automatic scan-match is disabled in this shortcut."
echo "RViz 2D Pose Estimate is enabled and can be clicked repeatedly."
echo

if [[ ! -f "$PBSTREAM" ]]; then
  echo "[loc-rviz-shortcut] ERROR: missing pbstream: $PBSTREAM"
  read -r -p "Press Enter to close." _
  exit 1
fi

if [[ ! -f "$MAP_YAML" ]]; then
  echo "[loc-rviz-shortcut] WARN: static yaml missing; localization script may export it from pbstream."
fi

AUTO_GLOBAL_INITIAL_POSE=0 \
ALLOW_GLOBAL_SCAN_MATCH=0 \
LOCAL_REFINE_INITIAL_POSE=1 \
AUTO_SCAN_MATCH_POSE=1 \
START_INITIALPOSE_LISTENER=1 \
INITIALPOSE_KEEP_ALIVE=1 \
INITIALPOSE_YAW_OFFSET_DEG=180 \
/mnt/sdcard/rk3588_start_localization_only.sh "$PBSTREAM" "$MAP_STEM"

echo
echo "[loc-rviz-shortcut] localization startup returned. Status snapshot:"
/mnt/sdcard/rk3588_check_localization_status.sh || true
echo
/mnt/sdcard/rk3588_check_brake_status.sh || true
echo
read -r -p "Localization RViz was opened. Press Enter to close this terminal." _
