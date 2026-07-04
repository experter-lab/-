#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

if [[ "${1:-}" != "--confirm" && "${CONFIRM_NAV2_DRIVE:-0}" != "1" ]]; then
  echo "[nav2-drive] REFUSED: explicit confirmation is required."
  echo "[nav2-drive] Run only when the area is clear and you are ready to allow chassis motion:"
  echo "[nav2-drive]   /mnt/sdcard/rk3588_enable_nav2_drive.sh --confirm"
  exit 2
fi

call_bool_once() {
  local service="$1"
  local value="$2"
  local label="$3"
  local timeout_sec="${4:-10}"
  echo "[nav2-drive] $label"
  timeout "$timeout_sec" ros2 service call "$service" std_srvs/srv/SetBool "{data: $value}" >/tmp/rk3588_enable_nav2_drive_last_call.log 2>&1 || {
    echo "[nav2-drive] ERROR: service call failed or timed out: $service"
    cat /tmp/rk3588_enable_nav2_drive_last_call.log 2>/dev/null || true
    return 1
  }
  cat /tmp/rk3588_enable_nav2_drive_last_call.log
}

wait_for_chassis_state() {
  local expected_mode="$1"
  local expected_authorized="$2"
  local expected_estop="$3"
  local timeout_sec="${4:-20}"
  local expected_base_mode="${5:-}"
  local deadline=$((SECONDS + timeout_sec))
  local tmp_json
  tmp_json="$(mktemp /tmp/rk3588_chassis_status.XXXXXX.jsonl)"

  while (( SECONDS < deadline )); do
    if timeout 5 ros2 topic echo /medicine/chassis_status --once --field data > "$tmp_json" 2>/dev/null; then
      if python3 - "$tmp_json" "$expected_mode" "$expected_authorized" "$expected_estop" "$expected_base_mode" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
expected_mode = sys.argv[2]
expected_authorized = sys.argv[3].lower() == "true"
expected_estop = sys.argv[4].lower() == "true"
expected_base_mode = sys.argv[5]

line = next((item for item in path.read_text().splitlines() if item.startswith("{")), "")
if not line:
    raise SystemExit(1)
status = json.loads(line)
ardupilot = status.get("ardupilot", {})
if status.get("control_authorized") != expected_authorized:
    raise SystemExit(1)
if status.get("emergency_stop") != expected_estop:
    raise SystemExit(1)
if ardupilot.get("custom_mode_name") != expected_mode:
    raise SystemExit(1)
if expected_base_mode and int(ardupilot.get("base_mode") or 0) != int(expected_base_mode):
    raise SystemExit(1)
raise SystemExit(0)
PY
      then
        rm -f "$tmp_json"
        return 0
      fi
    fi
    sleep 1
  done

  rm -f "$tmp_json"
  return 1
}

/mnt/sdcard/rk3588_safe_stop.sh
sleep 1
/mnt/sdcard/rk3588_check_brake_status.sh

if ! call_bool_once /chassis_bridge/authorize_control true "authorize_control=true" 10; then
  echo "[nav2-drive] WARN: authorize_control request did not complete"
fi
if ! call_bool_once /chassis_bridge/set_emergency_stop false "emergency_stop=false" 15; then
  echo "[nav2-drive] WARN: emergency_stop request did not complete"
fi
if ! wait_for_chassis_state HOLD True False 20; then
  echo "[nav2-drive] WARN: HOLD+authorized state did not settle cleanly"
fi
sleep 1
if ! call_bool_once /chassis_bridge/set_mode true "set_mode=MANUAL" 25; then
  echo "[nav2-drive] WARN: set_mode request did not complete; waiting for MANUAL confirmation"
fi
if ! wait_for_chassis_state MANUAL True False 25 65; then
  echo "[nav2-drive] WARN: MANUAL not confirmed after first request; retrying set_mode"
  call_bool_once /chassis_bridge/set_mode true "set_mode=MANUAL (retry)" 25 || true
  if ! wait_for_chassis_state MANUAL True False 25 65; then
    echo "[nav2-drive] ERROR: MANUAL was not confirmed"
    exit 1
  fi
fi
sleep 0.5
if ! call_bool_once /chassis_bridge/arm true "arm=true" 10; then
  echo "[nav2-drive] WARN: arm request did not complete"
fi
if ! wait_for_chassis_state MANUAL True False 15 193; then
  echo "[nav2-drive] WARN: MANUAL+ARM not confirmed cleanly; retrying arm"
  call_bool_once /chassis_bridge/arm true "arm=true (retry)" 10 || true
  if ! wait_for_chassis_state MANUAL True False 15 193; then
    echo "[nav2-drive] ERROR: MANUAL+ARM not confirmed"
    exit 1
  fi
fi

echo "[nav2-drive] enabled: authorized, emergency_stop=false, MANUAL, arm=true"
