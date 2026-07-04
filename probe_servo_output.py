#!/usr/bin/env python3
"""直接连飞控 MAVLink，抓 SERVO_OUTPUT_RAW + 关键参数。
跳过 chassis_bridge，独占串口前需先 kill chassis_bridge_node。"""
import sys, time
from pymavlink import mavutil

PORT = "/dev/ttyS9"
BAUD = 921600

print(f"==> connect {PORT}@{BAUD}")
m = mavutil.mavlink_connection(PORT, baud=BAUD, source_system=254, source_component=0)

print("==> wait heartbeat (5s)")
hb = m.wait_heartbeat(timeout=5)
if not hb:
    print("NO HEARTBEAT"); sys.exit(1)
print(f"  sys={m.target_system} comp={m.target_component} type={hb.type} ap={hb.autopilot}")
print(f"  base_mode=0x{hb.base_mode:02x} (ARMED={'Y' if hb.base_mode & 0x80 else 'N'})")
print(f"  custom_mode={hb.custom_mode} system_status={hb.system_status}")

# 请求 SERVO_OUTPUT_RAW 5Hz
print("==> request SERVO_OUTPUT_RAW & RC_CHANNELS @5Hz")
for stream in (mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS,
               mavutil.mavlink.MAV_DATA_STREAM_ALL):
    m.mav.request_data_stream_send(m.target_system, m.target_component,
                                    stream, 5, 1)

# 抓 6 秒数据
print("==> watching messages 6s ...")
t0 = time.time()
servo_raw = None
rc_in = None
sys_status = None
while time.time() - t0 < 6:
    msg = m.recv_match(blocking=True, timeout=0.5)
    if msg is None: continue
    t = msg.get_type()
    if t == "SERVO_OUTPUT_RAW":
        servo_raw = msg
    elif t == "RC_CHANNELS":
        rc_in = msg
    elif t == "SYS_STATUS":
        sys_status = msg

print()
print("=== SERVO_OUTPUT_RAW (飞控 → 电机/舵机口的真实 PWM) ===")
if servo_raw is None:
    print("  *** 没收到 SERVO_OUTPUT_RAW! 通道未启用或飞控固件不发 ***")
else:
    for i in range(1, 9):
        pwm = getattr(servo_raw, f"servo{i}_raw", None)
        print(f"  SERVO{i}: {pwm}")

print()
print("=== RC_CHANNELS (飞控当前 RC 输入,含 override) ===")
if rc_in is None:
    print("  (没收到)")
else:
    for i in range(1, 9):
        pwm = getattr(rc_in, f"chan{i}_raw", None)
        print(f"  CH{i}: {pwm}")
    print(f"  rssi: {rc_in.rssi}")

print()
print("=== SYS_STATUS ===")
if sys_status:
    print(f"  voltage_battery: {sys_status.voltage_battery} mV")
    print(f"  current_battery: {sys_status.current_battery} cA")
    print(f"  battery_remaining: {sys_status.battery_remaining}%")
    print(f"  onboard_sensors_present : 0x{sys_status.onboard_control_sensors_present:08x}")
    print(f"  onboard_sensors_enabled : 0x{sys_status.onboard_control_sensors_enabled:08x}")
    print(f"  onboard_sensors_health  : 0x{sys_status.onboard_control_sensors_health:08x}")
    print(f"  errors_count1: {sys_status.errors_count1}")

# 查关键参数
print()
print("=== fetch key params ===")
PARAMS = ["ARMING_CHECK","ARMING_REQUIRE","MOT_PWM_TYPE","FRAME_CLASS","FRAME_TYPE",
          "SERVO1_FUNCTION","SERVO2_FUNCTION","SERVO3_FUNCTION","SERVO4_FUNCTION",
          "SERVO5_FUNCTION","SERVO6_FUNCTION","SERVO7_FUNCTION","SERVO8_FUNCTION",
          "RC1_MIN","RC1_MAX","RC3_MIN","RC3_MAX",
          "FS_THR_ENABLE","FS_THR_VALUE","FS_ACTION","BRD_SAFETYENABLE",
          "PILOT_STEER_TYPE"]
for p in PARAMS:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode(), -1)
got = {}
t0 = time.time()
while time.time() - t0 < 3 and len(got) < len(PARAMS):
    msg = m.recv_match(type="PARAM_VALUE", blocking=True, timeout=0.3)
    if msg is None: continue
    name = msg.param_id.rstrip('\x00')
    if name in PARAMS and name not in got:
        got[name] = msg.param_value
for p in PARAMS:
    v = got.get(p, "(no reply)")
    print(f"  {p:20s} = {v}")
