import rclpy, json, time
from std_msgs.msg import String
rclpy.init()
n = rclpy.create_node("p")
msgs = []
n.create_subscription(String, "/medicine/chassis_status", lambda m: msgs.append(m.data), 10)
t0 = time.time()
while time.time() - t0 < 2 and not msgs:
    rclpy.spin_once(n, timeout_sec=0.3)
d = json.loads(msgs[-1])
a = d["ardupilot"]
rc = a["rc_override"]
print(f"cmd_count          = {d['cmd_count']}")
print(f"cmd_age_sec        = {d['cmd_age_sec']:.2f}  timed_out={d['cmd_timed_out']}")
print(f"target_linear      = {d['target_linear']:+.3f}")
print(f"current_linear     = {d['current_linear']:+.3f}")
print(f"last_throttle_pwm  = {rc['last_throttle_pwm']}  (mid=1500)")
print(f"last_steering_pwm  = {rc['last_steering_pwm']}")
print(f"vfr_hud.throttle   = {a['vfr_hud']['throttle']}  (ArduPilot 实际输出 %)")
rclpy.shutdown()
