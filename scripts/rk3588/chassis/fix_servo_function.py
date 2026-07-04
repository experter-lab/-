#!/usr/bin/env python3
"""把 SERVO_FUNCTION 改回 CH1/3 (左右 Throttle)，并清掉 CH7/8 的误配。
独占串口：运行前请 kill chassis_bridge_node。"""
import sys, time
from pymavlink import mavutil

PORT = "/dev/ttyS9"
BAUD = 921600

# 目标参数：4 轮差速（skid steering）标配
TARGETS = {
    "SERVO1_FUNCTION": 73.0,   # ThrottleLeft
    "SERVO3_FUNCTION": 74.0,   # ThrottleRight
    "SERVO7_FUNCTION": 0.0,    # Disabled
    "SERVO8_FUNCTION": 0.0,    # Disabled
}

print(f"==> connect {PORT}@{BAUD}")
m = mavutil.mavlink_connection(PORT, baud=BAUD,
                                source_system=254, source_component=0)
print("==> wait heartbeat (5s)")
hb = m.wait_heartbeat(timeout=5)
if not hb:
    print("NO HEARTBEAT"); sys.exit(1)
print(f"  sys={m.target_system} comp={m.target_component} armed={'Y' if hb.base_mode & 0x80 else 'N'} mode={hb.custom_mode}")

# 先读当前值
def read_param(name, timeout=2.0):
    m.mav.param_request_read_send(m.target_system, m.target_component, name.encode(), -1)
    t0 = time.time()
    while time.time() - t0 < timeout:
        msg = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
        if msg is None: continue
        if msg.param_id.rstrip('\x00') == name:
            return msg.param_value
    return None

print("\n==> BEFORE:")
for name in TARGETS:
    v = read_param(name)
    print(f"  {name:20s} = {v}")

# 写参数
print("\n==> SET params...")
for name, val in TARGETS.items():
    m.mav.param_set_send(m.target_system, m.target_component,
                          name.encode(), float(val),
                          mavutil.mavlink.MAV_PARAM_TYPE_REAL32)
    # 等 ack（飞控会回 PARAM_VALUE 表示已经接受）
    t0 = time.time()
    acked = None
    while time.time() - t0 < 2.0:
        msg = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
        if msg is None: continue
        if msg.param_id.rstrip('\x00') == name:
            acked = msg.param_value
            break
    print(f"  {name:20s} -> {val}   ack={acked}")

# 重新读
print("\n==> AFTER:")
for name in TARGETS:
    v = read_param(name)
    flag = "✓" if v == TARGETS[name] else "✗"
    print(f"  {flag}  {name:20s} = {v}")

print("\n==> done. ArduPilot 通常自动持久化 PARAM_SET 到 EEPROM (FRAM)；下次重启依然生效。")
print("    如想立即生效到 SERVO 输出，建议飞控掉电重启一次（或我们后面用 MAV_CMD_PREFLIGHT_REBOOT_SHUTDOWN）。")
