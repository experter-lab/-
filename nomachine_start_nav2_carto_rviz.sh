#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

RVIZ_CONFIG="${RVIZ_CONFIG:-/mnt/sdcard/medicine_robot_data/config/rk3588_nav2_view.rviz}"

clear
echo "RK3588 Nav2 RViz"
echo "Starting Cartographer localization + Nav2 with NAV2_ENABLE_DRIVE=0."
echo "This shortcut can plan, but it must not authorize chassis motion."
echo

if ! NAV2_ENABLE_DRIVE=0 \
  AUTO_GLOBAL_INITIAL_POSE=0 \
  ALLOW_GLOBAL_SCAN_MATCH=0 \
  LOCAL_REFINE_INITIAL_POSE=1 \
  AUTO_SCAN_MATCH_POSE=1 \
  REQUIRE_INITIAL_POSE_FOR_NAV2=1 \
  /mnt/sdcard/rk3588_start_nav2_carto.sh; then
  echo
  echo "[nav2-rviz-shortcut] RESULT FAIL: Nav2 startup failed or localization needs a trusted initial pose."
  /mnt/sdcard/rk3588_safe_stop.sh || true
  /mnt/sdcard/rk3588_check_brake_status.sh || true
  read -r -p "Press Enter to close." _
  exit 1
fi

echo
echo "[nav2-rviz-shortcut] status snapshot:"
/mnt/sdcard/rk3588_check_nav2_status.sh || true
echo
/mnt/sdcard/rk3588_check_brake_status.sh || true

export LIBGL_ALWAYS_SOFTWARE=1
export QT_OPENGL=software
export MESA_LOADER_DRIVER_OVERRIDE=llvmpipe

if [[ ! -f "$RVIZ_CONFIG" ]]; then
  echo "[nav2-rviz-shortcut] WARN: custom RViz config not found, fallback to Nav2 default"
  RVIZ_CONFIG=/opt/ros/humble/share/nav2_bringup/rviz/nav2_default_view.rviz
fi

echo
echo "[nav2-rviz-shortcut] Opening RViz2 Nav2 view."
echo "[nav2-rviz-shortcut] RViz config: $RVIZ_CONFIG"
echo "[nav2-rviz-shortcut] Use the separate 'enable Nav2 drive' shortcut only after visual verification."
exec rviz2 -d "$RVIZ_CONFIG"
