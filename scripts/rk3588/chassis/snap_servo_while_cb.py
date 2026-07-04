"""chassis_bridge 在跑 + cmd_vel 在发时，直接看 ArduPilot 的 SERVO_OUTPUT_RAW + RC_CHANNELS"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=253)
m.wait_heartbeat(timeout=5)
print(f"sys={m.target_system} mode={m.mode_mapping().get(m.flightmode)}")

# 请求 RC_CHANNELS + SERVO_OUTPUT_RAW 流
m.mav.request_data_stream_send(m.target_system, m.target_component, mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

# 收 3 秒样本
got_rc = []
got_servo = []
deadline = time.time() + 4
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None: time.sleep(0.01); continue
    t = msg.get_type()
    if t == "RC_CHANNELS":
        got_rc.append((msg.chan1_raw, msg.chan2_raw, msg.chan3_raw, msg.chan4_raw))
    elif t == "SERVO_OUTPUT_RAW":
        got_servo.append((msg.servo7_raw, msg.servo8_raw))
    elif t == "HEARTBEAT":
        pass

print(f"\nRC_CHANNELS samples: {len(got_rc)}")
if got_rc:
    ch1, ch2, ch3, ch4 = got_rc[-1]
    print(f"  last: ch1={ch1} ch2={ch2} ch3={ch3} ch4={ch4}")
    uniq = set(got_rc)
    if len(uniq) == 1:
        print(f"  ALL SAME: {list(uniq)[0]}")
    else:
        print(f"  unique values: {sorted(uniq)}")

print(f"\nSERVO_OUTPUT_RAW samples: {len(got_servo)}")
if got_servo:
    s7, s8 = got_servo[-1]
    print(f"  last: servo7(L)={s7} servo8(R)={s8}")
    uniq = set(got_servo)
    if len(uniq) == 1:
        print(f"  ALL SAME: {list(uniq)[0]}")
    else:
        print(f"  unique values: {sorted(uniq)}")
else:
    print("  NO SAMPLES")

m.close()
