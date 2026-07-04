"""发 cmd_vel 然后看 ArduPilot 的 SERVO_OUTPUT_RAW（实际输出到电机的 PWM）。"""
import time, threading
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

# 切 MANUAL + ARM（直接走 MAVLink，因为 chassis_bridge 没起）
m.mav.set_mode_send(m.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 0)
time.sleep(0.5)
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0,0,0,0,0,0)
time.sleep(1)

# 请求 SERVO_OUTPUT_RAW 流
m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

# 持续发 RC override 1500/1500，看 servo 怎么变
def pub_rc(throttle_pwm, steering_pwm, dur):
    """持续发 RC override。"""
    t0 = time.time()
    while time.time() - t0 < dur:
        ch = [65535]*8
        ch[0] = steering_pwm  # RC1
        ch[2] = throttle_pwm  # RC3
        m.mav.rc_channels_override_send(m.target_system, m.target_component,
            ch[0], ch[1], ch[2], ch[3], ch[4], ch[5], ch[6], ch[7])
        time.sleep(0.05)

def snap_servo(label):
    # 排队读 servo 输出
    deadline = time.time() + 1.0
    last = None
    while time.time() < deadline:
        msg = m.recv_match(type="SERVO_OUTPUT_RAW", blocking=False)
        if msg:
            last = msg
        time.sleep(0.01)
    if last:
        print(f"[{label}]  ch1={last.servo1_raw} ch2={last.servo2_raw} ch3={last.servo3_raw} ch4={last.servo4_raw}  "
              f"ch5={last.servo5_raw} ch6={last.servo6_raw} ch7={last.servo7_raw} ch8={last.servo8_raw}")

print("=== 1) 全中位 (steering=1500, throttle=1500) 2s ===")
th = threading.Thread(target=pub_rc, args=(1500, 1500, 3.0), daemon=True); th.start()
time.sleep(1.0)
snap_servo("中位")

print("=== 2) 前进 (steering=1500, throttle=1400) 2s ===")
th = threading.Thread(target=pub_rc, args=(1400, 1500, 3.0), daemon=True); th.start()
time.sleep(1.0)
snap_servo("前进")

print("=== 3) 左转 (steering=1400, throttle=1500) 2s ===")
th = threading.Thread(target=pub_rc, args=(1500, 1400, 3.0), daemon=True); th.start()
time.sleep(1.0)
snap_servo("左转")

print("=== 4) 右转 (steering=1600, throttle=1500) 2s ===")
th = threading.Thread(target=pub_rc, args=(1500, 1600, 3.0), daemon=True); th.start()
time.sleep(1.0)
snap_servo("右转")

# disarm
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0,0,0,0,0,0)

m.close()
print("done")
