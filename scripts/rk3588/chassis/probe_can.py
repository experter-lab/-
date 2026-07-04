"""读 CAN / DroneCAN / I2C ESC 等参数，看电机是不是走 CAN。"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

# 各种"非 PWM"电机驱动协议
params = [
    "CAN_D1_PROTOCOL", "CAN_D2_PROTOCOL",
    "CAN_P1_DRIVER", "CAN_P2_DRIVER",
    "CAN_P1_BITRATE", "CAN_P2_BITRATE",
    "DRONECAN_NODE", "DRONECAN_OPTION",
    "MOT_PWM_TYPE",  # 0=Normal PWM, 1=OneShot, ..., 4=DShot150, ...
    "SERVO_BLH_AUTO", "SERVO_BLH_MASK",
    "RC_OPTIONS",
    "BRD_PWM_COUNT",
]
for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

got = {}
deadline = time.time() + 4
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None: time.sleep(0.01); continue
    if msg.get_type() == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value

print("=== CAN / DroneCAN / 电机驱动 ===")
for p in params:
    print(f"  {p:24s} = {got.get(p)}")

m.close()
