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
print("=== full ardupilot dict ===")
print(json.dumps(a, indent=2, default=str))
rclpy.shutdown()
