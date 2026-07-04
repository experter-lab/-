#!/usr/bin/env bash
# 解析 chassis_status JSON 输出关键字段
set -eo pipefail

source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

ros2 topic echo /medicine/chassis_status --once --field data 2>/dev/null | python3 -c "
import sys, json
raw = sys.stdin.read()
# pick first JSON object: from first '{' to its matching '}'
i = raw.find('{')
j = raw.rfind('}')
d = json.loads(raw[i:j+1])
a = d.get('ardupilot', {})
print('=== chassis_bridge status ===')
print(f'  mode               : {d.get(\"mode\")}')
print(f'  emergency_stop     : {d.get(\"emergency_stop\")}')
print(f'  control_authorized : {d.get(\"control_authorized\")}')
print(f'  hardware_estop     : {d.get(\"hardware_estop_detected\")}')
print(f'  cmd_count          : {d.get(\"cmd_count\")}  age={d.get(\"cmd_age_sec\"):.2f}s  timed_out={d.get(\"cmd_timed_out\")}')
print(f'  target  lin/ang    : {d.get(\"target_linear\"):+.3f} / {d.get(\"target_angular\"):+.3f}')
print(f'  current lin/ang    : {d.get(\"current_linear\"):+.3f} / {d.get(\"current_angular\"):+.3f}')
print()
print('=== ArduPilot ===')
print(f'  port               : {a.get(\"port\")} @ {a.get(\"baudrate\")}')
print(f'  readonly           : {a.get(\"readonly\")}')
print(f'  control_enabled    : {a.get(\"control_enabled\")}')
print(f'  heartbeat_ok       : {a.get(\"heartbeat_ok\")}  count={a.get(\"heartbeat_count\")}  age={a.get(\"heartbeat_age_sec\")}')
print(f'  system_id/comp     : {a.get(\"system_id\")}/{a.get(\"component_id\")}')
print(f'  base_mode (hex)    : 0x{(a.get(\"base_mode\") or 0):02x}   (ARMED bit=0x80)')
print(f'  custom_mode        : {a.get(\"custom_mode\")}  ({a.get(\"custom_mode_name\")})')
print(f'  system_status      : {a.get(\"system_status\")}')
print(f'  error              : {a.get(\"error\")}')
batt = a.get('battery', {})
print(f'  battery            : {batt.get(\"voltage_v\")}V  {batt.get(\"current_a\")}A  {batt.get(\"remaining_pct\")}%')
rc = a.get('rc_override', {}) or {}
print(f'  last RC throttle/steer PWM : {rc.get(\"last_throttle_pwm\")} / {rc.get(\"last_steering_pwm\")}')
"
