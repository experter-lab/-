"""读 ArduPilot RC 通道 trim/min/max + servo 输出，定位 W=直行车却右转的原因。"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
print("waiting HB...")
m.wait_heartbeat(timeout=5)
print(f"  sys={m.target_system}")

params = [
    "RC1_MIN", "RC1_MAX", "RC1_TRIM", "RC1_REV", "RC1_DZ",
    "RC3_MIN", "RC3_MAX", "RC3_TRIM", "RC3_REV", "RC3_DZ",
    "SERVO1_MIN", "SERVO1_MAX", "SERVO1_TRIM", "SERVO1_REVERSED", "SERVO1_FUNCTION",
    "SERVO3_MIN", "SERVO3_MAX", "SERVO3_TRIM", "SERVO3_REVERSED", "SERVO3_FUNCTION",
    "RCMAP_THROTTLE", "RCMAP_ROLL", "RCMAP_PITCH", "RCMAP_YAW",
    "PILOT_STEER_TYPE",
]
for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

# 请求 SERVO_OUTPUT_RAW
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 5, 1)

got = {}
servo_raw = None
deadline = time.time() + 5
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None:
        time.sleep(0.01); continue
    t = msg.get_type()
    if t == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value
    elif t == "SERVO_OUTPUT_RAW":
        servo_raw = msg

print("\n=== RC1 (steering) ===")
for k in ["RC1_MIN", "RC1_MAX", "RC1_TRIM", "RC1_REV", "RC1_DZ"]:
    print(f"  {k:14s} = {got.get(k)}")
print("\n=== RC3 (throttle) ===")
for k in ["RC3_MIN", "RC3_MAX", "RC3_TRIM", "RC3_REV", "RC3_DZ"]:
    print(f"  {k:14s} = {got.get(k)}")
print("\n=== SERVO1 ===")
for k in ["SERVO1_MIN", "SERVO1_MAX", "SERVO1_TRIM", "SERVO1_REVERSED", "SERVO1_FUNCTION"]:
    print(f"  {k:18s} = {got.get(k)}")
print("\n=== SERVO3 ===")
for k in ["SERVO3_MIN", "SERVO3_MAX", "SERVO3_TRIM", "SERVO3_REVERSED", "SERVO3_FUNCTION"]:
    print(f"  {k:18s} = {got.get(k)}")
print("\n=== RCMAP / PILOT ===")
for k in ["RCMAP_THROTTLE", "RCMAP_ROLL", "RCMAP_PITCH", "RCMAP_YAW", "PILOT_STEER_TYPE"]:
    print(f"  {k:18s} = {got.get(k)}")

print("\n=== SERVO_OUTPUT_RAW (静止时实际 PWM 输出) ===")
if servo_raw:
    print(f"  ch1={servo_raw.servo1_raw} ch2={servo_raw.servo2_raw} ch3={servo_raw.servo3_raw} ch4={servo_raw.servo4_raw}")
    print(f"  ch5={servo_raw.servo5_raw} ch6={servo_raw.servo6_raw} ch7={servo_raw.servo7_raw} ch8={servo_raw.servo8_raw}")
else:
    print("  NO SERVO_OUTPUT_RAW")

m.close()
