#!/usr/bin/env python3
"""把 PWM 拉到 ±400 偏移 (1100/1900),测电机有没有反应。
独占串口：先 kill chassis_bridge_node。
"""
import sys, time
from pymavlink import mavutil

PORT = "/dev/ttyS9"
BAUD = 921600

m = mavutil.mavlink_connection(PORT, baud=BAUD, source_system=255, source_component=0)
hb = m.wait_heartbeat(timeout=5)
print(f"connected, mode={hb.custom_mode} armed={'Y' if hb.base_mode & 0x80 else 'N'}")

# 喂熟
print("==> 喂 1500/1500 中位 1 秒")
for _ in range(10):
    m.mav.rc_channels_override_send(m.target_system, m.target_component,
        1500, 65535, 1500, 65535, 65535, 65535, 65535, 65535)
    time.sleep(0.1)

# 切 MANUAL
base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
if hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
    base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
m.mav.set_mode_send(m.target_system, base_mode, 0)
time.sleep(0.5)

# 监听 SERVO_OUTPUT_RAW
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)

def burst(throttle, steering, label, seconds):
    print(f"\n==> {label}: throttle={throttle}, steering={steering}, {seconds}s")
    t0 = time.time()
    last_send = 0
    while time.time() - t0 < seconds:
        now = time.time()
        if now - last_send >= 0.1:
            m.mav.rc_channels_override_send(m.target_system, m.target_component,
                steering, 65535, throttle, 65535, 65535, 65535, 65535, 65535)
            last_send = now
        msg = m.recv_match(type="SERVO_OUTPUT_RAW", blocking=True, timeout=0.05)
        if msg:
            print(f"  t={now-t0:4.1f}s  SERVO7={msg.servo7_raw}  SERVO8={msg.servo8_raw}")
            time.sleep(0.4)

# 一连串测试
burst(1900, 1500, "全速前进 (PWM=1900)", 3.0)
burst(1500, 1500, "停 (PWM=1500)", 1.0)
burst(1100, 1500, "全速后退 (PWM=1100)", 3.0)
burst(1500, 1500, "停", 1.0)

# release
print("\n==> release override")
m.mav.rc_channels_override_send(m.target_system, m.target_component, 0,0,0,0,0,0,0,0)
print("done")
