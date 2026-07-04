import rclpy, json
from std_msgs.msg import String
import time
rclpy.init()
n = rclpy.create_node("probe")
msgs = []
n.create_subscription(String, "/medicine/chassis_status", lambda m: msgs.append(m.data), 10)
t0 = time.time()
while time.time() - t0 < 3 and not msgs:
    rclpy.spin_once(n, timeout_sec=0.5)
if msgs:
    d = json.loads(msgs[-1])
    a = d.get("ardupilot", {})
    es = d.get("emergency_stop")
    ca = d.get("control_authorized")
    he = d.get("hardware_estop_detected")
    cm = a.get("custom_mode_name")
    bm = a.get("base_mode") or 0
    ss = a.get("system_status")
    hb = a.get("heartbeat_ok")
    print(f"emergency_stop     : {es}")
    print(f"control_authorized : {ca}")
    print(f"hardware_estop     : {he}")
    print(f"custom_mode_name   : {cm}  (custom_mode={a.get('custom_mode')})")
    print(f"base_mode (hex)    : 0x{bm:02x}  (ARMED bit 0x80 set={bool(bm & 0x80)})")
    print(f"system_status      : {ss}")
    print(f"heartbeat_ok       : {hb}  age={a.get('heartbeat_age_sec')}")
else:
    print("NO MESSAGES")
rclpy.shutdown()
