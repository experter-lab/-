#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

if [[ "${1:-}" != "--confirm" && "${CONFIRM_MAPPING_DRIVE:-0}" != "1" ]]; then
  echo "[keyboard-drive] REFUSED: explicit confirmation is required."
  echo "[keyboard-drive] Use only when the area is clear and a human is watching the robot:"
  echo "[keyboard-drive]   /mnt/sdcard/rk3588_start_mapping_keyboard_drive.sh --confirm"
  exit 2
fi

if [[ ! -f /mnt/sdcard/rk3588_keyboard_drive.py ]]; then
  echo "[keyboard-drive] ERROR: missing /mnt/sdcard/rk3588_keyboard_drive.py"
  exit 1
fi

cleanup() {
  echo
  echo "[keyboard-drive] exiting; applying safe stop"
  /mnt/sdcard/rk3588_safe_stop.sh || true
}
trap cleanup EXIT INT TERM

echo "[keyboard-drive] checking safe state before manual keyboard drive"
if ! /mnt/sdcard/rk3588_check_brake_status.sh; then
  echo "[keyboard-drive] brake status is not safe; applying safe stop first"
  /mnt/sdcard/rk3588_safe_stop.sh || true
  sleep 1
  /mnt/sdcard/rk3588_check_brake_status.sh
fi

echo "[keyboard-drive] starting low-speed keyboard drive"
echo "[keyboard-drive] Keep speed low; press Q in the keyboard window to exit safely."
python3 /mnt/sdcard/rk3588_keyboard_drive.py
