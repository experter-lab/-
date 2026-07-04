#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

stop_mapping_drive_leftovers() {
  local pattern
  for pattern in \
    "teleop_twist_keyboard" \
    "rk3588_keyboard_drive.py" \
    "kbd_drive" \
    "rk3588_start_mapping_keyboard_drive.sh"; do
    local pids
    pids="$(pgrep -f "$pattern" || true)"
    if [[ -n "$pids" ]]; then
      echo "[safe-stop-shortcut] stopping drive leftover: $pattern"
      while read -r pid; do
        [[ -z "$pid" || "$pid" = "$$" || "$pid" = "$PPID" ]] && continue
        kill "$pid" 2>/dev/null || true
      done <<< "$pids"
    fi
  done
}

clear
echo "RK3588 safe stop"
echo "This shortcut stops manual drive leftovers, zeros /cmd_vel, HOLD/DISARMs,"
echo "sets software emergency stop, and revokes control authorization."
echo

stop_mapping_drive_leftovers
/mnt/sdcard/rk3588_safe_stop.sh || true

echo
echo "[safe-stop-shortcut] final brake status:"
if /mnt/sdcard/rk3588_check_brake_status.sh; then
  echo
  echo "RESULT OK: BRAKE_STATUS_SAFE"
else
  echo
  echo "RESULT FAIL: brake status is not safe. Use the hardware stop and inspect chassis_bridge."
fi

echo
read -r -p "Press Enter to close." _
