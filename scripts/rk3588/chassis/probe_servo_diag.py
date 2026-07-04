#!/usr/bin/env python3
"""直接 MAVLink 抓 SERVO7/8 + 关键参数 + 强 throttle override 看电机/SERVO 是否响应。
独占串口前必须 kill chassis_bridge (systemd: sudo systemctl stop rk3588-chassis-bridge).
"""
import sys, time
from pymavlink import mavutil

PORT = "/dev/ttyS9"
BAUD = 921600

# invert_throttle=true 时 chassis_bridge 内部:
#   实际下发的 throttle_pwm = MID - (cmd_vel.linear.x / max_lin) * (MAX - MID)
# yaml: min=1300 mid=1500 max=1700  → 前进 max 时下发 1300
THROTTLE_PWM = 1300   # 全速前进
STEERING_PWM = 1500
RC_THROTTLE_CH = 3
RC_STEERING_CH = 1

print(f"==> connect {PORT}@{BAUD}")
m = mavutil.mavlink_connection(PORT, baud=BAUD, source_system=255, source_component=0)
hb = m.wait_heartbeat(timeout=5)
if not hb:
    print("NO HEARTBEAT"); sys.exit(1)
print(f"  armed={'Y' if hb.base_mode & 0x80 else 'N'} custom_mode={hb.custom_mode} status={hb.system_status}")

m.mav.request_data_stream_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_DATA_STREAM_ALL, 10, 1)
m.mav.request_data_stream_send(m.target_system, m.target_component,
                                mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

# 1s 中位喂熟,再 SET_MODE MANUAL
print("==> 1s 中位 RC override + SET_MODE→MANUAL + re-ARM")
t0 = time.time()
while time.time() - t0 < 1.0:
    chans = [65535]*8
    chans[RC_THROTTLE_CH-1] = 1500
    chans[RC_STEERING_CH-1] = 1500
    m.mav.rc_channels_override_send(m.target_system, m.target_component, *chans)
    time.sleep(0.1)

base_mode = mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED
if hb.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED:
    base_mode |= mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED
m.mav.set_mode_send(m.target_system, base_mode, 0)
time.sleep(0.3)

# 强制 ARM
m.mav.command_long_send(m.target_system, m.target_component,
                        mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM,
                        0, 1, 0, 0, 0, 0, 0, 0)
time.sleep(0.5)

for _ in range(10):
    msg = m.recv_match(type="HEARTBEAT", blocking=True, timeout=0.3)
    if msg:
        hb = msg
        if msg.custom_mode == 0 and (msg.base_mode & 0x80):
            print(f"  ✓ MANUAL+ARMED, base=0x{hb.base_mode:02x}")
            break
else:
    print(f"  ✗ 状态不对: cm={msg.custom_mode if msg else '?'} base={hex(msg.base_mode) if msg else '?'}")

# 抓 SYS_STATUS 一次 + 关键参数
sys_status_v = None
t0 = time.time()
while time.time() - t0 < 1.0:
    msg = m.recv_match(type="SYS_STATUS", blocking=True, timeout=0.3)
    if msg:
        sys_status_v = msg
        break

print()
print("=== SYS_STATUS ===")
if sys_status_v:
    print(f"  voltage_battery   : {sys_status_v.voltage_battery} mV  (这是飞控板自身 USB 取电)")
    print(f"  errors_count1     : {sys_status_v.errors_count1}")
    print(f"  sensors_health    : 0x{sys_status_v.onboard_control_sensors_health:08x}")

# 查 SERVO_FUNCTION + 输出范围 + ARMING + 电池
PARAMS = ["ARMING_CHECK", "ARMING_REQUIRE", "BRD_SAFETY_DEFLT", "BRD_SAFETYENABLE",
          "SERVO1_FUNCTION","SERVO3_FUNCTION","SERVO7_FUNCTION","SERVO8_FUNCTION",
          "SERVO1_MIN","SERVO1_MAX","SERVO1_TRIM",
          "SERVO3_MIN","SERVO3_MAX","SERVO3_TRIM",
          "SERVO7_MIN","SERVO7_MAX","SERVO7_TRIM",
          "SERVO8_MIN","SERVO8_MAX","SERVO8_TRIM",
          "MOT_PWM_TYPE","MOT_SAFE_DISARM",
          "FRAME_CLASS","FRAME_TYPE",
          "MOT_THR_MIN","MOT_THR_MAX",
          "FS_THR_ENABLE","FS_THR_VALUE","FS_ACTION","FS_GCS_ENABLE",
          "RC1_MIN","RC1_MAX","RC1_TRIM",
          "RC3_MIN","RC3_MAX","RC3_TRIM",
          "BATT_LOW_VOLT","BATT_MONITOR",
          "DISARM_DELAY"]
print()
print("=== fetch key params ===")
for p in PARAMS:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode(), -1)
got = {}
t0 = time.time()
while time.time() - t0 < 4 and len(got) < len(PARAMS):
    msg = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
    if msg is None: continue
    name = msg.param_id.rstrip('\x00')
    if name in PARAMS and name not in got:
        got[name] = msg.param_value
for p in PARAMS:
    v = got.get(p, "(no reply)")
    print(f"  {p:20s} = {v}")

# 现在边发强 throttle override 边看 SERVO_OUTPUT_RAW
ch_raw = [None]*8
servo_raw = [None]*8

def send_override(throttle, steering):
    chans = [65535]*8
    chans[RC_THROTTLE_CH-1] = throttle
    chans[RC_STEERING_CH-1] = steering
    m.mav.rc_channels_override_send(m.target_system, m.target_component, *chans)

print()
print(f"==> 6s 全速前进: throttle={THROTTLE_PWM} steering={STEERING_PWM}")
print("    time   CH1   CH3      SERVO1 SERVO3 SERVO7 SERVO8   mode armed")
t_start = time.time()
last_send = 0
last_print = 0
while time.time() - t_start < 6.0:
    now = time.time()
    if now - last_send >= 0.1:
        send_override(THROTTLE_PWM, STEERING_PWM)
        last_send = now
    msg = m.recv_match(blocking=True, timeout=0.05)
    if msg is not None:
        t = msg.get_type()
        if t == "RC_CHANNELS":
            for i in range(1, 9):
                ch_raw[i-1] = getattr(msg, f"chan{i}_raw", None)
        elif t == "SERVO_OUTPUT_RAW":
            for i in range(1, 9):
                servo_raw[i-1] = getattr(msg, f"servo{i}_raw", None)
        elif t == "HEARTBEAT":
            hb = msg
    if now - last_print >= 0.4:
        last_print = now
        print(f"  {now-t_start:5.2f}  {ch_raw[0]} {ch_raw[2]}     "
              f"{servo_raw[0]}  {servo_raw[2]}  {servo_raw[6]}  {servo_raw[7]}    "
              f"cm={hb.custom_mode if hb else '?'} "
              f"armed={'Y' if hb and (hb.base_mode & 0x80) else 'N'}")

print()
print("==> release override")
m.mav.rc_channels_override_send(m.target_system, m.target_component, 0,0,0,0,0,0,0,0)
time.sleep(0.3)
print("done")
