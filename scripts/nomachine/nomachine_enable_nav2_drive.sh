#!/usr/bin/env bash
set -o pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

LOCK_FILE=/tmp/rk3588_nav2_drive_shortcut.lock
exec 9>"$LOCK_FILE"
if ! flock -n 9; then
  echo "[nav2-drive-shortcut] Another enable window is already running."
  echo "[nav2-drive-shortcut] Close the old window or finish its ENABLE prompt first."
  read -r -p "Press Enter to close." _
  exit 3
fi

print_drive_status() {
  local tmp=/tmp/rk3588_nav2_drive_status.jsonl
  if ! timeout 8 ros2 topic echo /medicine/chassis_status --once --field data > "$tmp" 2>/tmp/rk3588_nav2_drive_status.err; then
    echo "[nav2-drive-shortcut] WARN: could not read /medicine/chassis_status"
    cat /tmp/rk3588_nav2_drive_status.err 2>/dev/null || true
    return 1
  fi
  python3 - "$tmp" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
line = next((item for item in path.read_text().splitlines() if item.startswith("{")), "")
if not line:
    print("FAIL: no chassis status JSON")
    raise SystemExit(1)
status = json.loads(line)
ardupilot = status.get("ardupilot", {})
print(f"control_authorized={status.get('control_authorized')}")
print(f"emergency_stop={status.get('emergency_stop')}")
print(f"mode={ardupilot.get('custom_mode_name')}")
print(f"armed={ardupilot.get('armed')}")
ok = (
    status.get("control_authorized") is True and
    status.get("emergency_stop") is False
)
if ok:
    print("RESULT OK: Nav2 drive authorization is enabled")
else:
    print("RESULT FAIL: Nav2 drive authorization did not reach expected state")
    raise SystemExit(1)
PY
}

request_confirmation() {
  local confirm_text=""
  echo
  echo "============================================================"
  echo "   DANGER: THIS WILL ENABLE REAL CHASSIS MOTION"
  echo "============================================================"
  echo "Only continue if:"
  echo "  1. RViz scan/map/footprint are visually correct."
  echo "  2. The path is clear."
  echo "  3. The hardware stop/power switch is ready."
  echo
  echo "Type exactly: ENABLE"
  echo
  read -r -p "Authorize Nav2 chassis motion now? " confirm_text
  [[ "$confirm_text" == "ENABLE" ]]
}

run_precheck() {
  local label="$1"
  shift
  local safe_label
  safe_label="$(echo "$label" | tr -c 'A-Za-z0-9_' '_')"
  local log="/tmp/rk3588_nav2_drive_precheck_${safe_label}.log"

  echo "[nav2-drive-shortcut] check: $label"
  if timeout "${NAV2_DRIVE_CHECK_TIMEOUT:-10}" "$@" >"$log" 2>&1; then
    echo "OK $label"
    return 0
  fi

  local rc=$?
  echo "FAIL $label (rc=$rc)"
  sed -n '1,80p' "$log" 2>/dev/null || true
  return 1
}

fast_nav2_drive_precheck() {
  echo "[nav2-drive-shortcut] fast precheck before motion authorization"
  run_precheck "BRAKE_STATUS_SAFE" /mnt/sdcard/rk3588_check_brake_status.sh || return 1

  run_precheck "node /controller_server" bash -lc "ros2 node list | grep -Fx /controller_server" || return 1
  run_precheck "node /planner_server" bash -lc "ros2 node list | grep -Fx /planner_server" || return 1
  run_precheck "node /bt_navigator" bash -lc "ros2 node list | grep -Fx /bt_navigator" || return 1
  run_precheck "node /velocity_smoother" bash -lc "ros2 node list | grep -Fx /velocity_smoother" || return 1
  run_precheck "node /ekf_filter_node" bash -lc "ros2 node list | grep -Fx /ekf_filter_node" || return 1
  run_precheck "node /rk3588_guarded_odom" bash -lc "ros2 node list | grep -Fx /rk3588_guarded_odom" || return 1

  run_precheck "action /navigate_to_pose" bash -lc "ros2 action list | grep -Fx /navigate_to_pose && ros2 action info /navigate_to_pose | grep -q 'Action servers: 1'" || return 1

  run_precheck "topic /odom" ros2 topic info /odom || return 1
  run_precheck "topic /rf2o/odom_raw" ros2 topic info /rf2o/odom_raw || return 1
  run_precheck "topic /odom_rf2o_guarded" ros2 topic info /odom_rf2o_guarded || return 1
  run_precheck "topic /map_static" ros2 topic info /map_static || return 1
  run_precheck "topic /local_costmap/costmap" ros2 topic info /local_costmap/costmap || return 1
  run_precheck "topic /global_costmap/costmap" ros2 topic info /global_costmap/costmap || return 1

  run_precheck "tf map -> odom" bash -lc "log=/tmp/rk3588_nav2_drive_tf_map_odom.log; timeout 5 ros2 run tf2_ros tf2_echo map odom >\"\$log\" 2>&1 || true; grep -q 'Translation:' \"\$log\"" || return 1
  run_precheck "tf odom -> base_link" bash -lc "log=/tmp/rk3588_nav2_drive_tf_odom_base_link.log; timeout 5 ros2 run tf2_ros tf2_echo odom base_link >\"\$log\" 2>&1 || true; grep -q 'Translation:' \"\$log\"" || return 1
  run_precheck "tf base_link -> laser" bash -lc "log=/tmp/rk3588_nav2_drive_tf_base_link_laser.log; timeout 5 ros2 run tf2_ros tf2_echo base_link laser >\"\$log\" 2>&1 || true; grep -q 'Translation:' \"\$log\"" || return 1

  echo "[nav2-drive-shortcut] RESULT OK: fast precheck passed"
}

clear
echo "RK3588 enable Nav2 drive"
echo
echo "This is the only shortcut that authorizes chassis motion."
echo "Continue only when localization is visually correct, the route is clear,"
echo "and the hardware stop/power switch is ready."
echo

echo "[nav2-drive-shortcut] checking Nav2 planning stack and safe brake state"
if ! fast_nav2_drive_precheck; then
  echo
  echo "[nav2-drive-shortcut] RESULT FAIL: Nav2 is not healthy or brake state is not safe."
  echo "[nav2-drive-shortcut] Motion authorization refused."
  read -r -p "Press Enter to close." _
  exit 1
fi

echo
if ! request_confirmation; then
  echo "Cancelled. Nav2 drive was not enabled."
  read -r -p "Press Enter to close." _
  exit 2
fi

if ! /mnt/sdcard/rk3588_enable_nav2_drive.sh --confirm; then
  echo
  echo "[nav2-drive-shortcut] RESULT FAIL: enable command failed."
  read -r -p "Press Enter to close." _
  exit 1
fi

echo
print_drive_status || true
echo
echo "Nav2 drive is enabled. Keep the hardware stop/power switch ready."
read -r -p "Press Enter to close." _
