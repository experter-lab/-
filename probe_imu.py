"""探 ArduPilot IMU/EKF 状态：有没有可用 gyro/accel + EKF 是否健康。"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
print("waiting HB...")
m.wait_heartbeat(timeout=5)
print(f"  sys={m.target_system}")

# 请求 RAW_IMU + EKF_STATUS_REPORT + 一些 EK3 参数
params = ["AHRS_EKF_TYPE", "EK3_ENABLE", "EK2_ENABLE", "EK3_SRC1_POSXY", "EK3_SRC1_VELXY", "EK3_SRC1_POSZ", "EK3_SRC1_VELZ", "EK3_SRC1_YAW",
          "INS_USE", "INS_USE2", "INS_USE3", "COMPASS_USE", "COMPASS_USE2", "COMPASS_USE3",
          "GPS_TYPE"]
for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

# 让飞控发 EXTRA1 (RAW_IMU 在其中) 和 EXTRA2 (EKF) 流
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_RAW_SENSORS, 5, 1)
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_EXTRA1, 5, 1)
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_EXTRA2, 5, 1)

got_params = {}
raw_imu = None
ekf = None
attitude = None
texts = []

deadline = time.time() + 6
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None:
        time.sleep(0.01); continue
    t = msg.get_type()
    if t == "PARAM_VALUE":
        got_params[msg.param_id] = msg.param_value
    elif t == "RAW_IMU":
        raw_imu = msg
    elif t == "SCALED_IMU2":
        pass
    elif t == "EKF_STATUS_REPORT":
        ekf = msg
    elif t == "ATTITUDE":
        attitude = msg
    elif t == "STATUSTEXT":
        texts.append((msg.severity, msg.text))

print("\n=== PARAMS ===")
for p in params:
    v = got_params.get(p)
    print(f"  {p:18s} = {v}")

print("\n=== RAW_IMU ===")
if raw_imu:
    print(f"  xacc={raw_imu.xacc} yacc={raw_imu.yacc} zacc={raw_imu.zacc}")
    print(f"  xgyro={raw_imu.xgyro} ygyro={raw_imu.ygyro} zgyro={raw_imu.zgyro}")
    print(f"  xmag={raw_imu.xmag} ymag={raw_imu.ymag} zmag={raw_imu.zmag}")
else:
    print("  NO RAW_IMU received")

print("\n=== ATTITUDE ===")
if attitude:
    import math
    print(f"  roll={math.degrees(attitude.roll):.1f}deg pitch={math.degrees(attitude.pitch):.1f}deg yaw={math.degrees(attitude.yaw):.1f}deg")
    print(f"  yawspeed={math.degrees(attitude.yawspeed):.2f}deg/s")
else:
    print("  NO ATTITUDE received")

print("\n=== EKF_STATUS ===")
if ekf:
    print(f"  flags=0x{ekf.flags:04x}  velocity_variance={ekf.velocity_variance:.3f}  pos_horiz={ekf.pos_horiz_variance:.3f}  pos_vert={ekf.pos_vert_variance:.3f}")
    print(f"  compass_variance={ekf.compass_variance:.3f}  terrain={ekf.terrain_alt_variance:.3f}")
else:
    print("  NO EKF_STATUS_REPORT")

print(f"\n=== STATUSTEXT ({len(texts)}) ===")
for sev, text in texts[-10:]:
    print(f"  [sev={sev}] {text}")

m.close()
