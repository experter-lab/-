#!/usr/bin/env bash
# 一边发 cmd_vel,一边连续打印 PWM,确认到底有没有送达飞控
set -eo pipefail
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

# 后台 3 秒发 cmd_vel
( timeout 3 ros2 topic pub -r 20 /cmd_vel geometry_msgs/msg/Twist \
    "{linear: {x: 0.08}, angular: {z: 0.0}}" >/dev/null 2>&1 ) &
PUB_PID=$!

# 同时每 0.4s 采一次状态
echo "time  cmd_count  cmd_age  target_lin  current_lin  throttle_pwm  steer_pwm  mode"
for i in 1 2 3 4 5 6 7; do
  ros2 topic echo /medicine/chassis_status --once --field data 2>/dev/null | python3 -c "
import sys, json
raw = sys.stdin.read()
i = raw.find('{'); j = raw.rfind('}')
d = json.loads(raw[i:j+1])
a = d.get('ardupilot', {}) or {}
rc = a.get('rc_override', {}) or {}
print(f'{d[\"stamp_sec\"]%1000:7.2f}  {d[\"cmd_count\"]:>9}  {d[\"cmd_age_sec\"]:.2f}     {d[\"target_linear\"]:+.3f}      {d[\"current_linear\"]:+.3f}        {rc.get(\"last_throttle_pwm\")}        {rc.get(\"last_steering_pwm\")}     {a.get(\"custom_mode_name\")}')
"
  sleep 0.4
done

wait $PUB_PID 2>/dev/null || true
echo "==> done"
