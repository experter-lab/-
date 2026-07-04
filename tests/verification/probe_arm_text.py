"""检查 BRD_SAFETY / Arming / 看看 status text 在 ARM 时报什么"""
import time
from pymavlink import mavutil

m = mavutil.mavlink_connection("/dev/ttyS9", baud=921600, source_system=254)
m.wait_heartbeat(timeout=5)

params = ["BRD_SAFETY_DEFLT", "BRD_SAFETYENABLE", "BRD_SAFETY_MASK",
          "ARMING_CHECK", "ARMING_RUDDER", "ARMING_MAGTHRESH",
          "SCHED_DEBUG", "GCS_PID_MASK", "LOG_BITMASK"]
for p in params:
    m.mav.param_request_read_send(m.target_system, m.target_component, p.encode("ascii"), -1)

got = {}
texts = []

# 同步监听 STATUSTEXT 8 秒
deadline = time.time() + 3
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None: time.sleep(0.01); continue
    t = msg.get_type()
    if t == "PARAM_VALUE":
        got[msg.param_id] = msg.param_value
    elif t == "STATUSTEXT":
        texts.append((msg.severity, msg.text))

print("=== BRD_SAFETY / ARMING ===")
for p in params:
    print(f"  {p:20s} = {got.get(p)}")

print("\n=== 现在试 ARM 看 STATUSTEXT ===")
texts.clear()
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 1, 0,0,0,0,0,0)

deadline = time.time() + 5
while time.time() < deadline:
    msg = m.recv_match(blocking=False)
    if msg is None: time.sleep(0.01); continue
    t = msg.get_type()
    if t == "STATUSTEXT":
        texts.append((msg.severity, msg.text))
    elif t == "COMMAND_ACK":
        if msg.command == mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM:
            ACK = {0:"ACCEPTED", 4:"FAILED", 5:"IN_PROGRESS", 6:"CANCELLED"}.get(msg.result, str(msg.result))
            print(f"  ARM ACK: {ACK}")

print(f"\n=== STATUSTEXT ({len(texts)}) ===")
for sev, text in texts:
    print(f"  [sev={sev}] {text}")

# disarm
m.mav.command_long_send(m.target_system, m.target_component,
    mavutil.mavlink.MAV_CMD_COMPONENT_ARM_DISARM, 0, 0, 0,0,0,0,0,0)
m.close()
