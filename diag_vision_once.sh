#!/usr/bin/env bash
# 一次性诊断: 启动 vision 节点, 抓两帧 status 统计帧率/识别情况, 然后 kill。不留常驻进程。
source /opt/ros/humble/setup.bash
source /mnt/sdcard/medicine_robot_ws/install/setup.bash

PARAMS=/mnt/sdcard/medicine_robot_data/config/current_vision_config.yaml
LOG=/tmp/vision_diag.log

echo "==> params: $(readlink -f $PARAMS)"
pkill -f drug_info_detector_node 2>/dev/null
sleep 1

echo "==> 启动 vision 节点 (后台)"
nohup ros2 run medicine_vision_detector drug_info_detector_node \
  --ros-args --params-file "$PARAMS" > "$LOG" 2>&1 &
NODE_PID=$!
echo "    PID=$NODE_PID, 等 14s 让摄像头打开 + YOLO 模型加载..."
sleep 14

python3 - <<'PYEOF'
import json, time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

KEYS = ["camera_ok","last_camera_error","frame_count","frame_width","frame_height",
        "input_mode","source",
        "qr_enabled","qr_attempt_count","qr_success_count","qr_skip_count",
        "qr_candidate_count","qr_detected","qr_decode_failed","qr_text","last_qr_error",
        "decoder_backends","external_decode_attempt_count","external_decode_complete_count",
        "external_decode_timeout_count","external_decode_busy_count",
        "yolo_rknn_enabled","yolo_rknn_status","yolo_model_loaded","yolo_inference_ms",
        "yolo_detection_count","yolo_attempt_count","yolo_success_count","yolo_error"]

class Grab(Node):
    def __init__(self):
        super().__init__("vision_diag_grab")
        self.msgs=[]
        self.sub=self.create_subscription(String,"/medicine/drug_recognition_status",self.cb,10)
    def cb(self,m):
        try: self.msgs.append(json.loads(m.data))
        except: pass

rclpy.init()
n=Grab()
t0=time.time()
frame_a=None; fa_t=0.0
while time.time()-t0<10 and rclpy.ok():
    rclpy.spin_once(n,timeout_sec=0.5)
    if n.msgs and frame_a is None:
        frame_a=n.msgs[-1]; fa_t=time.time()
        print("=== 第1帧 status ===")
        for k in KEYS: print(f"  {k} = {frame_a.get(k)}")
        break
n.msgs.clear()
t1=time.time()
frame_b=None; fb_t=0.0
while time.time()-t1<8 and rclpy.ok():
    rclpy.spin_once(n,timeout_sec=0.5)
    if n.msgs:
        frame_b=n.msgs[-1]; fb_t=time.time(); break
if frame_a and frame_b:
    df=frame_b.get("frame_count",0)-frame_a.get("frame_count",0)
    dt=fb_t-fa_t
    print(f"\n=== 帧率: {df} 帧 / {dt:.1f}s = {df/dt if dt>0 else 0:.1f} fps ===")
    print(f"  qr_success 增量 = {frame_b.get('qr_success_count',0)-frame_a.get('qr_success_count',0)}")
    print(f"  qr_attempt 增量 = {frame_b.get('qr_attempt_count',0)-frame_a.get('qr_attempt_count',0)}")
    print(f"  yolo_success 增量 = {frame_b.get('yolo_success_count',0)-frame_a.get('yolo_success_count',0)}")
    print(f"  yolo_inference_ms = {frame_b.get('yolo_inference_ms')}")
elif not frame_a:
    print("!! 没收到任何 status 消息 — 节点可能崩了, 看下面日志")
n.destroy_node(); rclpy.shutdown()
PYEOF

echo
echo "==> kill vision 节点"
kill $NODE_PID 2>/dev/null; sleep 1; kill -9 $NODE_PID 2>/dev/null
pkill -f drug_info_detector_node 2>/dev/null

echo
echo "==> vision 日志尾部 (看 camera/YOLO 报错):"
tail -25 "$LOG"
