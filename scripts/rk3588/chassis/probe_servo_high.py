"""读 SERVO9-16 的 function。"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

# H743 板子可能有 SERVO9-16
params = []
for i in range(1, 17):
    params += [f"SERVO{i}_FUNCTION"]

for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

got = {}
deadline = time.time() + 5
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None:
        time.sleep(0.01); continue
    if msg.get_type() == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value

# ArduPilot SERVO_FUNCTION 参考
SF = {
    -1: "未配置", 0: "Disabled",
    26: "GroundSteering", 70: "Throttle",
    73: "ThrottleLeft", 74: "ThrottleRight",
    33: "Motor1", 34: "Motor2", 35: "Motor3", 36: "Motor4",
}

print(f"{'CH':6s} {'FUNCTION':30s}")
for i in range(1, 17):
    fn = got.get(f"SERVO{i}_FUNCTION")
    if fn is None:
        continue  # 不存在的通道
    fni = int(fn)
    name = SF.get(fni, f"id={fni}")
    print(f"SERVO{i:<2d} {name}")

m.close()
