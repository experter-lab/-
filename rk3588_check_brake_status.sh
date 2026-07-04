#!/usr/bin/env bash
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

TMP=/tmp/rk3588_brake_status.jsonl
timeout 5 ros2 topic echo /medicine/chassis_status --once --field data > "$TMP"

python3 - "$TMP" <<'PY'
import json
import math
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
line = next((item for item in path.read_text().splitlines() if item.startswith("{")), "")
if not line:
    print("FAIL: no chassis status JSON")
    raise SystemExit(1)

status = json.loads(line)
ardupilot = status.get("ardupilot", {})
rc = ardupilot.get("rc_override", {})

checks = []
checks.append(("emergency_stop", status.get("emergency_stop") is True, status.get("emergency_stop")))
checks.append(("control_authorized", status.get("control_authorized") is False, status.get("control_authorized")))
checks.append(("current_linear", math.isclose(float(status.get("current_linear") or 0.0), 0.0, abs_tol=1e-6), status.get("current_linear")))
checks.append(("current_angular", math.isclose(float(status.get("current_angular") or 0.0), 0.0, abs_tol=1e-6), status.get("current_angular")))
checks.append(("target_linear", math.isclose(float(status.get("target_linear") or 0.0), 0.0, abs_tol=1e-6), status.get("target_linear")))
checks.append(("target_angular", math.isclose(float(status.get("target_angular") or 0.0), 0.0, abs_tol=1e-6), status.get("target_angular")))
checks.append(("ardupilot_mode", ardupilot.get("custom_mode_name") == "HOLD", ardupilot.get("custom_mode_name")))

throttle_mid = rc.get("pwm_mid")
steering_mid = rc.get("steering_pwm_mid", throttle_mid)
checks.append(("throttle_pwm", rc.get("last_throttle_pwm") == throttle_mid, rc.get("last_throttle_pwm")))
checks.append(("steering_pwm", rc.get("last_steering_pwm") == steering_mid, rc.get("last_steering_pwm")))

failed = False
for name, ok, value in checks:
    print(f"{'OK' if ok else 'FAIL'} {name}: {value}")
    failed = failed or not ok

if failed:
    raise SystemExit(1)

print("BRAKE_STATUS_SAFE")
PY
