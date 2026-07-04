#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

clear
echo "RK3588 save Cartographer candidate map"
echo
echo "This saves a timestamped candidate map only."
echo "It does not overwrite rk3588_carto_latest.*"
echo

if ! ros2 node list 2>/dev/null | grep -Fxq /cartographer_node; then
  echo "[candidate-save-shortcut] ERROR: /cartographer_node is not running."
  echo "[candidate-save-shortcut] Start mapping and verify the map before saving."
  read -r -p "Press Enter to close." _
  exit 1
fi

if ! /mnt/sdcard/rk3588_save_candidate_map.sh; then
  echo
  echo "[candidate-save-shortcut] RESULT FAIL: candidate save failed."
  read -r -p "Press Enter to close." _
  exit 1
fi

echo
echo "[candidate-save-shortcut] RESULT OK: candidate map saved."
echo "[candidate-save-shortcut] Verify the candidate before promoting it to latest."
read -r -p "Press Enter to close this window..." _
