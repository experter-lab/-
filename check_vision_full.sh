#!/usr/bin/env bash
# 抓 vision 完整 status, 看所有 metrics
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

python3 - <<'PYEOF'
import json, time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class G(Node):
    def __init__(self):
        super().__init__("vision_full_grab")
        self.msgs=[]; self.dets=[]
        self.create_subscription(String,"/medicine/drug_recognition_status",
                                 lambda m: self.msgs.append(json.loads(m.data)), 10)
        self.create_subscription(String,"/medicine/vision_detections",
                                 lambda m: self.dets.append(json.loads(m.data)), 10)

rclpy.init()
n=G()
t0=time.time()
# 收 5 秒数据
while time.time()-t0<5 and rclpy.ok():
    rclpy.spin_once(n,timeout_sec=0.5)

if not n.msgs:
    print("!! no status");
else:
    s=n.msgs[-1]
    print("=== 摄像头 ===")
    print(f"  ok={s.get('camera_ok')} {s.get('frame_width')}x{s.get('frame_height')} frame#{s.get('frame_count')}")
    print(f"  source={s.get('source')}")
    print(f"\n=== QR / 条码 ===")
    print(f"  attempt={s.get('qr_attempt_count')}  success={s.get('qr_success_count')}  skip={s.get('qr_skip_count')}")
    print(f"  candidate/帧={s.get('qr_candidate_count')}  period={s.get('qr_recognition_period_sec')}s")
    print(f"  backends={s.get('decoder_backends')}")
    print(f"  最后命中: text={s.get('qr_text','')[:80]}")
    print(f"           method={s.get('code_method')}  type={s.get('code_type')}")
    print(f"  external: 完成{s.get('external_decode_complete_count')}  超时{s.get('external_decode_timeout_count')}  busy{s.get('external_decode_busy_count')}")
    print(f"\n=== YOLO ===")
    print(f"  status={s.get('yolo_rknn_status')}  model_loaded={s.get('yolo_model_loaded')}")
    print(f"  inference={s.get('yolo_inference_ms'):.1f}ms  detection_count={s.get('yolo_detection_count')}")
    print(f"  attempt={s.get('yolo_attempt_count')}  success={s.get('yolo_success_count')}")
    # 最近一次 vision_detections payload
    if n.dets:
        d = n.dets[-1]
        print(f"\n=== 最近 vision_detections ({len(d.get('detections',[]))} 个对象) ===")
        for det in d.get('detections',[])[:5]:
            print(f"  label={det.get('label')}  conf={det.get('confidence',0):.2f}  bbox={det.get('bbox_xyxy')}")
    print(f"\n=== OCR ===")
    print(f"  enabled={s.get('ocr_enabled')}  available={s.get('ocr_available')}  text={s.get('ocr_text','')[:60]!r}")
    # 性能
    print(f"\n=== 预览 ===")
    print(f"  client_req={s.get('preview_client_request_count')}  encoding_active={s.get('preview_encoding_active')}")
n.destroy_node(); rclpy.shutdown()
PYEOF
