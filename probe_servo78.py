"""读 frame/motor 配置 + 强制再发一组 RC override 看 servo7/8 反应。"""
import time, threading
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

# 关键参数
params = ["FRAME_CLASS", "FRAME_TYPE", "MOT_PWM_TYPE",
          "PILOT_STEER_TYPE", "MOT_SLEWRATE", "MOT_THR_MIN",
          "ATC_STR_RAT_FF", "ATC_STR_RAT_P", "ATC_SPEED_FF", "ATC_SPEED_P",
          "GCS_PID_MASK"]
for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

got = {}
deadline = time.time() + 3
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None:
        time.sleep(0.01); continue
    if msg.get_type() == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value

print("=== FRAME / MOTOR / ATC ===")
for p in params:
    print(f"  {p:18s} = {got.get(p)}")

# 切 MANUAL + ARM
m.mav.set_mode_send(m.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 0)
time.sleep(0.5)
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0,0,0,0,0,0)
time.sleep(1)

# 持续发 RC override + 同时读 servo
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

stop = False
def pub_rc(throttle_pwm, steering_pwm):
    while not stop:
        ch = [65535]*8
        ch[0] = steering_pwm
        ch[2] = throttle_pwm
        m.mav.rc_channels_override_send(m.target_system, m.target_component,
            *ch)
        time.sleep(0.05)

def snap(label, secs=1.0):
    deadline = time.time() + secs
    rec = []
    while time.time() < deadline:
        msg = m.recv_match(type="SERVO_OUTPUT_RAW", blocking=False)
        if msg:
            rec.append((msg.servo7_raw, msg.servo8_raw))
        time.sleep(0.02)
    if rec:
        # 取中间几个样本
        s7, s8 = rec[-1]
        print(f"  [{label}]  SERVO7(L)={s7}  SERVO8(R)={s8}  samples={len(rec)}")
    else:
        print(f"  [{label}]  NO SAMPLES")

print("\n=== 中位 (no override) 静止 2s ===")
time.sleep(2)
snap("静止")

print("=== 前进 throttle=1400, steering=1500 ===")
stop = False
th = threading.Thread(target=pub_rc, args=(1400, 1500), daemon=True); th.start()
time.sleep(2)
snap("前进")
stop = True; th.join(timeout=1)
time.sleep(0.5)

print("=== 左转 throttle=1500, steering=1400 ===")
stop = False
th = threading.Thread(target=pub_rc, args=(1500, 1400), daemon=True); th.start()
time.sleep(2)
snap("左转")
stop = True; th.join(timeout=1)
time.sleep(0.5)

# disarm
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0,0,0,0,0,0)

m.close()
print("done")
