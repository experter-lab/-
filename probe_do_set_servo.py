"""绕过控制器，直接用 MAV_CMD_DO_SET_SERVO 强制 servo7/8 输出 PWM。"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

# 切 MANUAL + ARM
m.mav.set_mode_send(m.target_system,
    mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 0)
time.sleep(0.5)
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0,0,0,0,0,0)
time.sleep(1)

m.mav.request_data_stream_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_DATA_STREAM_RC_CHANNELS, 10, 1)

def set_servo(channel, pwm):
    """MAV_CMD_DO_SET_SERVO: 强制 servo 输出 PWM。"""
    m.mav.command_long_send(m.target_system, m.target_component,
        mavutil.mavlink.MAV_CMD_DO_SET_SERVO, 0,
        channel, pwm, 0, 0, 0, 0, 0)

def snap(label, secs=0.8):
    deadline = time.time() + secs
    last = None
    while time.time() < deadline:
        msg = m.recv_match(type="SERVO_OUTPUT_RAW", blocking=False)
        if msg: last = msg
        time.sleep(0.02)
    if last:
        print(f"  [{label}]  SERVO7={last.servo7_raw} SERVO8={last.servo8_raw}")

print("=== DO_SET_SERVO 7=1600, 8=1600 (左轮 + 右轮都正向慢速 100us) ===")
for _ in range(20):
    set_servo(7, 1600)
    set_servo(8, 1600)
    time.sleep(0.1)
snap("set7=1600 set8=1600")

print("=== 停 (回到 1500) ===")
for _ in range(10):
    set_servo(7, 1500)
    set_servo(8, 1500)
    time.sleep(0.1)
snap("回 1500")

m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0,0,0,0,0,0)
m.close()
print("done")
