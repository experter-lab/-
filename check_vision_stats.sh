#!/usr/bin/env bash
# 抓一次 vision status, 不重启节点
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

python3 - <<'PYEOF'
import json, time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

KEYS = ["camera_ok","frame_count","qr_attempt_count","qr_success_count",
        "qr_candidate_count","qr_detected","qr_text","code_text","code_type","code_method",
        "raw_code_text","label_fields",
        "external_decode_complete_count","external_decode_timeout_count",
        "yolo_rknn_status","yolo_inference_ms","yolo_detection_count",
        "yolo_attempt_count","yolo_success_count","yolo_detections"]

class G(Node):
    def __init__(self):
        super().__init__("vision_stats_grab")
        self.msgs=[]
        self.create_subscription(String,"/medicine/drug_recognition_status",
                                 lambda m: self.msgs.append(json.loads(m.data)), 10)

rclpy.init()
n=G()
t0=time.time()
while time.time()-t0<6 and not n.msgs and rclpy.ok():
    rclpy.spin_once(n,timeout_sec=0.5)
if not n.msgs:
    print("!! 没收到 status — 节点可能没在跑")
else:
    s=n.msgs[-1]
    for k in KEYS: print(f"  {k} = {s.get(k)}")
n.destroy_node(); rclpy.shutdown()
PYEOF
