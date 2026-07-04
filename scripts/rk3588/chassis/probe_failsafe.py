"""直接连 /dev/ttyS9 用 pymavlink 拿 ArduPilot 的 STATUSTEXT + FS_* 参数。
本地连 ArduPilot 会和 chassis_bridge 抢串口，所以先停 chassis_bridge。
"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
print("waiting heartbeat...")
hb = m.wait_heartbeat(timeout=5)
print(f"HB: sys={m.target_system} comp={m.target_component} type={hb.type} mode={hb.custom_mode} status={hb.system_status}")

# 读相关 FS 参数 + ARMING_CHECK
params_to_read = [
    "FS_THR_ENABLE", "FS_THR_VALUE",
    "FS_ACTION", "FS_TIMEOUT",
    "FS_EKF_ACTION", "FS_EKF_THRESH",
    "FS_GCS_ENABLE", "FS_GCS_TIMEOUT",
    "FS_CRASH_CHECK", "FS_DRIVER_ENABLE",
    "ARMING_CHECK", "ARMING_REQUIRE",
    "RCMAP_THROTTLE", "RCMAP_ROLL",
    "MODE1", "MODE_CH",
    "MOT_THR_MIN", "MOT_SAFE_DISARM",
]

print("\nrequesting params...")
for p in params_to_read:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

# 监听 PARAM_VALUE + STATUSTEXT 5 秒
got = {}
texts = []
deadline = time.time() + 5
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None:
        time.sleep(0.01); continue
    t = msg.get_type()
    if t == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value
    elif t == "STATUSTEXT":
        texts.append((msg.severity, msg.text))

print("\n=== PARAMS ===")
for p in params_to_read:
    v = got.get(p)
    print(f"  {p:24s} = {v}")

print(f"\n=== STATUSTEXT ({len(texts)}) ===")
for sev, text in texts[-20:]:
    print(f"  [sev={sev}] {text}")

m.close()
