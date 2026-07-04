#!/usr/bin/env python3
"""snap chassis_status to stdout."""
import sys, json, subprocess, os
os.environ.setdefault("RCUTILS_COLORIZED_OUTPUT", "0")
out = subprocess.run(
    ["bash", "-c",
     "source /opt/ros/humble/setup.bash; timeout 2 ros2 topic echo --once --field data /medicine/chassis_status 2>/dev/null"],
    capture_output=True, text=True, timeout=5).stdout
line = out.strip().split("\n")[0]
if not line:
    print("NO DATA"); sys.exit(1)
j = json.loads(line)
a = j["ardupilot"]
rc = a["rc_override"]
mode = a["custom_mode"]
estop = j["emergency_stop"]
auth = j["control_authorized"]
hb_age = a["heartbeat_age_sec"]
thr = rc["last_throttle_pwm"]
st = rc["last_steering_pwm"]
tl = j["target_linear"]
cl = j["current_linear"]
cmd_age = j["cmd_age_sec"]
cmd_count = j["cmd_count"]
print(f"mode={mode} estop={estop} auth={auth} hb_age={hb_age:.2f}")
print(f"PWM thr={thr} st={st}")
print(f"target_lin={tl:.4f} current_lin={cl:.4f}")
print(f"cmd_age={cmd_age:.3f} cmd_count={cmd_count}")
