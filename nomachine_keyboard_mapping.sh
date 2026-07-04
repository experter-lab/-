#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

stop_old_keyboard_drives() {
  local pid cmdline
  for pid in $(pgrep -f "rk3588_keyboard_drive.py|rk3588_start_mapping_keyboard_drive.sh" || true); do
    [[ -z "$pid" || "$pid" = "$$" || "$pid" = "$PPID" ]] && continue
    cmdline="$(tr '\0' ' ' < "/proc/$pid/cmdline" 2>/dev/null || true)"
    case "$cmdline" in
      *rk3588_keyboard_drive.py*|*rk3588_start_mapping_keyboard_drive.sh*)
        echo "[keyboard-control] stopping old keyboard drive process: $pid"
        kill "$pid" 2>/dev/null || true
        ;;
    esac
  done
}

ensure_chassis_bridge() {
  if ros2 node list 2>/dev/null | grep -Fxq /chassis_bridge; then
    return 0
  fi

  echo "[keyboard-control] /chassis_bridge is not visible yet; trying service restart"
  systemctl restart rk3588-chassis-bridge.service 2>/dev/null || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ros2 node list 2>/dev/null | grep -Fxq /chassis_bridge; then
      return 0
    fi
    sleep 1
  done

  echo "[keyboard-control] ERROR: /chassis_bridge is not running."
  return 1
}

ensure_safe_before_drive() {
  if /mnt/sdcard/rk3588_check_brake_status.sh; then
    return 0
  fi

  echo
  echo "[keyboard-control] brake status is not safe; applying safe stop before keyboard drive"
  /mnt/sdcard/rk3588_safe_stop.sh || true
  sleep 1
  /mnt/sdcard/rk3588_check_brake_status.sh
}

cleanup() {
  echo
  echo "[keyboard-control] exiting; applying safe stop"
  /mnt/sdcard/rk3588_safe_stop.sh || true
  /mnt/sdcard/rk3588_check_brake_status.sh || true
}
trap cleanup EXIT INT TERM

clear
echo "RK3588 standalone keyboard drive"
echo
echo "This shortcut is independent from Cartographer/RViz/map state."
echo "It will authorize low-speed manual chassis motion until you press Q or close the window."
echo
echo "Controls:"
echo "  W/S: forward/back"
echo "  A/D: turn left/right"
echo "  Z/C: spin left/right"
echo "  Space: stop"
echo "  +/-: speed gear"
echo "  Q: exit and return to safe state"
echo

stop_old_keyboard_drives

if ! ensure_chassis_bridge; then
  read -r -p "Press Enter to close." _
  exit 1
fi

if ! ensure_safe_before_drive; then
  echo "[keyboard-control] ERROR: brake status is not safe."
  read -r -p "Press Enter to close." _
  exit 1
fi

/mnt/sdcard/rk3588_start_mapping_keyboard_drive.sh --confirm

echo
read -r -p "Keyboard control exited. Press Enter to close this window..." _
