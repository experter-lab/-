"""读 SERVO7/8 是什么用途，以及看看 RCMAP_THROTTLE=3 / ROLL=1 走通到哪儿。"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

params = []
for i in range(1, 9):
    params += [f"SERVO{i}_FUNCTION", f"SERVO{i}_MIN", f"SERVO{i}_MAX", f"SERVO{i}_TRIM", f"SERVO{i}_REVERSED"]

for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

got = {}
deadline = time.time() + 4
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None:
        time.sleep(0.01); continue
    if msg.get_type() == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value

# ArduPilot SERVO_FUNCTION 值对照（常见）
SF = {
    0: "Disabled", 1: "RCPassThru", 26: "GroundSteering", 70: "Throttle",
    73: "ThrottleLeft", 74: "ThrottleRight", 75: "TiltMotorsFront",
    33: "Motor1", 34: "Motor2", 35: "Motor3", 36: "Motor4",
    51: "RCIN1", 52: "RCIN2", 53: "RCIN3", 54: "RCIN4",
    55: "RCIN5", 56: "RCIN6", 57: "RCIN7", 58: "RCIN8",
}

print("=== SERVO 通道映射 ===")
print(f"{'CH':4s} {'FUNCTION':30s} {'MIN':6s} {'MAX':6s} {'TRIM':6s} {'REV':4s}")
for i in range(1, 9):
    fn = int(got.get(f"SERVO{i}_FUNCTION", -1))
    name = SF.get(fn, f"id={fn}")
    print(f"{i:<4d} {name:30s} "
          f"{int(got.get(f'SERVO{i}_MIN',0)):6d} "
          f"{int(got.get(f'SERVO{i}_MAX',0)):6d} "
          f"{int(got.get(f'SERVO{i}_TRIM',0)):6d} "
          f"{int(got.get(f'SERVO{i}_REVERSED',0)):4d}")

m.close()
